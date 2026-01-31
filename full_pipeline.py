"""
Full Pipeline: arXiv Search → Podcast Synthesis
Complete workflow from research query to podcast script
"""

from arxiv_semantic_search import semantic_research_search
from synthesize_podcast import synthesize_from_search_results, save_podcast_script


def create_podcast_from_query(query: str, context: str = "") -> dict:
    """
    Complete pipeline: Search arXiv → Get papers → Synthesize to podcast
    
    Args:
        query: Research query
        context: Optional user context
    
    Returns:
        dict with search results, podcast script, and files
    """
    print('\n' + '=' * 80)
    print('🎙️ FULL PIPELINE: RESEARCH → PODCAST')
    print('=' * 80)
    
    # Step 1: Search arXiv for relevant papers
    print('\n📚 STEP 1: Searching arXiv for papers...')
    search_results = semantic_research_search(query, context)
    
    print(f'\n✅ Found {len(search_results["top_5_links"])} papers')
    
    # Step 2: Synthesize papers into podcast
    print('\n🎙️ STEP 2: Synthesizing papers into podcast script...')
    podcast_result = synthesize_from_search_results(search_results)
    
    # Step 3: Save the podcast script
    print('\n💾 STEP 3: Saving podcast script...')
    script_file = save_podcast_script(podcast_result)
    
    # Display preview
    print('\n' + '=' * 80)
    print('📄 PODCAST SCRIPT PREVIEW')
    print('=' * 80)
    print(podcast_result['podcast_script'][:800] + '...\n')
    
    print('=' * 80)
    print('✅ PIPELINE COMPLETE!')
    print('=' * 80)
    print(f'\n📁 Generated Files:')
    print(f'   1. arXiv Results: {search_results["files"]["fullFile"]}')
    print(f'   2. Top 5 Links: {search_results["files"]["linksFile"]}')
    print(f'   3. Podcast Script: {script_file}')
    print(f'   4. Metadata: {script_file.replace(".md", "_metadata.json")}')
    
    return {
        'search_results': search_results,
        'podcast_result': podcast_result,
        'script_file': script_file
    }


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print('\n📖 Usage: python full_pipeline.py "your research query" ["optional context"]')
        print('\nExample:')
        print('  python full_pipeline.py "transformer architectures" "Looking for recent advances"')
        print('\nThis will:')
        print('  1. Search arXiv for relevant papers')
        print('  2. Get top 5 papers')
        print('  3. Synthesize them into a podcast script')
        print('  4. Save everything to files')
        exit(1)
    
    query = sys.argv[1]
    context = sys.argv[2] if len(sys.argv) > 2 else ''
    
    try:
        result = create_podcast_from_query(query, context)
        print('\n🎉 Success! Your podcast script is ready!')
    except Exception as error:
        print(f'\n❌ Error: {error}')
        exit(1)
