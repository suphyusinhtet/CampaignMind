# test_tools.py
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from pytrends.request import TrendReq

print("Testing dependencies...")

# Test 1: requests
print("\n1. Testing requests...")
response = requests.get("https://httpbin.org/get")
print(f"   ✅ requests working: {response.status_code == 200}")

# Test 2: BeautifulSoup
print("\n2. Testing BeautifulSoup...")
soup = BeautifulSoup("<html><body><h1>Test</h1></body></html>", "html.parser")
print(f"   ✅ BeautifulSoup working: {soup.h1.text == 'Test'}")

# Test 3: DuckDuckGo Search
print("\n3. Testing DuckDuckGo Search...")
try:
    with DDGS() as ddgs:
        results = list(ddgs.text("test query", max_results=1))
        print(f"   ✅ DuckDuckGo working: {len(results) > 0}")
except Exception as e:
    print(f"   ❌ DuckDuckGo error: {e}")

# Test 4: Google Trends
print("\n4. Testing Google Trends...")
try:
    pytrends = TrendReq(hl='en-US', tz=360)
    pytrends.build_payload(['python'], timeframe='today 1-m')
    data = pytrends.interest_over_time()
    print(f"   ✅ Google Trends working: {not data.empty}")
except Exception as e:
    print(f"   ❌ Google Trends error: {e}")

print("\n✅ All tools ready!")