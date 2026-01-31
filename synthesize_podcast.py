"""
Podcast Synthesizer - Convert arXiv Papers to Podcast Script
Uses Gemini PDF Document Processing to read and synthesize multiple papers
"""

import os
import io
from typing import List
from google import genai
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = 'gemini-2.5-flash'

if not GEMINI_API_KEY:
    print('❌ Error: GEMINI_API_KEY not found in .env file')
    exit(1)

# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)


def download_and_upload_pdfs(pdf_links: List[str]) -> List:
    """
    Download PDFs from arXiv and upload them to Gemini Files API
    
    Args:
        pdf_links: List of PDF URLs from arXiv
    
    Returns:
        List of uploaded file objects
    """
    uploaded_files = []
    
    print('\n📥 Downloading and uploading PDFs to Gemini...')
    
    for idx, pdf_url in enumerate(pdf_links, 1):
        try:
            print(f'   {idx}/{len(pdf_links)} Downloading: {pdf_url}')
            
            # Download PDF
            response = requests.get(pdf_url)
            response.raise_for_status()
            pdf_data = io.BytesIO(response.content)
            
            # Upload to Gemini Files API
            print(f'   {idx}/{len(pdf_links)} Uploading to Gemini...')
            uploaded_file = client.files.upload(
                file=pdf_data,
                config=dict(mime_type='application/pdf')
            )
            
            # Wait for file to be processed
            import time
            while True:
                file_status = client.files.get(name=uploaded_file.name)
                if file_status.state == 'ACTIVE':
                    print(f'   {idx}/{len(pdf_links)} ✅ Ready!')
                    break
                elif file_status.state == 'FAILED':
                    print(f'   {idx}/{len(pdf_links)} ❌ Failed to process')
                    raise Exception(f'File processing failed for {pdf_url}')
                else:
                    print(f'   {idx}/{len(pdf_links)} ⏳ Processing...')
                    time.sleep(2)
            
            uploaded_files.append(uploaded_file)
            
        except Exception as error:
            print(f'   ❌ Error with {pdf_url}: {error}')
            raise error
    
    print(f'\n✅ All {len(uploaded_files)} PDFs uploaded successfully!')
    return uploaded_files


def synthesize_papers_to_podcast(pdf_links: List[str], topic: str = "") -> dict:
    """
    Synthesize multiple arXiv papers into a podcast script using Gemini PDF processing
    
    Args:
        pdf_links: List of PDF URLs from arXiv
        topic: Optional topic/context for the synthesis
    
    Returns:
        dict with podcast_script and metadata
    """
    print('\n🎙️ PODCAST SYNTHESIS SYSTEM')
    print('=' * 80)
    print(f'\n📚 Synthesizing {len(pdf_links)} papers into podcast format...')
    
    # Display the papers being processed
    for idx, link in enumerate(pdf_links, 1):
        print(f'   {idx}. {link}')
    
    try:
        # Step 1: Download and upload PDFs to Gemini
        uploaded_files = download_and_upload_pdfs(pdf_links)
        
        # Step 2: Create the synthesis prompt
        prompt = f"""You are an expert science communicator creating a podcast script.

I have provided {len(pdf_links)} research papers from arXiv as PDF documents.

{f'Topic: {topic}' if topic else ''}

Your task is to:
1. Read and understand all {len(pdf_links)} papers thoroughly
2. Identify the common themes and key insights
3. Synthesize the information into a cohesive narrative
4. Create an engaging podcast script (10-15 minutes when spoken)

The podcast script should:
- Start with a compelling hook that explains why this research matters
- Explain the key concepts in accessible language (avoid jargon, or explain it clearly)
- Highlight the most important findings from across all papers
- Connect the papers together showing how they relate
- Use storytelling techniques (analogies, examples, real-world applications)
- End with implications and future directions
- Be conversational and engaging (written for speaking, not reading)

Format the output as:
# Podcast Script: [Catchy Title]

## Opening Hook (30 seconds)
[Engaging introduction that grabs attention]

## Context & Background (2-3 minutes)
[Explain the research area and why it matters]

## Key Findings (5-8 minutes)
[Main insights from the papers, woven together]

## Real-World Impact (2-3 minutes)
[Practical applications and implications]

## Closing & Future Outlook (1-2 minutes)
[Wrap up with exciting future possibilities]

---
## Technical Notes for Host
[Brief notes on pronunciation, key terms, paper references]
"""

        print('\n🤖 Gemini is reading and synthesizing the papers...')
        print('   (This may take 30-90 seconds)\n')
        
        # Build content with all PDFs + prompt
        contents = uploaded_files + [prompt]
        
        # Generate the synthesis
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents
        )
        
        # Extract the podcast script
        podcast_script = ""
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text'):
                podcast_script += part.text
        
        # Check token usage
        usage = None
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
        
        print('✅ Synthesis complete!')
        
        if usage:
            total_tokens = getattr(usage, 'total_token_count', 'N/A')
            print(f'📊 Tokens used: {total_tokens}')
        
        # Display file processing status
        print('\n📄 Processed PDFs:')
        for idx, file in enumerate(uploaded_files, 1):
            print(f'   ✅ {idx}. {file.name}')
        
        return {
            'podcast_script': podcast_script,
            'pdf_links': pdf_links,
            'topic': topic,
            'uploaded_files': uploaded_files,
            'usage': usage
        }
    
    except Exception as error:
        print(f'❌ Error synthesizing papers: {error}')
        raise error


