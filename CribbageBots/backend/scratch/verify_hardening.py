import asyncio
import websockets
import json
import time

async def test_token_throttling():
    print("Testing token throttling...")
    uri = "ws://localhost:8000/ws/bot/TestBot?token=secret"
    
    # First connection to claim ID
    async with websockets.connect(uri) as websocket:
        print("  ✓ Claimed TestBot with token 'secret'")
    
    # Attempt with wrong token
    start = time.time()
    try:
        async with websockets.connect("ws://localhost:8000/ws/bot/TestBot?token=wrong") as ws:
            pass
    except websockets.exceptions.ConnectionClosedOK:
        # FastAPI might close it with code 1008
        pass
    except Exception as e:
        print(f"  Caught expected close: {e}")
        
    elapsed = time.time() - start
    print(f"  Elapsed time for failed attempt: {elapsed:.2f}s")
    if elapsed >= 1.0:
        print("  ✓ Token throttling working correctly")
    else:
        print("  ✗ Token throttling failed (too fast)")

if __name__ == "__main__":
    try:
        asyncio.run(test_token_throttling())
    except Exception as e:
        print(f"Server might not be running: {e}")
