import time
import asyncio
import json
import urllib.request
from statistics import mean

async def benchmark_tournament(num_games=5):
    print(f"Starting performance benchmark: GeminiFlash vs GeminiFlash ({num_games} games)...")
    
    payload = {
        "p1_type": "flash",
        "p2_type": "flash",
        "p1_id": "Flash-1",
        "p2_id": "Flash-2",
        "num_games": num_games
    }
    
    start_time = time.time()
    
    try:
        req = urllib.request.Request(
            "http://localhost:8000/api/tournament",
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        total_time = time.time() - start_time
        avg_time = total_time / num_games
        
        print(f"\n--- Benchmark Results ---")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Avg Time per Game: {avg_time:.2f}s")
        print(f"Integrity Violated: {result.get('integrity_violated', False)}")
        print(f"-------------------------")
        
    except Exception as e:
        print(f"Benchmark failed: {e}")

if __name__ == "__main__":
    asyncio.run(benchmark_tournament())
