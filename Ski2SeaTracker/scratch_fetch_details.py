import urllib.request
import urllib.parse
import json

# Let's test 2024 (race_id 291757) and 2026 (race_id 399822)
for year, race_id, bib, key in [
    ("2024", 291757, 101, "b91f4cf20c7c01ff08d59f2cdb5db937"),
    ("2026", 399822, 101, "b91f4cf20c7c01ff08d59f2cdb5db937")
]:
    url = f"https://my2.raceresult.com/{race_id}/RRPublish/data/list"
    params = {
        "key": key,
        "listname": "Result Lists|Team Details",
        "page": "live",
        "contest": "0",
        "r": "search",
        "filterbib": str(bib)
    }

    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"
    print(f"\n--- {year} Team Details for BIB {bib} ---")
    print("URL:", full_url)

    try:
        req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
        data = json.loads(content)
        
        if "DataFields" in data:
            print("Fields:")
            for idx, field in enumerate(data["DataFields"]):
                print(f"  Field {idx}: {field}")
        if "data" in data:
            print("Data rows count:", len(data["data"]))
            if len(data["data"]) > 0:
                print("First row sample:")
                print(json.dumps(data["data"][0], indent=2))
            # If data is a dict or nested, print structure
            if isinstance(data["data"], dict):
                print("Data is a dict with keys:", data["data"].keys())
        else:
            print("No data key in response")
    except Exception as e:
        print("Error:", e)
