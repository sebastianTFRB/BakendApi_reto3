from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

from db.supabase_client import get_supabase_client
from repositories.interaction_repository import LeadInteractionRepository
from repositories.lead_repository import LeadRepository
from repositories.property_repository import PropertyRepository
from utils.scoring import calculate_intent_score, interest_from_category


def _parse_contact(contacto: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not contacto:
        return None, None
    c = contacto.strip()
    if not c:
        return None, None
    if "@" in c:
        return c, None
    digits = "".join(ch for ch in c if ch.isdigit() or ch == "+")
    if not digits:
        return None, None
    return None, digits


class ChatService:
    """
    Guarda preferencias progresivas de un comprador y crea/actualiza su lead.
    """

    def __init__(self) -> None:
        supabase = get_supabase_client()
        self.lead_repo = LeadRepository(supabase)
        self.interaction_repo = LeadInteractionRepository(supabase)
        self.property_repo = PropertyRepository(supabase)

    def _find_lead(self, email: Optional[str], phone: Optional[str], user_id: Optional[int], agency_id: Optional[int]):
        if user_id:
            found = self.lead_repo.find_by_user(user_id, agency_id)
            if found:
                return found
        if phone:
            found = self.lead_repo.find_by_phone(phone, agency_id)
            if found:
                return found
        if email:
            found = self.lead_repo.find_by_email(email, agency_id)
            if found:
                return found
        return None

    def _merge_notes(self, existing: Optional[str], payload: Dict[str, Any]) -> str:
        """
        Guarda preferencias en JSON dentro de notes para no perder compatibilidad.
        """
        base = {}
        if existing:
            try:
                base = json.loads(existing)
            except Exception:
                base = {"raw": existing}
        prefs = base.get("preferences", {})
        prefs.update(payload)
        base["preferences"] = prefs
        return json.dumps(base, ensure_ascii=False)

    def save_preferences(
        self,
        *,
        mensaje: str,
        canal: str,
        contacto: Optional[str],
        nombre: Optional[str],
        usuario_id: Optional[int],
        agency_id: Optional[int],
        preferencias: Dict[str, Any],
        property_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        email, phone = _parse_contact(contacto)
        property_ref = self.property_repo.get(property_id, None) if property_id else None
        if property_ref and property_ref.get("agency_id"):
            agency_id = agency_id or property_ref.get("agency_id")

        existing = self._find_lead(email, phone, usuario_id, agency_id)

        payload = {
            "full_name": nombre or (existing or {}).get("full_name") or contacto or "Lead",
            "email": email or (existing or {}).get("email"),
            "phone": phone or (existing or {}).get("phone"),
            "preferred_area": preferencias.get("zona")
            or (existing or {}).get("preferred_area")
            or (property_ref.get("location") if property_ref else None),
            "budget": preferencias.get("presupuesto")
            or (existing or {}).get("budget")
            or (property_ref.get("price") if property_ref else None),
            "urgency": preferencias.get("urgencia") or (existing or {}).get("urgency") or "medium",
            "status": (existing or {}).get("status") or "new",
            "agency_id": agency_id or (existing or {}).get("agency_id"),
            "user_id": usuario_id or (existing or {}).get("user_id"),
        }
        notes_pref = {
            "habitaciones": preferencias.get("habitaciones"),
            "banos": preferencias.get("banos"),
            "garaje": preferencias.get("garaje"),
            "tipo_propiedad": preferencias.get("tipo_propiedad"),
            "property_id": property_id,
            "property_title": property_ref.get("title") if property_ref else None,
        }
        payload["notes"] = self._merge_notes((existing or {}).get("notes"), notes_pref)

        properties_for_score = []
        if payload.get("agency_id"):
            try:
                properties_for_score = self.property_repo.list(payload.get("agency_id"))
            except Exception:
                properties_for_score = []
        score, category = calculate_intent_score(
            payload.get("preferred_area"),
            float(payload.get("budget")) if payload.get("budget") else None,
            payload.get("urgency"),
            properties_for_score,
        )
        payload["intent_score"] = score
        payload["category"] = getattr(category, "value", category)

        lead_record = existing
        if existing:
            lead_record = self.lead_repo.update(existing["id"], payload)
        else:
            lead_record = self.lead_repo.create(payload)

        # registrar interacción
        try:
            self.interaction_repo.create(
                {
                    "lead_id": lead_record["id"],
                    "channel": canal or "web",
                    "direction": "inbound",
                    "message": mensaje,
                }
            )
        except Exception:
            # no bloquear por logging
            pass

        interested, level = interest_from_category(lead_record.get("category"))
        return {
            "lead_id": lead_record.get("id"),
            "category": lead_record.get("category"),
            "intent_score": lead_record.get("intent_score"),
            "is_interested": interested,
            "interest_level": level,
            "preferences": notes_pref,
        }
