"""cloud_deploy/worker_service/main.py -- the worker as a real HTTP service, deploy to each cloud VM."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Optional
from local_parallel.worker import index_to_combo
from scoring.allocation_score import score_allocation
from scoring.constraints import is_valid_allocation

app = FastAPI(title="Disaster Response Search Worker")


class ScoreChunkRequest(BaseModel):
    start_index: int
    end_index: int
    zone_ids: list
    depot_options: list
    zones: Dict[str, dict]
    depots: Dict[str, dict]


class ScoreChunkResponse(BaseModel):
    best_allocation: Optional[Dict[str, Optional[str]]]
    best_score: float


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/score_chunk", response_model=ScoreChunkResponse)
def score_chunk(request: ScoreChunkRequest):
    best_allocation = None
    best_score = float("-inf")
    n_zones = len(request.zone_ids)
    for idx in range(request.start_index, request.end_index):
        combo = index_to_combo(idx, request.depot_options, n_zones)
        allocation = dict(zip(request.zone_ids, combo))
        if not is_valid_allocation(allocation, request.zones, request.depots):
            continue
        score = score_allocation(allocation, request.zones, request.depots)
        if score > best_score:
            best_score = score
            best_allocation = allocation
    return ScoreChunkResponse(best_allocation=best_allocation, best_score=best_score)
