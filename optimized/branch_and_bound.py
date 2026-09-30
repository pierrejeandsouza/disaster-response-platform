"""optimized/branch_and_bound.py -- pruned search: skip branches that can't beat the current best."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scoring.allocation_score import haversine_distance_km


def zone_depot_value(zone, depot):
    if depot is None:
        return 0.0
    distance = haversine_distance_km(zone["lat"], zone["lon"], depot["lat"], depot["lon"])
    return max(zone["severity"] - distance / 100.0, 0.0)


def branch_and_bound_search(zones, depots):
    zone_ids = list(zones.keys())
    depot_options = list(depots.keys()) + [None]
    n = len(zone_ids)
    suffix_upper = [0.0] * (n + 1)
    for i in range(n - 1, -1, -1):
        suffix_upper[i] = suffix_upper[i + 1] + zones[zone_ids[i]]["severity"]
    best_score = [float("-inf")]
    best_allocation = [None]
    depot_load = {}
    current_allocation = {}
    nodes_visited = [0]

    def recurse(i, current_score):
        nodes_visited[0] += 1
        if current_score + suffix_upper[i] <= best_score[0]:
            return
        if i == n:
            if current_score > best_score[0]:
                best_score[0] = current_score
                best_allocation[0] = dict(current_allocation)
            return
        zid = zone_ids[i]
        zone = zones[zid]
        for depot_id in depot_options:
            if depot_id is not None:
                load = depot_load.get(depot_id, 0)
                if load + 1 > depots[depot_id]["capacity"]:
                    continue
                depot_load[depot_id] = load + 1
            value = zone_depot_value(zone, depots[depot_id]) if depot_id is not None else 0.0
            current_allocation[zid] = depot_id
            recurse(i + 1, current_score + value)
            del current_allocation[zid]
            if depot_id is not None:
                depot_load[depot_id] -= 1
                if depot_load[depot_id] == 0:
                    del depot_load[depot_id]

    recurse(0, 0.0)
    return best_allocation[0], best_score[0], nodes_visited[0]


if __name__ == "__main__":
    import time
    from data.synthetic_generator import generate_zones, generate_depots
    zones = generate_zones(10)
    depots = generate_depots(4)
    total_combos = (len(depots) + 1) ** len(zones)
    t0 = time.time()
    allocation, score, nodes_visited = branch_and_bound_search(zones, depots)
    elapsed = time.time() - t0
    print(f"Best score: {score:.3f}")
    print(f"Time taken: {elapsed:.4f}s")
    print(f"Total possible combinations: {total_combos:,}")
    print(f"Nodes actually visited (with pruning): {nodes_visited:,}")
    print(f"Search space explored: {100*nodes_visited/total_combos:.4f}%")
