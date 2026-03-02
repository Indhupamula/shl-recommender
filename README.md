 SHL Assessment Recommendation System

An intelligent, RAG-based web application that recommends the most relevant SHL assessments given a natural language query, job description text, or URL.

 Live Demo

|  Frontend | https://thriving-sunburst-bc0edf.netlify.app |
|  API Endpoint | https://indhupamula-shl.hf.space |
|  GitHub | https://github.com/Indhupamula/shl-recommender |


##  Problem Statement

Hiring managers struggle to find the right SHL assessments for roles they are hiring for. This system simplifies the process by accepting a natural language query or job description and returning the most relevant **Individual Test Solutions** from SHL's product catalog in a tabular format.


##  System Architecture

User Query / JD Text / URL
        ↓
Gemini 2.0 Flash (Query Enhancement)
        ↓
FAISS Vector Search (Top-20 Candidates)
        ↓
Rule-Based Balancer (P / K / Other Types)
        ↓
Gemini 2.0 Flash (Reranking)
        ↓
Top-10 Recommendations (JSON + Table)




## 📁 Project Structure

shl-recommender/
├── scraper.py              # SHL catalog web scraper
├── embeddings.py           # Generate FAISS vector index
├── api.py                  # FastAPI backend
├── index.html              # Frontend web app
├── evaluate.py             # Mean Recall@10 evaluation
├── generate_predictions.py # Generate CSV predictions
├── assessments.json        # Scraped 389 assessments
├── vector_index.faiss      # FAISS vector index
├── assessment_data.pkl     # Assessment metadata
├── search_texts.pkl        # Search texts for embeddings
├── predictions.csv         # Test set predictions
├── evaluation_results.json # Evaluation results
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker deployment config
└── .gitignore


##  Tech Stack

| Component | Technology | Reason |
|---|---|---|
| Web Scraping | BeautifulSoup + Requests | Reliable HTML parsing |
| Embeddings | all-MiniLM-L6-v2 | Fast, accurate semantic vectors |
| Vector Search | FAISS IndexFlatL2 | Millisecond similarity search |
| LLM | Google Gemini 2.0 Flash | Query understanding + reranking |
| API | FastAPI | High-performance REST API |
| Frontend | HTML/CSS/JavaScript | Simple, clean table UI |
| Deployment | HuggingFace Spaces + Netlify | Free-tier cloud hosting |



##  Data Pipeline

1. Scraping — `scraper.py` crawls SHL catalog with `type=1` filter (Individual Test Solutions only)
2. Parsing — Extracts name, URL, test_type, remote_support, adaptive_support, description, duration
3. Storage — 389 unique assessments saved to `assessments.json`
4. Embedding — `embeddings.py` generates FAISS index from combined text fields


##  RAG Pipeline

1. Query Enhancement— Gemini expands query to identify technical skills, soft skills, job role
2. Retrieval — FAISS finds top-20 semantically similar assessments
3. Balancing — Ensures mix of P/B (Personality), K/A (Knowledge), and other types
4. Reranking — Gemini selects final top-10 most relevant assessments

##  API Endpoints

### GET /health
```json
{"status": "healthy"}
```

### POST /recommend
**Request:**
```json
{"query": "I need a Java developer who collaborates with business teams"}
```

**Response:**
```json
{
  "recommended_assessments": [
    {
      "url": "https://www.shl.com/solutions/products/product-catalog/view/java-new/",
      "name": "Java (New)",
      "adaptive_support": "No",
      "description": "...",
      "duration": 11,
      "remote_support": "Yes",
      "test_type": ["Knowledge & Skills"]
    }
  ]
}
```

---

## 📏 Evaluation

Mean Recall@10 implemented in `evaluate.py`:

Recall@K = Relevant found in top K / Total relevant
Mean Recall@10 = Average Recall@10 across all queries

Evaluation runs at both retrieval stage (FAISS candidates) and final recommendation stage (after reranking).[Pamula_Indhu.csv](https://github.com/user-attachments/files/25693151/Pamula_Indhu.csv)


## ⚙️ Local Setup

bash
# Clone the repo
git clone https://github.com/Indhupamula/shl-recommender.git
cd shl-recommender

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Add your Gemini API key
echo "GEMINI_API_KEY=your_key_here" > .env

# Run the API
python -m uvicorn api:app --reload

# Open frontend
start index.html

[SHL_INDHU.pdf](https://github.com/user-attachments/files/25693126/SHL_INDHU.pdf)
