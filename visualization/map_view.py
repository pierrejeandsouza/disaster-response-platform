"""visualization/map_view.py -- renders zones/depots/allocation on an interactive map."""
import folium


def _severity_color(severity):
    if severity >= 8: return "darkred"
    elif severity >= 6: return "red"
    elif severity >= 4: return "orange"
    elif severity >= 2: return "beige"
    else: return "green"


def build_map(zones, depots, allocation=None, output_path="allocation_map.html"):
    all_lats = [z["lat"] for z in zones.values()] + [d["lat"] for d in depots.values()]
    all_lons = [z["lon"] for z in zones.values()] + [d["lon"] for d in depots.values()]
    center = [sum(all_lats) / len(all_lats), sum(all_lons) / len(all_lons)]
    m = folium.Map(location=center, zoom_start=7, tiles="OpenStreetMap")

    served_zone_ids = set()
    if allocation:
        for zone_id, depot_id in allocation.items():
            if depot_id is not None:
                served_zone_ids.add(zone_id)

    for zone_id, zone in zones.items():
        is_unserved = allocation is not None and zone_id not in served_zone_ids
        label = zone.get("county_name", zone.get("designatedArea", zone_id))
        popup_text = f"{label}<br>Severity: {zone['severity']:.1f}"
        if "population" in zone:
            popup_text += f"<br>Population: ~{zone['population']:,}"
        if allocation is not None:
            popup_text += "<br><b>UNSERVED</b>" if is_unserved else "<br>Served"
        folium.CircleMarker(
            location=[zone["lat"], zone["lon"]], radius=9,
            color="black" if is_unserved else _severity_color(zone["severity"]),
            fill=True, fill_color=_severity_color(zone["severity"]),
            fill_opacity=0.4 if is_unserved else 0.85,
            weight=3 if is_unserved else 1, popup=popup_text,
        ).add_to(m)

    for depot_id, depot in depots.items():
        label = depot.get("name", depot_id)
        folium.Marker(
            location=[depot["lat"], depot["lon"]],
            popup=f"{label}<br>Capacity: {depot['capacity']}",
            icon=folium.Icon(color="blue", icon="home"),
        ).add_to(m)

    if allocation:
        for zone_id, depot_id in allocation.items():
            if depot_id is None:
                continue
            zone = zones[zone_id]
            depot = depots[depot_id]
            folium.PolyLine(
                locations=[[zone["lat"], zone["lon"]], [depot["lat"], depot["lon"]]],
                color="gray", weight=1.5, opacity=0.6,
            ).add_to(m)

    m.save(output_path)
    return output_path


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from data.curated_real_examples import build_florence_zones, build_florence_depots
    from optimized.branch_and_bound import branch_and_bound_search

    zones = build_florence_zones()
    depots = build_florence_depots()
    allocation, score, _ = branch_and_bound_search(zones, depots)

    out_path = os.path.join(os.path.dirname(__file__), "florence_allocation_map.html")
    build_map(zones, depots, allocation=allocation, output_path=out_path)
    print(f"Map saved to {out_path} (score: {score:.2f})")
