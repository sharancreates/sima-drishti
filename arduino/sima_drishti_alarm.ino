/*
 * =====================================================================
 * SIMA-DRISHTI: AI Tactical Perimeter Defense - Hardware Bridge
 * Target Microcontroller: Arduino Uno (ATmega328P)
 * Description: Listens on USB Serial for tactical breach commands
 *              ("ALERT_ON\n" / "ALERT_OFF\n") from SIMA-DRISHTI backend
 *              to trigger an audible buzzer and high-intensity strobe LED.
 * =====================================================================
 * 
 * WIRING DIAGRAM:
 * ---------------------------------------------------------------------
 * 1. Active Buzzer:
 *    - Positive (+) pin -> Arduino Digital Pin 8
 *    - Negative (-) pin -> Arduino GND
 * 
 * 2. Alarm LED (Red):
 *    - Anode (Long leg, +) -> 220 Ohm resistor -> Arduino Digital Pin 13 (or Pin 7)
 *    - Cathode (Short leg, -) -> Arduino GND
 *    *(Note: Pin 13 also controls the built-in LED on the Arduino Uno)*
 * ---------------------------------------------------------------------
 */

const int BUZZER_PIN = 8;     // Active buzzer trigger pin
const int LED_PIN = 13;       // Alert indicator LED (also Uno onboard LED)
const unsigned long ALARM_DURATION_MS = 4000; // Auto-silence safety timeout (4 seconds)

bool alarmActive = false;
unsigned long alarmStartTime = 0;
unsigned long lastStrobeToggle = 0;
bool strobeState = false;
String inputString = "";

void setup() {
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);

  // Ensure initial safe state (OFF)
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(LED_PIN, LOW);

  // Initialize Serial interface matching backend SERIAL_BAUD (9600)
  Serial.begin(9600);
  inputString.reserve(64);

  // Startup confirmation pulse (2 short beeps)
  digitalWrite(LED_PIN, HIGH);
  digitalWrite(BUZZER_PIN, HIGH);
  delay(80);
  digitalWrite(LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);
  delay(80);
  digitalWrite(LED_PIN, HIGH);
  digitalWrite(BUZZER_PIN, HIGH);
  delay(80);
  digitalWrite(LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);

  Serial.println(F("[ARDUINO] SIMA-DRISHTI Hardware Bridge Ready."));
}

void loop() {
  // 1. Process incoming serial commands from FastAPI backend
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n' || inChar == '\r') {
      inputString.trim();
      if (inputString.length() > 0) {
        handleCommand(inputString);
        inputString = "";
      }
    } else {
      inputString += inChar;
    }
  }

  // 2. Handle active alarm state (tactical strobe & siren pattern)
  if (alarmActive) {
    unsigned long currentMillis = millis();

    // Auto-silence safety check
    if (currentMillis - alarmStartTime >= ALARM_DURATION_MS) {
      stopAlarm();
      Serial.println(F("[ARDUINO] Alarm auto-silenced after timeout."));
    } else {
      // Tactical pulsed strobe (120ms ON, 80ms OFF)
      if (currentMillis - lastStrobeToggle >= (strobeState ? 120 : 80)) {
        strobeState = !strobeState;
        digitalWrite(LED_PIN, strobeState ? HIGH : LOW);
        digitalWrite(BUZZER_PIN, strobeState ? HIGH : LOW);
        lastStrobeToggle = currentMillis;
      }
    }
  }
}

void handleCommand(const String& cmd) {
  if (cmd == "ALERT_ON" || cmd == "1") {
    startAlarm();
  } else if (cmd == "ALERT_OFF" || cmd == "0") {
    stopAlarm();
  }
}

void startAlarm() {
  alarmActive = true;
  alarmStartTime = millis();
  strobeState = true;
  digitalWrite(LED_PIN, HIGH);
  digitalWrite(BUZZER_PIN, HIGH);
  lastStrobeToggle = millis();
  Serial.println(F("[ARDUINO] ALARM ACTIVATED -> LED & Buzzer ON"));
}

void stopAlarm() {
  alarmActive = false;
  strobeState = false;
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(LED_PIN, LOW);
  Serial.println(F("[ARDUINO] ALARM SILENCED -> LED & Buzzer OFF"));
}
