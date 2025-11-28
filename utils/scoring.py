from typing import Any, Iterable, Optional, Tuple

from core.domain import LeadCategory, LeadUrgency


def calculate_intent_score(preferred_area: Optional[str], budget: Optional[float], urgency: Any, properties: Iterable[Any]) -> Tuple[float, LeadCategory]:
    score = 0.0

    urgency_key = urgency.value if hasattr(urgency, "value") else urgency
    urgency_weight = {LeadUrgency.high.value: 40, LeadUrgency.medium.value: 25, LeadUrgency.low.value: 10}
    score += urgency_weight.get(urgency_key, 0)

    matched_area = False
    matched_budget = False
    for prop in properties:
        area_val = None
        if isinstance(prop, dict):
            area_val = prop.get("area")
            price_val = prop.get("price")
        else:
            area_val = getattr(prop, "area", None)
            price_val = getattr(prop, "price", None)

        if preferred_area and area_val and preferred_area.lower() in str(area_val).lower():
            matched_area = True
            score += 15
        if budget and price_val:
            diff = abs(float(price_val) - budget)
            tolerance = max(budget * 0.15, 1)
            if diff <= tolerance:
                matched_budget = True
                score += 25
    if matched_area and matched_budget:
        score += 10

    if budget and not matched_budget:
        score -= 5
    if not preferred_area:
        score -= 5

    score = max(0, min(score, 100))

    if score >= 70:
        category = LeadCategory.A
    elif score >= 40:
        category = LeadCategory.B
    else:
        category = LeadCategory.C

    return score, category
