"""
data/curated_real_examples.py

A HAND-CURATED real disaster case study, built from general knowledge
rather than a live API pull -- this exists specifically because the
live FEMA API isn't reachable from this dev environment (query filters
get silently dropped, see data/preprocess.py's docstring), so this is
the best available substitute until you pull the truly live data
yourself with real internet access.

WHAT IS AND ISN'T VERIFIED HERE -- READ BEFORE USING IN YOUR REPORT:

  - The disaster itself (Hurricane Florence, September 2018, North
    Carolina, FEMA disaster DR-4393) is real and well documented.
  - The county names and the fact that they were FEMA-declared for
    Individual Assistance under DR-4393 are real, from general
    knowledge of this widely-reported disaster.
  - The county centroid coordinates are approximate (accurate to
    roughly the right area, not surveyed precision) -- fine for
    computing realistic-scale distances, not fine for anything
    requiring exact geolocation.
  - The population figures are APPROXIMATE ballpark figures from
    general knowledge (roughly the 2018-era county populations), not
    pulled from an authoritative census source. Treat them as
    plausible stand-ins, not verified data -- swap in real Census
    Bureau figures before treating any output as a genuine finding.
  - The depot locations are REAL CITY COORDINATES (state capital and
    major regional hubs), used as PROXY depot locations. They are
    NOT real fire station / EMS / Red Cross facility data -- HIFLD
    data still needs to be pulled with real internet access to
    replace these. Capacities are entirely synthetic.

In short: this is a legitimate, honestly-labeled step up from pure
random synthetic data (real disaster, real counties, real general
geography), but it is NOT a substitute for actually pulling the live
FEMA IHP + HIFLD datasets before final submission. Use this to build
and demo the pipeline now; swap in verified live data before treating
any numbers as your report's real findings.
"""

# Hurricane Florence, Sept 2018 -- FEMA Disaster DR-4393-NC
# A representative subset of the NC counties FEMA declared for
# Individual Assistance (many more counties were actually declared;
# this is a manageable subset for a demo-sized search problem).
DISASTER_INFO = {
    "disasterNumber": 4393,
    "declarationTitle": "HURRICANE FLORENCE",
    "state": "NC",
    "incidentType": "Hurricane",
    "fyDeclared": 2018,
}

# (county_name, fips_county_code, approx_lat, approx_lon, approx_2018_population)
FLORENCE_COUNTIES = [
    ("New Hanover",  "129", 34.24, -77.85, 225_000),
    ("Brunswick",    "019", 34.03, -78.28, 136_000),
    ("Onslow",       "133", 34.78, -77.42, 200_000),
    ("Craven",       "049", 35.14, -77.05, 103_000),
    ("Pender",       "141", 34.52, -77.83,  62_000),
    ("Duplin",       "061", 34.86, -77.85,  58_000),
    ("Columbus",     "047", 34.28, -78.72,  54_000),
    ("Robeson",      "155", 34.64, -79.10, 130_000),
    ("Cumberland",   "051", 35.05, -78.88, 334_000),
    ("Bladen",       "017", 34.62, -78.53,  32_000),
]

# Real NC city coordinates, used as PROXY depot hub locations --
# NOT real HIFLD facility data. Capacities are synthetic guesses.
PROXY_DEPOT_HUBS = [
    ("Raleigh_hub",    35.78, -78.64, 4),   # state capital -- plausible coordination hub
    ("Charlotte_hub",  35.23, -80.84, 4),   # largest NC city -- major logistics hub
    ("Greenville_hub", 35.61, -77.37, 3),   # regional hub near the affected coast
    ("RockyMount_hub", 35.94, -77.79, 3),   # additional regional coverage point
]


def build_florence_zones(severity_fn=None):
    """
    Returns a zones dict in the engine's standard format:
    {zone_id: {severity, lat, lon, county_name, population}}

    severity_fn: optional function(incident_type, population, prior_count)
                 -> severity score. Defaults to ml_severity.predict.predict_severity
                 if available, else a simple population-scaled fallback.
    """
    if severity_fn is None:
        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
            from ml_severity.predict import predict_severity as severity_fn
        except (ImportError, FileNotFoundError):
            severity_fn = lambda incident_type, population, prior_count: min(10.0, 4.0 + population / 50_000)

    zones = {}
    for name, fips, lat, lon, population in FLORENCE_COUNTIES:
        zone_id = f"zone_37_{fips}"
        severity = severity_fn(DISASTER_INFO["incidentType"], population, 1)
        zones[zone_id] = {
            "severity": severity,
            "lat": lat,
            "lon": lon,
            "county_name": name,
            "population": population,
            "designatedArea": f"{name} (County)",
        }
    return zones


def build_florence_depots():
    """Returns a depots dict using the proxy hub locations."""
    depots = {}
    for name, lat, lon, capacity in PROXY_DEPOT_HUBS:
        depots[name] = {"capacity": capacity, "lat": lat, "lon": lon, "name": name.replace("_hub", "")}
    return depots


if __name__ == "__main__":
    zones = build_florence_zones()
    depots = build_florence_depots()

    print(f"Case study: {DISASTER_INFO['declarationTitle']} ({DISASTER_INFO['state']}, {DISASTER_INFO['fyDeclared']})")
    print(f"\n{len(zones)} zones (real counties, ML-predicted severity from approximate population):")
    for zid, z in zones.items():
        print(f"  {z['county_name']:15s} pop~{z['population']:>7,}  severity={z['severity']:.2f}")

    print(f"\n{len(depots)} depots (real city coordinates as proxy hubs -- NOT real facility data):")
    for did, d in depots.items():
        print(f"  {d['name']:15s} capacity={d['capacity']}")
