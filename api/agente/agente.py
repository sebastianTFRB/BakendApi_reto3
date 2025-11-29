from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from schemas.agent import AnalyticsSummary, LeadAnalyzeRequest, LeadAnalyzeResponse
from services.agent.history import resolve_history_key
from services.agent.lead_agent import LeadAgentService
from services.analytics import AnalyticsService

router = APIRouter(prefix="/api", tags=["lead-agent", "analytics"])


def _history_key_from_request(lead: LeadAnalyzeRequest) -> Optional[str]:
    # usa un id estable para compartir contexto entre front y WhatsApp
    return resolve_history_key(lead.usuario_id, lead.contacto, lead.nombre)


def _run_analysis(lead: LeadAnalyzeRequest) -> LeadAnalyzeResponse:
    history_key = _history_key_from_request(lead)
    service = LeadAgentService()
    result = service.analyze_and_persist(lead, history_key=history_key)
    return LeadAnalyzeResponse(**result)


@router.post("/agent/analyze", response_model=LeadAnalyzeResponse)
async def analyze_lead(lead: LeadAnalyzeRequest) -> LeadAnalyzeResponse:
    try:
        return _run_analysis(lead)
    except Exception as exc:  # Defensive: unexpected runtime issues.
        raise HTTPException(status_code=500, detail="Error interno del agente") from exc


@router.post("/lead/analyze", response_model=LeadAnalyzeResponse)
async def analyze_lead_legacy(lead: LeadAnalyzeRequest) -> LeadAnalyzeResponse:
    # Alias para compatibilidad con el path previo.
    return await analyze_lead(lead)


@router.get("/analytics/leads/summary", response_model=AnalyticsSummary)
async def analytics_summary(
    channel: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
) -> AnalyticsSummary:
    service = AnalyticsService()
    return AnalyticsSummary(**service.get_lead_summary(channel=channel, from_date=from_date, to_date=to_date))


@router.get("/analytics/leads/summary-by-agency/{agency_id}", response_model=AnalyticsSummary)
async def analytics_summary_by_agency(
    agency_id: int,
    channel: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
) -> AnalyticsSummary:
    service = AnalyticsService()
    return AnalyticsSummary(
        **service.get_lead_summary_by_agency(
            agency_id=agency_id,
            channel=channel,
            from_date=from_date,
            to_date=to_date,
        )
    )


@router.get("/analytics/summary", response_model=AnalyticsSummary)
async def analytics_summary_alias(
    channel: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
) -> AnalyticsSummary:
    # Alias para mantener compatibilidad con el path anterior.
    return await analytics_summary(channel=channel, from_date=from_date, to_date=to_date)
