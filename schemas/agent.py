"""
Pydantic schemas for the lead analysis API.
"""

from typing import Dict, Literal, Optional, List

from pydantic import BaseModel, Field


class LeadAnalyzeRequest(BaseModel):
    mensaje: str = Field(..., description="Mensaje o texto libre del lead.")
    canal: Optional[str] = Field("web", description="Origen del lead: web, whatsapp, telegram, etc.")
    nombre: Optional[str] = Field(None, description="Nombre de la persona.")
    contacto: Optional[str] = Field(None, description="Datos de contacto: email o whatsapp.")
    agency_id: Optional[int] = Field(None, description="Agencia vinculada al lead si aplica.")
    post_id: Optional[str] = Field(None, description="ID de la publicación o propiedad si ya existe.")
    usuario_id: Optional[str] = Field(
        None, description="Identificador unico (usuario/sesion) para unir historial entre front y WhatsApp."
    )


class LeadAnalyzeResponse(BaseModel):
    lead_id: Optional[int] = Field(None, description="Identificador del lead en Supabase.")
    lead_score: Literal["A", "B", "C"] = Field(..., description="Clasificación del lead.")
    is_interested: bool = Field(..., description="Interesado verdadero si score A/B.")
    interest_level: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        ..., description="Nivel derivado de A/B/C."
    )
    presupuesto: Optional[int] = Field(
        None, description="Presupuesto en moneda local sin símbolos, o null."
    )
    zona: Optional[str] = Field(None, description="Ciudad o zona indicada, o null.")
    tipo_propiedad: Optional[
        Literal["apartamento", "casa", "local", "oficina", "lote", "finca", "otro"]
    ] = Field(
        None, description="Tipo de propiedad normalizado."
    )
    urgencia: Literal["alta", "media", "baja"] = Field(..., description="Nivel de urgencia.")
    intencion_real: Optional[str] = Field(None, description="Resumen corto de la intención declarada.")
    razonamiento: str = Field(..., description="Breve explicación del score.")
    recommendations: Optional[List[Dict[str, object]]] = Field(
        None,
        description="Listado de propiedades recomendadas según preferencias (id, title, price, location, property_type, bedrooms, bathrooms, parking, photos).",
    )


class AnalyticsSummary(BaseModel):
    total_leads: int
    by_score: Dict[str, int]
    by_interest: Dict[str, int]
    by_channel: Dict[str, int]
