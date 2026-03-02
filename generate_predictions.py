import requests
import csv
import time

# These are the 9 test queries from the PDF (Appendix 1)
test_queries = [
    "I am hiring for Java developers who can also collaborate effectively with my business teams.",
    "Looking to hire mid-level professionals who are proficient in Python, SQL and Java Script.",
    "I am hiring for an analyst and wants applications to screen using Cognitive and personality tests",
    "I want to hire a customer service representative who is good at problem solving and communication",
    "Looking for a senior software engineer with leadership skills",
    "Need to hire a sales manager who can manage teams and has good communication skills",
    "Hiring a data scientist who knows machine learning and statistics",
    "Looking for a project manager with good organizational and leadership skills",
    "Need a financial analyst with attention to detail and analytical skills"
]

def get_recommendations(query, api_url="http://localhost:8000"):
    try:
        response = requests.post(
            f"{api_url}/recommend",
            json={"query": query},
            timeout=60
        )
        data = response.json()
        recommended_urls = [
            item["url"]
            for item in data.get("recommended_assessments", [])
        ]
        return recommended_urls
    except Exception as err:
        print(f"Error for query: {err}")
        return []

def generate_csv_predictions():
    print("=" * 60)
    print("Generating CSV Predictions on Test Queries...")
    print("=" * 60)

    all_rows = []

    for idx, query in enumerate(test_queries):
        print(f"\nQuery {idx + 1}/{len(test_queries)}: {query[:60]}...")
        
        recommended_urls = get_recommendations(query)
        print(f"  Got {len(recommended_urls)} recommendations")

        for url in recommended_urls:
            all_rows.append({
                "query": query,
                "assessment_url": url
            })

        time.sleep(2)

    # Save to CSV
    output_file = "predictions.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["query", "assessment_url"])
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n{'='*60}")
    print(f"CSV saved to {output_file}")
    print(f"Total rows: {len(all_rows)}")
    print(f"Total queries: {len(test_queries)}")
    print("="*60)

if __name__ == "__main__":
    generate_csv_predictions()
