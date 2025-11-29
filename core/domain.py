import enum


class LeadUrgency(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class LeadCategory(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"


class UserRole(str, enum.Enum):
    user = "user"
    agency_admin = "agency_admin"
    superadmin = "superadmin"
