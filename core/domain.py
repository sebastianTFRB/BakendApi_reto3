import enum


class LeadUrgency(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class LeadCategory(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
