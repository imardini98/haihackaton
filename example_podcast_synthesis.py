"""
Example: How to use the Podcast Synthesizer

This demonstrates 3 different ways to create podcast scripts
"""

# Example 1: Complete pipeline (easiest)
def example_complete_pipeline():
    """Run the complete pipeline: search → synthesize → save"""
    from full_pipeline import create_podcast_from_query
    
    print('\n' + '=' * 80)
    print('EXAMPLE 1: Complete Pipeline')
    print('=' * 80)
    
    result = create_podcast_from_query(
        "large language models",
        "Recent advances in efficiency and performance"
    )
    
    print('\n✅ Complete! All files saved.')
    return result


# Example 2: Two-step process (more control)
def example_two_step():
    """First search, then synthesize separately"""
    from arxiv_semantic_search import semantic_research_search
    from synthesize_podcast import synthesize_from_search_results, save_podcast_script
    
    print('\n' + '=' * 80)
    print('EXAMPLE 2: Two-Step Process')
    print('=' * 80)
    
    # Step 1: Search
    print('\n📚 Searching arXiv...')
    search_results = semantic_research_search(
        "quantum computing algorithms"
    )
    
    # You can inspect/modify the results here before synthesis
    print(f'\nFound papers:')
    for idx, link in enumerate(search_results['top_5_links'], 1):
        print(f'  {idx}. {link}')
    
    # Step 2: Synthesize
    print('\n🎙️ Synthesizing podcast...')
    podcast = synthesize_from_search_results(search_results)
    
    # Step 3: Save
    script_file = save_podcast_script(podcast)
    
    print(f'\n✅ Saved to: {script_file}')
    return podcast


# Example 3: Direct synthesis with custom links (most flexible)
def example_custom_links():
    """Use your own list of arXiv PDF links"""
    from synthesize_podcast import synthesize_papers_to_podcast, save_podcast_script
    
    print('\n' + '=' * 80)
    print('EXAMPLE 3: Custom Links')
    print('=' * 80)
    
    # Your custom list of arXiv PDF links
    custom_links = [
        'http://arxiv.org/pdf/1706.03762',  # Attention Is All You Need
        'http://arxiv.org/pdf/1810.04805',  # BERT
        'http://arxiv.org/pdf/1910.10683',  # T5
        'http://arxiv.org/pdf/2005.14165',  # GPT-3
        'http://arxiv.org/pdf/2204.02311',  # PaLM
    ]
    
    print(f'\n📚 Synthesizing {len(custom_links)} custom papers...')
    
    podcast = synthesize_papers_to_podcast(
        custom_links,
        topic="Evolution of Transformer Language Models"
    )
    
    script_file = save_podcast_script(podcast, 'custom_podcast_transformers.md')
    
    print(f'\n✅ Saved to: {script_file}')
    return podcast


# Example 4: Programmatic usage with result inspection
def example_programmatic():
    """Full programmatic control with result inspection"""
    from arxiv_semantic_search import semantic_research_search
    from synthesize_podcast import synthesize_papers_to_podcast, save_podcast_script
    
    print('\n' + '=' * 80)
    print('EXAMPLE 4: Programmatic Usage')
    print('=' * 80)
    
    # Search
    results = semantic_research_search("neural networks for computer vision")
    
    # Extract just the links
    pdf_links = results['top_5_links']
    
    print(f'\n📊 Search Stats:')
    print(f'   Query: {results["refined_query"]["refined_query"]}')
    print(f'   Papers found: {len(pdf_links)}')
    
    # Synthesize with custom topic
    podcast = synthesize_papers_to_podcast(
        pdf_links,
        topic="Neural Networks in Computer Vision - Recent Advances"
    )
    
    # Access the script
    script = podcast['podcast_script']
    
    print(f'\n📝 Script length: {len(script)} characters')
    print(f'📝 Script preview:\n{script[:500]}...\n')
    
    # Save with custom name
    save_podcast_script(podcast, 'vision_podcast.md')
    
    return podcast


if __name__ == '__main__':
    import sys
    
    examples = {
        '1': example_complete_pipeline,
        '2': example_two_step,
        '3': example_custom_links,
        '4': example_programmatic
    }
    
    example_num = sys.argv[1] if len(sys.argv) > 1 else '1'
    
    if example_num in examples:
        print(f'\n🎯 Running Example {example_num}...')
        examples[example_num]()
        print('\n✨ Done!')
    else:
        print('\n📖 Usage: python example_podcast_synthesis.py [1|2|3|4]')
        print('\nExamples:')
        print('  1 - Complete pipeline (easiest)')
        print('  2 - Two-step process (more control)')
        print('  3 - Custom links (most flexible)')
        print('  4 - Programmatic usage (full control)')
        print('\nOr run without arguments to use Example 1')
