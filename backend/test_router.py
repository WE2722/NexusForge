import asyncio
from app.core.llm_router import LLMRouter
from app.models.schemas import LLMRequest, LLMProvider

async def test_providers():
    router = LLMRouter()
    
    req_groq = LLMRequest(provider=LLMProvider.GROQ, prompt="Say hello", max_tokens=100)
    req_mistral = LLMRequest(provider=LLMProvider.MISTRAL, prompt="Say hello", max_tokens=100)
    
    print("Testing Groq...")
    try:
        resp1 = await router._call_groq(req_groq)
        print("Groq Success:", resp1.success)
    except Exception as e:
        print("Groq Error:", e)
        
    print("Testing Mistral...")
    try:
        resp2 = await router._call_mistral(req_mistral)
        print("Mistral Success:", resp2.success)
    except Exception as e:
        print("Mistral Error:", e)

if __name__ == "__main__":
    asyncio.run(test_providers())
