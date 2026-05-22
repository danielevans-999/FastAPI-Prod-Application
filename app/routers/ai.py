from fastapi import APIRouter, Depends, HTTPException
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import AIRequest, AIResponse, MessageResponse
import httpx

router = APIRouter(prefix="/api/ai", tags=["AI Features"])


async def call_openai(prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> dict:
    """Call OpenAI Responses API"""
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "input": prompt,
                "max_output_tokens": max_tokens,
            }
        )
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="AI service error")
        return response.json()


@router.post("/chat", response_model=AIResponse)
async def ai_chat(
    request: AIRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a prompt to AI and get a response"""
    result = await call_openai(request.prompt, request.max_tokens, request.temperature)

    # Extract text from Responses API format
    output_text = ""
    for item in result.get("output", []):
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    output_text += content.get("text", "")

    return {
        "response":    output_text,
        "tokens_used": result.get("usage", {}).get("total_tokens", 0),
        "model":       result.get("model", "gpt-4o")
    }


@router.post("/summarize", response_model=AIResponse)
async def summarize_text(
    text: str,
    current_user: User = Depends(get_current_user)
):
    """Summarize a block of text using AI"""
    prompt = f"Summarize the following text concisely:\n\n{text}"
    result = await call_openai(prompt, max_tokens=300)

    output_text = ""
    for item in result.get("output", []):
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    output_text += content.get("text", "")

    return {
        "response":    output_text,
        "tokens_used": result.get("usage", {}).get("total_tokens", 0),
        "model":       result.get("model", "gpt-4o")
    }


@router.post("/analyze-payment", response_model=AIResponse)
async def analyze_payment_patterns(
    db=Depends(lambda: None),
    current_user: User = Depends(get_current_user)
):
    """AI powered payment pattern analysis"""
    prompt = f"""
    Analyze payment behavior for user {current_user.username} 
    and provide insights about their spending patterns.
    Keep it concise and actionable.
    """
    result = await call_openai(prompt, max_tokens=400)

    output_text = ""
    for item in result.get("output", []):
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    output_text += content.get("text", "")

    return {
        "response":    output_text,
        "tokens_used": result.get("usage", {}).get("total_tokens", 0),
        "model":       result.get("model", "gpt-4o")
    }
