import xml.etree.ElementTree as ET
import os

def get_gpx_endpoints(filepath):
    if not os.path.exists(filepath):
        print(f"File {filepath} not found.")
        return None
        
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    namespace = ""
    if root.tag.startswith("{"):
        namespace = root.tag.split("}")[0] + "}"
        
    pts = []
    for trkpt in root.findall(f".//{namespace}trkpt"):
        lat = float(trkpt.attrib["lat"])
        lon = float(trkpt.attrib["lon"])
        pts.append((lat, lon))
        
    if not pts:
        return None
        
    return pts[0], pts[-1]

run_ends = get_gpx_endpoints("Ski_to_sea_run_leg.gpx")
bike_ends = get_gpx_endpoints("Ski_to_sea_bike_leg.gpx")

if run_ends:
    print(f"Run Leg: Start = {run_ends[0]}, End = {run_ends[1]}")
if bike_ends:
    print(f"Bike Leg: Start = {bike_ends[0]}, End = {bike_ends[1]}")
