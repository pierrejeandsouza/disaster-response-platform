"""
data/preprocess.py -- turns raw FEMA/HIFLD data into the engine's zones/depots format.
NEEDS REAL INTERNET ACCESS for fetch_ihp_data() -- run that part on your own machine.
See data/curated_real_examples.py for a usable stand-in until you do.
"""
import json, csv, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def load_disaster_summaries_json(path):
    with open(path) as f:
        return json.load(f)


def find_ia_eligible_disasters(records):
    seen = {}
    for r in records:
        if r.get("iaProgramDeclared") is True:
            dn = r["disasterNumber"]
            if dn not in seen:
                seen[dn] = {"disasterNumber": dn, "declarationTitle": r["declarationTitle"],
                            "state": r["state"], "incidentType": r["incidentType"],
                            "declarationDate": r["declarationDate"], "counties": []}
            seen[dn]["counties"].append({"designatedArea": r["designatedArea"],
                "fipsStateCode": r["fipsStateCode"], "fipsCountyCode": r["fipsCountyCode"]})
    return list(seen.values())


def fetch_ihp_data(disaster_number):
    """REQUIRES INTERNET ACCESS TO fema.gov -- run on your own machine."""
    import requests
    url = "https://www.fema.gov/api/open/v2/IndividualsAndHouseholdsProgramValidRegistrations"
    params = {"$filter": f"disasterNumber eq {disaster_number}", "$top": 5000}
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()["IndividualsAndHouseholdsProgramValidRegistrations"]


def load_county_centroids(gazetteer_path):
    centroids = {}
    with open(gazetteer_path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            geoid = row["GEOID"].strip()
            centroids[(geoid[:2], geoid[2:])] = (float(row["INTPTLAT"]), float(row["INTPTLONG"]))
    return centroids


def build_zones_from_disaster(disaster_record, county_centroids=None, severity_fn=None):
    if severity_fn is None:
        severity_fn = lambda county: 5.0
    zones = {}
    for county in disaster_record["counties"]:
        zone_id = f"zone_{county['fipsStateCode']}_{county['fipsCountyCode']}"
        if county_centroids is not None:
            lat, lon = county_centroids.get((county["fipsStateCode"], county["fipsCountyCode"]), (0.0, 0.0))
        else:
            lat, lon = 0.0, 0.0
        zones[zone_id] = {"severity": severity_fn(county), "lat": lat, "lon": lon,
                           "designatedArea": county["designatedArea"]}
    return zones


def load_hifld_depots(csv_path, lat_col="LATITUDE", lon_col="LONGITUDE", name_col="NAME", default_capacity=3):
    depots = {}
    with open(csv_path) as f:
        for i, row in enumerate(csv.DictReader(f)):
            try:
                lat, lon = float(row[lat_col]), float(row[lon_col])
            except (ValueError, KeyError):
                continue
            depots[f"depot_{i}"] = {"capacity": default_capacity, "lat": lat, "lon": lon,
                                     "name": row.get(name_col, f"depot_{i}")}
    return depots


if __name__ == "__main__":
    fixture_path = os.path.join(os.path.dirname(__file__), "sample_fixtures", "sample_declarations.json")
    records = load_disaster_summaries_json(fixture_path)
    ia_disasters = find_ia_eligible_disasters(records)
    print(f"Found {len(ia_disasters)} IA-eligible disaster(s) in the sample fixture.")
