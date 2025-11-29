from fastapi import APIRouter
from pydantic import BaseModel
from services.conversational_service import ConversationalAgentService

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])

class ChatRequest(BaseModel):
    message: str
    contact_key: str | None = None

@router.post("/")
def chat(req: ChatRequest):
    agent = ConversationalAgentService()
    result = agent.get_reply(req.message, contact_key=req.contact_key)
    return result
