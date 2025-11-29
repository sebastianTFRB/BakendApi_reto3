"""
Lead analysis agent that uses LangChain + LLM to classify real-estate leads and persist them.
"""

from __future__ import annotations

import json
import re
import logging
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from core.config import settings
from core.domain import LeadUrgency
from db.supabase_client import get_supabase_client
from repositories.interaction_repository import LeadInteractionRepository
from repositories.lead_repository import LeadRepository
from services.agent.history import format_history, history_store
from services.agent.prompts import BASE_PROMPT
from utils.scoring import interest_from_category

load_dotenv()

MODEL_NAME = settings.llm_model
TEMPERATURE = settings.llm_temperature

logger = logging.getLogger(__name__)

DEFAULT_RESPONSE: Dict[str, Any] = {
    "presupuesto": None,
    "zona": None,
    "tipo_propiedad": None,
    "urgencia": "media",
    "lead_score": "C",
    "intencion_real": None,
    "razonamiento": "No se pudo interpretar bien el mensaje",
    "is_interested": False,
    "interest_level": "LOW",
}


def _get_value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _build_agent_summary(result: Dict[str, Any]) -> str:
    return (
        "Datos detectados -> "
        f"presupuesto: {result.get('presupuesto') or 'sin dato'}, "
        f"zona: {result.get('zona') or 'sin dato'}, "
        f"tipo: {result.get('tipo_propiedad') or 'sin dato'}, "
        f"urgencia: {result.get('urgencia') or 'sin dato'}, "
        f"lead_score: {result.get('lead_score') or 'C'}; "
        f"razonamiento: {result.get('razonamiento') or 'sin razonamiento'}"
    )


def _persist_history(history_key: Optional[str], user_message: str, result: Dict[str, Any]) -> None:
    if not history_key:
        return
    history_store.append(history_key, "user", user_message)
    history_store.append(history_key, "agent", _build_agent_summary(result))


def _build_prompt(message: str, history_key: Optional[str]) -> str:
    history_text = format_history(history_store.get(history_key))
    return BASE_PROMPT.replace("{historial}", history_text).replace("{mensaje}", message)


def _load_llm() -> Optional[ChatOpenAI]:
    """
    Configure ChatOpenAI using environment variables; the OpenAI client
    reads OPENAI_API_KEY from the environment by default.
    """
    try:
        return ChatOpenAI(model=MODEL_NAME, temperature=TEMPERATURE)
    except Exception:
        return None


llm = _load_llm()


def _parse_json_response(content: str) -> Dict[str, Any]:
    """
    Attempt to parse the LLM response as JSON; tolerate fenced code blocks.
    """
    cleaned = content.strip()

    # Remove Markdown code fences if present.
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        fence_index = cleaned.find("{")
        if fence_index != -1:
            cleaned = cleaned[fence_index:]

    # Some models return double braces {{ ... }}; trim one layer.
    if cleaned.startswith("{{") and cleaned.endswith("}}"):
        cleaned = cleaned[1:-1].strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                pass
        return DEFAULT_RESPONSE.copy()


def _normalize_presupuesto(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit())
        return int(digits) if digits else None
    return None


def _normalize_tipo_propiedad(value: Any) -> Optional[str]:
    if value is None:
        return None

    if isinstance(value, str):
        v = value.strip().lower()
        if not v:
            return None
        if v in {"apartamento", "apto", "departamento", "dept", "dept.", "apartment"}:
            return "apartamento"
        if v in {"casa", "house"}:
            return "casa"
        if v in {"local", "local comercial", "comercial"}:
            return "local"
        if v in {"lote", "terreno", "parcela"}:
            return "lote"
        if v in {"oficina", "office"}:
            return "oficina"
        if v in {"finca", "granja"}:
            return "finca"
        if v in {"otro", "otros", "other"}:
            return "otro"
        return "otro"

    return None


def _normalize_urgencia(value: Any) -> str:
    if isinstance(value, str):
        urg = value.strip().lower()
    else:
        urg = "media"

    if urg not in {"alta", "media", "baja"}:
        return "media"
    return urg


def _normalize_lead_score(value: Any) -> str:
    score = str(value).upper() if value is not None else "C"
    if score not in {"A", "B", "C"}:
        score = "C"
    return score


def _normalize_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return str(value)


