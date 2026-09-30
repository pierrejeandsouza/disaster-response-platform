"""local_parallel/fault_injector.py -- kills a worker mid-search, proves recovery."""
import sys, os, time, math
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from master import parallel_search
from baseline.brute_force_serial import brute_force_search
from data.synthetic_generator import generate_zones, generate_depots


def scores_match(a, b):
    if math.isinf(a) and math.isinf(b):
        return True
    return abs(a - b) < 1e-9


def run_fault_tolerance_test(n_zones=8, n_depots=4, n_workers=4, kill_worker=1):
    zones = generate_zones(n_zones)
    depots = generate_depots(n_depots)
    _, true_best_score = brute_force_search(zones, depots)
    t0 = time.time()
    _, clean_score, clean_recovery = parallel_search(zones, depots, n_workers=n_workers)
    clean_time = time.time() - t0
    t0 = time.time()
    _, faulty_score, faulty_recovery = parallel_search(zones, depots, n_workers=n_workers, simulate_kill_worker=kill_worker)
    faulty_time = time.time() - t0
    print(f"True best score (brute force):      {true_best_score:.3f}")
    print(f"Clean parallel run score:            {clean_score:.3f}  (time: {clean_time:.3f}s, recovered: {clean_recovery})")
    print(f"Faulty parallel run score:            {faulty_score:.3f}  (time: {faulty_time:.3f}s, recovered: {faulty_recovery})")
    print(f"Result still correct despite fault:  {scores_match(true_best_score, faulty_score)}")
    print(f"Worker {kill_worker} was actually killed and reassigned: {kill_worker in faulty_recovery}")


if __name__ == "__main__":
    run_fault_tolerance_test()
