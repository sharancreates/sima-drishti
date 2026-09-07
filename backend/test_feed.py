import time
import requests
import json

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "sima-drishti-secure-key-2026"

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    print(f"[Health Check] Status: {response.status_code}, Body: {response.json()}")

def simulate_detection(payload):
    headers = {"X-API-Key": API_KEY}
    response = requests.post(f"{BASE_URL}/detection", json=payload, headers=headers)
    print(f"[{payload['object_class']} | Track ID: {payload['track_id']}] -> Status: {response.status_code}, Response: {response.json()}")
    return response

def test_dispatch(alert_id):
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    payload = {
        "alert_id": alert_id,
        "unit_id": "alpha",
        "target_sector": "Sector 04-North",
        "notes": "Automated QRT dispatch verification"
    }
    response = requests.post(f"{BASE_URL}/dispatch", json=payload, headers=headers)
    print(f"[Dispatch Test | Alert ID: {alert_id}] -> Status: {response.status_code}, Response: {response.json()}")
    return response

def run_tests():
    test_health()
    print("\n--- Test 1: Simulating an Animal (Should be Filtered) ---")
    dog_payload = {
        "object_class": "dog",
        "confidence": 0.88,
        "bbox": [100.0, 150.0, 200.0, 250.0],
        "track_id": 1,
        "in_zone": True,
        "timestamp": time.time()
    }
    simulate_detection(dog_payload)

    print("\n--- Test 2: Simulating Person Outside Zone (Should be Filtered) ---")
    person_outside = {
        "object_class": "person",
        "confidence": 0.92,
        "bbox": [300.0, 200.0, 400.0, 450.0],
        "track_id": 2,
        "in_zone": False,
        "timestamp": time.time()
    }
    simulate_detection(person_outside)

    print("\n--- Test 3: Simulating Person in Zone (Persistence Check) ---")
    for frame in range(1, 7):
        person_inside = {
            "object_class": "person",
            "confidence": 0.95,
            "bbox": [50.0, 50.0, 150.0, 300.0],
            "track_id": 3,
            "in_zone": True,
            "timestamp": time.time()
        }
        print(f"Sending frame {frame}...")
        simulate_detection(person_inside)
        time.sleep(0.5)

    print("\n--- Test 4: Fetch Alerts from Database ---")
    alerts_response = requests.get(f"{BASE_URL}/alerts")
    alerts = alerts_response.json()
    print(f"Total alerts in DB: {len(alerts)}")
    print(json.dumps(alerts, indent=2))

    if alerts and len(alerts) > 0:
        latest_alert_id = alerts[0]["alert_id"]
        print(f"\n--- Test 5: Simulating QRT Dispatch for Alert ID: {latest_alert_id} ---")
        test_dispatch(latest_alert_id)

if __name__ == "__main__":
    run_tests()