"""
arXiv Semantic Search System - Python Version
Powered by arXiv API + Google Gemini Interactions API
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import pikepdf
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
ARXIV_API_BASE = 'http://export.arxiv.org/api/query'
MAX_ARXIV_RESULTS = 20
TOP_N_RESULTS = 5
GEMINI_MODEL = 'gemini-2.5-flash'
MAX_PDF_PAGES = 50  # Maximum allowed pages for PDFs
PAGE_CHECK_WORKERS = 5  # Number of parallel workers for page checking (faster!)

# Validate API key
if not GEMINI_API_KEY:
    print('❌ Error: GEMINI_API_KEY not found in .env file')
    print('Please add to .env file: GEMINI_API_KEY=your_api_key_here')
    exit(1)

# Initialize Gemini AI Client
client = genai.Client(api_key=GEMINI_API_KEY)


def refine_user_query(user_query: str, user_context: str = '') -> Dict[str, Any]:
    """
    Step 1: Refine user query using Gemini (optimized for speed)
    """
    print('\n🔍 Step 1: Refining user query with Gemini...')
    print(f'   Original query: "{user_query}"')
    
    # Optimized prompt - more concise
    prompt = f"""Refine this arXiv search query.

Query: "{user_query}"
{f'Context: {user_context}' if user_context else ''}

Create optimized arXiv query with operators (ti:, abs:, cat:, all:).
Identify 3-5 key concepts and brief focus statement.

