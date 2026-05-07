import asyncio
from app.core.llm_router import LLMRouter
from app.models.schemas import LLMRequest, LLMProvider

async def test_full_chain():
    router = LLMRouter()
    
    # Test Groq with large max_tokens
    req = LLMRequest(provider=LLMProvider.GROQ, prompt="Write a huge text.", max_tokens=4096)
    
    print("Testing Groq...")
    resp1 = await router.generate(req)
    print("Groq Success:", resp1.success, "Error:", resp1.error)

    # Test Mistral with large max_tokens
    req = LLMRequest(provider=LLMProvider.MISTRAL, prompt="Write a huge text.", max_tokens=4096)
    print("Testing Mistral...")
    resp2 = await router.generate(req)
    print("Mistral Success:", resp2.success, "Error:", resp2.error)

if __name__ == "__main__":
    asyncio.run(test_full_chain())
