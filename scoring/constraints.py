"""scoring/constraints.py -- hard validity checks for an allocation plan."""


def is_valid_allocation(allocation, zones, depots, max_zones_per_depot=None):
    depot_load = {}
    for zone_id, depot_id in allocation.items():
        if depot_id is None:
            continue
        if depot_id not in depots:
            return False
        depot_load[depot_id] = depot_load.get(depot_id, 0) + 1
    for depot_id, load in depot_load.items():
        cap = max_zones_per_depot if max_zones_per_depot is not None else depots[depot_id]["capacity"]
        if load > cap:
            return False
    return True
