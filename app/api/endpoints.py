from fastapi import APIRouter, Depends
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()

@router.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Endpoint xử lý chat với user
    """
    try:
        # Lấy response từ chat service
        response = await chat_service.process_message(
            message=request.message,
            user_id=request.user_id
        )
        
        # Trả về ChatResponse với format mới
        return ChatResponse(
            message=response["message"],
            recommendations=response["recommendations"]
        )
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return ChatResponse(
            message="Xin lỗi, có lỗi xảy ra. Vui lòng thử lại.",
            recommendations=None
        ) 