def _apply_rule_based_score(
    lead_score: str,
    presupuesto: Optional[int],
    zona: Optional[str],
    tipo_propiedad: Optional[str],
    urgencia: str,
    intencion_real: Optional[str],
) -> str:
    """
    Lightweight heuristics to reinforce LLM output.
    """
    has_budget = presupuesto is not None
    has_location = bool(zona)
    has_property_type = bool(tipo_propiedad)
    high_intent = urgencia == "alta"
    medium_intent = urgencia == "media"
    has_intention = bool(intencion_real)

    if (has_budget and (has_location or has_property_type) and has_intention) and (high_intent or medium_intent):
        return "A"

    if (has_budget and medium_intent) or (has_property_type and medium_intent):
        return "B"

    if lead_score == "A" and not has_budget and not has_location:
        return "B"
    if lead_score == "B" and urgencia == "baja":
        return "C"
    if has_budget or has_property_type or has_location:
        return lead_score if lead_score in {"A", "B"} else "B"
    return lead_score


def _interest_flags(lead_score: str) -> Tuple[bool, str]:
    interested, level = interest_from_category(lead_score)
    return interested, level


def _intent_score_from_result(result: Dict[str, Any]) -> float:
    """
    Provide a stable numeric intent score derived from the qualitative output.
    """
    base_map = {"A": 88.0, "B": 65.0, "C": 32.0}
    score = base_map.get(result.get("lead_score"), 20.0)

    urg = result.get("urgencia")
    if urg == "alta":
        score += 7
    elif urg == "media":
        score += 3

    if result.get("presupuesto"):
        score += 3
    if result.get("zona"):
        score += 2
    if result.get("tipo_propiedad"):
        score += 2

    return max(0.0, min(score, 100.0))


def _map_urgency_to_domain(urgencia: str) -> LeadUrgency:
    if urgencia == "alta":
        return LeadUrgency.high
    if urgencia == "baja":
        return LeadUrgency.low
    return LeadUrgency.medium


def _normalize_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {
        "presupuesto": _normalize_presupuesto(data.get("presupuesto")),
        "zona": _normalize_text(data.get("zona")),
        "tipo_propiedad": _normalize_tipo_propiedad(data.get("tipo_propiedad")),
        "urgencia": _normalize_urgencia(data.get("urgencia")),
        "lead_score": _normalize_lead_score(data.get("lead_score")),
        "intencion_real": _normalize_text(data.get("intencion_real")),
        "razonamiento": _normalize_text(data.get("razonamiento"))
        or "Sin razonamiento proporcionado",
    }

    normalized["lead_score"] = _apply_rule_based_score(
        lead_score=normalized["lead_score"],
        presupuesto=normalized["presupuesto"],
        zona=normalized["zona"],
        tipo_propiedad=normalized["tipo_propiedad"],
        urgencia=normalized["urgencia"],
        intencion_real=normalized["intencion_real"],
    )
    interested, level = _interest_flags(normalized["lead_score"])
    normalized["is_interested"] = interested
    normalized["interest_level"] = level
    normalized["intent_score"] = _intent_score_from_result(normalized)
    normalized["urgency_value"] = _map_urgency_to_domain(normalized["urgencia"]).value
    return normalized


