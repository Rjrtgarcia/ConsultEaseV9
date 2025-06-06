/**
 * Button Diagnostic Test for ESP32 Faculty Desk Unit
 * This is a minimal test program to diagnose button functionality
 * 
 * Use this to test if your physical buttons are working properly
 * Upload this to your ESP32 and monitor the serial output
 */

// Button pin definitions (same as your config.h)
#define BUTTON_A_PIN 15               // Blue button (Acknowledge)
#define BUTTON_B_PIN 4                // Red button (Busy)
#define BUTTON_DEBOUNCE_DELAY 50      // Debounce delay in milliseconds

// Built-in LED for visual feedback
#define LED_PIN 2

// Button state tracking
bool lastStateA = HIGH;
bool lastStateB = HIGH;
unsigned long lastDebounceA = 0;
unsigned long lastDebounceB = 0;
bool buttonAPressed = false;
bool buttonBPressed = false;

// Status tracking
unsigned long lastStatusPrint = 0;
unsigned long buttonTestStart = 0;
int buttonAPressCount = 0;
int buttonBPressCount = 0;

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  while (!Serial && millis() < 3000); // Wait for serial connection
  
  Serial.println("=== ESP32 BUTTON DIAGNOSTIC TEST ===");
  Serial.println("This program tests the physical buttons on the faculty desk unit");
  Serial.println();
  
  // Configure button pins
  pinMode(BUTTON_A_PIN, INPUT_PULLUP);
  pinMode(BUTTON_B_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  
  Serial.printf("Button A (Acknowledge/Blue): Pin %d\n", BUTTON_A_PIN);
  Serial.printf("Button B (Busy/Red): Pin %d\n", BUTTON_B_PIN);
  Serial.printf("Debounce delay: %d ms\n", BUTTON_DEBOUNCE_DELAY);
  Serial.println();
  
  // Test initial pin states
  Serial.println("=== INITIAL PIN STATE TEST ===");
  bool initialA = digitalRead(BUTTON_A_PIN);
  bool initialB = digitalRead(BUTTON_B_PIN);
  
  Serial.printf("Button A initial state: %s (Pin %d = %s)\n", 
                initialA ? "HIGH (Not Pressed)" : "LOW (Pressed)", 
                BUTTON_A_PIN, 
                initialA ? "HIGH" : "LOW");
  
  Serial.printf("Button B initial state: %s (Pin %d = %s)\n", 
                initialB ? "HIGH (Not Pressed)" : "LOW (Pressed)", 
                BUTTON_B_PIN, 
                initialB ? "HIGH" : "LOW");
  
  if (!initialA) {
    Serial.println("⚠️  WARNING: Button A is showing LOW (pressed) at startup!");
    Serial.println("   This could indicate a wiring issue or the button is stuck");
  }
  
  if (!initialB) {
    Serial.println("⚠️  WARNING: Button B is showing LOW (pressed) at startup!");
    Serial.println("   This could indicate a wiring issue or the button is stuck");
  }
  
  Serial.println();
  Serial.println("=== STARTING BUTTON MONITORING ===");
  Serial.println("Press Button A (Pin 15) or Button B (Pin 4) to test...");
  Serial.println("Button presses will be logged with timestamps");
  Serial.println("LED will blink when buttons are pressed");
  Serial.println();
  
  buttonTestStart = millis();
  
  // Flash LED to indicate start
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }
}

