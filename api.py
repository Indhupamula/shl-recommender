import json
import pickle
import numpy as np
import faiss
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)

app = FastAPI(title="SHL Assessment Recommender")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Load all saved data
print("Loading assessment data and models...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
faiss_index = faiss.read_index("vector_index.faiss")

with open("assessment_data.pkl", "rb") as data_file:
    stored_assessments = pickle.load(data_file)

with open("search_texts.pkl", "rb") as text_file:
    stored_texts = pickle.load(text_file)

gemini_model = genai.GenerativeModel("gemini-2.0-flash")
print("All models loaded successfully!")

class QueryInput(BaseModel):
    query: str

def extract_text_from_url(target_url):
    try:
        url_response = requests.get(target_url, timeout=10)
        url_soup = BeautifulSoup(url_response.content, "html.parser")
        extracted_text = url_soup.get_text(separator=" ", strip=True)
        return extracted_text[:3000]
    except Exception as url_error:
        print(f"Could not fetch URL: {url_error}")
        return target_url

def enhance_query_with_gemini(raw_query):
    enhancement_prompt = f"""
    Analyze this job description or query and extract key skills and requirements:
    
    Query: {raw_query}
    
    Return a enhanced search query focusing on:
    1. Technical skills needed
    2. Soft skills needed  
    3. Job role and level
    4. Assessment types that would be relevant
    
    Keep response under 100 words.
    """
    try:
        gemini_response = gemini_model.generate_content(enhancement_prompt)
        return gemini_response.text
    except Exception as gemini_error:
        print(f"Gemini error: {gemini_error}")
        return raw_query

def find_similar_assessments(search_query, top_k=20):
    query_vector = embedding_model.encode([search_query]).astype("float32")
    similarity_distances, similar_indices = faiss_index.search(query_vector, top_k)
    candidate_assessments = []
    for idx in similar_indices[0]:
        if idx < len(stored_assessments):
            candidate_assessments.append(stored_assessments[idx])
    return candidate_assessments

def balance_recommendations(candidates, final_count=10):
    personality_types = ["P", "B"]
    knowledge_types = ["K", "A"]
    other_types = ["C", "E", "S", "D"]
    
    personality_items = []
    knowledge_items = []
    other_items = []
    
    for item in candidates:
        item_types = item.get("test_type", [])
        if any(t in personality_types for t in item_types):
            personality_items.append(item)
        elif any(t in knowledge_types for t in item_types):
            knowledge_items.append(item)
        else:
            other_items.append(item)
    
    balanced_results = []
    personality_quota = final_count // 3
    knowledge_quota = final_count // 3
    other_quota = final_count - personality_quota - knowledge_quota
    
    balanced_results.extend(personality_items[:personality_quota])
    balanced_results.extend(knowledge_items[:knowledge_quota])
    balanced_results.extend(other_items[:other_quota])
    
    # Fill remaining slots if any category is short
    all_remaining = [i for i in candidates if i not in balanced_results]
    while len(balanced_results) < final_count and all_remaining:
        balanced_results.append(all_remaining.pop(0))
    
    return balanced_results[:final_count]

def rerank_with_gemini(raw_query, candidate_list):
    candidates_text = ""
    for idx, item in enumerate(candidate_list[:15]):
        candidates_text += f"{idx+1}. {item['name']} (Types: {item.get('test_type', [])})\n"
    
    rerank_prompt = f"""
    Job Query: {raw_query}
    
    Available assessments:
    {candidates_text}
    
    Select the 10 most relevant assessments for this query.
    Consider both technical AND soft skills balance.
    Return ONLY the numbers of selected assessments as comma separated values.
    Example: 1,3,5,7,2,4,6,8,9,10
    """
    try:
        rerank_response = gemini_model.generate_content(rerank_prompt)
        selected_numbers = rerank_response.text.strip().split(",")
        reranked = []
        for num_str in selected_numbers:
            try:
                num = int(num_str.strip()) - 1
                if 0 <= num < len(candidate_list):
                    reranked.append(candidate_list[num])
            except ValueError:
                continue
        return reranked[:10] if reranked else candidate_list[:10]
    except Exception as rerank_error:
        print(f"Reranking error: {rerank_error}")
        return candidate_list[:10]

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/recommend")
def get_recommendations(user_input: QueryInput):
    input_query = user_input.query
    
    # Check if query is a URL
    if input_query.startswith("http"):
        print("URL detected, extracting text...")
        input_query = extract_text_from_url(input_query)
    
    # Enhance query with Gemini
    print("Enhancing query with Gemini...")
    enhanced_query = enhance_query_with_gemini(input_query)
    
    # Find similar assessments using FAISS
    print("Finding similar assessments...")
    candidate_pool = find_similar_assessments(enhanced_query, top_k=20)
    
    # Balance recommendations
    balanced_pool = balance_recommendations(candidate_pool, final_count=15)
    
    # Rerank with Gemini
    print("Reranking with Gemini...")
    final_recommendations = rerank_with_gemini(input_query, balanced_pool)
    
    # Format response
    response_items = []
    for item in final_recommendations[:10]:
        response_items.append({
            "url": item.get("url", ""),
            "name": item.get("name", ""),
            "adaptive_support": item.get("adaptive_support", "No"),
            "description": item.get("description", ""),
            "duration": item.get("duration", 0),
            "remote_support": item.get("remote_support", "No"),
            "test_type": item.get("test_type", [])
        })
    
    return {"recommended_assessments": response_items}
