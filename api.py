import json
import pickle
import numpy as np
import faiss
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import os
import requests
from bs4 import BeautifulSoup

app = FastAPI(title="SHL Assessment Recommender")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

print("Loading models...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
faiss_index = faiss.read_index("vector_index.faiss")

with open("assessment_data.pkl", "rb") as f:
    stored_assessments = pickle.load(f)

print("Models loaded!")

class QueryInput(BaseModel):
    query: str

def find_similar(query, top_k=10):
    vec = embedding_model.encode([query]).astype("float32")
    _, indices = faiss_index.search(vec, top_k)
    results = []
    for idx in indices[0]:
        if idx < len(stored_assessments):
            results.append(stored_assessments[idx])
    return results

def balance(candidates):
    p_types = ["P", "B"]
    k_types = ["K", "A"]
    p_items = [i for i in candidates if any(t in p_types for t in i.get("test_type", []))]
    k_items = [i for i in candidates if any(t in k_types for t in i.get("test_type", []))]
    o_items = [i for i in candidates if i not in p_items and i not in k_items]
    result = []
    result.extend(p_items[:3])
    result.extend(k_items[:3])
    result.extend(o_items[:4])
    remaining = [i for i in candidates if i not in result]
    while len(result) < 10 and remaining:
        result.append(remaining.pop(0))
    return result[:10]

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/recommend")
def recommend(user_input: QueryInput):
    query = user_input.query
    if query.startswith("http"):
        try:
            r = requests.get(query, timeout=10)
            soup = BeautifulSoup(r.content, "html.parser")
            query = soup.get_text(separator=" ", strip=True)[:3000]
        except:
            pass
    candidates = find_similar(query, top_k=20)
    final = balance(candidates)
    response = []
    for item in final:
        response.append({
            "url": item.get("url", ""),
            "name": item.get("name", ""),
            "adaptive_support": item.get("adaptive_support", "No"),
            "description": item.get("description", ""),
            "duration": item.get("duration", 0),
            "remote_support": item.get("remote_support", "No"),
            "test_type": item.get("test_type", [])
        })
    return {"recommended_assessments": response}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