void loop() {
  unsigned long currentTime = millis();
  
  // Read current button states
  bool currentA = digitalRead(BUTTON_A_PIN);
  bool currentB = digitalRead(BUTTON_B_PIN);
  
  // Button A handling with debounce
  if (currentA != lastStateA) {
    lastDebounceA = currentTime;
  }
  
  if ((currentTime - lastDebounceA) > BUTTON_DEBOUNCE_DELAY) {
    if (currentA == LOW && lastStateA == HIGH) {
      // Button A pressed (falling edge)
      buttonAPressed = true;
      buttonAPressCount++;
      
      Serial.printf("[%lu ms] 🔵 BUTTON A PRESSED! (Count: %d)\n", currentTime, buttonAPressCount);
      Serial.printf("        Pin %d: HIGH -> LOW (Button pressed)\n", BUTTON_A_PIN);
      
      // Flash LED
      digitalWrite(LED_PIN, HIGH);
      delay(100);
      digitalWrite(LED_PIN, LOW);
    }
    else if (currentA == HIGH && lastStateA == LOW) {
      // Button A released (rising edge)
      Serial.printf("[%lu ms] 🔵 BUTTON A RELEASED\n", currentTime);
      Serial.printf("        Pin %d: LOW -> HIGH (Button released)\n", BUTTON_A_PIN);
    }
  }
  lastStateA = currentA;
  
  // Button B handling with debounce
  if (currentB != lastStateB) {
    lastDebounceB = currentTime;
  }
  
  if ((currentTime - lastDebounceB) > BUTTON_DEBOUNCE_DELAY) {
    if (currentB == LOW && lastStateB == HIGH) {
      // Button B pressed (falling edge)
      buttonBPressed = true;
      buttonBPressCount++;
      
      Serial.printf("[%lu ms] 🔴 BUTTON B PRESSED! (Count: %d)\n", currentTime, buttonBPressCount);
      Serial.printf("        Pin %d: HIGH -> LOW (Button pressed)\n", BUTTON_B_PIN);
      
      // Flash LED twice
      for (int i = 0; i < 2; i++) {
        digitalWrite(LED_PIN, HIGH);
        delay(50);
        digitalWrite(LED_PIN, LOW);
        delay(50);
      }
    }
    else if (currentB == HIGH && lastStateB == LOW) {
      // Button B released (rising edge)
      Serial.printf("[%lu ms] 🔴 BUTTON B RELEASED\n", currentTime);
      Serial.printf("        Pin %d: LOW -> HIGH (Button released)\n", BUTTON_B_PIN);
    }
  }
  lastStateB = currentB;
  
  // Print status every 10 seconds
  if (currentTime - lastStatusPrint > 10000) {
    lastStatusPrint = currentTime;
    float testDurationMin = (currentTime - buttonTestStart) / 60000.0;
    
    Serial.println();
    Serial.printf("=== STATUS UPDATE (%.1f min) ===\n", testDurationMin);
    Serial.printf("Button A presses: %d\n", buttonAPressCount);
    Serial.printf("Button B presses: %d\n", buttonBPressCount);
    Serial.printf("Current Pin States: A=%s, B=%s\n", 
                  currentA ? "HIGH" : "LOW", 
                  currentB ? "HIGH" : "LOW");
    
    if (buttonAPressCount == 0 && buttonBPressCount == 0) {
      Serial.println("⚠️  No button presses detected yet");
      Serial.println("   Check wiring and button connections");
    } else {
      Serial.println("✅ Buttons are working!");
    }
    Serial.println();
  }
  
  // Small delay to prevent overwhelming the serial output
  delay(10);
}

/**
 * TROUBLESHOOTING GUIDE:
 * 
 * 1. If you see "WARNING: Button is showing LOW at startup":
 *    - Check if button is physically stuck
 *    - Check wiring connections
 *    - Verify button is normally open (not normally closed)
 * 
 * 2. If no button presses are detected:
 *    - Verify GPIO pins 15 and 4 are correctly wired
 *    - Check if buttons are normally open push buttons
 *    - Ensure buttons connect the pin to GND when pressed
 *    - Verify ESP32 is powered properly
 * 
 * 3. If only one button works:
 *    - Check individual wiring for the non-working button
 *    - Swap button connections to isolate hardware vs software issue
 * 
 * 4. If buttons trigger multiple times:
 *    - May be normal due to mechanical switch bounce
 *    - Check if BUTTON_DEBOUNCE_DELAY needs adjustment
 *    - Verify stable power supply
 * 
 * EXPECTED BEHAVIOR:
 * - Initial pin states should be HIGH (not pressed)
 * - Pressing button should show LOW state
 * - Releasing button should show HIGH state
 * - LED should flash when buttons are pressed
 * - Serial output should show press/release events with timestamps
 */ 