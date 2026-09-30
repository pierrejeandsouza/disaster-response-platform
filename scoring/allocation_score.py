"""
scoring/allocation_score.py
Scores how "good" a resource allocation plan is.
allocation = {zone_id: depot_id or None}
Zones can be left unserved (depot_id=None) since real disasters often
have more need than capacity -- requiring full coverage would make
many realistic scenarios unsolvable.
"""
import math


def haversine_distance_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def score_allocation(allocation, zones, depots):
    total_score = 0.0
    depot_load = {}
    for zone_id, depot_id in allocation.items():
        if depot_id is None:
            continue
        zone = zones[zone_id]
        depot = depots[depot_id]
        distance = haversine_distance_km(zone["lat"], zone["lon"], depot["lat"], depot["lon"])
        coverage_value = max(zone["severity"] - distance / 100.0, 0.0)
        total_score += coverage_value
        depot_load[depot_id] = depot_load.get(depot_id, 0) + 1
    for depot_id, load in depot_load.items():
        capacity = depots[depot_id]["capacity"]
        if load > capacity:
            total_score -= (load - capacity) * 50
    return total_score