Output JSON: {{"refined_query": "...", "key_concepts": ["..."], "search_focus": "...", "additional_filters": {{"categories": ["..."], "date_range": "..."}}}}"""

    try:
        # Use structured output for faster processing
        response_schema = {
            "type": "object",
            "properties": {
                "refined_query": {"type": "string"},
                "key_concepts": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "search_focus": {"type": "string"},
                "additional_filters": {
                    "type": "object",
                    "properties": {
                        "categories": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "date_range": {"type": "string"}
                    }
                }
            },
            "required": ["refined_query", "key_concepts", "search_focus"]
        }
        
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": response_schema
            }
        )
        
        # Direct JSON parsing (faster with structured output)
        refined_data = json.loads(response.text)
        
        print('   ✓ Query refined successfully!')
        print(f'   Refined query: "{refined_data["refined_query"]}"')
        print(f'   Key concepts: {", ".join(refined_data["key_concepts"])}')
        print(f'   Focus: {refined_data["search_focus"]}')
        
        return refined_data
    
    except Exception as error:
        print(f'   ✗ Error refining query: {error}')
        # Fallback to original query
        return {
            'refined_query': f'all:{user_query}',
            'key_concepts': [user_query],
            'search_focus': 'General search',
            'additional_filters': {}
        }


def check_pdf_page_count(pdf_url: str, timeout: int = 15) -> Optional[int]:
    """
    Check the number of pages in a PDF
    
    Args:
        pdf_url: URL to the PDF
        timeout: Request timeout in seconds
    
    Returns:
        Number of pages, or None if error
    """
    try:
        # Download PDF with timeout
        response = requests.get(pdf_url, timeout=timeout)
        response.raise_for_status()
        
        # Load PDF into memory buffer
        pdf_buffer = io.BytesIO(response.content)
        
        # Check page count with pikepdf
        with pikepdf.open(pdf_buffer) as pdf:
            num_pages = len(pdf.pages)
            return num_pages
    
    except requests.Timeout:
        return None
    except requests.RequestException:
        return None
    except Exception:
        return None


def check_single_paper(paper: Dict[str, Any], max_pages: int) -> Dict[str, Any]:
    """
    Check a single paper's page count and return result
    
    Args:
        paper: Paper dictionary
        max_pages: Maximum allowed pages
    
    Returns:
        Dict with paper and status info
    """
    pdf_url = paper['pdf_link']
    arxiv_id = paper['arxiv_id']
    
    page_count = check_pdf_page_count(pdf_url)
    
    result = {
        'paper': paper,
        'arxiv_id': arxiv_id,
        'page_count': page_count,
        'included': False,
        'reason': ''
    }
    
    if page_count is None:
        # If we can't check, include it (benefit of doubt)
        paper['page_count'] = 'Unknown'
        result['included'] = True
        result['reason'] = 'Unknown (included)'
    elif page_count <= max_pages:
        paper['page_count'] = page_count
        result['included'] = True
        result['reason'] = f'✅ {page_count} pages'
    else:
        paper['page_count'] = page_count
        result['included'] = False
        result['reason'] = f'❌ {page_count} pages (excluded)'
    
    return result


def filter_papers_by_page_count(papers: List[Dict[str, Any]], max_pages: int = MAX_PDF_PAGES, max_workers: int = PAGE_CHECK_WORKERS) -> tuple:
    """
    Filter papers to only include those with <= max_pages (parallel processing)
    
    Args:
        papers: List of paper dictionaries
        max_pages: Maximum allowed pages
        max_workers: Number of concurrent threads
    
    Returns:
        Tuple of (filtered_papers, excluded_papers)
    """
    print(f'\n📄 Checking PDF page counts (max: {max_pages} pages) - using {max_workers} parallel workers...')
    print(f'   Processing {len(papers)} papers...\n')
    
    filtered_papers = []
    excluded_papers = []
    
    # Process papers concurrently
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_paper = {
            executor.submit(check_single_paper, paper, max_pages): paper 
            for paper in papers
        }
        
        # Process results as they complete
        completed = 0
        for future in as_completed(future_to_paper):
            completed += 1
            try:
                result = future.result()
                
                # Print progress
                print(f'   [{completed}/{len(papers)}] {result["arxiv_id"]} - {result["reason"]}')
                
                if result['included']:
                    filtered_papers.append(result['paper'])
                else:
                    excluded_papers.append(result['paper'])
                    
            except Exception as exc:
                paper = future_to_paper[future]
                print(f'   [{completed}/{len(papers)}] {paper["arxiv_id"]} - ⚠️  Error: {exc}')
                # Include on error (benefit of doubt)
                paper['page_count'] = 'Error'
                filtered_papers.append(paper)
    
    print(f'\n   ✅ {len(filtered_papers)} papers kept')
    print(f'   ❌ {len(excluded_papers)} papers excluded (too long)')
    
    return filtered_papers, excluded_papers


def search_arxiv(refined_query: Dict[str, Any], max_results: int = MAX_ARXIV_RESULTS) -> List[Dict[str, Any]]:
    """
    Step 2: Search arXiv API with refined query
    """
    print(f'\n📚 Step 2: Searching arXiv for {max_results} papers...')
    
    params = {
        'search_query': refined_query['refined_query'],
        'start': 0,
        'max_results': max_results,
        'sortBy': 'relevance',
        'sortOrder': 'descending'
    }
    
    try:
        response = requests.get(ARXIV_API_BASE, params=params)
        response.raise_for_status()
        
        # Parse XML response
        root = ET.fromstring(response.content)
        
        # Define namespaces
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        
        # Extract entries
        entries = root.findall('atom:entry', namespaces)
        
        # Filter out error entries
        papers = []
        for index, entry in enumerate(entries, 1):
            entry_id = entry.find('atom:id', namespaces).text
            
            # Skip error entries
            if 'api/errors' in entry_id:
                continue
            
            # Extract arXiv ID from URL
            arxiv_id = entry_id.split('/abs/')[-1]
            
            # Extract authors
            authors = entry.findall('atom:author', namespaces)
            author_names = ', '.join([a.find('atom:name', namespaces).text for a in authors])
            
            # Extract categories
            categories = [cat.get('term') for cat in entry.findall('atom:category', namespaces)]
            
            # Get primary category
            primary_cat = entry.find('arxiv:primary_category', namespaces)
            primary_category = primary_cat.get('term') if primary_cat is not None else (categories[0] if categories else '')
            
            # Extract other fields
            title = entry.find('atom:title', namespaces).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', namespaces).text.strip().replace('\n', ' ')
            published = entry.find('atom:published', namespaces).text
            updated = entry.find('atom:updated', namespaces).text
            
            paper = {
                'index': index,
                'title': title,
                'authors': author_names,
                'arxiv_id': arxiv_id,
                'summary': summary,
                'published': published,
                'updated': updated,
                'categories': categories,
                'primary_category': primary_category,
                'pdf_link': f'http://arxiv.org/pdf/{arxiv_id}',
                'abstract_link': f'http://arxiv.org/abs/{arxiv_id}'
            }
            
            papers.append(paper)
        
        print(f'   ✓ Found {len(papers)} papers from arXiv')
        return papers
    
    except Exception as error:
        print(f'   ✗ Error searching arXiv: {error}')
        raise error


def rank_papers_with_gemini(
    papers: List[Dict[str, Any]], 
    original_query: str, 
    refined_query: Dict[str, Any], 
    top_n: int = TOP_N_RESULTS
) -> Dict[str, Any]:
    """
    Step 3: Use Gemini to classify and rank the papers (optimized for speed)
    """
    print(f'\n🎯 Step 3: Using Gemini to rank papers (selecting top {top_n})...')
    
    # Prepare compact paper summaries for Gemini (optimized)
    paper_summaries = [
        {
            'index': paper['index'],
            'title': paper['title'],
            'abstract': paper['summary'][:300] + '...',  # Reduced from 500 to 300 chars
            'arxiv_id': paper['arxiv_id']
        }
        for paper in papers
    ]
    
    # Optimized prompt - more concise, same quality
    prompt = f"""Evaluate and rank these {len(papers)} arXiv papers for relevance.

