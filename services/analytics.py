"""
Analytics service that pulls lead and interaction data from Supabase.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from db.supabase_client import get_supabase_client
from repositories.interaction_repository import LeadInteractionRepository
from repositories.lead_repository import LeadRepository
from utils.scoring import interest_from_category


def _to_iso(dt: Optional[Any]) -> Optional[str]:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    try:
        return datetime.fromisoformat(str(dt)).isoformat()
    except Exception:
        return None


class AnalyticsService:
    def __init__(self) -> None:
        supabase = get_supabase_client()
        self.lead_repo = LeadRepository(supabase)
        self.interaction_repo = LeadInteractionRepository(supabase)

    def _leads_in_scope(
        self,
        *,
        agency_id: Optional[int],
        channel: Optional[str],
        from_date: Optional[str],
        to_date: Optional[str],
    ) -> List[Dict[str, Any]]:
        lead_ids: Optional[List[int]] = None
        if channel:
            interactions = self.interaction_repo.list_filtered(
                channel=channel, from_date=from_date, to_date=to_date
            )
            lead_ids = list({int(item["lead_id"]) for item in interactions if item.get("lead_id") is not None})
            if not lead_ids:
                return []
        return self.lead_repo.list_filtered(
            agency_id=agency_id,
            user_id=None,
            lead_ids=lead_ids,
            from_date=from_date,
            to_date=to_date,
        )

    def _channel_counts(
        self, lead_ids: Iterable[int], from_date: Optional[str], to_date: Optional[str]
    ) -> Tuple[Dict[str, int], Set[int]]:
        lead_id_list = [int(lid) for lid in lead_ids if lid is not None]
        if not lead_id_list:
            return {}, set()

        interactions = self.interaction_repo.list_filtered(
            lead_ids=lead_id_list, from_date=from_date, to_date=to_date
        )

        channel_by_lead: Dict[int, str] = {}
        for item in interactions:
            lead_id = item.get("lead_id")
            if lead_id is None or lead_id in channel_by_lead:
                continue
            channel_by_lead[int(lead_id)] = (item.get("channel") or "unknown").lower()

        counts: Dict[str, int] = {}
        for channel in channel_by_lead.values():
            counts[channel] = counts.get(channel, 0) + 1

        return counts, set(channel_by_lead.keys())

    def get_lead_summary(
        self,
        *,
        agency_id: Optional[int] = None,
        channel: Optional[str] = None,
        from_date: Optional[Any] = None,
        to_date: Optional[Any] = None,
    ) -> Dict[str, Any]:
        from_iso = _to_iso(from_date)
        to_iso = _to_iso(to_date)

        channel_filter = channel.lower() if channel else None
        leads = self._leads_in_scope(
            agency_id=agency_id, channel=channel_filter, from_date=from_iso, to_date=to_iso
        )

        by_score: Dict[str, int] = {"A": 0, "B": 0, "C": 0}
        by_interest: Dict[str, int] = {"interested": 0, "not_interested": 0}

        for lead in leads:
            category = str(lead.get("category") or "C").upper()
            if category not in by_score:
                by_score[category] = 0
            by_score[category] += 1
            interested, _ = interest_from_category(category)
            if interested:
                by_interest["interested"] += 1
            else:
                by_interest["not_interested"] += 1

        lead_ids = {int(lead["id"]) for lead in leads if lead.get("id") is not None}
        by_channel, leads_with_channel = self._channel_counts(lead_ids, from_iso, to_iso)
        missing_channels = lead_ids - leads_with_channel
        if missing_channels:
            by_channel["unknown"] = by_channel.get("unknown", 0) + len(missing_channels)

        return {
            "total_leads": len(leads),
            "by_score": by_score,
            "by_interest": by_interest,
            "by_channel": by_channel,
        }

    def get_lead_summary_by_agency(
        self,
        agency_id: int,
        *,
        channel: Optional[str] = None,
        from_date: Optional[Any] = None,
        to_date: Optional[Any] = None,
    ) -> Dict[str, Any]:
        return self.get_lead_summary(
            agency_id=agency_id,
            channel=channel,
            from_date=from_date,
            to_date=to_date,
        )
