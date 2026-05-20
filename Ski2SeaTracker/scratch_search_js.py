import re
import urllib.request

# The React JS bundle URL from previous session
js_url = "https://results.pacificmultisports.com/assets/index-DnPyknRT.js"

try:
    req = urllib.request.Request(js_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        js_content = response.read().decode('utf-8')
    
    # Search for year configurations, e.g. "2024:{" or similar
    print("Searching for year config in JS bundle:")
    
    # Print occurrences of patterns like raceId:
    configs = re.findall(r'(\d{4}):\s*\{[^}]*?raceId:\s*(\d+)[^}]*?\}', js_content)
    for cfg in configs:
        print(f"Year {cfg[0]}: raceId = {cfg[1]}")
        
    # Let's extract blocks around "2024:" or "2025:"
    for yr in ["2024", "2025", "2026"]:
        pos = js_content.find(f'{yr}:')
        if pos != -1:
            print(f"\nSnippet for {yr}:")
            print(js_content[pos:pos+500])
            
except Exception as e:
    print("Error:", e)
