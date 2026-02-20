# test_api.py
import json

import requests

# API endpoint
BASE_URL = "http://localhost:8000"

# Test brief
test_brief = """
Campaign Objective: Launch awareness campaign for new sustainable sneaker line

Target Audience: Environmentally conscious millennials and Gen Z

Product: Eco-friendly sneakers made from recycled ocean plastic

Timeline: Q2 2025

Geography: United States, urban markets
"""


def test_health_check():
    """Test the health check endpoint."""
    print("\n" + "=" * 70)
    print("TEST 1: Health Check")
    print("=" * 70)

    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_knowledge_stats():
    """Test the knowledge stats endpoint."""
    print("\n" + "=" * 70)
    print("TEST 2: Knowledge Base Stats")
    print("=" * 70)

    response = requests.get(f"{BASE_URL}/api/v1/knowledge-stats")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_query_knowledge():
    """Test direct RAG query."""
    print("\n" + "=" * 70)
    print("TEST 3: Direct RAG Query")
    print("=" * 70)

    # Fix: Use query parameters instead of JSON body
    params = {"query": "AI personalization", "doc_type": "trends", "n_results": 2}

    response = requests.post(
        f"{BASE_URL}/api/v1/query-knowledge",
        params=params,  # Changed from json=payload to params=params
    )
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Found {len(result.get('results', []))} results")
    if result.get("results"):
        print(f"First result: {result['results'][0]['content'][:200]}...")


def test_enhance_brief():
    """Test the main brief enhancement endpoint."""
    print("\n" + "=" * 70)
    print("TEST 4: Brief Enhancement (Full Pipeline)")
    print("=" * 70)

    payload = {
        "brief": test_brief,
        "include_trends": True,
        "include_cases": True,
        "include_landscape": True,
        "n_results": 3,  # Fewer results for faster testing
    }

    print("Sending request...")
    response = requests.post(f"{BASE_URL}/api/v1/enhance-brief", json=payload)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\nProcessing Time: {result['processing_time_seconds']:.2f} seconds")
        print(
            f"\nBrief Analysis (first 300 chars):\n{result['brief_analysis'][:300]}..."
        )
        print(
            f"\nFinal Insights (first 500 chars):\n{result['final_insights'][:500]}..."
        )

        # Save full response to file
        with open("api_response.json", "w") as f:
            json.dump(result, f, indent=2)
        print("\nFull response saved to api_response.json")
    else:
        print(f"Error: {response.text}")


if __name__ == "__main__":
    print("PATHFINDER AI - API TESTS")
    print("=" * 70)

    try:
        test_health_check()
        test_knowledge_stats()
        test_query_knowledge()
        test_enhance_brief()

        print("\n" + "=" * 70)
        print("ALL TESTS COMPLETE ✓")
        print("=" * 70)

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API. Make sure the server is running:")
        print("   pipenv run python main.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
