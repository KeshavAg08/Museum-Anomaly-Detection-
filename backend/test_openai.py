#!/usr/bin/env python3
"""Test script to verify OpenAI API connection"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def test_openai():
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not found in environment variables")
        return
    
    print(f"✅ OPENAI_API_KEY found (starts with: {OPENAI_API_KEY[:10]}...)")
    
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        print("✅ OpenAI client created successfully")
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in one sentence."}
        ]
        
        print("🔄 Testing OpenAI API call...")
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2,
        )
        
        reply = resp.choices[0].message.content
        print(f"✅ OpenAI API call successful!")
        print(f"Response: {reply}")
        
    except Exception as e:
        print(f"❌ OpenAI API call failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_openai())
