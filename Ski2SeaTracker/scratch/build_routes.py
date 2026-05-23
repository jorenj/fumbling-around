import os
import xml.etree.ElementTree as ET
import json
import urllib.request
import urllib.parse

# Mapping of leg IDs to GPX files
GPX_FILES = {
    "xcski": "Nordic_ski_leg_1.gpx",
    "dhski": "Ski_to_Sea_Downhill_Ski_Leg.gpx",
    "run": "Ski_to_sea_run_leg.gpx",
    "bike": "Ski_to_sea_bike_leg.gpx",
    "cyclox": "cyclox_leg.gpx",
    "kayak": "kayak_leg.gpx"
}

# Color palette for each leg
LEG_STYLES = {
    "xcski": {"name": "Leg 1: Cross Country Ski", "color": "#14b8a6"}, # teal
    "dhski": {"name": "Leg 2: Downhill Ski", "color": "#3b82f6"},      # blue
    "run": {"name": "Leg 3: Running", "color": "#10b981"},            # green
    "bike": {"name": "Leg 4: Road Biking", "color": "#f59e0b"},        # amber
    "canoe": {"name": "Leg 5: Canoeing (River)", "color": "#06b6d4"},  # cyan
    "cyclox": {"name": "Leg 6: Cyclocross", "color": "#8b5cf6"},       # purple
    "kayak": {"name": "Leg 7: Sea Kayaking", "color": "#ec4899"}       # pink
}

def parse_gpx(filepath, downsample_rate=10):
    """Parses a GPX file and returns a list of [lng, lat] coordinates."""
    if not os.path.exists(filepath):
        print(f"Warning: File {filepath} not found.")
        return []
    
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return []
    
    # Handle GPX namespaces
    namespace = ""
    if root.tag.startswith("{"):
        namespace = root.tag.split("}")[0] + "}"
        
    coords = []
    # Find all track points
    for trkpt in root.findall(f".//{namespace}trkpt"):
        lat = float(trkpt.attrib["lat"])
        lon = float(trkpt.attrib["lon"])
        coords.append([lon, lat])
        
    if not coords:
        return []
    
    # Downsample to keep the GeoJSON file lightweight
    downsampled = coords[::downsample_rate]
    # Ensure the last coordinate is included
    if coords[-1] not in downsampled:
        downsampled.append(coords[-1])
        
    print(f"Parsed {filepath}: extracted {len(coords)} points, downsampled to {len(downsampled)}.")
    return downsampled

def fetch_canoe_river_route():
    """Fetches the Nooksack River geometry between Everson and Ferndale from OpenStreetMap Overpass API."""
    print("Fetching Nooksack River geometry from OSM Overpass API...")
    
    # Overpass QL query:
    # Bounding box covers the Nooksack River from Everson (48.917) down to Ferndale (48.836).
    query = """
    [out:json][timeout:30];
    (
      way["waterway"="river"]["name"="Nooksack River"](48.80,-122.65,48.95,-122.30);
    );
    out geom;
    """
    
    url = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({'data': query}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Ski2SeaTracker/1.0'})
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Failed to fetch Nooksack River waterway: {e}")
        return []
        
    elements = res_data.get("elements", [])
    if not elements:
        print("No elements returned from Overpass API.")
        return []
        
    print(f"Found {len(elements)} river way segments.")
    
    # We need to assemble the river segments from Everson (East/North) to Ferndale (West/South).
    # Each element represents a way with a "geometry" list of {"lat": ..., "lon": ...}
    # Let's collect all segments.
    segments = []
    for el in elements:
        geom = el.get("geometry", [])
        if geom:
            coords = [[pt["lon"], pt["lat"]] for pt in geom]
            segments.append(coords)
            
    if not segments:
        return []
        
    # Let's stitch the segments together.
    # We want a continuous line starting from Everson (approx [-122.349, 48.917])
    # to Ferndale (approx [-122.594, 48.836]).
    # We can perform a greedy stitch.
    stitched = []
    remaining = list(segments)
    
    # Start with the segment closest to Everson hand-off
    everson_pt = [-122.349, 48.917]
    
    def dist_sq(p1, p2):
        return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2
        
    # Find initial segment
    best_idx = 0
    min_d = float('inf')
    reverse_initial = False
    
    for i, seg in enumerate(remaining):
        d_start = dist_sq(seg[0], everson_pt)
        d_end = dist_sq(seg[-1], everson_pt)
        if d_start < min_d:
            min_d = d_start
            best_idx = i
            reverse_initial = False
        if d_end < min_d:
            min_d = d_end
            best_idx = i
            reverse_initial = True
            
    current_seg = remaining.pop(best_idx)
    if reverse_initial:
        current_seg.reverse()
    stitched.extend(current_seg)
    
    # Greedily connect other segments
    while remaining:
        end_pt = stitched[-1]
        best_idx = -1
        min_d = 0.005 # Match tolerance (within ~500m)
        reverse = False
        
        for i, seg in enumerate(remaining):
            d_start = dist_sq(seg[0], end_pt)
            d_end = dist_sq(seg[-1], end_pt)
            if d_start < min_d:
                min_d = d_start
                best_idx = i
                reverse = False
            elif d_end < min_d:
                min_d = d_end
                best_idx = i
                reverse = True
                
        if best_idx != -1:
            next_seg = remaining.pop(best_idx)
            if reverse:
                next_seg.reverse()
            # Avoid duplicating connection point
            stitched.extend(next_seg[1:])
        else:
            # If no connected segment is found, find the closest one
            best_idx = 0
            min_d = float('inf')
            reverse = False
            for i, seg in enumerate(remaining):
                d_start = dist_sq(seg[0], end_pt)
                d_end = dist_sq(seg[-1], end_pt)
                if d_start < min_d:
                    min_d = d_start
                    best_idx = i
                    reverse = False
                if d_end < min_d:
                    min_d = d_end
                    best_idx = i
                    reverse = True
            
            next_seg = remaining.pop(best_idx)
            if reverse:
                next_seg.reverse()
            stitched.extend(next_seg)
            
    print(f"Stitched river route has {len(stitched)} coordinates.")
    
    # Downsample the river route to keep it small
    downsampled_river = stitched[::5]
    if stitched[-1] not in downsampled_river:
        downsampled_river.append(stitched[-1])
        
    return downsampled_river

def main():
    features = []
    
    # 1. Parse GPX files
    for leg_id, filename in GPX_FILES.items():
        coords = parse_gpx(filename, downsample_rate=10)
        if coords:
            features.append({
                "type": "Feature",
                "properties": {
                    "leg": leg_id,
                    "name": LEG_STYLES[leg_id]["name"],
                    "color": LEG_STYLES[leg_id]["color"]
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                }
            })
            
    # 2. Fetch/Build Canoe (River) Leg
    canoe_coords = fetch_canoe_river_route()
    if canoe_coords:
        features.append({
            "type": "Feature",
            "properties": {
                "leg": "canoe",
                "name": LEG_STYLES["canoe"]["name"],
                "color": LEG_STYLES["canoe"]["color"]
            },
            "geometry": {
                "type": "LineString",
                "coordinates": canoe_coords
            }
        })
    else:
        print("Warning: Canoe leg could not be built.")
        
    # Write to route.geojson
    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    
    output_path = "public/data/route.geojson"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, indent=2)
        
    print(f"Successfully compiled route.geojson with {len(features)} legs!")

if __name__ == "__main__":
    main()
