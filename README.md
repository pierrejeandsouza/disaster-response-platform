# Disaster Response Resource Allocation Platform

An algorithms project for allocating limited relief resources (depots) to disaster-affected
zones. It implements and benchmarks four different ways of solving the same optimization
problem — serial brute force, local parallel (multiprocessing), pruned branch-and-bound, and
a cloud-style HTTP-distributed version — plus a small ML model for estimating zone severity
and a map-based visualizer for the resulting allocation.

A related but separate sub-project, a coordination dashboard, lives in `coord-dashboard/` —
see its own README for details.

## The problem

Given a set of disaster-affected **zones** (each with a location and a severity score) and a
set of **depots** (each with a location and a capacity), assign each zone to at most one
depot (or leave it unserved) to maximize total "coverage value" — severity minus a distance
penalty — without exceeding any depot's capacity. Zones can go unserved: requiring every zone
to be covered would make many realistic scenarios (where need exceeds supply) impossible to
solve at all.

Scoring and validity rules live in `scoring/allocation_score.py` (haversine distance +
coverage value) and `scoring/constraints.py` (capacity checks).

## The four solvers

| Method | File | Approach |
|---|---|---|
| Serial brute force | `baseline/brute_force_serial.py` | Tries every possible zone-to-depot combination, single process. Correct but exponential. |
| Local parallel | `local_parallel/master.py`, `worker.py`, `reduce.py` | Splits the combination space into index ranges across multiple OS processes (`multiprocessing`), reduces to the best result. Includes fault tolerance: `fault_injector.py` kills a worker mid-run and `master.py` detects the dead process and respawns it on the same index range. |
| Branch and bound | `optimized/branch_and_bound.py` | Recursive search that prunes any branch whose best-possible remaining score can't beat the current best, using a precomputed suffix upper bound. Same optimal answer as brute force, far fewer nodes visited. |
| Cloud (HTTP) | `cloud_deploy/master_cloud.py`, `cloud_deploy/worker_service/main.py` | Same chunked-search idea as the local parallel version, but workers are independent FastAPI services reached over HTTP. The master checks worker health first and reroutes a chunk to a healthy backup if a worker is down. |

## ML severity model

`ml_severity/train_model.py` trains a `RandomForestRegressor` (scikit-learn) to predict a
zone's severity (0–10) from incident type, population affected, and prior disaster count. It
trains on synthetically generated data with a known underlying formula (not real historical
FEMA records), so treat the model as a stand-in for a real severity model rather than a
validated one. The trained pipeline is saved as `ml_severity/severity_model.joblib` and
loaded by `ml_severity/predict.py`.

## Visualization

`visualization/map_view.py` renders zones and depots on an interactive Folium map —
color-coded by severity, with lines connecting served zones to their assigned depot and
unserved zones marked separately.

## Case study: Hurricane Florence (2018, North Carolina)

`data/curated_real_examples.py` builds a 10-county, 4-depot scenario from Hurricane Florence
(FEMA disaster DR-4393). This was hand-assembled rather than pulled from a live API, because
the dev environment it was built in didn't have outbound internet access to fema.gov. Read
the module's docstring for exactly what's verified vs. approximate:

- The disaster, the county names, and their FEMA Individual-Assistance declaration are real.
- County coordinates and 2018-era populations are approximate (ballpark, not survey/census
  precision).
- Depot locations are real North Carolina city coordinates (Raleigh, Charlotte, Greenville,
  Rocky Mount) used as stand-ins for real relief facilities — actual HIFLD facility data was
  never pulled in. Depot capacities are synthetic guesses.

On this scenario (9,765,625 possible allocations), branch-and-bound reaches the same score as
brute force while visiting only ~1.16% of the search space — see `benchmarks/results.csv` for
the full numbers across problem sizes, and `benchmarks/*.png` for the generated charts.
`data/preprocess.py` has a `fetch_ihp_data()` function ready to pull the real live FEMA data
if run somewhere with internet access, to replace this curated stand-in.

## Tech stack

Python, FastAPI, scikit-learn, pandas, joblib, Folium, matplotlib, `multiprocessing`,
`concurrent.futures`.

## How to run it

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Train the ML severity model (needed before running the case study)
python3 ml_severity/train_model.py

# 3. Build the Hurricane Florence case study and run branch-and-bound on it
python3 -c "
from data.curated_real_examples import build_florence_zones, build_florence_depots
from optimized.branch_and_bound import branch_and_bound_search
zones = build_florence_zones()
depots = build_florence_depots()
alloc, score, nodes = branch_and_bound_search(zones, depots)
print(f'Score: {score:.2f}, nodes visited: {nodes:,}')
for zone_id, depot_id in alloc.items():
    print(f\"  {zones[zone_id]['county_name']} -> {depots[depot_id]['name'] if depot_id else 'UNSERVED'}\")
"

# 4. Generate the case study map (writes visualization/florence_allocation_map.html)
python3 visualization/map_view.py

# 5. Fault tolerance and engine tests (synthetic data)
python3 local_parallel/fault_injector.py
python3 baseline/brute_force_serial.py
python3 local_parallel/master.py

# 6. Full benchmark suite (writes benchmarks/results.csv and benchmarks/*.png)
python3 benchmarks/run_all.py

# 7. Cloud deployment test (two terminals for workers, then the master)
cd cloud_deploy/worker_service
uvicorn main:app --host 127.0.0.1 --port 8001 &
uvicorn main:app --host 127.0.0.1 --port 8002 &
cd ../..
python3 cloud_deploy/master_cloud.py
```

## Known limitations

- Zones can go unserved when capacity is short — this is by design, not a bug, but it means
  "score" isn't the same as "everyone got help."
- Depot capacities are guesses in both the synthetic and curated-real scenarios, not sourced
  data.
- Local-parallel speedup depends on how many CPU cores the machine running it has; re-run
  `benchmarks/run_all.py` locally for numbers that reflect your own hardware.
- The severity ML model is trained on synthetic data with a known generating formula, not
  real historical disaster records — it demonstrates the pipeline, not a validated model.
- The Hurricane Florence case study mixes real (disaster, counties) and approximate/proxy
  (coordinates, populations, depot locations) data — see `data/curated_real_examples.py` for
  the full breakdown of what's verified.
