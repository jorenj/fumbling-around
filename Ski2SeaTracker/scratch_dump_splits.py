import urllib.request
import json

for year, race_id in [("2024", 291757), ("2026", 399822)]:
    url = f"https://my.raceresult.com/{race_id}/RRPublish/data/config?page=live&v=1"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
        data = json.loads(content)
        print(f"\n--- {year} Splits (race_id: {race_id}) ---")
        if "splits" in data:
            for s in data["splits"]:
                print(f"  ID: {s.get('ID')}, Name: {s.get('Name')}, Contest: {s.get('Contest')}, Label: {s.get('Label')}")

        else:
            print("No splits found in config")
    except Exception as e:
        print(f"Error {year}:", e)
