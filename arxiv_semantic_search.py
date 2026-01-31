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

import requests
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

# Validate API key
if not GEMINI_API_KEY:
    print('❌ Error: GEMINI_API_KEY not found in .env file')
    print('Please add to .env file: GEMINI_API_KEY=your_api_key_here')
    exit(1)

# Initialize Gemini AI Client
client = genai.Client(api_key=GEMINI_API_KEY)


def refine_user_query(user_query: str, user_context: str = '') -> Dict[str, Any]:
    """
    Step 1: Refine user query using Gemini to understand what they really need
    """
    print('\n🔍 Step 1: Refining user query with Gemini...')
    print(f'   Original query: "{user_query}"')
    
    prompt = f"""You are a research assistant helping to refine academic search queries for arXiv.

User Query: "{user_query}"
{f'User Context: {user_context}' if user_context else ''}

Your task is to:
1. Understand what the user is really looking for
2. Identify key concepts, methodologies, and domains
3. Generate an optimized search query for arXiv that will find the most relevant papers

Provide your response in the following JSON format:
{{
  "refined_query": "optimized search query with arXiv search operators",
  "key_concepts": ["concept1", "concept2", "concept3"],
  "search_focus": "brief explanation of what to focus on",
  "additional_filters": {{
    "categories": ["suggested arXiv categories like cs.AI, cs.LG"],
    "date_range": "recent or specify if historical context needed"
  }}
}}

Important: Use arXiv search operators:
- ti: for title search
- abs: for abstract search
- au: for author search
- cat: for category search
- all: for all fields

Example: ti:"neural networks" AND abs:transformer AND cat:cs.LG"""

    try:
        interaction = client.interactions.create(
            model=GEMINI_MODEL,
            input=prompt
        )
        
        # Get the text output from the interaction
        text_output = next((o for o in interaction.outputs if o.type == 'text'), None)
        if not text_output:
            raise Exception('No text output from Gemini')
        
        text = text_output.text
        
        # Extract JSON from the response (handling markdown code blocks)
        import re
        json_match = re.search(r'\{[\s\S]*\}', text)
        if not json_match:
            raise Exception('Could not extract JSON from Gemini response')
        
        refined_data = json.loads(json_match.group(0))
        
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
    Step 3: Use Gemini to classify and rank the papers
    """
    print(f'\n🎯 Step 3: Using Gemini to rank papers (selecting top {top_n})...')
    
    # Prepare paper summaries for Gemini
    paper_summaries = [
        {
            'index': paper['index'],
            'title': paper['title'],
            'authors': paper['authors'],
            'abstract': paper['summary'][:500] + '...',  # Limit abstract length
            'categories': ', '.join(paper['categories']),
            'arxiv_id': paper['arxiv_id']
        }
        for paper in papers
    ]
    
    prompt = f"""You are an expert research paper evaluator and classifier.

Original User Query: "{original_query}"
Refined Search Focus: "{refined_query['search_focus']}"
Key Concepts: {', '.join(refined_query['key_concepts'])}

Below are {len(papers)} papers from arXiv. Your task is to:
1. Evaluate each paper's relevance to the user's research needs
2. Consider: title relevance, abstract quality, author credibility, recency, and domain fit
3. Rank them and select the TOP {top_n} most relevant papers
4. Provide a relevance score (0-100) and justification for each selected paper

Papers to evaluate:
{json.dumps(paper_summaries, indent=2)}

Provide your response in the following JSON format:
{{
  "top_papers": [
    {{
      "index": 1,
      "relevance_score": 95,
      "relevance_reason": "Brief explanation of why this paper is highly relevant",
      "key_contributions": "What makes this paper valuable for the query"
    }}
  ],
  "overall_analysis": "Brief overview of the paper landscape and why these top papers were selected"
}}

Return ONLY the JSON, no markdown formatting."""

    try:
        interaction = client.interactions.create(
            model=GEMINI_MODEL,
            input=prompt
        )
        
        # Get the text output from the interaction
        text_output = next((o for o in interaction.outputs if o.type == 'text'), None)
        if not text_output:
            raise Exception('No text output from Gemini')
        
        text = text_output.text
        
        # Extract JSON from the response
        import re
        json_match = re.search(r'\{[\s\S]*\}', text)
        if not json_match:
            raise Exception('Could not extract JSON from Gemini response')
        
        ranking_data = json.loads(json_match.group(0))
        
        print('   ✓ Papers ranked successfully!')
        print(f'   Analysis: {ranking_data["overall_analysis"]}')
        
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
        
        if 'relevance_score' in paper:
            print(f'\n⭐ Relevance Score: {paper["relevance_score"]}/100')
            print(f'💡 Why Relevant: {paper["relevance_reason"]}')
            print(f'🎯 Key Contributions: {paper["key_contributions"]}')
        
        print(f'\n📄 Abstract:\n{paper["summary"][:400]}...')
        print(f'\n🔗 Links:')
        print(f'   PDF: {paper["pdf_link"]}')
        print(f'   Abstract: {paper["abstract_link"]}')
    
    print('\n' + '=' * 80)


def save_results(results: Dict[str, Any], user_query: str) -> Dict[str, str]:
    """Save results to JSON files"""
    timestamp = datetime.now().isoformat().replace(':', '-').replace('.', '-')
    filename = f'arxiv_results_{timestamp}.json'
    links_filename = f'arxiv_top5_links_{timestamp}.json'
    
    # Full detailed output
    output = {
        'query': user_query,
        'timestamp': datetime.now().isoformat(),
        'total_papers_analyzed': MAX_ARXIV_RESULTS,
        'top_papers_count': len(results['top_papers']),
        'overall_analysis': results['overall_analysis'],
        'papers': results['top_papers']
    }
    
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
        
        # Step 3: Rank papers with Gemini
        results = rank_papers_with_gemini(papers, user_query, refined_query, top_n)
        
        # Display results
        display_results(results)
        
        # Save results
        saved_files = save_results(results, user_query)
        
        print('\n✅ Research search completed successfully!')
        
        return {
            **results,
            'refined_query': refined_query,
            'files': saved_files
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
        semantic_research_search(user_query, user_context)
        print('\n👋 Done!')
    except Exception as error:
        print(f'\n💥 Fatal error: {error}')
        sys.exit(1)
