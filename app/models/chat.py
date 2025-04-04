from pydantic import BaseModel
from typing import List, Optional, Dict

class ChatRequest(BaseModel):
    message: str
    user_id: str

class ChatResponse(BaseModel):
    message: str
    recommendations: Optional[List[Dict]] = None

class ChatMessage(BaseModel):
    user_id: str
    message: str
    response: str
    intent: str
    recommendations: Optional[List[Dict]] = None 