def analyze_lead_message(message: str, *, history_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze the lead message using the LLM and normalize the response.
    Stores a short chat history per usuario to avoid re-asking for data.
    """
    if llm is None:
        fallback = DEFAULT_RESPONSE.copy()
        fallback["razonamiento"] = "LLM no disponible (clave o dependencia faltante)"
        _persist_history(history_key, message, fallback)
        return fallback

    prompt = _build_prompt(message, history_key)

    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
    except Exception:
        fallback = DEFAULT_RESPONSE.copy()
        _persist_history(history_key, message, fallback)
        return fallback

    parsed = _parse_json_response(content)
    normalized = _normalize_payload(parsed)
    _persist_history(history_key, message, normalized)
    return normalized


class LeadAgentService:
    """
    High-level orchestration: call the LLM agent, persist leads/interactions in Supabase,
    and return a response that the API can expose.
    """

    def __init__(self) -> None:
        supabase = get_supabase_client()
        self.lead_repo = LeadRepository(supabase)
        self.interaction_repo = LeadInteractionRepository(supabase)

    def _parse_contact(self, contact: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        if not contact:
            return None, None
        contact = contact.strip()
        if not contact:
            return None, None
        if "@" in contact:
            return contact, None
        digits = re.sub(r"[^\d+]", "", contact)
        if not digits:
            return None, None
        if digits.startswith("+"):
            return None, digits
        return None, digits

    def _choose_name(self, lead_data: Any, existing: Optional[Dict[str, Any]]) -> str:
        name = _get_value(lead_data, "nombre") or (existing or {}).get("full_name")
        if name:
            return name
        contact = _get_value(lead_data, "contacto")
        if contact:
            return str(contact)
        return "Lead sin nombre"

    def _build_notes(self, existing_notes: Optional[str], result: Dict[str, Any]) -> str:
        details = []
        if result.get("tipo_propiedad"):
            details.append(f"tipo: {result['tipo_propiedad']}")
        if result.get("zona"):
            details.append(f"zona: {result['zona']}")
        if result.get("intencion_real"):
            details.append(f"intencion: {result['intencion_real']}")
        summary = f"Agente -> score {result.get('lead_score')} ({result.get('razonamiento')})"
        block = summary
        if details:
            block = f"{summary}; " + ", ".join(details)
        if existing_notes and block not in existing_notes:
            return f"{existing_notes}\n{block}"
        return block if not existing_notes else existing_notes

    def _build_lead_payload(
        self,
        lead_data: Any,
        result: Dict[str, Any],
        email: Optional[str],
        phone: Optional[str],
        existing: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        preferred_area = result.get("zona") or (existing or {}).get("preferred_area")
        budget = result.get("presupuesto")
        if budget is None and existing:
            budget = existing.get("budget")

        urgency_value = result.get("urgency_value") or _map_urgency_to_domain(result.get("urgencia", "media")).value

        payload = {
            "full_name": self._choose_name(lead_data, existing),
            "email": email or (existing or {}).get("email"),
            "phone": phone or (existing or {}).get("phone"),
            "preferred_area": preferred_area,
            "budget": budget,
            "urgency": urgency_value,
            "notes": self._build_notes((existing or {}).get("notes"), result),
            "status": (existing or {}).get("status") or "new",
            "category": result.get("lead_score"),
            "intent_score": result.get("intent_score"),
            "post_id": _get_value(lead_data, "post_id") or (existing or {}).get("post_id"),
            "agency_id": _get_value(lead_data, "agency_id") or (existing or {}).get("agency_id"),
        }

        # Remove None values to avoid overwriting existing data with nulls.
        return {k: v for k, v in payload.items() if v is not None}

    def _find_existing_lead(
        self, email: Optional[str], phone: Optional[str], agency_id: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        if phone:
            found = self.lead_repo.find_by_phone(phone, agency_id=agency_id)
            if found:
                return found
        if email:
            found = self.lead_repo.find_by_email(email, agency_id=agency_id)
            if found:
                return found
        return None

    def _record_interactions(self, lead_id: int, message: str, channel: str, result: Dict[str, Any]) -> None:
        message_text = message if isinstance(message, str) else str(message)
        if not message_text:
            message_text = "mensaje vacio"

        inbound = {
            "lead_id": lead_id,
            "channel": channel,
            "direction": "inbound",
            "message": message_text,
        }
        self.interaction_repo.create(inbound)

        agent_message = _build_agent_summary(result)
        outbound = {
            "lead_id": lead_id,
            "channel": channel,
            "direction": "outbound",
            "message": agent_message,
        }
        self.interaction_repo.create(outbound)

    def analyze_and_persist(self, lead_data: Any, *, history_key: Optional[str]) -> Dict[str, Any]:
        message = _get_value(lead_data, "mensaje") or ""
        channel = (_get_value(lead_data, "canal") or "web").lower()
        result = analyze_lead_message(message, history_key=history_key)

        # Ensure interest flags even if LLM was unavailable.
        interested, level = _interest_flags(result.get("lead_score"))
        result["is_interested"] = result.get("is_interested", interested)
        result["interest_level"] = result.get("interest_level", level)
        result["intent_score"] = result.get("intent_score") or _intent_score_from_result(result)

        email, phone = self._parse_contact(_get_value(lead_data, "contacto"))
        lead_record: Dict[str, Any] = {"id": None}

        try:
            existing = self._find_existing_lead(email, phone, _get_value(lead_data, "agency_id"))
            payload = self._build_lead_payload(lead_data, result, email, phone, existing)
            if existing:
                lead_record = self.lead_repo.update(existing["id"], payload)
            else:
                lead_record = self.lead_repo.create(payload)
        except Exception as exc:
            logger.error("Lead persistence failed: %s", exc, exc_info=True)
            lead_record = {"id": None}

        try:
            if lead_record.get("id"):
                self._record_interactions(lead_record["id"], message, channel, result)
        except Exception as exc:
            logger.error("Interaction logging failed: %s", exc, exc_info=True)
            pass

        return {
            "lead_id": lead_record.get("id"),
            **result,
        }
