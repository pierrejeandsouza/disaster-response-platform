"""baseline/brute_force_serial.py -- naive full search, single process."""
import itertools
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scoring.allocation_score import score_allocation
from scoring.constraints import is_valid_allocation


def brute_force_search(zones, depots):
    zone_ids = list(zones.keys())
    depot_options = list(depots.keys()) + [None]
    best_allocation = None
    best_score = float("-inf")
    for combo in itertools.product(depot_options, repeat=len(zone_ids)):
        allocation = dict(zip(zone_ids, combo))
        if not is_valid_allocation(allocation, zones, depots):
            continue
        score = score_allocation(allocation, zones, depots)
        if score > best_score:
            best_score = score
            best_allocation = allocation
    return best_allocation, best_score


if __name__ == "__main__":
    import time
    from data.synthetic_generator import generate_zones, generate_depots
    zones = generate_zones(6)
    depots = generate_depots(3)
    t0 = time.time()
    alloc, score = brute_force_search(zones, depots)
    print(f"Best score: {score:.2f}  Time: {time.time()-t0:.4f}s")
