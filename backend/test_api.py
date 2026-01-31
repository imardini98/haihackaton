"""
Test script for arXiv search + podcast synthesis flow
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api/v1"


def test_arxiv_search_and_synthesis():
    """Test the complete flow: search -> synthesis"""

    # Step 1: Search arXiv papers
    print("\n" + "=" * 60)
    print("STEP 1: Searching arXiv papers...")
    print("=" * 60)

    search_request = {
        "query": "transformer architecture efficiency",
        "context": "making transformers faster and smaller",
        "max_results": 5,
        "top_n": 3,
        "max_pdf_pages": 30
    }

    print(f"\n📝 Query: {search_request['query']}")
    print(f"📝 Context: {search_request['context']}")

    try:
        search_response = requests.post(
            f"{BASE_URL}/arxiv/search",
            json=search_request,
            timeout=120
        )

        if search_response.status_code != 200:
            print(f"\n❌ Search failed with status {search_response.status_code}")
            print(f"Error: {search_response.text}")
            return

        search_data = search_response.json()

        print(f"\n✅ Search successful!")
        print(f"📊 Found {search_data['total_papers_found']} papers")
        print(f"📊 Filtered to {search_data['papers_after_filtering']} papers")
        print(f"🎯 Top {search_data['top_papers_count']} papers ranked")

        # Display top papers
        print("\n🏆 Top Papers:")
        for idx, paper in enumerate(search_data['top_papers'], 1):
            print(f"\n   {idx}. {paper['title'][:80]}...")
            print(f"      Relevance: {paper.get('relevance_score', 'N/A')}/100")
            print(f"      Pages: {paper.get('page_count', 'Unknown')}")

        # Step 2: Synthesize podcast
        print("\n" + "=" * 60)
        print("STEP 2: Synthesizing podcast from PDF links...")
        print("=" * 60)

        pdf_links = search_data['top_5_links'][:3]  # Use top 3 for faster test
        topic = search_data['refined_query']['search_focus']

        print(f"\n📚 Using {len(pdf_links)} papers")
        print(f"📝 Topic: {topic}")
        print("\n📄 PDF Links:")
        for idx, link in enumerate(pdf_links, 1):
            print(f"   {idx}. {link}")

        synthesis_request = {
            "pdf_links": pdf_links,
            "topic": topic
        }

        print("\n⏳ Synthesis in progress... (this may take 30-60 seconds)")

        synthesis_response = requests.post(
            f"{BASE_URL}/podcasts/synthesize",
            json=synthesis_request,
            timeout=180  # 3 minutes timeout for synthesis
        )

        if synthesis_response.status_code != 200:
            print(f"\n❌ Synthesis failed with status {synthesis_response.status_code}")
            print(f"Error: {synthesis_response.text}")
            return

        synthesis_data = synthesis_response.json()

        print(f"\n✅ Synthesis successful!")
        print(f"📝 Tokens used: {synthesis_data.get('tokens_used', 'N/A')}")
        print(f"📅 Timestamp: {synthesis_data['timestamp']}")

        # Display podcast script preview
        print("\n" + "=" * 60)
        print("PODCAST SCRIPT PREVIEW")
        print("=" * 60)
        print(synthesis_data['podcast_script'][:1500] + "...")
        print("\n" + "=" * 60)

        # Save to file (replace colons for Windows compatibility)
        safe_timestamp = synthesis_data['timestamp'].replace(':', '-')
        filename = f"test_podcast_{safe_timestamp}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(synthesis_data['podcast_script'])
        print(f"\n💾 Full script saved to: {filename}")

        return synthesis_data

    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to the API")
        print("💡 Make sure the server is running: uvicorn app.main:app --reload --port 8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    test_arxiv_search_and_synthesis()
