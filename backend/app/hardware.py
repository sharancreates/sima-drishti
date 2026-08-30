import logging
from typing import Optional

logger = logging.getLogger("hardware")

class ArduinoBridge:
    """
    Serial trigger bridge for Arduino alert indicators (LED/Buzzer).
    Falls back gracefully if hardware is not connected.
    """
    def __init__(self, port: Optional[str] = None, baudrate: int = 9600):
        self.ser = None
        self.connected = False
        if port:
            self.connect(port, baudrate)

    def connect(self, port: str, baudrate: int = 9600):
        try:
            import serial
            self.ser = serial.Serial(port, baudrate, timeout=1)
            self.connected = True
            logger.info(f"Connected to Arduino on port {port}")
        except Exception as e:
            self.connected = False
            logger.warning(f"Arduino connection failed on {port}: {e}. Mock mode active.")

    def trigger_alert(self):
        if self.connected and self.ser:
            try:
                self.ser.write(b"ALERT_ON\n")
            except Exception as e:
                logger.error(f"Failed to write to serial: {e}")
        else:
            logger.info("[MOCK ARDUINO] Signal sent: ALERT_ON")

    def reset_alert(self):
        if self.connected and self.ser:
            try:
                self.ser.write(b"ALERT_OFF\n")
            except Exception as e:
                logger.error(f"Failed to write to serial: {e}")
        else:
            logger.info("[MOCK ARDUINO] Signal sent: ALERT_OFF")

hardware_bridge = ArduinoBridge()