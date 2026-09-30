"""
benchmarks/run_all.py

Runs the serial baseline, local parallel search, and branch-and-bound
across a range of problem sizes, logs timing to a CSV, and generates
comparison graphs.
"""

import sys
import os
import time
import csv
import multiprocessing

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from baseline.brute_force_serial import brute_force_search
from local_parallel.master import parallel_search
from optimized.branch_and_bound import branch_and_bound_search
from data.synthetic_generator import generate_zones, generate_depots


def run_benchmarks(sizes, n_workers=4):
    results = []
    cpu_count = multiprocessing.cpu_count()

    for n_zones, n_depots in sizes:
        zones = generate_zones(n_zones)
        depots = generate_depots(n_depots)
        total_combos = (n_depots + 1) ** n_zones

        row = {"n_zones": n_zones, "n_depots": n_depots, "total_combos": total_combos, "cpu_count": cpu_count}

        t0 = time.time()
        _, serial_score = brute_force_search(zones, depots)
        row["serial_time"] = time.time() - t0
        row["serial_score"] = serial_score

        t0 = time.time()
        _, parallel_score, _ = parallel_search(zones, depots, n_workers=n_workers)
        row["parallel_time"] = time.time() - t0
        row["parallel_score"] = parallel_score

        t0 = time.time()
        _, bnb_score, nodes_visited = branch_and_bound_search(zones, depots)
        row["bnb_time"] = time.time() - t0
        row["bnb_score"] = bnb_score
        row["bnb_nodes_visited"] = nodes_visited
        row["bnb_search_space_pct"] = 100 * nodes_visited / total_combos

        results.append(row)
        print(f"Done: {n_zones}z/{n_depots}d -- serial={row['serial_time']:.3f}s  "
              f"parallel={row['parallel_time']:.3f}s  bnb={row['bnb_time']:.3f}s "
              f"({row['bnb_search_space_pct']:.2f}% explored)")

    return results


def save_csv(results, path):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)


def make_plots(results, output_dir):
    import matplotlib.pyplot as plt

    sizes_label = [f"{r['n_zones']}z/{r['n_depots']}d" for r in results]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(sizes_label, [r["serial_time"] for r in results], marker="o", label="Serial brute force")
    ax.plot(sizes_label, [r["parallel_time"] for r in results], marker="o", label=f"Local parallel ({results[0]['cpu_count']} cores)")
    ax.plot(sizes_label, [r["bnb_time"] for r in results], marker="o", label="Branch & bound")
    ax.set_xlabel("Problem size")
    ax.set_ylabel("Time (seconds)")
    ax.set_title("Runtime comparison across search methods")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "runtime_comparison.png"), dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(sizes_label, [r["bnb_search_space_pct"] for r in results], color="darkorange")
    ax.set_xlabel("Problem size")
    ax.set_ylabel("% of search space explored")
    ax.set_title("Branch & bound pruning effectiveness")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "bnb_pruning.png"), dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    speedups = [r["serial_time"] / r["bnb_time"] if r["bnb_time"] > 0 else 0 for r in results]
    ax.bar(sizes_label, speedups, color="seagreen")
    ax.set_xlabel("Problem size")
    ax.set_ylabel("Speedup (x times faster than serial)")
    ax.set_title("Branch & bound speedup over brute force")
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "bnb_speedup.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    output_dir = os.path.dirname(__file__)
    sizes = [(6, 3), (8, 4), (9, 4), (10, 4)]
    results = run_benchmarks(sizes)

    csv_path = os.path.join(output_dir, "results.csv")
    save_csv(results, csv_path)
    print(f"\nResults saved to {csv_path}")

    make_plots(results, output_dir)
    print(f"Plots saved to {output_dir}/*.png")

    cpu_count = multiprocessing.cpu_count()
    if cpu_count <= 1:
        print(f"\nNOTE: this machine has only {cpu_count} CPU core -- "
              f"local parallel numbers above reflect overhead, not real speedup.")
    else:
        avg_speedup = sum(r["serial_time"] / r["parallel_time"] for r in results if r["parallel_time"] > 0) / len(results)
        print(f"\nMachine has {cpu_count} CPU cores -- parallel search shows real speedup "
              f"(avg {avg_speedup:.2f}x across tested sizes).")
