# test_new_key.py
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os

async def test_key():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    print(f"Testing API key: {api_key[:15]}...{api_key[-5:]}")
    
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    
    try:
        response = await client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=20
        )
        print(f"✅ SUCCESS! Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_key())