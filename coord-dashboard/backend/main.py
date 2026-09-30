"""
backend/main.py

FastAPI backend for the disaster coordination dashboard -- now backed
by real Supabase persistence (see database.py), not in-memory dicts.

Run with: uvicorn backend.main:app --reload --port 8000
Requires: a .env file with SUPABASE_URL and SUPABASE_KEY, and the two
tables from schema.sql already created in your Supabase project.
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend import database
from backend.models import (
    EmergencyRequest, Resource, Severity, RequestStatus,
    calculate_priority_score, find_best_resource, rank_pending_requests,
)

app = FastAPI(title="Disaster Coordination Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class EmergencyRequestIn(BaseModel):
    location: str
    request_type: str
    people_affected: int
    severity: Severity
    description: str


class ResourceIn(BaseModel):
    name: str
    resource_type: str
    location: str
    capacity: int


def _row_to_request(row: dict) -> EmergencyRequest:
    """Converts a Supabase row (dict) into our EmergencyRequest dataclass,
    so the existing tested logic in models.py can be reused unchanged."""
    return EmergencyRequest(
        id=row["id"], location=row["location"], request_type=row["request_type"],
        people_affected=row["people_affected"], severity=Severity(row["severity"]),
        description=row.get("description") or "", status=RequestStatus(row["status"]),
        assigned_resource_id=row.get("assigned_resource_id"),
    )


def _row_to_resource(row: dict) -> Resource:
    return Resource(
        id=row["id"], name=row["name"], resource_type=row["resource_type"],
        location=row["location"], capacity=row["capacity"], available=row["available"],
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/emergency-requests")
def create_request(payload: EmergencyRequestIn):
    inserted = database.insert_request({
        "location": payload.location, "request_type": payload.request_type,
        "people_affected": payload.people_affected, "severity": payload.severity.value,
        "description": payload.description, "status": RequestStatus.PENDING.value,
    })
    request = _row_to_request(inserted)

    available_rows = database.get_all_resources(available_only=True)
    available = [_row_to_resource(r) for r in available_rows]
    best = find_best_resource(request, available)

    if best:
        database.update_request(request.id, {"status": RequestStatus.ASSIGNED.value, "assigned_resource_id": best.id})
        database.update_resource(best.id, {"available": False})
        request.status = RequestStatus.ASSIGNED
        request.assigned_resource_id = best.id
        best.available = False  # keep the in-memory object consistent with the DB update above

    return {"request": request, "assigned_resource": best}


@app.get("/emergency-requests")
def list_requests(status: Optional[RequestStatus] = None):
    rows = database.get_all_requests(status=status.value if status else None)
    return [_row_to_request(r) for r in rows]


@app.get("/emergency-requests/ranked")
def ranked_requests():
    rows = database.get_all_requests(status=RequestStatus.PENDING.value)
    requests = [_row_to_request(r) for r in rows]
    return rank_pending_requests(requests)


@app.post("/resources")
def create_resource(payload: ResourceIn):
    inserted = database.insert_resource({
        "name": payload.name, "resource_type": payload.resource_type,
        "location": payload.location, "capacity": payload.capacity, "available": True,
    })
    return _row_to_resource(inserted)


@app.get("/resources")
def list_resources(available_only: bool = False):
    rows = database.get_all_resources(available_only=available_only)
    return [_row_to_resource(r) for r in rows]


@app.get("/dashboard-summary")
def dashboard_summary():
    all_requests = [_row_to_request(r) for r in database.get_all_requests()]
    all_resources = [_row_to_resource(r) for r in database.get_all_resources()]
    return {
        "active_incidents": len([r for r in all_requests if r.status != RequestStatus.RESOLVED]),
        "people_needing_help": sum(r.people_affected for r in all_requests if r.status != RequestStatus.RESOLVED),
        "available_resources": len([r for r in all_resources if r.available]),
        "total_resources": len(all_resources),
        "pending_count": len([r for r in all_requests if r.status == RequestStatus.PENDING]),
    }


@app.post("/emergency-requests/{request_id}/resolve")
def resolve_request(request_id: str):
    existing = database.get_request_by_id(request_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Request not found")

    database.update_request(request_id, {"status": RequestStatus.RESOLVED.value})
    if existing.get("assigned_resource_id"):
        database.update_resource(existing["assigned_resource_id"], {"available": True})

    return _row_to_request(database.get_request_by_id(request_id))