def save_podcast_script(synthesis_result: dict, filename: str = None) -> str:
    """Save the podcast script to a markdown file"""
    import json
    from datetime import datetime
    
    if not filename:
        timestamp = datetime.now().isoformat().replace(':', '-').replace('.', '-')
        filename = f'podcast_script_{timestamp}.md'
    
    # Save the script
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(synthesis_result['podcast_script'])
    
    print(f'\n💾 Podcast script saved to: {filename}')
    
    # Also save metadata as JSON
    metadata_file = filename.replace('.md', '_metadata.json')
    
    # Get file names from uploaded files if available
    uploaded_file_names = []
    if 'uploaded_files' in synthesis_result:
        uploaded_file_names = [f.name for f in synthesis_result['uploaded_files']]
    
    metadata = {
        'topic': synthesis_result.get('topic', ''),
        'pdf_links': synthesis_result['pdf_links'],
        'uploaded_files': uploaded_file_names,
        'timestamp': datetime.now().isoformat(),
        'tokens_used': str(synthesis_result.get('usage', 'N/A'))
    }
    
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print(f'💾 Metadata saved to: {metadata_file}')
    
    return filename


def synthesize_from_search_results(search_results: dict) -> dict:
    """
    Convenience function to synthesize directly from arxiv_semantic_search results
    
    Args:
        search_results: The results dict from semantic_research_search()
    
    Returns:
        dict with podcast synthesis
    """
    pdf_links = search_results['top_5_links']
    topic = search_results.get('refined_query', {}).get('search_focus', '')
    
    return synthesize_papers_to_podcast(pdf_links, topic)


if __name__ == '__main__':
    import sys
    
    print('\n🎙️ Podcast Synthesizer')
    print('=' * 80)
    
    # Option 1: Provide PDF links directly as arguments
    if len(sys.argv) > 1:
        pdf_links = sys.argv[1:]
        print(f'\n📚 Synthesizing {len(pdf_links)} papers from command line arguments...')
        
        result = synthesize_papers_to_podcast(pdf_links)
        
        # Display a preview
        print('\n' + '=' * 80)
        print('📄 PODCAST SCRIPT PREVIEW')
        print('=' * 80)
        print(result['podcast_script'][:1000] + '...\n')
        
        # Save to file
        save_podcast_script(result)
        
        print('\n✅ Done!')
    
    # Option 2: Run a demo with sample arXiv papers
    else:
        print('\n💡 Usage Options:')
        print('\n1. From command line with PDF links:')
        print('   python synthesize_podcast.py "http://arxiv.org/pdf/1234.5678" "http://arxiv.org/pdf/2345.6789"')
        print('\n2. From Python code with search results:')
        print('   from arxiv_semantic_search import semantic_research_search')
        print('   from synthesize_podcast import synthesize_from_search_results')
        print('   ')
        print('   results = semantic_research_search("your query")')
        print('   podcast = synthesize_from_search_results(results)')
        print('\n3. Directly with links:')
        print('   from synthesize_podcast import synthesize_papers_to_podcast')
        print('   ')
        print('   links = ["pdf1", "pdf2", "pdf3", "pdf4", "pdf5"]')
        print('   podcast = synthesize_papers_to_podcast(links, "Topic description")')
        print('\n💡 Tip: First run arxiv_semantic_search.py to get relevant papers!')
