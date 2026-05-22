from openai import OpenAI
from fastapi import HTTPException
from ..config import settings
from ..schemas import AIRequest, AIResponse
import logging

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)


async def get_ai_response(request: AIRequest) -> AIResponse:
    """
    Call OpenAI API and return structured response
    """
    try:
        messages = []

        # add system context if provided
        if request.context:
            messages.append({
                "role":    "system",
                "content": request.context
            })

        messages.append({
            "role":    "user",
            "content": request.prompt
        })

        response = client.chat.completions.create(
            model       = "gpt-4o",
            messages    = messages,
            max_tokens  = request.max_tokens,
            temperature = request.temperature,
        )

        return AIResponse(
            response    = response.choices[0].message.content,
            tokens_used = response.usage.total_tokens,
            model       = response.model
        )

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(status_code=502, detail="AI service temporarily unavailable")


async def analyze_document(file_content: str, question: str) -> str:
    """Analyze a document with AI"""
    try:
        response = client.chat.completions.create(
            model = "gpt-4o",
            messages = [
                {
                    "role":    "system",
                    "content": "You are a helpful document analyzer. Be concise and accurate."
                },
                {
                    "role":    "user",
                    "content": f"Document:\n{file_content}\n\nQuestion: {question}"
                }
            ],
            max_tokens = 1000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        raise HTTPException(status_code=502, detail="Analysis failed")


async def generate_embeddings(text: str) -> list:
    """Generate embeddings for semantic search"""
    try:
        response = client.embeddings.create(
            model = "text-embedding-3-small",
            input = text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=502, detail="Embedding generation failed")
