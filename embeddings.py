import json
import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer

def load_assessment_data():
    with open("assessments.json", "r", encoding="utf-8") as data_file:
        assessment_list = json.load(data_file)
    return assessment_list

def build_search_text(single_assessment):
    name_part = single_assessment.get("name", "")
    desc_part = single_assessment.get("description", "")
    type_part = " ".join(single_assessment.get("test_type", []))
    combined_text = f"{name_part} {type_part} {desc_part}"
    return combined_text.strip()

def create_embeddings():
    print("Loading assessment data...")
    all_assessments = load_assessment_data()
    print(f"Loaded {len(all_assessments)} assessments")

    print("Loading AI embedding model...")
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    print("Creating search texts...")
    search_texts = [build_search_text(item) for item in all_assessments]

    print("Generating embeddings (this may take 2-3 minutes)...")
    text_vectors = embedding_model.encode(
        search_texts,
        show_progress_bar=True,
        batch_size=32
    )

    text_vectors = np.array(text_vectors).astype("float32")

    print("Building FAISS vector index...")
    vector_dimension = text_vectors.shape[1]
    faiss_index = faiss.IndexFlatL2(vector_dimension)
    faiss_index.add(text_vectors)

    print("Saving index and data...")
    faiss.write_index(faiss_index, "vector_index.faiss")

    with open("assessment_data.pkl", "wb") as pkl_file:
        pickle.dump(all_assessments, pkl_file)

    with open("search_texts.pkl", "wb") as txt_file:
        pickle.dump(search_texts, txt_file)

    print(f"Done! Indexed {faiss_index.ntotal} assessments")
    print("Files saved: vector_index.faiss, assessment_data.pkl, search_texts.pkl")

if __name__ == "__main__":
    create_embeddings()
