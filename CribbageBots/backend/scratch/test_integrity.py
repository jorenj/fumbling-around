import asyncio
import threading
import time
import os

def simulate_attack():
    """Simulates an attacker editing rules.py mid-tournament."""
    # Give the tournament a few seconds to start
    time.sleep(3)
    print("\n[ATTACK] Modifying rules.py to trigger integrity guard...")
    
    rules_path = "backend/src/cribbage/rules.py"
    with open(rules_path, "r") as f:
        original_content = f.read()
    
    try:
        # Append a tiny comment that changes the SHA-256
        with open(rules_path, "a") as f:
            f.write("\n# Integrity Test Comment")
            
        time.sleep(5)
        print("[ATTACK] Modification complete. Waiting for engine to detect...")
        
    finally:
        # Restore original content
        with open(rules_path, "w") as f:
            f.write(original_content)
        print("[ATTACK] rules.py restored.")

async def run_integrity_test():
    print("Starting Integrity Guard verification...")
    
    # Start the attack thread
    threading.Thread(target=simulate_attack, daemon=True).start()
    
    # Start a long tournament via POST
    payload = {
        "p1_type": "greedy",
        "p2_type": "random",
        "p1_id": "P1",
        "p2_id": "P2",
        "num_games": 50
    }
    
    print("[TEST] Launching 50-game tournament...")
    try:
        import urllib.request
        import json
        
        req = urllib.request.Request(
            "http://localhost:8000/api/tournament",
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        if "error" in result:
            print(f"[TEST] Result: {result['error']}")
            if "Security Violation" in result["error"]:
                print("  ✓ SUCCESS: Integrity guard detected the modification!")
            else:
                print("  ✗ FAILED: Tournament failed but for the wrong reason.")
        else:
            print("  ✗ FAILED: Tournament completed successfully despite code modification.")
    except Exception as e:
        # Check if the error message itself contains the security violation
        err_msg = str(e)
        if "Security Violation" in err_msg:
             print(f"[TEST] Caught in exception: {err_msg}")
             print("  ✓ SUCCESS: Integrity guard detected the modification!")
        else:
             print(f"[TEST] Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_integrity_test())
