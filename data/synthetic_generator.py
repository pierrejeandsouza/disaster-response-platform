"""data/synthetic_generator.py -- fake zones/depots for engine testing."""
import random

US_LAT_RANGE = (25.0, 49.0)
US_LON_RANGE = (-124.0, -67.0)


def generate_zones(n, seed=42):
    rng = random.Random(seed)
    zones = {}
    for i in range(n):
        zones[f"zone_{i}"] = {
            "severity": round(rng.uniform(1, 10), 2),
            "lat": rng.uniform(*US_LAT_RANGE),
            "lon": rng.uniform(*US_LON_RANGE),
        }
    return zones


def generate_depots(n, seed=7):
    rng = random.Random(seed)
    depots = {}
    for i in range(n):
        depots[f"depot_{i}"] = {
            "capacity": rng.randint(1, 5),
            "lat": rng.uniform(*US_LAT_RANGE),
            "lon": rng.uniform(*US_LON_RANGE),
        }
    return depots