Query: "{original_query}"
Focus: {refined_query['search_focus']}
Concepts: {', '.join(refined_query['key_concepts'][:3])}

Papers:
{json.dumps(paper_summaries, indent=1)}

Select TOP {top_n} by relevance. For each: index, score (0-100), reason (1 sentence), contributions (1 sentence).
Output JSON: {{"top_papers": [{{"index": 1, "relevance_score": 95, "relevance_reason": "...", "key_contributions": "..."}}], "overall_analysis": "..."}}"""

    try:
        # Define JSON schema for structured output (faster than parsing)
        response_schema = {
            "type": "object",
            "properties": {
                "top_papers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "index": {"type": "integer"},
                            "relevance_score": {"type": "integer"},
                            "relevance_reason": {"type": "string"},
                            "key_contributions": {"type": "string"}
                        },
                        "required": ["index", "relevance_score", "relevance_reason", "key_contributions"]
                    }
                },
                "overall_analysis": {"type": "string"}
            },
            "required": ["top_papers", "overall_analysis"]
        }
        
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": response_schema
            }
        )
        
        # Direct JSON parsing (no regex needed with structured output)
        ranking_data = json.loads(response.text)
        
        print('   ✓ Papers ranked successfully!')
        print(f'   Analysis: {ranking_data["overall_analysis"][:100]}...')
        
        # Merge ranking data with original papers
        top_papers = []
        for ranked_paper in ranking_data['top_papers']:
            original_paper = next((p for p in papers if p['index'] == ranked_paper['index']), None)
            if original_paper:
                merged_paper = {
                    **original_paper,
                    'relevance_score': ranked_paper['relevance_score'],
                    'relevance_reason': ranked_paper['relevance_reason'],
                    'key_contributions': ranked_paper['key_contributions']
                }
                top_papers.append(merged_paper)
        
        return {
            'top_papers': top_papers,
            'overall_analysis': ranking_data['overall_analysis']
        }
    
    except Exception as error:
        print(f'   ✗ Error ranking papers with Gemini: {error}')
        # Fallback: return top N papers by order
        return {
            'top_papers': papers[:top_n],
            'overall_analysis': 'Papers returned in relevance order from arXiv (Gemini ranking unavailable)'
        }


def display_results(results: Dict[str, Any]):
    """Display results in a nice format"""
    print('\n' + '=' * 80)
    print('📊 TOP RESEARCH PAPERS - RESULTS')
    print('=' * 80)
    
    print(f'\n📈 Overall Analysis:\n{results["overall_analysis"]}\n')
    
    for idx, paper in enumerate(results['top_papers']):
        print(f'\n{"─" * 80}')
        print(f'\n🏆 #{idx + 1} - {paper["title"]}')
        print(f'\n📝 Authors: {paper["authors"]}')
        print(f'\n🆔 arXiv ID: {paper["arxiv_id"]}')
        print(f'📂 Categories: {", ".join(paper["categories"])}')
        print(f'📅 Published: {datetime.fromisoformat(paper["published"].replace("Z", "+00:00")).strftime("%Y-%m-%d")}')
        
        # Show page count if available
        if 'page_count' in paper:
            print(f'📄 Pages: {paper["page_count"]}')
        
        if 'relevance_score' in paper:
            print(f'\n⭐ Relevance Score: {paper["relevance_score"]}/100')
            print(f'💡 Why Relevant: {paper["relevance_reason"]}')
            print(f'🎯 Key Contributions: {paper["key_contributions"]}')
        
        print(f'\n📄 Abstract:\n{paper["summary"][:400]}...')
        print(f'\n🔗 Links:')
        print(f'   PDF: {paper["pdf_link"]}')
        print(f'   Abstract: {paper["abstract_link"]}')
    
    print('\n' + '=' * 80)


def save_results(results: Dict[str, Any], user_query: str, excluded_papers: List[Dict[str, Any]] = None, total_found: int = 0) -> Dict[str, str]:
    """Save results to JSON files"""
    timestamp = datetime.now().isoformat().replace(':', '-').replace('.', '-')
    filename = f'arxiv_results_{timestamp}.json'
    links_filename = f'arxiv_top5_links_{timestamp}.json'
    
    # Full detailed output
    output = {
        'query': user_query,
        'timestamp': datetime.now().isoformat(),
        'total_papers_found': total_found,
        'papers_excluded_by_page_limit': len(excluded_papers) if excluded_papers else 0,
        'total_papers_analyzed': MAX_ARXIV_RESULTS,
        'top_papers_count': len(results['top_papers']),
        'max_pdf_pages': MAX_PDF_PAGES,
        'overall_analysis': results['overall_analysis'],
        'papers': results['top_papers']
    }
    
    # Add excluded papers info if available
    if excluded_papers and len(excluded_papers) > 0:
        output['excluded_papers'] = [
            {
                'title': p['title'],
                'arxiv_id': p['arxiv_id'],
                'page_count': p.get('page_count', 'Unknown'),
                'pdf_link': p['pdf_link']
            }
            for p in excluded_papers
        ]
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f'\n💾 Full results saved to: {filename}')
    
    # Simplified links-only output
    links_output = {
        'query': user_query,
        'timestamp': datetime.now().isoformat(),
        'top_5_papers': [
            {
                'rank': idx + 1,
                'title': paper['title'],
                'arxiv_id': paper['arxiv_id'],
                'pdf_link': paper['pdf_link'],
                'abstract_link': paper['abstract_link'],
                'relevance_score': paper.get('relevance_score', None)
            }
            for idx, paper in enumerate(results['top_papers'])
        ]
    }
    
    with open(links_filename, 'w', encoding='utf-8') as f:
        json.dump(links_output, f, indent=2, ensure_ascii=False)
    
    print(f'💾 Top 5 links saved to: {links_filename}')
    
    return {'fullFile': filename, 'linksFile': links_filename}


def semantic_research_search(
    user_query: str, 
    user_context: str = '', 
    max_results: int = MAX_ARXIV_RESULTS,
    top_n: int = TOP_N_RESULTS
) -> Optional[Dict[str, Any]]:
    """
    Main function to orchestrate the semantic search
    """
    print('\n' + '=' * 80)
    print('🚀 ARXIV SEMANTIC RESEARCH SYSTEM')
    print('   Powered by arXiv API + Google Gemini')
    print(f'   PDF Page Limit: {MAX_PDF_PAGES} pages')
    print(f'   Parallel Workers: {PAGE_CHECK_WORKERS} (faster checking!)')
    print('=' * 80)
    
    try:
        # Step 1: Refine the query
        refined_query = refine_user_query(user_query, user_context)
        
        # Add a small delay to respect rate limits
        time.sleep(1)
        
        # Step 2: Search arXiv
        papers = search_arxiv(refined_query, max_results)
        
        if len(papers) == 0:
            print('\n⚠️  No papers found. Try a different query.')
            return None
        
        # Add a small delay to respect rate limits
        time.sleep(1)
        
        # Step 2.5: Filter papers by page count (parallel processing)
        filtered_papers, excluded_papers = filter_papers_by_page_count(papers, MAX_PDF_PAGES, PAGE_CHECK_WORKERS)
        
        if len(filtered_papers) == 0:
            print('\n⚠️  No papers remain after filtering. All papers exceed page limit.')
            return None
        
        # Add a small delay to respect rate limits
        time.sleep(1)
        
        # Step 3: Rank papers with Gemini
        results = rank_papers_with_gemini(filtered_papers, user_query, refined_query, top_n)
        
        # Display results
        display_results(results)
        
        # Save results
        saved_files = save_results(results, user_query, excluded_papers, len(papers))
        
        # Create simple array of top 5 PDF links
        top_5_links = [paper['pdf_link'] for paper in results['top_papers']]
        
        print('\n✅ Research search completed successfully!')
        
        return {
            **results,
            'refined_query': refined_query,
            'files': saved_files,
            'top_5_links': top_5_links,
            'excluded_papers': excluded_papers,
            'total_papers_found': len(papers),
            'papers_after_filtering': len(filtered_papers)
        }
    
    except Exception as error:
        print(f'\n❌ Error during semantic research search: {error}')
        raise error


if __name__ == '__main__':
    import sys
    
    # Direct function call with query parameter
    if len(sys.argv) >= 2:
        user_query = sys.argv[1]
        user_context = sys.argv[2] if len(sys.argv) > 2 else ''
    else:
        # Default query if none provided
        user_query = "large language models"
        user_context = "Recent advances and efficiency improvements"
        print(f'\n📌 No query provided, using default: "{user_query}"')
        print('💡 Usage: python arxiv_semantic_search.py "your query" ["optional context"]\n')
    
    try:
        results = semantic_research_search(user_query, user_context)
        
        # Display the simple links array
        print('\n📎 Top 5 Links Array:')
        for idx, link in enumerate(results['top_5_links'], 1):
            print(f"  {idx}. {link}")
        
        # Show filtering stats if available
        if 'excluded_papers' in results and len(results['excluded_papers']) > 0:
            print(f'\n📊 Filtering Summary:')
            print(f"   Total papers found: {results.get('total_papers_found', 'N/A')}")
            print(f"   Papers after filtering: {results.get('papers_after_filtering', 'N/A')}")
            print(f"   Papers excluded (>{MAX_PDF_PAGES} pages): {len(results['excluded_papers'])}")
        
        print('\n👋 Done!')
    except Exception as error:
        print(f'\n💥 Fatal error: {error}')
        sys.exit(1)
