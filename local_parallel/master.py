"""local_parallel/master.py -- coordinates workers by index range, with built-in fault tolerance."""
import multiprocessing, queue, sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from worker import worker_process
from reduce import reduce_results


def split_index_range(total, n_chunks):
    """Splits [0, total) into EXACTLY n_chunks ranges -- remainder spread
    across the first few chunks instead of creating an extra leftover one."""
    chunk_size, remainder = divmod(total, n_chunks)
    ranges = []
    start = 0
    for i in range(n_chunks):
        size = chunk_size + (1 if i < remainder else 0)
        end = start + size
        ranges.append((start, end))
        start = end
    return ranges


def parallel_search(zones, depots, n_workers=4, simulate_kill_worker=None, result_timeout=2):
    zone_ids = list(zones.keys())
    depot_options = list(depots.keys()) + [None]
    total_combos = len(depot_options) ** len(zone_ids)
    chunk_ranges = split_index_range(total_combos, n_workers)
    result_queue = multiprocessing.Queue()

    def spawn_worker(worker_id, start, end):
        p = multiprocessing.Process(target=worker_process,
            args=(worker_id, start, end, zone_ids, depot_options, zones, depots, result_queue))
        p.start()
        return p

    processes = {}
    for worker_id, (start, end) in enumerate(chunk_ranges):
        processes[worker_id] = spawn_worker(worker_id, start, end)

    if simulate_kill_worker is not None and simulate_kill_worker in processes:
        time.sleep(0.05)
        processes[simulate_kill_worker].terminate()

    results = {}
    pending = set(range(len(chunk_ranges)))
    recovery_events = []

    while pending:
        try:
            worker_id, allocation, score = result_queue.get(timeout=result_timeout)
            if worker_id in pending:
                results[worker_id] = (allocation, score)
                pending.discard(worker_id)
        except queue.Empty:
            for worker_id in list(pending):
                p = processes[worker_id]
                if not p.is_alive() and p.exitcode is not None:
                    start, end = chunk_ranges[worker_id]
                    recovery_events.append(worker_id)
                    processes[worker_id] = spawn_worker(worker_id, start, end)

    for p in processes.values():
        p.join()

    final_results = [(wid, alloc, score) for wid, (alloc, score) in results.items()]
    best_allocation, best_score = reduce_results(final_results)
    return best_allocation, best_score, recovery_events


if __name__ == "__main__":
    from data.synthetic_generator import generate_zones, generate_depots
    zones = generate_zones(9)
    depots = generate_depots(4)
    t0 = time.time()
    alloc, score, recovery = parallel_search(zones, depots, n_workers=4)
    print(f"Best score: {score:.2f}  Time: {time.time()-t0:.4f}s  Recovery: {recovery}")
