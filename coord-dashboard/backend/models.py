"""
backend/models.py

Core data structures and logic for the disaster coordination dashboard.
Deliberately kept independent of any database -- these are plain Python
functions you can test right now, before Supabase is even connected.
Swapping in real Supabase calls later only touches database.py, not this file.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RequestStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    RESOLVED = "RESOLVED"


@dataclass
class EmergencyRequest:
    id: str
    location: str
    request_type: str          # "Medical", "Food", "Shelter", "Rescue", etc.
    people_affected: int
    severity: Severity
    description: str
    status: RequestStatus = RequestStatus.PENDING
    assigned_resource_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Resource:
    id: str
    name: str
    resource_type: str         # "Ambulance", "Volunteer Team", "Supply Truck", etc.
    location: str
    capacity: int              # how many people this resource can help at once
    available: bool = True


# Severity carries a numeric weight for priority scoring -- higher severity
# should win when multiple requests are competing for the same resource.
SEVERITY_WEIGHT = {
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


def calculate_priority_score(request: EmergencyRequest) -> float:
    """
    Higher score = more urgent. Combines severity (dominant factor) with
    how many people are affected (secondary factor) -- a CRITICAL request
    affecting 2 people should still outrank a LOW request affecting 50,
    which is why severity is weighted far more heavily.
    """
    severity_component = SEVERITY_WEIGHT[request.severity] * 100
    scale_component = min(request.people_affected, 500) / 10  # capped so it can't overwhelm severity
    return severity_component + scale_component


def find_best_resource(request: EmergencyRequest, available_resources: list[Resource]) -> Optional[Resource]:
    """
    Picks the best available resource for a request. For this first
    version: prefer a resource whose type matches the request type and
    whose capacity can cover the people affected; if no exact type match
    exists, fall back to any available resource with enough capacity.

    Note: this is intentionally simple (no distance calculation yet,
    unlike the disaster response search engine project) -- it can be
    upgraded later to reuse that project's haversine distance logic if
    real coordinates are added to Resource/EmergencyRequest.
    """
    candidates = [r for r in available_resources if r.available and r.capacity >= 1]
    if not candidates:
        return None

    type_matches = [r for r in candidates if r.resource_type.lower() == request.request_type.lower()]
    pool = type_matches if type_matches else candidates

    # Among the pool, prefer the resource with the smallest capacity that
    # still covers the request -- avoids "wasting" a huge resource on a
    # small request when a smaller one would do.
    sufficient = [r for r in pool if r.capacity >= request.people_affected]
    if sufficient:
        return min(sufficient, key=lambda r: r.capacity)

    # Nothing fully covers it -- return the largest available as a
    # partial-help fallback, better than nothing.
    return max(pool, key=lambda r: r.capacity)


def rank_pending_requests(requests: list[EmergencyRequest]) -> list[EmergencyRequest]:
    """Returns pending requests sorted by priority, most urgent first."""
    pending = [r for r in requests if r.status == RequestStatus.PENDING]
    return sorted(pending, key=calculate_priority_score, reverse=True)
