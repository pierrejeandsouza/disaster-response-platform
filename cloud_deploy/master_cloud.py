"""cloud_deploy/master_cloud.py -- coordinates real HTTP-based workers, CONCURRENTLY."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import requests
import concurrent.futures
from local_parallel.reduce import reduce_results
from local_parallel.master import split_index_range


def check_worker_health(url, timeout=5):
    try:
        r = requests.get(f"{url}/health", timeout=timeout)
        return r.status_code == 200
    except requests.RequestException:
        return False


def send_chunk_to_worker(url, start, end, zone_ids, depot_options, zones, depots, timeout=300):
    payload = {"start_index": start, "end_index": end, "zone_ids": zone_ids,
               "depot_options": depot_options, "zones": zones, "depots": depots}
    response = requests.post(f"{url}/score_chunk", json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    return data["best_allocation"], data["best_score"]


def cloud_parallel_search(zones, depots, worker_urls, simulate_kill_worker_index=None):
    zone_ids = list(zones.keys())
    depot_options = list(depots.keys()) + [None]
    total_combos = len(depot_options) ** len(zone_ids)
    chunk_ranges = split_index_range(total_combos, len(worker_urls))

    def is_healthy(worker_id, url):
        if worker_id == simulate_kill_worker_index:
            return False
        return check_worker_health(url)

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(worker_urls)) as ex:
        health = {wid: ex.submit(is_healthy, wid, url) for wid, url in enumerate(worker_urls)}
        health = {wid: f.result() for wid, f in health.items()}

    recovery_events = []
    assignments = {}
    for worker_id, url in enumerate(worker_urls):
        if health.get(worker_id):
            assignments[worker_id] = url
        else:
            recovery_events.append(worker_id)
            backup = next((u for wid2, u in enumerate(worker_urls) if wid2 != worker_id and health.get(wid2)), None)
            if backup is None:
                raise RuntimeError(f"Worker {worker_id} failed and no healthy backup was available")
            assignments[worker_id] = backup

    def do_chunk(worker_id):
        start, end = chunk_ranges[worker_id]
        return worker_id, send_chunk_to_worker(assignments[worker_id], start, end, zone_ids, depot_options, zones, depots)

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(worker_urls)) as ex:
        futures = [ex.submit(do_chunk, wid) for wid in range(len(chunk_ranges))]
        for f in concurrent.futures.as_completed(futures):
            worker_id, (allocation, score) = f.result()
            results.append((worker_id, allocation, score))

    best_allocation, best_score = reduce_results(results)
    return best_allocation, best_score, recovery_events


if __name__ == "__main__":
    from data.curated_real_examples import build_florence_zones, build_florence_depots

    zones = build_florence_zones()
    depots = build_florence_depots()
    worker_urls = ["http://127.0.0.1:8001", "http://127.0.0.1:8002"]

    t0 = time.time()
    best_allocation, best_score, recovery = cloud_parallel_search(zones, depots, worker_urls)
    elapsed = time.time() - t0

    print(f"Best score: {best_score:.2f}")
    print(f"Time taken: {elapsed:.3f}s")
    print(f"Recovery events: {recovery}")
