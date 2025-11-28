"""
Lead analysis agent that uses LangChain + LLM to classify real-estate leads.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from core.config import settings
from services.agent.prompts import BASE_PROMPT

load_dotenv()

MODEL_NAME = settings.llm_model
TEMPERATURE = settings.llm_temperature

DEFAULT_RESPONSE: Dict[str, Any] = {
    "presupuesto": None,
    "zona": None,
    "tipo_propiedad": None,
    "urgencia": "media",
    "lead_score": "C",
    "razonamiento": "No se pudo interpretar bien el mensaje",
}


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
) -> str:
    """
    Lightweight heuristics to reinforce LLM output.
    """
    has_budget = presupuesto is not None
    has_location = bool(zona)
    has_property_type = bool(tipo_propiedad)
    high_intent = urgencia == "alta"
    medium_intent = urgencia == "media"

    if (has_budget and (has_location or has_property_type)) and (high_intent or medium_intent):
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


def _normalize_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {
        "presupuesto": _normalize_presupuesto(data.get("presupuesto")),
        "zona": _normalize_text(data.get("zona")),
        "tipo_propiedad": _normalize_tipo_propiedad(data.get("tipo_propiedad")),
        "urgencia": _normalize_urgencia(data.get("urgencia")),
        "lead_score": _normalize_lead_score(data.get("lead_score")),
        "razonamiento": _normalize_text(data.get("razonamiento"))
        or "Sin razonamiento proporcionado",
    }

    normalized["lead_score"] = _apply_rule_based_score(
        lead_score=normalized["lead_score"],
        presupuesto=normalized["presupuesto"],
        zona=normalized["zona"],
        tipo_propiedad=normalized["tipo_propiedad"],
        urgencia=normalized["urgencia"],
    )
    return normalized


def analyze_lead_message(message: str) -> Dict[str, Any]:
    """
    Analyze the lead message using the LLM and normalize the response.
    """
    if llm is None:
        fallback = DEFAULT_RESPONSE.copy()
        fallback["razonamiento"] = "LLM no disponible (clave o dependencia faltante)"
        return fallback

    prompt = BASE_PROMPT.replace("{mensaje}", message)

    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
    except Exception:
        return DEFAULT_RESPONSE.copy()

    parsed = _parse_json_response(content)
    return _normalize_payload(parsed)
