from fastapi import APIRouter, HTTPException

from schemas.agent import AnalyticsSummary, LeadAnalyzeRequest, LeadAnalyzeResponse
from services.agent.lead_agent import analyze_lead_message
from services.analytics import get_analytics_summary, record_lead_event

router = APIRouter(prefix="/api", tags=["lead-agent"])


@router.post("/lead/analyze", response_model=LeadAnalyzeResponse)
async def analyze_lead(lead: LeadAnalyzeRequest) -> LeadAnalyzeResponse:
    try:
        result = analyze_lead_message(lead.mensaje)
    except Exception as exc:  # Defensive: unexpected runtime issues.
        raise HTTPException(status_code=500, detail="Error interno del agente") from exc

    record_lead_event(lead.dict(), result)

    return LeadAnalyzeResponse(
        lead_score=result.get("lead_score"),
        presupuesto=result.get("presupuesto"),
        zona=result.get("zona"),
        tipo_propiedad=result.get("tipo_propiedad"),
        urgencia=result.get("urgencia"),
        razonamiento=result.get("razonamiento"),
    )


@router.get("/analytics/summary", response_model=AnalyticsSummary)
async def analytics_summary() -> AnalyticsSummary:
    return AnalyticsSummary(**get_analytics_summary())
