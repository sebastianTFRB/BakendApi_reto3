from typing import Iterable, Optional, Tuple

from models.lead import LeadCategory, LeadUrgency
from models.property import Property


def calculate_intent_score(preferred_area: Optional[str], budget: Optional[float], urgency: LeadUrgency, properties: Iterable[Property]) -> Tuple[float, LeadCategory]:
    score = 0.0

    urgency_weight = {LeadUrgency.high: 40, LeadUrgency.medium: 25, LeadUrgency.low: 10}
    score += urgency_weight.get(urgency, 0)

    matched_area = False
    matched_budget = False
    for prop in properties:
        if preferred_area and prop.area and preferred_area.lower() in prop.area.lower():
            matched_area = True
            score += 15
        if budget and prop.price:
            diff = abs(float(prop.price) - budget)
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
