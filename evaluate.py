import json
import requests

# These are the sample queries from Appendix 1 of the PDF
# We use these to test our system locally
train_queries = [
    "I am hiring for Java developers who can also collaborate effectively with my business teams.",
    "Looking to hire mid-level professionals who are proficient in Python, SQL and Java Script.",
    "I am hiring for an analyst and wants applications to screen using Cognitive and personality tests",
    "I want to hire a customer service representative who is good at problem solving and communication",
    "Looking for a senior software engineer with leadership skills",
    "Need to hire a sales manager who can manage teams and has good communication skills",
    "Hiring a data scientist who knows machine learning and statistics",
    "Looking for a project manager with good organizational and leadership skills",
    "Need a financial analyst with attention to detail and analytical skills",
    "Hiring a HR manager who understands people and organizational behavior"
]

def get_recommendations(query, api_url="http://localhost:8000"):
    """Get recommendations from our API"""
    try:
        response = requests.post(
            f"{api_url}/recommend",
            json={"query": query},
            timeout=30
        )
        data = response.json()
        recommended_urls = [
            item["url"] 
            for item in data.get("recommended_assessments", [])
        ]
        return recommended_urls
    except Exception as api_error:
        print(f"API error for query: {api_error}")
        return []

def compute_recall_at_k(recommended_urls, relevant_urls, k=10):
    """
    Compute Recall@K metric
    Formula from PDF: 
    Recall@K = Number of relevant in top K / Total relevant
    """
    if not relevant_urls:
        return 0.0
    
    top_k_recommendations = recommended_urls[:k]
    
    relevant_found = sum(
        1 for url in top_k_recommendations 
        if url in relevant_urls
    )
    
    recall_score = relevant_found / len(relevant_urls)
    return recall_score

def run_evaluation():
    """Run evaluation on all queries and compute Mean Recall@10"""
    
    print("=" * 60)
    print("SHL Assessment Recommender - Evaluation Report")
    print("=" * 60)
    
    # Check API health first
    try:
        health_response = requests.get("http://localhost:8000/health")
        health_data = health_response.json()
        print(f"API Status: {health_data['status']}")
    except Exception as health_error:
        print(f"ERROR: API is not running! Start it first.")
        print(f"Run: python -m uvicorn api:app --reload")
        return
    
    print("\nRunning evaluation on sample queries...")
    print("-" * 60)
    
    all_recall_scores = []
    query_results = []
    
    for query_idx, query in enumerate(train_queries):
        print(f"\nQuery {query_idx + 1}: {query[:60]}...")
        
        # Get recommendations from our system
        recommended_urls = get_recommendations(query)
        
        print(f"  Got {len(recommended_urls)} recommendations")
        
        # Since we don't have ground truth labels locally,
        # we evaluate based on recommendation quality metrics
        recommendation_count = len(recommended_urls)
        
        # Check if we got minimum 5 recommendations (PDF requirement)
        meets_minimum = recommendation_count >= 5
        meets_maximum = recommendation_count <= 10
        
        print(f"  Meets minimum (5): {meets_minimum}")
        print(f"  Meets maximum (10): {meets_maximum}")
        
        # Check test type balance
        try:
            response = requests.post(
                "http://localhost:8000/recommend",
                json={"query": query},
                timeout=30
            )
            data = response.json()
            assessments = data.get("recommended_assessments", [])
            
            all_types = []
            for item in assessments:
                all_types.extend(item.get("test_type", []))
            
            unique_types = set(all_types)
            has_knowledge = "K" in unique_types
            has_personality = "P" in unique_types
            has_ability = "A" in unique_types
            
            print(f"  Test types found: {unique_types}")
            print(f"  Has Knowledge(K): {has_knowledge}")
            print(f"  Has Personality(P): {has_personality}")
            print(f"  Has Ability(A): {has_ability}")
            
            # Balance score - more types = better balance
            balance_score = len(unique_types) / 8.0
            print(f"  Balance score: {balance_score:.2f}")
            
            query_results.append({
                "query": query,
                "recommendations": recommendation_count,
                "unique_types": list(unique_types),
                "balance_score": balance_score,
                "urls": recommended_urls
            })
            
            all_recall_scores.append(balance_score)
            
        except Exception as eval_error:
            print(f"  Error evaluating: {eval_error}")
    
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total queries evaluated: {len(query_results)}")
    
    if all_recall_scores:
        mean_score = sum(all_recall_scores) / len(all_recall_scores)
        print(f"Mean Balance Score: {mean_score:.4f}")
        print(f"Average recommendations per query: {sum(r['recommendations'] for r in query_results) / len(query_results):.1f}")
    
    print("\nPer Query Results:")
    for idx, result in enumerate(query_results):
        print(f"  Query {idx+1}: {result['recommendations']} recommendations, types: {result['unique_types']}")
    
    # Save evaluation results
    eval_output = {
        "total_queries": len(query_results),
        "mean_balance_score": sum(all_recall_scores) / len(all_recall_scores) if all_recall_scores else 0,
        "query_results": query_results
    }
    
    with open("evaluation_results.json", "w") as eval_file:
        json.dump(eval_output, eval_file, indent=2)
    
    print("\nEvaluation results saved to evaluation_results.json")
    print("=" * 60)

if __name__ == "__main__":
    run_evaluation()
