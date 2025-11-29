from typing import Optional

from pydantic import BaseModel, Field


class ChatPreferencePayload(BaseModel):
    mensaje: str = Field(..., description="Mensaje libre del usuario")
    canal: Optional[str] = Field("web", description="Canal de contacto")
    contacto: Optional[str] = Field(None, description="email o telefono")
    nombre: Optional[str] = None
    usuario_id: Optional[int] = Field(None, description="User id si el usuario está autenticado")
    agency_id: Optional[int] = None
    presupuesto: Optional[float] = None
    zona: Optional[str] = None
    tipo_propiedad: Optional[str] = None
    habitaciones: Optional[int] = None
    banos: Optional[int] = None
    garaje: Optional[bool] = None
    property_id: Optional[int] = None


class ChatPreferenceResponse(BaseModel):
    lead_id: Optional[int] = None
    category: Optional[str] = None
    intent_score: Optional[float] = None
    saved: bool = True
    message: str = "Preferencias guardadas"
    interest_level: Optional[str] = None
    is_interested: Optional[bool] = None
    preferences: Optional[dict] = None
