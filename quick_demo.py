"""
Quick Demo of arXiv Semantic Search - Python Version

This is a simple demo to test if everything is working correctly
"""

from arxiv_semantic_search import semantic_research_search


def run_demo():
    print('\n' + '=' * 80)
    print('🎯 QUICK DEMO: arXiv Semantic Search System')
    print('=' * 80)
    
    print('\nThis demo will search for papers on "large language models"')
    print('and demonstrate the full pipeline: refine → search → rank\n')
    
    try:
        results = semantic_research_search(
            "large language models",
            "I want to understand recent advances in LLMs, especially efficiency improvements",
            max_results=10,  # Search 10 papers (faster for demo)
            top_n=3          # Return top 3 (easier to review)
        )
        
        if results:
            print('\n✨ Demo completed successfully!')
            print(f'\n📁 Files saved:')
            print(f'   📄 Full details: {results["files"]["fullFile"]}')
            print(f'   🔗 Top 5 links: {results["files"]["linksFile"]}')
            print('\n💡 Tips:')
            print('   - Try your own query: python arxiv_semantic_search.py "your query here"')
            print('   - Run examples: python example_usage.py 1')
            print('   - Read docs: ARXIV_SEMANTIC_SEARCH.md')
    
    except Exception as error:
        print(f'\n❌ Demo failed: {error}')
        
        if 'GEMINI_API_KEY' in str(error):
            print('\n🔑 Setup Required:')
            print('   1. Get Gemini API key: https://makersuite.google.com/app/apikey')
            print('   2. Add to .env file: GEMINI_API_KEY=your_key_here')
            print('   3. Run this demo again')


if __name__ == '__main__':
    run_demo()
