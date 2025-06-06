/**
 * ULTRA-SIMPLE Button Test for ESP32
 * No debouncing, no classes, just raw pin reading
 * Use this if the main diagnostic test doesn't work
 */

#define BUTTON_A_PIN 15
#define BUTTON_B_PIN 4
#define LED_PIN 2

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("=== ULTRA-SIMPLE BUTTON TEST ===");
  
  // Configure pins
  pinMode(BUTTON_A_PIN, INPUT_PULLUP);
  pinMode(BUTTON_B_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  
  Serial.printf("Reading pins %d and %d continuously...\n", BUTTON_A_PIN, BUTTON_B_PIN);
  Serial.println("Press buttons - any state change will be logged");
  
  // Flash LED to show startup
  for(int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }
}

void loop() {
  // Read pins directly
  bool pinA = digitalRead(BUTTON_A_PIN);
  bool pinB = digitalRead(BUTTON_B_PIN);
  
  // Print state every 100ms
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 100) {
    Serial.printf("Pin %d=%s, Pin %d=%s\n", 
                  BUTTON_A_PIN, pinA ? "HIGH" : "LOW",
                  BUTTON_B_PIN, pinB ? "HIGH" : "LOW");
    lastPrint = millis();
  }
  
  // Flash LED when any button is pressed (pin goes LOW)
  if (!pinA || !pinB) {
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(LED_PIN, LOW);
  }
  
  delay(10);
} 