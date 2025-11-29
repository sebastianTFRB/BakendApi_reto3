from fastapi import APIRouter, Depends

from core.security import get_current_user
from schemas.chatbot import ChatPreferencePayload, ChatPreferenceResponse
from services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["chatbot"])


@router.post("/preferences", response_model=ChatPreferenceResponse)
def save_preferences(payload: ChatPreferencePayload, current_user=Depends(get_current_user)):
    """
    Guarda preferencias paso a paso desde el chatbot web.
    """
    service = ChatService()
    result = service.save_preferences(
        mensaje=payload.mensaje,
        canal=payload.canal or "web",
        contacto=payload.contacto,
        nombre=payload.nombre,
        usuario_id=payload.usuario_id or (current_user.get("id") if current_user else None),
        agency_id=payload.agency_id or current_user.get("agency_id"),
        property_id=payload.property_id,
        preferencias={
            "presupuesto": payload.presupuesto,
            "zona": payload.zona,
            "tipo_propiedad": payload.tipo_propiedad,
            "habitaciones": payload.habitaciones,
            "banos": payload.banos,
            "garaje": payload.garaje,
        },
    )
    return ChatPreferenceResponse(**result, saved=True)
