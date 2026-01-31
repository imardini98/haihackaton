# arXiv Semantic Search System 🔬🤖

An intelligent research paper discovery system that combines arXiv API with Google Gemini AI for advanced semantic search and ranking.

## 🌟 Features

1. **Intelligent Query Refinement**: Uses Gemini AI to understand what you really need
2. **Advanced arXiv Search**: Leverages arXiv API with optimized search operators
3. **AI-Powered Ranking**: Gemini classifies and ranks papers by relevance
4. **Context-Aware**: Takes into account your research background and needs
5. **Top Results**: Returns the top 5 most relevant papers from 20 initial results

## 🚀 How It Works

```
User Query → Gemini Refines → arXiv Search (20 papers) → Gemini Ranks → Top 5 Results
```

### Step 1: Query Refinement
- Gemini analyzes your query and context
- Identifies key concepts and research domains
- Generates optimized arXiv search query with proper operators
- Suggests relevant categories and filters

### Step 2: arXiv Search
- Searches arXiv API with refined query
- Retrieves up to 20 most relevant papers
- Extracts full metadata (title, authors, abstract, categories, etc.)
- Sorts by relevance

### Step 3: Intelligent Ranking
- Gemini evaluates each paper's relevance
- Considers: title relevance, abstract quality, author credibility, recency
- Assigns relevance scores (0-100)
- Provides justification for each selection
- Returns top 5 papers with detailed analysis

## 📦 Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Required packages:
# - google-genai (Gemini Interactions API)
# - requests (HTTP requests)
# - python-dotenv (Environment variables)
# - xml.etree.ElementTree (Built-in Python XML parser)
```

**Note:** This uses the new **Gemini Interactions API** (`google-genai` for Python) which provides a more unified and powerful interface.

## ⚙️ Configuration

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

2. Add to your `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## 💻 Usage

### Command Line

```bash
# Basic usage
node arxiv-semantic-search.js "your research query"

# With context
node arxiv-semantic-search.js "transformer architectures" "I'm researching efficient vision models"

# Examples
node example-usage.js 1     # Run example 1
node example-usage.js all   # Run all examples
```

### Programmatic Usage

```javascript
const { semanticResearchSearch } = require('./arxiv-semantic-search');

// Simple query
await semanticResearchSearch(
  "deep learning for image classification"
);

// With context
await semanticResearchSearch(
  "quantum computing algorithms",
  "I'm researching quantum error correction"
);

// Custom options
await semanticResearchSearch(
  "attention mechanisms in NLP",
  "Looking for transformer variants",
  {
    maxResults: 30,  // Get 30 papers from arXiv (default: 20)
    topN: 10         // Return top 10 (default: 5)
  }
);
```

## 📊 Output Format

The system provides:

1. **Console Output**:
   - Step-by-step progress
   - Refined query details
   - Overall analysis
   - Top papers with scores and justifications

2. **Full JSON File** (`arxiv_results_*.json`):
   - Saved automatically with timestamp
   - Complete metadata for all top papers
   - Full abstracts and details
   - Relevance scores and reasons
   - Links to PDF and abstract pages

3. **Links-Only JSON File** (`arxiv_top5_links_*.json`) ⭐ NEW!:
   - Simplified format with just the top 5 links
   - Perfect for quick access or integration
   - Contains: rank, title, arXiv ID, PDF link, abstract link, relevance score
   - Clean, minimal JSON structure

### Sample Output Structure

#### Full Results (`arxiv_results_*.json`)
```json
{
  "query": "original user query",
  "timestamp": "2026-01-31T...",
  "total_papers_analyzed": 20,
  "top_papers_count": 5,
  "overall_analysis": "Brief overview...",
  "papers": [
    {
      "title": "Paper Title",
      "authors": "Author Names",
      "arxiv_id": "2301.12345",
      "summary": "Abstract text...",
      "categories": ["cs.AI", "cs.LG"],
      "pdf_link": "http://arxiv.org/pdf/2301.12345",
      "abstract_link": "http://arxiv.org/abs/2301.12345",
      "relevance_score": 95,
      "relevance_reason": "Why this paper is relevant...",
      "key_contributions": "What makes it valuable..."
    }
  ]
}
```

#### Links Only (`arxiv_top5_links_*.json`) ⭐ NEW!
```json
{
  "query": "transformer architectures for computer vision",
  "timestamp": "2026-01-31T16:00:00.000Z",
  "top_5_papers": [
    {
      "rank": 1,
      "title": "Attention Is All You Need",
      "arxiv_id": "1706.03762",
      "pdf_link": "http://arxiv.org/pdf/1706.03762",
      "abstract_link": "http://arxiv.org/abs/1706.03762",
      "relevance_score": 98
    }
  ]
}
```

