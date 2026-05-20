import urllib.request
import urllib.parse
import json

year = 2026
config = {"race_id": 399822, "api_url_key": "02PHAOGJWM5QHZELNBVH09BKZDMR3IWT"}
bib = 101

fields = [
    "id","TeamName","Division","XC_Ski_Racer","DH_Ski_Snowboard_Racer","Run_Racer","Road_Bike_Racer","RD_Bike_Racer","Canoers","CX_Racer","Kayak_Racer","Started","XC_Ski_Time","DH_Ski_Time","Run_Time","Road_Bike_Time","Canoe_Time","Cyclocross_Time","Kayak_Time","XC_Ski_Rank","DH_Ski_Rank","Run_Rank","Road_Bike_Rank","Canoe_Rank","Cyclocross_Rank","Kayak_Rank","XC_SKI_SPLIT","XCSkiRank","DH_SKI_SPLIT","DHSkiRank","RUN_SPLIT","RunRank","ROAD_BIKE_SPLIT","RoadBikeRank","CANOE_SPLIT","CanoeRank","CYCLOCROSS_SPLIT","CyclocrossRank","KAYAK_SPLIT","KayakRank"
]

url = f"https://api.raceresult.com/{config['race_id']}/{config['api_url_key']}"
params = {
    "listFormat": "JSON",
    "fields": ",".join(fields),
    "filterbib": str(bib)
}
query_string = urllib.parse.urlencode(params)
full_url = f"{url}?{query_string}"
try:
    req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        content = response.read().decode('utf-8')
    data = json.loads(content)
    if data and len(data) > 0:
        row = data[0]
        mapped_data = {fields[i]: row[i] for i in range(len(fields))}
        print(json.dumps(mapped_data, indent=2))
    else:
        print("No data found")
except Exception as e:
    print("Error:", e)
















