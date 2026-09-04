import serial
import time
import threading

class HardwareBridge:
    def __init__(self, port: str = "COM3", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self._connect()

    def _connect(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Allow Arduino reset on connection
            print(f"[Hardware] Successfully connected to microcontroller on {self.port}")
        except Exception as e:
            print(f"[Hardware Warning] Microcontroller not detected on {self.port} ({e}). Running in fallback mode.")
            self.serial_conn = None

    def trigger_alert(self):
        """Sends pulse trigger '1' to Arduino buzzer/relay circuit."""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                # Run in thread so serial I/O never blocks main event loop
                threading.Thread(target=self._send_signal, daemon=True).start()
            except Exception as e:
                print(f"[Hardware Error] Failed to send trigger: {e}")
        else:
            print("[Hardware Mock] BUZZER/RELAY TRIGGERED (No active serial port)")

    def _send_signal(self):
        try:
            self.serial_conn.write(b'1\n')
            time.sleep(1)
            self.serial_conn.write(b'0\n')
        except Exception as e:
            print(f"[Hardware Error] Serial write failed: {e}")

hardware_bridge = HardwareBridge()