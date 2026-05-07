import asyncio
import httpx
from app.core.config import settings

async def test_apis():
    client = httpx.AsyncClient()
    
    # Test Groq
    try:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 4096},
            headers={"Authorization": f"Bearer {settings.groq_api_key}"}
        )
        print("Groq:", resp.status_code, resp.text)
    except Exception as e:
        print("Groq Exception:", e)

if __name__ == "__main__":
    asyncio.run(test_apis())
