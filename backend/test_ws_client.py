import asyncio
import websockets
import json

WS_URL = "ws://127.0.0.1:8000/ws/alerts"

async def listen_alerts():
    print(f"Connecting to live alert stream at {WS_URL}...")
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("[Connected] Waiting for real-time security alerts from backend...\n")
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print("=" * 50)
                print("🚨 REAL-TIME ALERT RECEIVED ON WEBSOCKET 🚨")
                print(f"Alert ID     : {data.get('alert_id')}")
                print(f"Target Class : {data.get('object_class')}")
                print(f"Zone         : {data.get('zone')}")
                print(f"Coordinates  : Lat {data.get('lat')}, Lng {data.get('lng')}")
                print(f"Timestamp    : {data.get('timestamp')}")
                print("=" * 50 + "\n")
    except Exception as e:
        print(f"WebSocket connection error: {e}")

if __name__ == "__main__":
    asyncio.run(listen_alerts())