See [SAMPLE_TOP5_LINKS.json](./SAMPLE_TOP5_LINKS.json) for a complete example.

## 🎯 Use Cases

### 1. Literature Review
```javascript
await semanticResearchSearch(
  "survey of deep learning in medical imaging",
  "Starting PhD in AI for radiology"
);
```

### 2. Stay Updated
```javascript
await semanticResearchSearch(
  "latest advances in large language models",
  "Following developments in prompt engineering and efficiency"
);
```

### 3. Specific Problem Solving
```javascript
await semanticResearchSearch(
  "solutions for catastrophic forgetting in continual learning",
  "Working on a system that needs to learn incrementally"
);
```

### 4. Cross-Domain Research
```javascript
await semanticResearchSearch(
  "physics-informed neural networks for fluid dynamics",
  "Combining ML with computational physics"
);
```

## 🚀 Powered by Gemini 2.5 Flash

This system uses the latest **Gemini 2.5 Flash** model via the **Interactions API**:
- ⚡ Faster response times
- 🎯 More accurate understanding
- 💰 Cost-effective
- 🔄 Better state management
- 🛠️ Native tool integration support

[Read about the Interactions API →](https://ai.google.dev/gemini-api/docs/interactions)

## 🔧 Advanced Features

### arXiv Search Operators

The system uses arXiv's advanced search operators:

- `ti:` - Search in title
- `abs:` - Search in abstract
- `au:` - Search by author
- `cat:` - Search by category
- `all:` - Search all fields

### Boolean Operators

- `AND` - Both terms must appear
- `OR` - Either term can appear
- `ANDNOT` - Exclude terms

### Example Query Generated by Gemini

```
ti:"neural networks" AND abs:transformer AND cat:cs.LG AND submittedDate:[20250101+TO+20260131]
```

## 📚 arXiv Categories

Common categories the system works with:

- **Computer Science**: cs.AI, cs.LG, cs.CV, cs.CL, cs.RO
- **Physics**: physics.comp-ph, quant-ph
- **Mathematics**: math.OC, math.ST
- **Quantitative Biology**: q-bio.QM, q-bio.NC
- **Statistics**: stat.ML, stat.AP

## ⚡ Performance Tips

1. **Be Specific**: More specific queries yield better results
   - ❌ "machine learning"
   - ✅ "few-shot learning for text classification"

2. **Provide Context**: Helps Gemini understand your needs
   - Good context: "I'm a robotics engineer working on manipulation"

3. **Use Custom Options**: Adjust based on your needs
   - Narrow field: `topN: 3, maxResults: 15`
   - Broad survey: `topN: 10, maxResults: 30`

4. **Rate Limits**: 
   - arXiv API: Max 2000 results per query, recommended 3s delay between calls
   - Gemini API: Check your quota limits

## 🔄 Integration with PodAsk AI

This system is designed to integrate with the PodAsk AI platform:

1. **Paper Discovery**: Find relevant papers automatically
2. **Content Pipeline**: Feed top papers to Gemini for synthesis
3. **Podcast Generation**: Convert analyzed content to audio via ElevenLabs
4. **Interactive Layer**: Enable "raise hand" feature for deep dives

### Pipeline Integration

```python
# 1. Discover papers
results = semantic_research_search(user_query, context)

# 2. Pass to synthesis (for PodAsk)
top_papers = results['top_papers']
# → Send to Gemini for deep analysis
# → Generate podcast script
# → Convert to audio with ElevenLabs
```

## 🐛 Troubleshooting

### "GEMINI_API_KEY not found"
- Make sure `.env` file exists in project root
- Check that you've added: `GEMINI_API_KEY=your_key`
- Restart your terminal/IDE after adding the key

### "No papers found"
- Try a broader query
- Check arXiv categories are correct
- Remove date filters if too restrictive

### "Could not extract JSON from Gemini"
- Gemini response format may have changed
- Check your API quota/limits
- Try running again (rate limit issue)

## 📖 API Documentation

- [arXiv API User Manual](https://info.arxiv.org/help/api/user-manual.html)
- [Google Gemini API](https://ai.google.dev/docs)

## 🤝 Contributing

This is a hackathon project for **PodAsk AI**. Feel free to:
- Suggest improvements
- Add new features
- Report bugs
- Share your use cases

## 📄 License

MIT

## 🎓 Citation

If you use this system in your research, please cite:

```bibtex
@software{arxiv_semantic_search,
  title={arXiv Semantic Search System},
  author={PodAsk AI Team},
  year={2026},
  description={Intelligent research paper discovery using arXiv API and Google Gemini AI}
}
```

---

**Built with ❤️ for the research community**

*Part of the PodAsk AI platform - "Don't just listen. Ask the science."*
