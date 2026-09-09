import os
import serial
from dotenv import load_dotenv

load_dotenv()

SERIAL_PORT = os.getenv("SERIAL_PORT", "COM3")
SERIAL_BAUD = int(os.getenv("SERIAL_BAUD", 9600))
FALLBACK_MODE = os.getenv("FALLBACK_MODE", "False").lower() == "true"

class HardwareBridge:
    def __init__(self):
        self.serial_conn = None
        if not FALLBACK_MODE:
            try:
                self.serial_conn = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1, write_timeout=1)
                print(f"[Hardware] Connected to serial port {SERIAL_PORT} at {SERIAL_BAUD} baud.")
            except Exception as e:
                print(f"[Hardware Warning] Could not connect to {SERIAL_PORT}: {e}. Running in simulation/fallback mode.")
                self.serial_conn = None

    def trigger_alert(self):
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(b"ALERT_ON\n")
                self.serial_conn.flush()
                print("[Hardware] Serial signal sent: 'ALERT_ON\\n'")
            except Exception as e:
                print(f"[Hardware Error] Failed to write to serial: {e}")
        else:
            print("[Hardware Simulation] Alert triggered: 'ALERT_ON' (Fallback Mode).")

    def silence_alert(self):
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(b"ALERT_OFF\n")
                self.serial_conn.flush()
                print("[Hardware] Serial signal sent: 'ALERT_OFF\\n'")
            except Exception as e:
                print(f"[Hardware Error] Failed to write to serial: {e}")
        else:
            print("[Hardware Simulation] Alert silenced: 'ALERT_OFF' (Fallback Mode).")

hardware_bridge = HardwareBridge()