import urllib.request
import json

race_id = 399822 # 2026
url = f"https://my.raceresult.com/{race_id}/RRPublish/data/config?page=live&v=1"

try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        content = response.read().decode('utf-8')
    data = json.loads(content)
    
    if "splits" in data:
        print("Splits is a:", type(data["splits"]))
        print("First 3 elements of splits:")
        print(json.dumps(data["splits"][:3], indent=2))
    else:
        print("No splits key in config")
except Exception as e:
    print("Error:", e)
