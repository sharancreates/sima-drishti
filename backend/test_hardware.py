import os
import time
import serial
from dotenv import load_dotenv

load_dotenv()

PORT = os.getenv("SERIAL_PORT", "COM3")
BAUD = int(os.getenv("SERIAL_BAUD", 9600))

print(f"==================================================")
print(f"   SIMA-DRISHTI ARDUINO HARDWARE BRIDGE TESTER   ")
print(f"==================================================")
print(f"Connecting to Arduino Uno on {PORT} at {BAUD} baud...")

try:
    ser = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(2.0)  # Wait for Arduino auto-reset on DTR
    print(f"Connected to {PORT} successfully!")
    
    # Read any startup line from Arduino
    if ser.in_waiting:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        print(f"[Arduino Response] {line}")

    print("\n[Step 1] Sending 'ALERT_ON\\n' (Buzzer & LED should strobe for 3 seconds)...")
    ser.write(b"ALERT_ON\n")
    ser.flush()
    time.sleep(3.0)

    print("\n[Step 2] Sending 'ALERT_OFF\\n' (Buzzer & LED should silence)...")
    ser.write(b"ALERT_OFF\n")
    ser.flush()
    time.sleep(1.0)

    if ser.in_waiting:
        while ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"[Arduino Response] {line}")

    ser.close()
    print("\n[SUCCESS] Hardware test completed successfully.")

except serial.SerialException as e:
    print(f"\n[FAILED] Could not connect to {PORT}: {e}")
    print("Troubleshooting tips:")
    print("1. Check Windows Device Manager under 'Ports (COM & LPT)' to confirm your Arduino's COM port number.")
    print("2. Ensure Arduino IDE Serial Monitor is closed (it locks the COM port).")
    print("3. Update SERIAL_PORT in backend/.env to match your actual COM port (e.g. COM4, COM5).")
