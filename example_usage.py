"""
Example Usage of arXiv Semantic Search System - Python Version

This file demonstrates different ways to use the semantic research system
"""

from arxiv_semantic_search import semantic_research_search
import time


def example1():
    """Example 1: Simple query"""
    print('\n📌 EXAMPLE 1: Simple Query')
    print('=' * 60)
    
    semantic_research_search(
        "deep learning for image classification"
    )


def example2():
    """Example 2: Query with user context"""
    print('\n📌 EXAMPLE 2: Query with Context')
    print('=' * 60)
    
    semantic_research_search(
        "quantum computing algorithms",
        "I'm a PhD student researching quantum error correction and need recent advances in the field"
    )


def example3():
    """Example 3: Custom options (more papers)"""
    print('\n📌 EXAMPLE 3: Custom Options')
    print('=' * 60)
    
    semantic_research_search(
        "attention mechanisms in natural language processing",
        "Looking for transformer variants and efficiency improvements",
        max_results=30,  # Get 30 papers from arXiv
        top_n=10         # Return top 10 after ranking
    )


def example4():
    """Example 4: Specific research area"""
    print('\n📌 EXAMPLE 4: Specific Research Area')
    print('=' * 60)
    
    semantic_research_search(
        "reinforcement learning for robotics manipulation",
        "I need papers about sim-to-real transfer and contact-rich tasks"
    )


def example5():
    """Example 5: Medical/Biology research"""
    print('\n📌 EXAMPLE 5: Cross-domain Research')
    print('=' * 60)
    
    semantic_research_search(
        "machine learning for drug discovery",
        "Interested in molecular property prediction and generative models for molecules"
    )


def main():
    """Run examples"""
    import sys
    
    # Choose which example to run
    example_number = sys.argv[1] if len(sys.argv) > 1 else '1'
    
    examples = {
        '1': example1,
        '2': example2,
        '3': example3,
        '4': example4,
        '5': example5
    }
    
    if example_number == 'all':
        for i in range(1, 4):  # Run first 3 examples
            examples[str(i)]()
            print('\n⏳ Waiting 3 seconds before next example...')
            time.sleep(3)
    elif example_number in examples:
        examples[example_number]()
    else:
        print('Usage: python example_usage.py [1-5|all]')
        print('Examples:')
        print('  python example_usage.py 1    - Run example 1')
        print('  python example_usage.py all  - Run multiple examples')


if __name__ == '__main__':
    main()
