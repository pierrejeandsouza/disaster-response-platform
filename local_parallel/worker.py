"""local_parallel/worker.py -- worker generates its own combos from an index range."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scoring.allocation_score import score_allocation
from scoring.constraints import is_valid_allocation


def index_to_combo(index, depot_options, n_zones):
    k = len(depot_options)
    combo = []
    for _ in range(n_zones):
        index, remainder = divmod(index, k)
        combo.append(depot_options[remainder])
    return tuple(combo)


def worker_process(worker_id, start_index, end_index, zone_ids, depot_options, zones, depots, result_queue):
    best_allocation = None
    best_score = float("-inf")
    n_zones = len(zone_ids)
    for idx in range(start_index, end_index):
        combo = index_to_combo(idx, depot_options, n_zones)
        allocation = dict(zip(zone_ids, combo))
        if not is_valid_allocation(allocation, zones, depots):
            continue
        score = score_allocation(allocation, zones, depots)
        if score > best_score:
            best_score = score
            best_allocation = allocation
    result_queue.put((worker_id, best_allocation, best_score))
