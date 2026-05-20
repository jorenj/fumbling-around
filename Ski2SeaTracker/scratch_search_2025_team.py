import urllib.request
import urllib.parse
import json

race_id = 340596 # 2025
key = "02PHAOGJWM5QHZELNBVH09BKZDMR3IWT"

fields = [
    "BIB", "id", "TeamName", "Division",
    "XC_Ski_Racer", "XCSKI_SPLIT", "XCSKIRank",
    "DH_Ski_Snowboard_Racer", "DHSKI_SPLIT", "DHSKIRank",
    "Run_Racer", "RUN_SPLIT", "RunRank",
    "RD_Bike_Racer", "ROADBIKE_SPLIT", "RoadBikeRank",
    "Canoers", "CANOE_SPLIT", "CanoeRank",
    "CX_Racer", "CYCLOCROSS_SPLIT", "CyclocrossRank",
    "Kayak_Racer", "KAYAK_SPLIT", "KayakRank"
]
url = f"https://api.raceresult.com/{race_id}/{key}"
params = {
    "listFormat": "JSON",
    "fields": ",".join(fields),
    "filterbib": "471"
}
query_string = urllib.parse.urlencode(params)
full_url = f"{url}?{query_string}"

try:
    req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as response:
        content = response.read().decode('utf-8')
    data = json.loads(content)
    if data and len(data) > 0:
        row = data[0]
        mapped = {fields[i]: row[i] for i in range(len(fields))}
        print(json.dumps(mapped, indent=2))
    else:
        print("No data found for 471")
except Exception as e:
    print("Error:", e)
