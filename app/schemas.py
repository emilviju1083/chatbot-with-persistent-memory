
from datetime import datetime
from pydantic import BaseModel, Field


# Data received from the user
class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=5000
    )
    conversation_id: int | None = None


# Data returned for a single message
class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


# Data returned for a conversation
class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


# Complete chatbot response
class ChatResponse(BaseModel):
    conversation_id: int
    user_message: MessageResponse
    assistant_message: MessageResponse

class ConversationSummary(BaseModel):
    title: str
    summary: str
    action_items: list[str] = Field(default_factory=list)
