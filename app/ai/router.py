from fastapi import APIRouter, HTTPException, Request, status

from app.ai import service
from app.ai.exceptions import InvalidRequest, OpenAIError
from app.ai.schemas import AskRequest, AskResponse

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask_ai(request_data: AskRequest, request: Request):
    """Ask a question to the AI assistant with access to procurement system data."""
    try:
        if not request_data.question.strip():
            raise InvalidRequest("Question cannot be empty")

        answer = await service.ask_ai_with_mcp(request_data.question, request)
        return AskResponse(answer=answer)

    except InvalidRequest as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except OpenAIError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
