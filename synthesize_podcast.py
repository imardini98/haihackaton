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
        prompt = f"""You are an expert science communicator creating a podcast script that makes research accessible to everyone.

I have provided {len(pdf_links)} research papers from arXiv as PDF documents.

{f'Topic: {topic}' if topic else ''}

Your task is to:
1. Read and understand all {len(pdf_links)} papers thoroughly
2. Identify the common themes and key insights
3. **Find the connections and relationships between the papers**
4. Synthesize the information into a cohesive, interconnected narrative
5. Create an engaging podcast script (10-15 minutes when spoken)

CRITICAL GUIDELINES FOR ACCESSIBILITY:
- Use simple, everyday language - write as if explaining to a curious friend
- Replace technical jargon with plain language (e.g., "neural network" → "a computer system that learns like a brain")
- When technical terms are necessary, immediately explain them in simple words
- Break down complex ideas into smaller, easy-to-grasp concepts
- Use analogies and real-world examples that everyone can relate to
- Keep sentences short and clear
- Include all important details, but explain them simply
- Focus on what things DO rather than what they ARE

The podcast script should:
- Start with a compelling hook that explains why this research matters in everyday terms
- Explain the key concepts using simple, accessible language (imagine explaining to someone with no technical background)
- **STRONGLY EMPHASIZE THE CONNECTIONS between papers:**
  * Show how papers build on each other's ideas
  * Highlight where papers agree or provide complementary perspectives
  * Point out contrasting approaches or findings between papers
  * Explain how together they tell a bigger story than individually
  * Use explicit transition phrases: "This builds on...", "While the first paper showed X, the second paper takes it further...", "Interestingly, this contrasts with..."
  * Weave papers together rather than presenting them sequentially
- Highlight the most important findings with clear explanations and real-world examples
- Create a narrative arc that shows the evolution or progression of ideas across papers
- Use storytelling techniques (analogies, metaphors, everyday examples)
- Include specific details and numbers, but explain what they mean in practical terms
- Reference specific papers by author/institution to show connections: "The Stanford team found X, which the MIT researchers then used to..."
- End with implications and future directions that listeners can easily understand
- Be conversational and friendly (written for speaking, not reading)
- Avoid academic or overly complex vocabulary

Format the output as:
# Podcast Script: [Catchy, Easy-to-Understand Title]

## Opening Hook (30 seconds)
[Engaging introduction that immediately connects to everyday life]

## Context & Background (2-3 minutes)
[Explain the research area using simple language and relatable examples. Introduce how these papers connect to each other.]

## Key Findings (5-8 minutes)
[Main insights explained simply with clear examples and analogies. WEAVE THE PAPERS TOGETHER:
- Show how findings from different papers relate
- Highlight agreements, disagreements, or complementary approaches
- Use explicit connecting phrases between papers
- Create a narrative that shows progression or evolution of ideas
- Reference papers by author/institution to clarify connections]

## Real-World Impact (2-3 minutes)
[Practical applications explained in terms everyone can understand]

## Closing & Future Outlook (1-2 minutes)
[Wrap up with exciting future possibilities in accessible language]

---
## Technical Notes for Host
[Brief notes on pronunciation, key terms simplified, paper references]
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
