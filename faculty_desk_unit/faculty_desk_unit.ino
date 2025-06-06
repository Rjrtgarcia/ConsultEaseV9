// ================================
// NU FACULTY DESK UNIT - ESP32
// ================================
// Capstone Project by Jeysibn
// WITH ADAPTIVE BLE SCANNER & GRACE PERIOD SYSTEM
// Date: May 29, 2025 23:19 (Philippines Time)
// Updated: Added 1-minute grace period for BLE disconnections
// 
// ✅ PERFORMANCE OPTIMIZATIONS APPLIED:
// - Reduced BLE scan frequency from 1s to 8s (major performance fix)
// - Enhanced MQTT publishing with forced processing loops
// - Optimized main loop timing to reduce from 3241ms to <100ms
// - Improved button response time with faster debouncing
// - Better queue processing with exponential backoff
// ================================


#include <WiFi.h>
#include <PubSubClient.h>
#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <SPI.h>
#include <time.h>
#include "config.h"
#include <ArduinoJson.h> // For parsing JSON MQTT messages

// ================================
// GLOBAL OBJECTS
// ================================
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_RST);
BLEScan* pBLEScan;

// ================================
// MQTT STATE DEFINITIONS AND HELPERS
// ================================
const char* getMqttStateString(int state) {
  switch(state) {
    case -4: return "CONNECTION_TIMEOUT";
    case -3: return "CONNECTION_LOST"; 
    case -2: return "CONNECT_FAILED";
    case -1: return "DISCONNECTED";
    case 0:  return "CONNECTED";
    case 1:  return "BAD_PROTOCOL";
    case 2:  return "BAD_CLIENT_ID";
    case 3:  return "UNAVAILABLE";
    case 4:  return "BAD_CREDENTIALS";
    case 5:  return "UNAUTHORIZED";
    default: return "UNKNOWN_STATE";
  }
}

bool isMqttReallyConnected() {
  bool connected = mqttClient.connected();
  int state = mqttClient.state();
  
  DEBUG_PRINTF("🔍 MQTT Status Check - connected(): %s, state(): %d (%s)\n", 
               connected ? "TRUE" : "FALSE", 
               state, 
               getMqttStateString(state));
  
  // Only consider truly connected if both conditions are met
  bool reallyConnected = connected && (state == 0);
  
  if (!reallyConnected) {
    DEBUG_PRINTF("⚠️ MQTT Connection Issue - connected=%s but state=%d (%s)\n",
                 connected ? "TRUE" : "FALSE",
                 state,
                 getMqttStateString(state));
  }
  
  return reallyConnected;
}

// ================================
// UI AND BUTTON VARIABLES
// ================================
bool timeInitialized = false;
unsigned long lastAnimationTime = 0;
bool animationState = false;

// Button variables
bool buttonAPressed = false;
bool buttonBPressed = false;
unsigned long buttonALastDebounce = 0;
unsigned long buttonBLastDebounce = 0;
bool buttonALastState = HIGH;
bool buttonBLastState = HIGH;

// Message variables
bool messageDisplayed = false;
unsigned long messageDisplayStart = 0;
String lastReceivedMessage = "";
String g_receivedConsultationId = "";

// Global variables
unsigned long lastHeartbeat = 0;
unsigned long lastMqttReconnect = 0;

bool wifiConnected = false;
bool mqttConnected = false;
String currentMessage = "";
String lastDisplayedTime = "";
String lastDisplayedDate = "";

// NTP synchronization variables
bool ntpSyncInProgress = false;
unsigned long lastNtpSyncAttempt = 0;
int ntpRetryCount = 0;
String ntpSyncStatus = "PENDING";

// ================================
// SIMPLE OFFLINE MESSAGE QUEUE
// ================================

struct SimpleMessage {
  char topic[64];
  char payload[512];
  unsigned long timestamp;
  int retry_count;
  bool is_response;
};

// Queue variables
SimpleMessage messageQueue[10];  // Adjust size as needed
int queueCount = 0;
bool systemOnline = false;

// ================================
// OFFLINE QUEUE FUNCTIONS
// ================================

void initOfflineQueue() {
  queueCount = 0;
  systemOnline = false;
  DEBUG_PRINTLN("📥 Offline message queue initialized");
}

bool queueMessage(const char* topic, const char* payload, bool isResponse = false) {
  if (queueCount >= 10) {
    DEBUG_PRINTLN("⚠️ Queue full, dropping oldest message");
    // Shift queue to make room
    for (int i = 0; i < 9; i++) {
      messageQueue[i] = messageQueue[i + 1];
    }
    queueCount = 9;
  }

  // Add new message
  strncpy(messageQueue[queueCount].topic, topic, 63);
  strncpy(messageQueue[queueCount].payload, payload, 511);
  messageQueue[queueCount].topic[63] = '\0';
  messageQueue[queueCount].payload[511] = '\0';
  messageQueue[queueCount].timestamp = millis();
  messageQueue[queueCount].retry_count = 0;
  messageQueue[queueCount].is_response = isResponse;

  queueCount++;
  DEBUG_PRINTF("📥 Queued message (%d in queue): %s\n", queueCount, topic);
  return true;
}

bool processQueuedMessages() {
  // ✅ ENHANCED: Use detailed MQTT state checking instead of just connected()
  if (!isMqttReallyConnected() || queueCount == 0) {
    if (queueCount > 0 && !isMqttReallyConnected()) {
      DEBUG_PRINTF("📥 Cannot process %d queued messages - MQTT not properly connected\n", queueCount);
    }
    return false;
  }

  // ✅ ENHANCED: Process one message at a time with better error handling
  DEBUG_PRINTF("📤 Processing queued message: %s\n", messageQueue[0].topic);
  
  // ✅ ENHANCED: Pre-publish validation
  int payloadLength = strlen(messageQueue[0].payload);
  DEBUG_PRINTF("📄 Queue message payload: %d bytes\n", payloadLength);
  
  // ✅ CRITICAL FIX: Use QoS 0 and NO retained flag for responses
  bool success = mqttClient.publish(messageQueue[0].topic, messageQueue[0].payload, false); // retained = false

  if (success) {
    DEBUG_PRINTF("✅ Sent queued message: %s (%d bytes)\n", messageQueue[0].topic, payloadLength);
    
    // ✅ CRITICAL FIX: Reduced MQTT processing to prevent blocking
    for (int i = 0; i < 3; i++) { // Reduced from 10 to 3
      mqttClient.loop();
      delay(10); // Reduced from 30ms to 10ms
    }

    // Remove processed message by shifting queue
    for (int i = 0; i < queueCount - 1; i++) {
      messageQueue[i] = messageQueue[i + 1];
    }
    queueCount--;
    return true;
  } else {
    // ✅ ENHANCED: Better error diagnostics with MQTT state checking
    int mqttState = mqttClient.state();
    messageQueue[0].retry_count++;
    
    DEBUG_PRINTF("❌ MQTT publish retry %d/3 FAILED for: %s\n", 
                 messageQueue[0].retry_count, messageQueue[0].topic);
    DEBUG_PRINTF("   📊 MQTT State: %d (%s)\n", mqttState, getMqttStateString(mqttState));
    DEBUG_PRINTF("   📄 Payload size: %d bytes\n", payloadLength);
    DEBUG_PRINTF("   🔌 WiFi connected: %s\n", wifiConnected ? "TRUE" : "FALSE");
    
    // ✅ ENHANCED: Check if we need to force reconnection
    if (mqttState != 0) {
      DEBUG_PRINTF("🔄 MQTT state not CONNECTED (%d), may need reconnection\n", mqttState);
      mqttConnected = false; // Force reconnection attempt in main loop
    }
    
    if (messageQueue[0].retry_count > 3) {
      DEBUG_PRINTF("❌ Message failed after 3 retries, dropping: %s\n", messageQueue[0].topic);
      DEBUG_PRINTF("   Final MQTT state was: %d (%s)\n", mqttState, getMqttStateString(mqttState));
      
      // Remove failed message
      for (int i = 0; i < queueCount - 1; i++) {
        messageQueue[i] = messageQueue[i + 1];
      }
      queueCount--;
    }
    // ✅ CRITICAL FIX: Removed blocking retry delay
    return false;
  }
}

void updateOfflineQueue() {
  // Update online status with enhanced MQTT checking
  bool wasOnline = systemOnline;
  systemOnline = wifiConnected && isMqttReallyConnected();

  // If just came online, process queue
  if (!wasOnline && systemOnline && queueCount > 0) {
    DEBUG_PRINTF("🌐 System online - processing %d queued messages\n", queueCount);
  }

  // ✅ CRITICAL FIX: Process multiple messages per cycle for better throughput
  if (systemOnline && queueCount > 0) {
    int processedCount = 0;
    int maxProcessPerCycle = min(3, queueCount); // Process up to 3 messages per cycle
    
    for (int i = 0; i < maxProcessPerCycle; i++) {
      if (processQueuedMessages()) {
        processedCount++;
      } else {
        break; // Stop if processing fails
      }
    }
    
    if (processedCount > 0) {
      DEBUG_PRINTF("📤 Processed %d queued messages this cycle\n", processedCount);
    }
  }
}

// Enhanced publish function with queuing
bool publishWithQueue(const char* topic, const char* payload, bool isResponse = false) {
  DEBUG_PRINTF("📤 Publishing to topic: %s\n", topic);
  DEBUG_PRINTF("📄 Payload length: %d bytes (MQTT limit: %d bytes)\n", strlen(payload), MQTT_MAX_PACKET_SIZE);
  
  // ✅ ENHANCED: Check payload size before attempting publish
  int payload_length = strlen(payload);
  if (payload_length > MQTT_MAX_PACKET_SIZE - 50) {
    DEBUG_PRINTF("❌ PAYLOAD TOO LARGE: %d bytes exceeds MQTT limit of %d bytes\n", 
                 payload_length, MQTT_MAX_PACKET_SIZE - 50);
    return false;
  }
  
  // ✅ ENHANCED: Use detailed MQTT state checking instead of just connected()
  if (isMqttReallyConnected()) {
    DEBUG_PRINTF("🔍 MQTT verified as properly connected, attempting direct publish\n");
    
    // ✅ CRITICAL FIX: No retained flag for responses, only for status updates
    bool useRetained = !isResponse; // Only retain status updates, not responses
    bool success = mqttClient.publish(topic, payload, useRetained);
    
    if (success) {
      DEBUG_PRINTF("✅ Direct MQTT publish SUCCESS (%d bytes)\n", payload_length);
      
      // ✅ CRITICAL FIX: Reduced MQTT processing to prevent blocking
      for (int i = 0; i < 3; i++) { // Reduced from 10 to 3
        mqttClient.loop();
        delay(15); // Reduced from 50ms to 15ms
      }
      
      return true;
    } else {
      // ✅ ENHANCED: Better error diagnostics with MQTT state after failed publish
      int mqttState = mqttClient.state();
      bool stillConnected = mqttClient.connected();
      
      DEBUG_PRINTF("❌ Direct MQTT publish FAILED (%d bytes), queuing message\n", payload_length);
      DEBUG_PRINTF("   📊 MQTT State after failure: %d (%s)\n", mqttState, getMqttStateString(mqttState));
      DEBUG_PRINTF("   🔌 Connected status after failure: %s\n", stillConnected ? "TRUE" : "FALSE");
      DEBUG_PRINTF("   🔌 WiFi status: %s\n", wifiConnected ? "TRUE" : "FALSE");
      
      // ✅ ENHANCED: Force reconnection if state changed
      if (mqttState != 0) {
        DEBUG_PRINTF("🔄 MQTT state corrupted after publish failure, forcing reconnection\n");
        mqttConnected = false; // Force reconnection attempt in main loop
      }
      
      // MQTT publish failed, queue the message
      return queueMessage(topic, payload, isResponse);
    }
  } else {
    // ✅ ENHANCED: Better diagnostics for connection issues
    int mqttState = mqttClient.state();
    bool connected = mqttClient.connected();
    
    DEBUG_PRINTF("❌ MQTT not properly connected, queuing message (%d bytes)\n", payload_length);
    DEBUG_PRINTF("   📊 MQTT State: %d (%s)\n", mqttState, getMqttStateString(mqttState));
    DEBUG_PRINTF("   🔌 Connected status: %s\n", connected ? "TRUE" : "FALSE");
    DEBUG_PRINTF("   🔌 WiFi status: %s\n", wifiConnected ? "TRUE" : "FALSE");
    
    // Not properly connected, queue the message
    return queueMessage(topic, payload, isResponse);
  }
}

// ================================
// FORWARD DECLARATIONS
// ================================
void publishPresenceUpdate();
void updateMainDisplay();
void updateSystemStatus();

// ================================
// BEACON VALIDATOR
// ================================
bool isFacultyBeacon(BLEAdvertisedDevice& device) {
  String deviceMAC = device.getAddress().toString().c_str();
  deviceMAC.toUpperCase();

  String expectedMAC = String(FACULTY_BEACON_MAC);
  expectedMAC.toUpperCase();

  return deviceMAC.equals(expectedMAC);
}

// ================================
// BUTTON HANDLING CLASS
// ================================
class ButtonHandler {
private:
  int pinA, pinB;
  bool lastStateA, lastStateB;
  unsigned long lastDebounceA, lastDebounceB;

public:
  ButtonHandler(int buttonAPin, int buttonBPin) {
    pinA = buttonAPin;
    pinB = buttonBPin;
    lastStateA = HIGH;
    lastStateB = HIGH;
    lastDebounceA = 0;
    lastDebounceB = 0;
  }

  void init() {
    pinMode(pinA, INPUT_PULLUP);
    pinMode(pinB, INPUT_PULLUP);
    DEBUG_PRINTLN("Buttons initialized:");
    DEBUG_PRINTF("  Button A (Blue/Acknowledge): Pin %d\n", pinA);
    DEBUG_PRINTF("  Button B (Red/Busy): Pin %d\n", pinB);
  }

  void update() {
    // Add debug logging for button states - REDUCED frequency for better real-time monitoring
    static unsigned long lastDebugPrint = 0;
    bool currentA = digitalRead(pinA);
    bool currentB = digitalRead(pinB);
    
    // Print raw button states every 10 seconds instead of 2 now that it's working
    if (millis() - lastDebugPrint > 10000) {
      DEBUG_PRINTF("🔧 Button Debug - Raw states: A(Pin%d)=%s, B(Pin%d)=%s\n", 
                   pinA, currentA ? "HIGH" : "LOW", 
                   pinB, currentB ? "HIGH" : "LOW");
      DEBUG_PRINTF("🔧 Button Debug - Flag states: buttonAPressed=%s, buttonBPressed=%s\n",
                   buttonAPressed ? "TRUE" : "FALSE",
                   buttonBPressed ? "TRUE" : "FALSE");
      lastDebugPrint = millis();
    }

    // Button A (Acknowledge) handling
    bool readingA = digitalRead(pinA);
    if (readingA != lastStateA) {
      lastDebounceA = millis();
      DEBUG_PRINTF("🔧 Button A state change: %s -> %s at %lu ms (debounce timer reset)\n", 
                   lastStateA ? "HIGH" : "LOW", 
                   readingA ? "HIGH" : "LOW",
                   millis());
      
      // IMMEDIATE DETECTION - Set flag instantly on press to handle slow main loops
      if (readingA == LOW && lastStateA == HIGH) {
        buttonAPressed = true;
        DEBUG_PRINTLN("🔵 BUTTON A PRESSED - FLAG SET IMMEDIATELY (no debounce wait)!");
      }
    }

    unsigned long currentTime = millis();
    unsigned long debounceElapsed = currentTime - lastDebounceA;
    
    if (debounceElapsed > BUTTON_DEBOUNCE_DELAY) {
      if (readingA == LOW && lastStateA == HIGH) {
        buttonAPressed = true;
        DEBUG_PRINTF("🔵 BUTTON A (ACKNOWLEDGE) PRESSED - FLAG SET! (debounce: %lu ms)\n", debounceElapsed);
      }
    } else {
      // Debug why debounce is blocking
      if (readingA == LOW && lastStateA == HIGH) {
        DEBUG_PRINTF("🕐 Button A press BLOCKED by debounce (elapsed: %lu ms < required: %d ms)\n", 
                     debounceElapsed, BUTTON_DEBOUNCE_DELAY);
      }
    }
    lastStateA = readingA;

    // Button B (Busy) handling
    bool readingB = digitalRead(pinB);
    if (readingB != lastStateB) {
      lastDebounceB = millis();
      DEBUG_PRINTF("🔧 Button B state change: %s -> %s at %lu ms (debounce timer reset)\n", 
                   lastStateB ? "HIGH" : "LOW", 
                   readingB ? "HIGH" : "LOW",
                   millis());
      
      // IMMEDIATE DETECTION - Set flag instantly on press to handle slow main loops
      if (readingB == LOW && lastStateB == HIGH) {
        buttonBPressed = true;
        DEBUG_PRINTLN("🔴 BUTTON B PRESSED - FLAG SET IMMEDIATELY (no debounce wait)!");
      }
    }

    unsigned long debounceElapsedB = currentTime - lastDebounceB;
    
    if (debounceElapsedB > BUTTON_DEBOUNCE_DELAY) {
      if (readingB == LOW && lastStateB == HIGH) {
        buttonBPressed = true;
        DEBUG_PRINTF("🔴 BUTTON B (BUSY) PRESSED - FLAG SET! (debounce: %lu ms)\n", debounceElapsedB);
      }
    } else {
      // Debug why debounce is blocking
      if (readingB == LOW && lastStateB == HIGH) {
        DEBUG_PRINTF("🕐 Button B press BLOCKED by debounce (elapsed: %lu ms < required: %d ms)\n", 
                     debounceElapsedB, BUTTON_DEBOUNCE_DELAY);
      }
    }
    lastStateB = readingB;
  }

  bool isButtonAPressed() {
    if (buttonAPressed) {
      DEBUG_PRINTLN("🔵 Button A flag was SET, clearing and returning TRUE");
      buttonAPressed = false;
      return true;
    }
    return false;
  }

  bool isButtonBPressed() {
    if (buttonBPressed) {
      DEBUG_PRINTLN("🔴 Button B flag was SET, clearing and returning TRUE");
      buttonBPressed = false;
      return true;
    }
    return false;
  }
};

// ================================
// ENHANCED PRESENCE DETECTOR WITH GRACE PERIOD
// ================================
class BooleanPresenceDetector {
private:
  bool currentPresence = false;           // Current confirmed status
  bool lastKnownPresence = false;         // Last status before disconnection
  unsigned long lastDetectionTime = 0;   // Last successful BLE detection
  unsigned long lastStateChange = 0;      // Last confirmed status change
  unsigned long gracePeriodStartTime = 0; // When grace period started

  // Grace period state
  bool inGracePeriod = false;
  int gracePeriodAttempts = 0;

  // Detection counters for immediate detection
  int consecutiveDetections = 0;
  int consecutiveMisses = 0;

  const int CONFIRM_SCANS = 2;            // Scans needed to confirm presence
  const int CONFIRM_ABSENCE_SCANS = 3;    // More scans needed to confirm absence

public:
  void checkBeacon(bool beaconFound, int rssi = 0) {
    unsigned long now = millis();

    if (beaconFound) {
      // Beacon detected!
      lastDetectionTime = now;
      consecutiveDetections++;
      consecutiveMisses = 0;

      // Optional RSSI filtering for better reliability
      if (rssi != 0 && rssi < BLE_SIGNAL_STRENGTH_THRESHOLD) {
        DEBUG_PRINTF("⚠️ Beacon found but signal weak: %d dBm (threshold: %d)\n",
                    rssi, BLE_SIGNAL_STRENGTH_THRESHOLD);
        return; // Ignore weak signals
      }

      // If we were in grace period, cancel it
      if (inGracePeriod) {
        DEBUG_PRINTF("✅ BLE reconnected during grace period! (attempt %d/%d)\n",
                   gracePeriodAttempts, BLE_RECONNECT_MAX_ATTEMPTS);
        endGracePeriod(true); // Successfully reconnected
      }

      // Confirm presence if we have enough detections
      if (consecutiveDetections >= CONFIRM_SCANS && !currentPresence) {
        updatePresenceStatus(true, now);
      }

    } else {
      // Beacon NOT detected
      consecutiveMisses++;
      consecutiveDetections = 0;

      // Handle absence detection
      if (currentPresence && consecutiveMisses >= CONFIRM_ABSENCE_SCANS) {
        // Professor was present but now we can't detect beacon
        if (!inGracePeriod) {
          startGracePeriod(now);
        } else {
          updateGracePeriod(now);
        }
      } else if (!currentPresence) {
        // Professor was already away, continue normal operation
        inGracePeriod = false;
      }
    }
  }

private:
  void startGracePeriod(unsigned long now) {
    inGracePeriod = true;
    gracePeriodStartTime = now;
    gracePeriodAttempts = 0;
    lastKnownPresence = currentPresence; // Remember status before grace period

    DEBUG_PRINTF("⏳ Starting grace period - Professor was PRESENT, giving %d seconds to reconnect...\n",
                BLE_GRACE_PERIOD_MS / 1000);

    // Note: No display changes - your existing display will continue showing "AVAILABLE"
    // until grace period expires, which is exactly what we want!
  }

  void updateGracePeriod(unsigned long now) {
    gracePeriodAttempts++;

    unsigned long elapsed = now - gracePeriodStartTime;
    unsigned long remaining = BLE_GRACE_PERIOD_MS - elapsed;

    DEBUG_PRINTF("⏳ Grace period: attempt %d/%d | %lu seconds remaining\n",
                gracePeriodAttempts, BLE_RECONNECT_MAX_ATTEMPTS, remaining / 1000);

    // Check if grace period expired
    if (elapsed >= BLE_GRACE_PERIOD_MS || gracePeriodAttempts >= BLE_RECONNECT_MAX_ATTEMPTS) {
      DEBUG_PRINTLN("⏰ Grace period expired - Professor confirmed AWAY");
      endGracePeriod(false); // Grace period failed
    }
  }

  void endGracePeriod(bool reconnected) {
    inGracePeriod = false;
    gracePeriodAttempts = 0;

    if (reconnected) {
      // Beacon reconnected - maintain PRESENT status
      DEBUG_PRINTLN("🔄 Grace period ended - Professor still PRESENT (reconnected)");
      // Status doesn't change, just clear grace period state
      // Display will continue showing "AVAILABLE" - no change needed!
    } else {
      // Grace period expired - confirm AWAY
      DEBUG_PRINTLN("🔄 Grace period expired - Professor confirmed AWAY");
      updatePresenceStatus(false, millis());
    }
  }

  void updatePresenceStatus(bool newPresence, unsigned long now) {
    if (newPresence != currentPresence) {
      currentPresence = newPresence;
      lastStateChange = now;

      DEBUG_PRINTF("🔄 Professor status CONFIRMED: %s\n",
                 currentPresence ? "PRESENT" : "AWAY");

      // Reset counters
      consecutiveDetections = 0;
      consecutiveMisses = 0;

      // Update systems
      publishPresenceUpdate();
      updateMainDisplay(); // This will call your existing display function
    }
  }

public:
  // Public getters (keeping your existing interface)
  bool getPresence() const {
    // During grace period, still return true (professor considered present)
    if (inGracePeriod) {
      return lastKnownPresence;
    }
    return currentPresence;
  }

  String getStatusString() const {
    // During grace period, maintain last known status
    if (inGracePeriod) {
      return lastKnownPresence ? "AVAILABLE" : "AWAY";
    }
    return currentPresence ? "AVAILABLE" : "AWAY";
  }

  // Additional methods for debugging (optional)
  bool isInGracePeriod() const { return inGracePeriod; }

  unsigned long getGracePeriodRemaining() const {
    if (!inGracePeriod) return 0;
    unsigned long elapsed = millis() - gracePeriodStartTime;
    return elapsed < BLE_GRACE_PERIOD_MS ? (BLE_GRACE_PERIOD_MS - elapsed) : 0;
  }

  String getDetailedStatus() const {
    if (inGracePeriod) {
      unsigned long remaining = getGracePeriodRemaining() / 1000;
      return "AVAILABLE (reconnecting... " + String(remaining) + "s)";
    }
    return getStatusString();
  }
};

// ================================
// ADAPTIVE BLE SCANNER CLASS (Enhanced for Grace Period)
// ================================
class AdaptiveBLEScanner {
private:
    enum ScanMode {
        SEARCHING,      // Looking for professor (frequent scans)
        MONITORING,     // Professor present (occasional scans)
        VERIFYING       // Confirming state change
    };

    ScanMode currentMode = SEARCHING;
    unsigned long lastScanTime = 0;
    unsigned long modeChangeTime = 0;
    unsigned long statsReportTime = 0;

    // Detection counters
    int consecutiveDetections = 0;
    int consecutiveMisses = 0;

    // Reference to presence detector (will be set in init)
    BooleanPresenceDetector* presenceDetectorPtr = nullptr;

    // Performance stats
    struct {
        unsigned long totalScans = 0;
        unsigned long successfulDetections = 0;
        unsigned long gracePeriodActivations = 0;
        unsigned long gracePeriodSuccesses = 0;
        unsigned long timeInSearching = 0;
        unsigned long timeInMonitoring = 0;
        unsigned long timeInVerifying = 0;
        unsigned long lastModeStart = 0;
    } stats;

    // Dynamic intervals based on mode and grace period
    unsigned long getCurrentScanInterval() {
        // During grace period, scan more frequently to catch reconnections
        if (presenceDetectorPtr && presenceDetectorPtr->isInGracePeriod()) {
            return BLE_RECONNECT_ATTEMPT_INTERVAL;
        }

        switch(currentMode) {
            case SEARCHING: return BLE_SCAN_INTERVAL_SEARCHING;
            case MONITORING: return BLE_SCAN_INTERVAL_MONITORING;
            case VERIFYING: return BLE_SCAN_INTERVAL_VERIFICATION;
            default: return BLE_SCAN_INTERVAL_SEARCHING;
        }
    }

    int getCurrentScanDuration() {
        // During grace period, use quick scans to save power while still being responsive
        if (presenceDetectorPtr && presenceDetectorPtr->isInGracePeriod()) {
            return BLE_SCAN_DURATION_QUICK;
        }

        switch(currentMode) {
            case SEARCHING: return BLE_SCAN_DURATION_FULL;
            case MONITORING: return BLE_SCAN_DURATION_QUICK;
            case VERIFYING: return BLE_SCAN_DURATION_QUICK;
            default: return BLE_SCAN_DURATION_FULL;
        }
    }

    void updateStats(unsigned long now) {
        // Update time in current mode
        unsigned long timeInMode = now - stats.lastModeStart;
        switch(currentMode) {
            case SEARCHING: stats.timeInSearching += timeInMode; break;
            case MONITORING: stats.timeInMonitoring += timeInMode; break;
            case VERIFYING: stats.timeInVerifying += timeInMode; break;
        }
        stats.lastModeStart = now;

        // Report stats periodically
        if (now - statsReportTime > BLE_STATS_REPORT_INTERVAL) {
            reportStats();
            statsReportTime = now;
        }
    }

    void reportStats() {
        unsigned long totalTime = stats.timeInSearching + stats.timeInMonitoring + stats.timeInVerifying;
        if (totalTime > 0) {
            float searchingPercent = (stats.timeInSearching * 100.0) / totalTime;
            float monitoringPercent = (stats.timeInMonitoring * 100.0) / totalTime;
            float verifyingPercent = (stats.timeInVerifying * 100.0) / totalTime;
            float successRate = (stats.successfulDetections * 100.0) / max(stats.totalScans, 1UL);
            float gracePeriodSuccessRate = stats.gracePeriodActivations > 0 ?
                                         (stats.gracePeriodSuccesses * 100.0) / stats.gracePeriodActivations : 0;

            DEBUG_PRINTLN("📊 === BLE SCANNER STATS (WITH GRACE PERIOD) ===");
            DEBUG_PRINTF("   Total Scans: %lu | Success Rate: %.1f%%\n",
                        stats.totalScans, successRate);
            DEBUG_PRINTF("   Grace Periods: %lu activated | %.1f%% successful reconnections\n",
                        stats.gracePeriodActivations, gracePeriodSuccessRate);
            DEBUG_PRINTF("   Time Distribution - Searching: %.1f%% | Monitoring: %.1f%% | Verifying: %.1f%%\n",
                        searchingPercent, monitoringPercent, verifyingPercent);
            DEBUG_PRINTF("   Current Mode: %s | Interval: %lums\n",
                        getModeString().c_str(), getCurrentScanInterval());
        }
    }

public:
    void init(BooleanPresenceDetector* detector) {
        presenceDetectorPtr = detector;
        currentMode = SEARCHING;
        lastScanTime = 0;
        modeChangeTime = millis();
        statsReportTime = millis();
        stats.lastModeStart = millis();

        DEBUG_PRINTLN("🔍 Adaptive BLE Scanner with Grace Period initialized");
        DEBUG_PRINTF("   Searching Mode: %dms interval, %ds duration\n",
                    BLE_SCAN_INTERVAL_SEARCHING, BLE_SCAN_DURATION_FULL);
        DEBUG_PRINTF("   Monitoring Mode: %dms interval, %ds duration\n",
                    BLE_SCAN_INTERVAL_MONITORING, BLE_SCAN_DURATION_QUICK);
        DEBUG_PRINTF("   Grace Period: %ds with %dms reconnect attempts\n",
                    BLE_GRACE_PERIOD_MS / 1000, BLE_RECONNECT_ATTEMPT_INTERVAL);
    }

    void update() {
        if (!presenceDetectorPtr) return;  // Safety check

        unsigned long now = millis();
        unsigned long interval = getCurrentScanInterval();

        // Check if it's time to scan
        if (now - lastScanTime < interval) return;

        // Update stats before scanning
        updateStats(now);

        // Perform adaptive scan
        bool beaconFound = performScan();
        lastScanTime = now;
        stats.totalScans++;

        if (beaconFound) {
            stats.successfulDetections++;
            consecutiveDetections++;
            consecutiveMisses = 0;
        } else {
            consecutiveMisses++;
            consecutiveDetections = 0;
        }

        // Smart mode switching (enhanced for grace period)
        updateScanMode(beaconFound, now);

        // Send to presence detector (this handles grace period logic)
        presenceDetectorPtr->checkBeacon(beaconFound);

        // Debug info (show grace period status)
        if (stats.totalScans % 10 == 0 || beaconFound || presenceDetectorPtr->isInGracePeriod()) {
            String gracePeriodInfo = "";
            if (presenceDetectorPtr->isInGracePeriod()) {
                unsigned long remaining = presenceDetectorPtr->getGracePeriodRemaining() / 1000;
                gracePeriodInfo = " | GRACE: " + String(remaining) + "s";
            }

            DEBUG_PRINTF("🔍 BLE Scan #%lu: %s | Mode: %s%s | Next: %lums\n",
                        stats.totalScans,
                        beaconFound ? "✅ FOUND" : "❌ MISS",
                        getModeString().c_str(),
                        gracePeriodInfo.c_str(),
                        interval);
        }
    }

    // Get current scanning statistics
    String getStatsString() {
        float efficiency = 0;
        unsigned long totalActiveTime = stats.timeInSearching + stats.timeInMonitoring;
        if (totalActiveTime > 0) {
            efficiency = (stats.timeInMonitoring * 100.0) / totalActiveTime;
        }

        String modeStr = getModeString().substring(0, 3);
        if (presenceDetectorPtr && presenceDetectorPtr->isInGracePeriod()) {
            modeStr = "GRC"; // Grace period indicator
        }

        return modeStr + ":" + String(efficiency, 0) + "%";
    }

private:
    bool performScan() {
        int duration = getCurrentScanDuration();

        // Add error handling for BLE scan
        BLEScanResults* results = nullptr;
        bool beaconDetected = false;
        int bestRSSI = -999;

        try {
            results = pBLEScan->start(duration, false);

            if (results && results->getCount() > 0) {
                for (int i = 0; i < results->getCount(); i++) {
                    BLEAdvertisedDevice device = results->getDevice(i);
                    if (isFacultyBeacon(device)) {
                        beaconDetected = true;
                        bestRSSI = device.getRSSI();

                        // Log RSSI occasionally for signal strength monitoring
                        if (stats.totalScans % 20 == 0) {
                            DEBUG_PRINTF("📶 Beacon RSSI: %d dBm\n", bestRSSI);
                        }
                        break;
                    }
                }
            }

            pBLEScan->clearResults();

        } catch (...) {
            DEBUG_PRINTLN("⚠️ BLE scan error - continuing");
            beaconDetected = false;
        }

        return beaconDetected;
    }

    void updateScanMode(bool beaconFound, unsigned long now) {
        ScanMode newMode = currentMode;

        switch(currentMode) {
            case SEARCHING:
                // Switch to verification after consistent detections
                if (consecutiveDetections >= 2) {
                    newMode = VERIFYING;
                    DEBUG_PRINTLN("📡 BLE Mode: SEARCHING -> VERIFYING (beacon detected)");
                }
                break;

            case MONITORING:
                // Switch to verification if beacon goes missing
                if (consecutiveMisses >= 2) {
                    newMode = VERIFYING;
                    DEBUG_PRINTLN("📡 BLE Mode: MONITORING -> VERIFYING (beacon lost)");
                }
                break;

            case VERIFYING:
                // Stay in verification for minimum time, then decide
                if (now - modeChangeTime > PRESENCE_CONFIRM_TIME) {
                    if (consecutiveDetections > consecutiveMisses) {
                        newMode = MONITORING;
                        DEBUG_PRINTLN("📡 BLE Mode: VERIFYING -> MONITORING (presence confirmed)");
                    } else {
                        newMode = SEARCHING;
                        DEBUG_PRINTLN("📡 BLE Mode: VERIFYING -> SEARCHING (absence confirmed)");
                    }
                }
                break;
        }

        // Execute mode change
        if (newMode != currentMode) {
            // Update stats for old mode
            updateStats(now);

            // Change mode
            currentMode = newMode;
            modeChangeTime = now;
            consecutiveDetections = 0;
            consecutiveMisses = 0;

            DEBUG_PRINTF("🔄 New scan interval: %lums, duration: %ds\n",
                        getCurrentScanInterval(), getCurrentScanDuration());
        }
    }

    String getModeString() {
        switch(currentMode) {
            case SEARCHING: return "SEARCHING";
            case MONITORING: return "MONITORING";
            case VERIFYING: return "VERIFYING";
            default: return "UNKNOWN";
        }
    }
};

// ================================
// GLOBAL INSTANCES (CORRECT ORDER)
// ================================
BooleanPresenceDetector presenceDetector;
ButtonHandler buttons(BUTTON_A_PIN, BUTTON_B_PIN);
AdaptiveBLEScanner adaptiveScanner;

// ================================
// BLE CALLBACK CLASS
// ================================
class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice advertisedDevice) {}
};

// ================================
// SIMPLE UI HELPER FUNCTIONS (UNCHANGED)
// ================================
void drawSimpleCard(int x, int y, int w, int h, uint16_t color) {
  tft.fillRect(x, y, w, h, color);
  tft.drawRect(x, y, w, h, COLOR_ACCENT);
}

void drawStatusIndicator(int x, int y, bool available) {
  int radius = 12;
  if (available) {
    if (animationState) {
      tft.fillCircle(x, y, radius + 2, COLOR_SUCCESS);
      tft.fillCircle(x, y, radius, COLOR_ACCENT);
    } else {
      tft.fillCircle(x, y, radius, COLOR_SUCCESS);
    }
    tft.fillCircle(x, y, radius - 4, COLOR_WHITE);
    tft.fillCircle(x, y, 3, COLOR_SUCCESS);
  } else {
    tft.fillCircle(x, y, radius, COLOR_ERROR);
    tft.fillCircle(x, y, radius - 4, COLOR_WHITE);
    tft.fillCircle(x, y, 3, COLOR_ERROR);
  }
}

int getCenterX(String text, int textSize) {
  int charWidth = 6 * textSize;
  int textWidth = text.length() * charWidth;
  return (SCREEN_WIDTH - textWidth) / 2;
}

// ================================
// MESSAGE DISPLAY WITH ENHANCED CONSULTATION REQUEST HANDLING
// ================================
void displayIncomingMessage(String message) {
  currentMessage = message;
  messageDisplayed = true;
  messageDisplayStart = millis();

  // Clear main area
  tft.fillRect(0, MAIN_AREA_Y, SCREEN_WIDTH, MAIN_AREA_HEIGHT, COLOR_PANEL);

  // Enhanced message header with consultation ID - MADE SMALLER (20px instead of 30px)
  drawSimpleCard(10, MAIN_AREA_Y + 5, SCREEN_WIDTH - 20, 20, COLOR_ACCENT);

  int headerX = getCenterX("CONSULTATION REQUEST", 1); // Reduced text size from 2 to 1
  tft.setCursor(headerX, MAIN_AREA_Y + 10); // Adjusted Y position for smaller banner
  tft.setTextColor(COLOR_BACKGROUND);
  tft.setTextSize(1); // Reduced from size 2 to 1 to fit in smaller banner
  tft.print("CONSULTATION REQUEST");

  // Display consultation ID if available - moved up since banner is smaller
  if (!g_receivedConsultationId.isEmpty()) {
    tft.setCursor(15, MAIN_AREA_Y + 18); // Moved up from 25 to 18
    tft.setTextColor(COLOR_BACKGROUND);
    tft.setTextSize(1);
    tft.print("ID: " + g_receivedConsultationId);
  }

  // Message content area with better formatting - starts earlier due to smaller banner
  tft.setCursor(15, MAIN_AREA_Y + 32); // Moved up from 45 to 32 (saved 13px from smaller banner)
  tft.setTextColor(COLOR_TEXT);
  tft.setTextSize(2); // INCREASED from size 1 to 2 for larger, more readable text

  int lineHeight = 18; // INCREASED from 10 to 18 for larger text spacing
  int maxCharsPerLine = 25; // REDUCED from 38 to 25 due to larger font size
  int currentY = MAIN_AREA_Y + 32; // Moved up from 45 to 32
  int maxLines = 8; // INCREASED from 6 to 8 lines - using space freed from removing on-screen buttons

  // Parse and display student info if available
  int fromIndex = message.indexOf("From:");
  int sidIndex = message.indexOf("(SID:");
  int messageIndex = message.indexOf("): ");
  
  if (fromIndex != -1 && sidIndex != -1 && messageIndex != -1) {
    // Extract student name
    String studentName = message.substring(fromIndex + 5, sidIndex);
    studentName.trim();
    
    // Display student info with LARGER font
    tft.setCursor(15, currentY);
    tft.setTextColor(COLOR_ACCENT);
    tft.setTextSize(2); // INCREASED from size 1 to 2
    tft.print("Student: ");
    tft.setTextColor(COLOR_BLACK); // Changed from COLOR_TEXT to COLOR_BLACK for better readability
    tft.print(studentName);
    currentY += lineHeight + 4; // INCREASED spacing
    
    // Extract and display the actual consultation message
    String consultationMsg = message.substring(messageIndex + 3);
    consultationMsg.trim();
    
    tft.setCursor(15, currentY);
    tft.setTextColor(COLOR_ACCENT);
    tft.setTextSize(2); // INCREASED from size 1 to 2
    tft.print("Request:");
    currentY += lineHeight;
    
    // Display consultation message with word wrapping - LARGER FONT AND MORE LINES
    int linesUsed = 0;
    for (int i = 0; i < consultationMsg.length() && linesUsed < maxLines - 2; i += maxCharsPerLine) {
      String line = consultationMsg.substring(i, min(i + maxCharsPerLine, (int)consultationMsg.length()));
      tft.setCursor(15, currentY);
      tft.setTextColor(COLOR_BLACK); // Changed from COLOR_TEXT to COLOR_BLACK for better readability
      tft.setTextSize(2); // INCREASED from size 1 to 2 for much larger, easier to read text
      tft.print(line);
      currentY += lineHeight;
      linesUsed++;
    }
  } else {
    // Fallback: display raw message with word wrapping - LARGER FONT AND MORE LINES
    int linesUsed = 0;
    for (int i = 0; i < message.length() && linesUsed < maxLines; i += maxCharsPerLine) {
      String line = message.substring(i, min(i + maxCharsPerLine, (int)message.length()));
      tft.setCursor(15, currentY);
      tft.setTextColor(COLOR_BLACK); // Changed from COLOR_TEXT to COLOR_BLACK for better readability
      tft.setTextSize(2); // INCREASED from size 1 to 2 for much larger, easier to read text
      tft.print(line);
      currentY += lineHeight;
      linesUsed++;
    }
  }

  // REMOVED ON-SCREEN BUTTONS - Physical buttons only!
  // Physical button instructions at bottom of display - NO VISUAL BUTTONS
  tft.setCursor(15, MAIN_AREA_Y + 120); // Position near bottom of main area
  tft.setTextColor(COLOR_ACCENT);
  tft.setTextSize(1);
  tft.print("Use PHYSICAL buttons: BLUE=Accept | RED=Busy");

  // REMOVED timeout indicator - messages persist until button press
  // No more "Auto-clear in 30s" message

  DEBUG_PRINTF("📱 Enhanced consultation request displayed (NO AUTO-EXPIRY). ID: %s\n", g_receivedConsultationId.c_str());
}

// ================================
// BUTTON RESPONSE FUNCTIONS (UNCHANGED)
// ================================
void handleAcknowledgeButton() {
  DEBUG_PRINTLN("🔵 handleAcknowledgeButton() called!");
  
  // Debug all the conditions that could cause early return
  DEBUG_PRINTF("   messageDisplayed: %s\n", messageDisplayed ? "TRUE" : "FALSE");
  DEBUG_PRINTF("   currentMessage.isEmpty(): %s\n", currentMessage.isEmpty() ? "TRUE" : "FALSE");
  DEBUG_PRINTF("   currentMessage content: '%s'\n", currentMessage.c_str());
  
  if (!messageDisplayed || currentMessage.isEmpty()) {
    DEBUG_PRINTLN("❌ EARLY RETURN: No message displayed or message is empty");
    return;
  }

  // Check if faculty is present before allowing response
  bool facultyPresent = presenceDetector.getPresence();
  DEBUG_PRINTF("   Faculty present: %s\n", facultyPresent ? "TRUE" : "FALSE");
  
  if (!facultyPresent) {
    DEBUG_PRINTLN("❌ Cannot send ACKNOWLEDGE: Faculty not present");
    showResponseConfirmation("NOT PRESENT!", COLOR_ERROR);
    return;
  }

  DEBUG_PRINTF("   g_receivedConsultationId: '%s'\n", g_receivedConsultationId.c_str());
  DEBUG_PRINTF("   g_receivedConsultationId.isEmpty(): %s\n", g_receivedConsultationId.isEmpty() ? "TRUE" : "FALSE");
  
  if (g_receivedConsultationId.isEmpty()) {
    DEBUG_PRINTLN("❌ Cannot send ACKNOWLEDGE: Missing Consultation ID (CID).");
    showResponseConfirmation("NO CID!", COLOR_ERROR);
    return;
  }

  DEBUG_PRINTLN("📤 Sending ACKNOWLEDGE response to central terminal");
  DEBUG_PRINTF("   MQTT connected: %s\n", mqttClient.connected() ? "TRUE" : "FALSE");
  DEBUG_PRINTF("   WiFi connected: %s\n", wifiConnected ? "TRUE" : "FALSE");

  // Create acknowledge response with enhanced data
  String response = "{";
  response += "\"faculty_id\":" + String(FACULTY_ID) + ",";
  response += "\"faculty_name\":\"" + String(FACULTY_NAME) + "\",";
  response += "\"response_type\":\"ACKNOWLEDGE\",";
  response += "\"message_id\":\"" + g_receivedConsultationId + "\",";
  // ✅ REMOVED: original_message field to reduce payload size
  response += "\"timestamp\":\"" + String(millis()) + "\",";
  response += "\"faculty_present\":true,";
  response += "\"response_method\":\"physical_button\",";
  response += "\"status\":\"Professor acknowledges the request and will respond accordingly\"";
  response += "}";

  DEBUG_PRINTF("📝 Response JSON (%d bytes): %s\n", response.length(), response.c_str());
  DEBUG_PRINTF("📡 Publishing to topic: %s\n", MQTT_TOPIC_RESPONSES);
  
  // ✅ CRITICAL CHECK: Verify payload size before publishing
  if (response.length() > MQTT_MAX_PACKET_SIZE - 50) { // Leave 50 bytes margin for MQTT headers
    DEBUG_PRINTF("⚠️ WARNING: Payload size %d bytes may exceed MQTT limit!\n", response.length());
  }

  // Publish response with offline queuing support
  bool success = publishWithQueue(MQTT_TOPIC_RESPONSES, response.c_str(), true);
  DEBUG_PRINTF("   publishWithQueue result: %s\n", success ? "SUCCESS" : "FAILED");
  
  if (success) {
    if (mqttClient.connected()) {
      DEBUG_PRINTLN("✅ ACKNOWLEDGE response sent successfully");
      DEBUG_PRINTF("📡 Response sent to central system via topic: %s\n", MQTT_TOPIC_RESPONSES);
      showResponseConfirmation("ACKNOWLEDGED", COLOR_BLUE);
    } else {
      DEBUG_PRINTLN("📥 ACKNOWLEDGE response queued (offline)");
      DEBUG_PRINTF("📥 Response queued for central system, queue size: %d\n", queueCount);
      showResponseConfirmation("QUEUED", COLOR_WARNING);
    }
  } else {
    DEBUG_PRINTLN("❌ Failed to send/queue ACKNOWLEDGE response");
    DEBUG_PRINTF("❌ Central system communication failed for topic: %s\n", MQTT_TOPIC_RESPONSES);
    showResponseConfirmation("FAILED", COLOR_ERROR);
  }

  // Clear message
  DEBUG_PRINTLN("🧹 Calling clearCurrentMessage()");
  clearCurrentMessage();
}

void handleBusyButton() {
  DEBUG_PRINTLN("🔴 handleBusyButton() called!");
  
  // Debug all the conditions that could cause early return
  DEBUG_PRINTF("   messageDisplayed: %s\n", messageDisplayed ? "TRUE" : "FALSE");
  DEBUG_PRINTF("   currentMessage.isEmpty(): %s\n", currentMessage.isEmpty() ? "TRUE" : "FALSE");
  DEBUG_PRINTF("   currentMessage content: '%s'\n", currentMessage.c_str());
  
  if (!messageDisplayed || currentMessage.isEmpty()) {
    DEBUG_PRINTLN("❌ EARLY RETURN: No message displayed or message is empty");
    return;
  }

  // Check if faculty is present before allowing response
  bool facultyPresent = presenceDetector.getPresence();
  DEBUG_PRINTF("   Faculty present: %s\n", facultyPresent ? "TRUE" : "FALSE");
  
  if (!facultyPresent) {
    DEBUG_PRINTLN("❌ Cannot send BUSY: Faculty not present");
    showResponseConfirmation("NOT PRESENT!", COLOR_ERROR);
    return;
  }

  DEBUG_PRINTF("   g_receivedConsultationId: '%s'\n", g_receivedConsultationId.c_str());
  DEBUG_PRINTF("   g_receivedConsultationId.isEmpty(): %s\n", g_receivedConsultationId.isEmpty() ? "TRUE" : "FALSE");
  
  if (g_receivedConsultationId.isEmpty()) {
    DEBUG_PRINTLN("❌ Cannot send BUSY: Missing Consultation ID (CID).");
    showResponseConfirmation("NO CID!", COLOR_ERROR);
    return;
  }

  DEBUG_PRINTLN("📤 Sending BUSY response to central terminal");
  DEBUG_PRINTF("   MQTT connected: %s\n", mqttClient.connected() ? "TRUE" : "FALSE");
  DEBUG_PRINTF("   WiFi connected: %s\n", wifiConnected ? "TRUE" : "FALSE");

  // Create busy response with enhanced data
  String response = "{";
  response += "\"faculty_id\":" + String(FACULTY_ID) + ",";
  response += "\"faculty_name\":\"" + String(FACULTY_NAME) + "\",";
  response += "\"response_type\":\"BUSY\",";
  response += "\"message_id\":\"" + g_receivedConsultationId + "\",";
  // ✅ REMOVED: original_message field to reduce payload size
  response += "\"timestamp\":\"" + String(millis()) + "\",";
  response += "\"faculty_present\":true,";
  response += "\"response_method\":\"physical_button\",";
  response += "\"status\":\"Professor is currently busy and cannot cater to this request\"";
  response += "}";

  DEBUG_PRINTF("📝 Response JSON (%d bytes): %s\n", response.length(), response.c_str());
  DEBUG_PRINTF("📡 Publishing to topic: %s\n", MQTT_TOPIC_RESPONSES);
  
  // ✅ CRITICAL CHECK: Verify payload size before publishing
  if (response.length() > MQTT_MAX_PACKET_SIZE - 50) { // Leave 50 bytes margin for MQTT headers
    DEBUG_PRINTF("⚠️ WARNING: Payload size %d bytes may exceed MQTT limit!\n", response.length());
  }

  // Publish response with offline queuing support
  bool success = publishWithQueue(MQTT_TOPIC_RESPONSES, response.c_str(), true);
  DEBUG_PRINTF("   publishWithQueue result: %s\n", success ? "SUCCESS" : "FAILED");
  
  if (success) {
    if (mqttClient.connected()) {
      DEBUG_PRINTLN("✅ BUSY response sent successfully");
      DEBUG_PRINTF("📡 Response sent to central system via topic: %s\n", MQTT_TOPIC_RESPONSES);
      showResponseConfirmation("MARKED BUSY", COLOR_ERROR);
    } else {
      DEBUG_PRINTLN("📥 BUSY response queued (offline)");
      DEBUG_PRINTF("📥 Response queued for central system, queue size: %d\n", queueCount);
      showResponseConfirmation("QUEUED", COLOR_WARNING);
    }
  } else {
    DEBUG_PRINTLN("❌ Failed to send/queue BUSY response");
    DEBUG_PRINTF("❌ Central system communication failed for topic: %s\n", MQTT_TOPIC_RESPONSES);
    showResponseConfirmation("FAILED", COLOR_ERROR);
  }

  // Clear message
  DEBUG_PRINTLN("🧹 Calling clearCurrentMessage()");
  clearCurrentMessage();
}

void showResponseConfirmation(String confirmText, uint16_t color) {
  // Clear main area
  tft.fillRect(0, MAIN_AREA_Y, SCREEN_WIDTH, MAIN_AREA_HEIGHT, COLOR_WHITE);

  // Show confirmation card
  drawSimpleCard(20, STATUS_CENTER_Y - 30, 280, 60, color);

  int confirmX = getCenterX(confirmText, 2);
  tft.setCursor(confirmX, STATUS_CENTER_Y - 15);
  tft.setTextSize(2);
  tft.setTextColor(COLOR_WHITE);
  tft.print(confirmText);

  tft.setCursor(getCenterX("Response Sent", 1), STATUS_CENTER_Y + 10);
  tft.setTextSize(1);
  tft.setTextColor(COLOR_WHITE);
  tft.print("Response Sent");

  delay(CONFIRMATION_DISPLAY_TIME);
}

// ================================
// CANCELLATION NOTIFICATION DISPLAY
// ================================
void showCancellationNotification() {
  tft.fillRect(0, MAIN_AREA_Y, SCREEN_WIDTH, MAIN_AREA_HEIGHT, COLOR_PANEL); // Clear main area
  drawSimpleCard(20, STATUS_CENTER_Y - 20, SCREEN_WIDTH - 40, 40, COLOR_WARNING); // Use a warning color

  String cancelMsg = "Consultation Cancelled";
  int msgX = getCenterX(cancelMsg, 2);
  tft.setCursor(msgX, STATUS_CENTER_Y - 7);
  tft.setTextSize(2);
  tft.setTextColor(COLOR_WHITE);
  tft.print(cancelMsg);

  DEBUG_PRINTLN("📺 Displayed cancellation notification.");
  delay(CANCEL_NOTIFICATION_DISPLAY_TIME);
  updateMainDisplay(); // Go back to the default display
}

void clearCurrentMessage() {
  DEBUG_PRINTLN("📱 Consultation message manually dismissed via physical button");
  currentMessage = "";
  messageDisplayed = false;
  messageDisplayStart = 0;
  g_receivedConsultationId = "";
  updateMainDisplay(); // Return to normal display
}

// ================================
// WIFI FUNCTIONS (UNCHANGED)
// ================================
void setupWiFi() {
  DEBUG_PRINT("Connecting to WiFi: ");
  DEBUG_PRINTLN(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long startTime = millis();
  while (WiFi.status() != WL_CONNECTED &&
         (millis() - startTime) < WIFI_CONNECT_TIMEOUT) {
    delay(500);
    DEBUG_PRINT(".");
    updateSystemStatus();
  }

  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    DEBUG_PRINTLN(" connected!");
    DEBUG_PRINT("IP address: ");
    DEBUG_PRINTLN(WiFi.localIP());
    setupTimeWithRetry();
  } else {
    wifiConnected = false;
    DEBUG_PRINTLN(" failed!");
  }
  updateSystemStatus();
}

void checkWiFiConnection() {
  if (WiFi.status() != WL_CONNECTED) {
    if (wifiConnected) {
      wifiConnected = false;
      timeInitialized = false;
      updateSystemStatus();
    }

    static unsigned long lastReconnectAttempt = 0;
    if (millis() - lastReconnectAttempt > WIFI_RECONNECT_INTERVAL) {
      WiFi.reconnect();
      lastReconnectAttempt = millis();
    }
  } else if (!wifiConnected) {
    wifiConnected = true;
    setupTimeWithRetry();
    updateSystemStatus();
  }
}

// ================================
// ENHANCED NTP TIME FUNCTIONS
// ================================
void setupTimeWithRetry() {
  DEBUG_PRINTLN("Setting up enhanced NTP time synchronization...");
  ntpSyncInProgress = true;
  ntpRetryCount = 0;
  ntpSyncStatus = "SYNCING";

  // Try multiple NTP servers for better reliability
  configTime(TIME_ZONE_OFFSET * 3600, 0, NTP_SERVER_PRIMARY, NTP_SERVER_SECONDARY, NTP_SERVER_TERTIARY);

  unsigned long startTime = millis();
  struct tm timeinfo;

  while (!getLocalTime(&timeinfo) && (millis() - startTime) < NTP_SYNC_TIMEOUT) {
    delay(1000);
    DEBUG_PRINT(".");
    updateSystemStatus(); // Update display during sync
  }

  if (getLocalTime(&timeinfo)) {
    timeInitialized = true;
    ntpSyncInProgress = false;
    ntpSyncStatus = "SYNCED";
    ntpRetryCount = 0;
    DEBUG_PRINTLN(" Time synced successfully!");
    DEBUG_PRINTF("Current time: %04d-%02d-%02d %02d:%02d:%02d\n",
                timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
                timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec);
    updateTimeAndDate();
    updateSystemStatus();

    // Publish NTP sync status to central system
    publishNtpSyncStatus(true);
  } else {
    timeInitialized = false;
    ntpSyncInProgress = false;
    ntpSyncStatus = "FAILED";
    ntpRetryCount++;
    DEBUG_PRINTLN(" Time sync failed!");

    // Publish NTP sync failure to central system
    publishNtpSyncStatus(false);
  }
}

void updateTimeAndDate() {
  if (!wifiConnected) {
    if (lastDisplayedTime != "OFFLINE") {
      lastDisplayedTime = "OFFLINE";
      lastDisplayedDate = "NO WIFI";

      tft.fillRect(TIME_X, TIME_Y, 120, 15, COLOR_PANEL);
      tft.setCursor(TIME_X, TIME_Y);
      tft.setTextColor(COLOR_ERROR);
      tft.setTextSize(1);
      tft.print("TIME: OFFLINE");

      tft.fillRect(DATE_X - 60, DATE_Y, 70, 15, COLOR_PANEL);
      tft.setCursor(DATE_X - 60, DATE_Y);
      tft.setTextColor(COLOR_ERROR);
      tft.setTextSize(1);
      tft.print("NO WIFI");
    }
    return;
  }

  struct tm timeinfo;
  if (getLocalTime(&timeinfo) && timeInitialized) {
    char timeStr[12];
    strftime(timeStr, sizeof(timeStr), "%H:%M:%S", &timeinfo);

    char dateStr[15];
    strftime(dateStr, sizeof(dateStr), "%b %d, %Y", &timeinfo);

    String currentTimeStr = String(timeStr);
    String currentDateStr = String(dateStr);

    if (currentTimeStr != lastDisplayedTime) {
      lastDisplayedTime = currentTimeStr;

      tft.fillRect(TIME_X, TIME_Y, 120, 15, COLOR_PANEL);
      tft.setCursor(TIME_X, TIME_Y);
      tft.setTextColor(COLOR_ACCENT);
      tft.setTextSize(1);
      tft.print("TIME: ");
      tft.print(timeStr);
    }

    if (currentDateStr != lastDisplayedDate) {
      lastDisplayedDate = currentDateStr;

      tft.fillRect(DATE_X - 90, DATE_Y, 90, 15, COLOR_PANEL);
      tft.setCursor(DATE_X - 90, DATE_Y);
      tft.setTextColor(COLOR_ACCENT);
      tft.setTextSize(1);
      tft.print("DATE: ");
      tft.print(dateStr);
    }
  } else {
    if (lastDisplayedTime != "SYNCING") {
      lastDisplayedTime = "SYNCING";
      lastDisplayedDate = "SYNCING";

      tft.fillRect(TIME_X, TIME_Y, 120, 15, COLOR_PANEL);
      tft.setCursor(TIME_X, TIME_Y);
      tft.setTextColor(COLOR_WARNING);
      tft.setTextSize(1);
      tft.print("TIME: SYNCING...");

      tft.fillRect(DATE_X - 90, DATE_Y, 90, 15, COLOR_PANEL);
      tft.setCursor(DATE_X - 90, DATE_Y);
      tft.setTextColor(COLOR_WARNING);
      tft.setTextSize(1);
      tft.print("WAIT...");
    }
  }
}

void checkPeriodicTimeSync() {
  static unsigned long lastNTPSync = 0;
  unsigned long now = millis();

  // Periodic sync for already synchronized time
  if (timeInitialized && wifiConnected && (now - lastNTPSync > NTP_UPDATE_INTERVAL)) {
    DEBUG_PRINTLN("Performing periodic NTP sync...");
    ntpSyncInProgress = true;
    ntpSyncStatus = "SYNCING";

    configTime(TIME_ZONE_OFFSET * 3600, 0, NTP_SERVER_PRIMARY, NTP_SERVER_SECONDARY);

    // Quick check for sync success
    delay(2000);
    struct tm timeinfo;
    if (getLocalTime(&timeinfo)) {
      ntpSyncStatus = "SYNCED";
      DEBUG_PRINTLN("Periodic NTP sync successful");
      publishNtpSyncStatus(true);
    } else {
      ntpSyncStatus = "FAILED";
      DEBUG_PRINTLN("Periodic NTP sync failed");
      publishNtpSyncStatus(false);
    }

    ntpSyncInProgress = false;
    lastNTPSync = now;
  }

  // Retry failed sync attempts
  if (!timeInitialized && wifiConnected && !ntpSyncInProgress &&
      (now - lastNtpSyncAttempt > NTP_RETRY_INTERVAL) &&
      ntpRetryCount < NTP_MAX_RETRIES) {
    DEBUG_PRINTF("Retrying NTP sync (attempt %d/%d)...\n", ntpRetryCount + 1, NTP_MAX_RETRIES);
    lastNtpSyncAttempt = now;
    setupTimeWithRetry();
  }
}

// ================================
// MQTT FUNCTIONS (UNCHANGED)
// ================================
void setupMQTT() {
  // ✅ ADD THIS LINE: Set buffer size BEFORE setting server
  mqttClient.setBufferSize(MQTT_MAX_PACKET_SIZE);
  
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(onMqttMessage);
  mqttClient.setKeepAlive(MQTT_KEEPALIVE);
  
  // ✅ ADD DEBUG: Verify buffer size was set
  DEBUG_PRINTF("📦 MQTT Buffer Size set to: %d bytes\n", MQTT_MAX_PACKET_SIZE);
}

void connectMQTT() {
  if (millis() - lastMqttReconnect < 5000) return;
  lastMqttReconnect = millis();

  DEBUG_PRINT("MQTT connecting...");

  if (mqttClient.connect(MQTT_CLIENT_ID, MQTT_USERNAME, MQTT_PASSWORD)) {
    mqttConnected = true;
    DEBUG_PRINTLN(" connected!");
    mqttClient.subscribe(MQTT_TOPIC_MESSAGES, MQTT_QOS);
    publishPresenceUpdate();
    updateSystemStatus();
  } else {
    mqttConnected = false;
    DEBUG_PRINTLN(" failed!");
    updateSystemStatus();
  }
}

void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  DEBUG_PRINTF("📨 onMqttMessage called - Topic: %s, Length: %d\n", topic, length);
  
  if (length == 0) {
    DEBUG_PRINTLN("⚠️ Empty MQTT message received. Ignoring.");
    return;
  }

  // Bounds checking for security - ensure space for null terminator if MAX_MESSAGE_LENGTH is exact buffer size
  unsigned int procesLength = length;
  if (procesLength >= MAX_MESSAGE_LENGTH) { 
    DEBUG_PRINTF("⚠️ Message too long (%u bytes), truncating to %d\n", procesLength, MAX_MESSAGE_LENGTH - 1);
    procesLength = MAX_MESSAGE_LENGTH - 1;
  }

  // Create a null-terminated buffer for payload processing (safer for string functions and JSON parsing)
  char messageBuffer[procesLength + 1];
  memcpy(messageBuffer, payload, procesLength);
  messageBuffer[procesLength] = '\0'; // Null-terminate

  DEBUG_PRINTF("📨 Message content (%u bytes): %s\n", procesLength, messageBuffer);

  // Attempt to parse JSON
  const size_t jsonCapacity = JSON_OBJECT_SIZE(3) + 200; // Enough for type, id, and message fields + values
  DynamicJsonDocument doc(jsonCapacity);
  DeserializationError error = deserializeJson(doc, messageBuffer, procesLength); // Use null-terminated messageBuffer

  bool handledAsJson = false;

  if (!error) { // JSON parsing was successful
    const char* type = doc["type"];
    DEBUG_PRINTF("JSON Type: %s\n", type ? type : "null");

    if (type && strcmp(type, "consultation_cancellation") == 0) {
      const char* consultationId_json = doc["consultation_id"];
      if (consultationId_json) {
        DEBUG_PRINTF("✅ Received JSON cancellation for CID: %s\n", consultationId_json);
        bool facultyPresent = presenceDetector.getPresence(); // Check presence before altering display
        if (facultyPresent) {
            if (g_receivedConsultationId.length() > 0 && g_receivedConsultationId.equals(consultationId_json)) {
                DEBUG_PRINTLN("⚡️ Matching CID. Clearing display and showing cancellation.");
                clearCurrentMessage(); // Clears g_receivedConsultationId too
                showCancellationNotification();
            } else {
                DEBUG_PRINTF("ℹ️ Cancellation for CID %s does not match current display CID %s. Ignoring visual update.\n",
                            consultationId_json, g_receivedConsultationId.c_str());
            }
        } else {
             DEBUG_PRINTLN("ℹ️ Faculty not present. Cancellation for CID %s received but not updating display.");
        }
      } else {
        DEBUG_PRINTLN("⚠️ JSON cancellation message missing 'consultation_id'.");
      }
      handledAsJson = true; // Mark as handled, even if not acted upon due to non-matching CID or faculty away
    }
    // Future: Handle other JSON message types here, e.g.:
    // else if (type && strcmp(type, "new_consultation_request_json") == 0) {
    //   const char* consultationId_json = doc["consultation_id"];
    //   const char* displayMessage_json = doc["display_message"]; // Assuming central system sends pre-formatted string
    //   if (consultationId_json && displayMessage_json) {
    //     g_receivedConsultationId = String(consultationId_json);
    //     bool facultyPresent = presenceDetector.getPresence();
    //     if (facultyPresent) {
    //       lastReceivedMessage = String(displayMessage_json);
    //       displayIncomingMessage(String(displayMessage_json));
    //     } else { DEBUG_PRINTLN("📭 New JSON consultation request ignored - Professor is AWAY"); }
    //   } else { DEBUG_PRINTLN("⚠️ New JSON consultation request missing 'consultation_id' or 'display_message'."); }
    //   handledAsJson = true;
    // }

  } else {
    DEBUG_PRINTF("⚠️ JSON parsing failed: %s. Assuming plain text message.\n", error.c_str());
  }

  // If not handled as any known JSON type, proceed with existing logic for new (string-based) consultation requests
  if (!handledAsJson) {
    DEBUG_PRINTLN("📨 Message not a handled JSON type, processing as standard text message.");
    
    // Convert original payload to String for legacy processing (using procesLength for safety)
    String messageContent = "";
    messageContent.reserve(procesLength + 1);
    for (unsigned int i = 0; i < procesLength; i++) {
        messageContent += (char)payload[i]; // Use original payload here, up to procesLength
    }

    // --- EXISTING STRING PARSING FOR CID (from original code) ---
    DEBUG_PRINTLN("🔍 Starting CID parsing from plain text...");
    int cidStartIndex = messageContent.indexOf("CID:");
    DEBUG_PRINTF("   CID: search index = %d\n", cidStartIndex);
    
    int cidEndIndex = -1;
    String parsedConsultationId = "";

    if (cidStartIndex != -1) {
      cidStartIndex += 4; // Length of "CID:"
      DEBUG_PRINTF("   CID: start position = %d\n", cidStartIndex);
      
      cidEndIndex = messageContent.indexOf(" ", cidStartIndex); 
      DEBUG_PRINTF("   CID: end position = %d\n", cidEndIndex);
      
      if (cidEndIndex != -1) {
        parsedConsultationId = messageContent.substring(cidStartIndex, cidEndIndex);
      } else {
        DEBUG_PRINTLN("   CID: No space found after CID, taking rest of string");
        parsedConsultationId = messageContent.substring(cidStartIndex); 
      }
      // IMPORTANT: Only set g_receivedConsultationId if this is a new message intended for display
      // Avoid overwriting g_receivedConsultationId if a JSON message was already processed (e.g. a quick cancellation)
      // This path is for *new* display messages.
      g_receivedConsultationId = parsedConsultationId; // Set global CID for new plain text message
      DEBUG_PRINTF("🔑 Parsed Consultation ID (CID) from plain text: '%s'\n", g_receivedConsultationId.c_str());
    } else {
      DEBUG_PRINTLN("⚠️ Consultation ID (CID:) not found in plain text message.");
      // If no CID, this message likely won't be actionable with buttons. Displaying it might be confusing.
      // Consider if g_receivedConsultationId should be cleared or if message should be ignored if CID is vital.
      // For now, it will be displayed without a usable CID for responses.
    }
    
    // --- EXISTING DISPLAY LOGIC (from original code) ---
    bool facultyPresent = presenceDetector.getPresence();
    DEBUG_PRINTF("👤 Faculty presence check for plain text message: %s\n", facultyPresent ? "PRESENT" : "AWAY");
    
    if (facultyPresent) {
      lastReceivedMessage = messageContent; 
      DEBUG_PRINTF("💾 Stored plain text message in lastReceivedMessage: '%s'\n", lastReceivedMessage.c_str());
      DEBUG_PRINTLN("📱 Calling displayIncomingMessage() for plain text message.");
      displayIncomingMessage(messageContent); 
      DEBUG_PRINTF("🎯 Message display state after plain text - messageDisplayed: %s\n", messageDisplayed ? "TRUE" : "FALSE");
    } else {
      DEBUG_PRINTLN("📭 Plain text message ignored - Professor is AWAY");
    }
  }
}

void publishPresenceUpdate() {
  String payload = "{";
  payload += "\"faculty_id\":" + String(FACULTY_ID) + ",";
  payload += "\"faculty_name\":\"" + String(FACULTY_NAME) + "\",";
  payload += "\"present\":" + String(presenceDetector.getPresence() ? "true" : "false") + ",";
  payload += "\"status\":\"" + presenceDetector.getStatusString() + "\",";
  payload += "\"timestamp\":" + String(millis()) + ",";
  payload += "\"ntp_sync_status\":\"" + ntpSyncStatus + "\"";

  // Add grace period information for debugging
  if (presenceDetector.isInGracePeriod()) {
    payload += ",\"grace_period_remaining\":" + String(presenceDetector.getGracePeriodRemaining());
    payload += ",\"in_grace_period\":true";
  } else {
    payload += ",\"in_grace_period\":false";
  }

  // Add detailed status for central system
  payload += ",\"detailed_status\":\"" + presenceDetector.getDetailedStatus() + "\"";

  payload += "}";

  // Publish with offline queuing support
  bool success1 = publishWithQueue(MQTT_TOPIC_STATUS, payload.c_str(), false);
  bool success2 = publishWithQueue(MQTT_LEGACY_STATUS, payload.c_str(), false);

  if (success1 || success2) {
    if (mqttClient.connected()) {
      DEBUG_PRINTF("📡 Published presence update: %s\n", presenceDetector.getStatusString().c_str());
    } else {
      DEBUG_PRINTF("📥 Queued presence update: %s\n", presenceDetector.getStatusString().c_str());
    }
  } else {
    DEBUG_PRINTLN("❌ Failed to send/queue presence update");
  }
}

void publishNtpSyncStatus(bool success) {
  if (!mqttClient.connected()) return;

  String payload = "{";
  payload += "\"faculty_id\":" + String(FACULTY_ID) + ",";
  payload += "\"ntp_sync_success\":" + String(success ? "true" : "false") + ",";
  payload += "\"ntp_sync_status\":\"" + ntpSyncStatus + "\",";
  payload += "\"retry_count\":" + String(ntpRetryCount) + ",";
  payload += "\"timestamp\":" + String(millis());

  if (success && timeInitialized) {
    struct tm timeinfo;
    if (getLocalTime(&timeinfo)) {
      char timeStr[32];
      strftime(timeStr, sizeof(timeStr), "%Y-%m-%d %H:%M:%S", &timeinfo);
      payload += ",\"current_time\":\"" + String(timeStr) + "\"";
    }
  }

  payload += "}";

  mqttClient.publish(MQTT_TOPIC_HEARTBEAT, payload.c_str(), MQTT_QOS);
  DEBUG_PRINTF("📡 Published NTP sync status: %s\n", success ? "SUCCESS" : "FAILED");
}

void publishHeartbeat() {
  if (!mqttClient.connected()) return;

  String payload = "{";
  payload += "\"faculty_id\":" + String(FACULTY_ID) + ",";
  payload += "\"uptime\":" + String(millis()) + ",";
  payload += "\"free_heap\":" + String(ESP.getFreeHeap()) + ",";
  payload += "\"wifi_connected\":" + String(wifiConnected ? "true" : "false") + ",";
  payload += "\"time_initialized\":" + String(timeInitialized ? "true" : "false") + ",";
  payload += "\"ntp_sync_status\":\"" + ntpSyncStatus + "\",";
  payload += "\"presence_status\":\"" + presenceDetector.getStatusString() + "\"";
  payload += "}";

  mqttClient.publish(MQTT_TOPIC_HEARTBEAT, payload.c_str());
}

// ================================
// BLE FUNCTIONS (UNCHANGED)
// ================================
void setupBLE() {
  DEBUG_PRINTLN("Initializing BLE...");

  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan();
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setActiveScan(true);
  pBLEScan->setInterval(100);
  pBLEScan->setWindow(99);

  DEBUG_PRINTLN("BLE ready");
}

// ================================
// DISPLAY FUNCTIONS (UNCHANGED - Your existing display logic!)
// ================================
void setupDisplay() {
  tft.init(240, 320);
  tft.setRotation(3);
  tft.fillScreen(COLOR_WHITE);

  DEBUG_PRINTLN("Display initialized - With Grace Period BLE System");

  tft.fillScreen(COLOR_BACKGROUND);

  tft.setCursor(getCenterX("NU FACULTY", 3), 100);
  tft.setTextColor(COLOR_ACCENT);
  tft.setTextSize(3);
  tft.print("NU FACULTY");

  tft.setCursor(getCenterX("DESK UNIT", 2), 130);
  tft.setTextSize(2);
  tft.setTextColor(COLOR_TEXT);
  tft.print("DESK UNIT");

  tft.setCursor(getCenterX("Grace Period BLE", 1), 160);
  tft.setTextSize(1);
  tft.setTextColor(COLOR_ACCENT);
  tft.print("Grace Period BLE");

  delay(2000);
}

void drawCompleteUI() {
  tft.fillScreen(COLOR_BACKGROUND);

  tft.fillRect(0, TOP_PANEL_Y, SCREEN_WIDTH, TOP_PANEL_HEIGHT, COLOR_PANEL);

  tft.setCursor(PROFESSOR_NAME_X, PROFESSOR_NAME_Y);
  tft.setTextColor(COLOR_ACCENT);
  tft.setTextSize(1);
  tft.print("PROFESSOR: ");
  tft.setTextSize(1);
  tft.print(FACULTY_NAME);

  tft.setCursor(DEPARTMENT_X, DEPARTMENT_Y);
  tft.setTextColor(COLOR_ACCENT);
  tft.setTextSize(1);
  tft.print("DEPARTMENT: ");
  tft.print(FACULTY_DEPARTMENT);

  tft.fillRect(0, STATUS_PANEL_Y, SCREEN_WIDTH, STATUS_PANEL_HEIGHT, COLOR_PANEL_DARK);
  tft.fillRect(0, BOTTOM_PANEL_Y, SCREEN_WIDTH, BOTTOM_PANEL_HEIGHT, COLOR_PANEL);

  updateTimeAndDate();
  updateMainDisplay();
  updateSystemStatus();
}

void updateMainDisplay() {
  tft.fillRect(0, MAIN_AREA_Y, SCREEN_WIDTH, MAIN_AREA_HEIGHT, COLOR_WHITE);

  if (presenceDetector.getPresence()) {
    drawSimpleCard(20, STATUS_CENTER_Y - 40, 280, 70, COLOR_PANEL);

    int availableX = getCenterX("AVAILABLE", 4);
    tft.setCursor(availableX, STATUS_CENTER_Y - 25);
    tft.setTextSize(4);
    tft.setTextColor(COLOR_SUCCESS);
    tft.print("AVAILABLE");

    int subtitleX = getCenterX("Ready for Consultation", 2);
    tft.setCursor(subtitleX, STATUS_CENTER_Y + 5);
    tft.setTextSize(2);
    tft.setTextColor(COLOR_ACCENT);
    tft.print("Ready for Consultation");

    drawStatusIndicator(STATUS_CENTER_X, STATUS_CENTER_Y + 50, true);

  } else {
    drawSimpleCard(20, STATUS_CENTER_Y - 40, 280, 70, COLOR_GRAY_LIGHT);

    int awayX = getCenterX("AWAY", 4);
    tft.setCursor(awayX, STATUS_CENTER_Y - 25);
    tft.setTextSize(4);
    tft.setTextColor(COLOR_ERROR);
    tft.print("AWAY");

    int notAvailableX = getCenterX("Not Available", 2);
    tft.setCursor(notAvailableX, STATUS_CENTER_Y + 5);
    tft.setTextSize(2);
    tft.setTextColor(COLOR_WHITE);
    tft.print("Not Available");

    drawStatusIndicator(STATUS_CENTER_X, STATUS_CENTER_Y + 50, false);
  }
}

void updateSystemStatus() {
  tft.fillRect(2, STATUS_PANEL_Y + 1, SCREEN_WIDTH - 4, STATUS_PANEL_HEIGHT - 2, COLOR_PANEL_DARK);

  int topLineY = STATUS_PANEL_Y + 3;

  tft.setCursor(10, topLineY);
  tft.setTextColor(COLOR_ACCENT);
  tft.setTextSize(1);
  tft.print("WiFi:");
  if (wifiConnected) {
    tft.setTextColor(COLOR_SUCCESS);
    tft.print("CONNECTED");
  } else {
    tft.setTextColor(COLOR_ERROR);
    tft.print("FAILED");
  }

  tft.setCursor(120, topLineY);
  tft.setTextColor(COLOR_ACCENT);
  tft.print("MQTT:");
  if (mqttConnected) {
    tft.setTextColor(COLOR_SUCCESS);
    tft.print("ONLINE");
  } else {
    tft.setTextColor(COLOR_ERROR);
    tft.print("OFFLINE");
  }

  tft.setCursor(230, topLineY);
  tft.setTextColor(COLOR_ACCENT);
  tft.print("BLE:");
  tft.setTextColor(COLOR_SUCCESS);
  tft.print("ACTIVE");

  int bottomLineY = STATUS_PANEL_Y + 15;

  tft.setCursor(10, bottomLineY);
  tft.setTextColor(COLOR_ACCENT);
  tft.print("TIME:");
  if (timeInitialized) {
    tft.setTextColor(COLOR_SUCCESS);
    tft.print("SYNCED");
  } else if (ntpSyncInProgress) {
    tft.setTextColor(COLOR_WARNING);
    tft.print("SYNCING");
  } else if (ntpSyncStatus == "FAILED") {
    tft.setTextColor(COLOR_ERROR);
    tft.print("FAILED");
  } else {
    tft.setTextColor(COLOR_WARNING);
    tft.print("PENDING");
  }

  tft.setCursor(120, bottomLineY);
  tft.setTextColor(COLOR_ACCENT);
  tft.print("RAM:");
  int freeHeapKB = ESP.getFreeHeap() / 1024;
  tft.printf("%dKB", freeHeapKB);

  tft.setCursor(200, bottomLineY);
  tft.setTextColor(COLOR_ACCENT);
  tft.print("UPTIME:");
  unsigned long uptimeMinutes = millis() / 60000;
  if (uptimeMinutes < 60) {
    tft.printf("%dm", uptimeMinutes);
  } else {
    tft.printf("%dh%dm", uptimeMinutes / 60, uptimeMinutes % 60);
  }
}

// ================================
// MAIN SETUP FUNCTION - OPTIMIZED
// ================================
void setup() {
  if (ENABLE_SERIAL_DEBUG) {
    Serial.begin(SERIAL_BAUD_RATE);
    while (!Serial && millis() < 3000);
  }

  DEBUG_PRINTLN("=== NU FACULTY DESK UNIT - ENHANCED CONSULTATION SYSTEM ===");
  DEBUG_PRINTLN("=== PERSISTENT MESSAGES + PHYSICAL BUTTON CONTROL ===");
  DEBUG_PRINTLN("=== PERFORMANCE OPTIMIZED VERSION ===");
  DEBUG_PRINTLN("✅ BLE scan frequency reduced from 1s to 8s");
  DEBUG_PRINTLN("✅ Enhanced MQTT reliability with forced processing");
  DEBUG_PRINTLN("✅ Optimized main loop for <100ms response time");
  DEBUG_PRINTLN("✅ Improved button debouncing for faster response");

  if (!validateConfiguration()) {
    while(true) delay(5000);
  }

  DEBUG_PRINTF("Faculty: %s\n", FACULTY_NAME);
  DEBUG_PRINTF("Department: %s\n", FACULTY_DEPARTMENT);
  DEBUG_PRINTF("iBeacon: %s\n", FACULTY_BEACON_MAC);
  DEBUG_PRINTF("WiFi: %s\n", WIFI_SSID);
  DEBUG_PRINTF("Grace Period: %d seconds\n", BLE_GRACE_PERIOD_MS / 1000);

  // Initialize offline operation system
  DEBUG_PRINTLN("🔄 Initializing optimized offline operation system...");
  initOfflineQueue();

  // Initialize components
  buttons.init();
  setupDisplay();
  setupWiFi();

  if (wifiConnected) {
    setupMQTT();
  }

  setupBLE();
  adaptiveScanner.init(&presenceDetector);  // Pass reference to presence detector

  DEBUG_PRINTLN("=== OPTIMIZED CONSULTATION SYSTEM READY ===");
  DEBUG_PRINTLN("✅ BLE disconnections now have 1-minute grace period!");
  DEBUG_PRINTLN("✅ Consultation messages persist until physical button press!");
  DEBUG_PRINTLN("✅ Larger, more readable consultation message display!");
  DEBUG_PRINTLN("✅ Physical button-only control (no on-screen buttons)!");
  DEBUG_PRINTLN("✅ Performance optimized for fast button response!");
  drawCompleteUI();
}

// ================================
// MAIN LOOP WITH GRACE PERIOD BLE SCANNER - OPTIMIZED
// ================================
void loop() {
  // Add loop timing monitoring for button debugging
  unsigned long loopStart = millis();
  static unsigned long lastLoopTime = 0;
  static unsigned long maxLoopTime = 0;
  static unsigned long loopCount = 0;

  // ✅ CRITICAL FIX: MQTT LOOP FIRST AND FREQUENT
  if (mqttConnected) {
    mqttClient.loop();
  }

  // PRIORITY 1: Update button states FIRST and FREQUENTLY
  // Run button updates multiple times per main loop to catch quick presses
  for (int i = 0; i < 3; i++) {  // Reduced from 5 to 3 for performance
    buttons.update();
    
    // Handle button presses immediately
    if (buttons.isButtonAPressed()) {
      DEBUG_PRINTLN("🎯 BUTTON A PRESS DETECTED IN MAIN LOOP!");
      handleAcknowledgeButton();
      break; // Exit loop if button handled
    }

    if (buttons.isButtonBPressed()) {
      DEBUG_PRINTLN("🎯 BUTTON B PRESS DETECTED IN MAIN LOOP!");
      handleBusyButton();
      break; // Exit loop if button handled
    }
    
    delay(2); // Small delay between button checks
  }

  // Handle button presses
  static unsigned long lastButtonCheck = 0;
  static int buttonCheckCount = 0;
  
  // Debug button checking frequency every 1000 checks (reduced from 100)
  buttonCheckCount++;
  if (buttonCheckCount % 1000 == 0) {
    unsigned long checkInterval = millis() - lastButtonCheck;
    DEBUG_PRINTF("🔍 Button check #%d - last 1000 checks took %lu ms (avg: %.1f ms per check)\n", 
                 buttonCheckCount, checkInterval, (float)checkInterval / 1000.0);
    lastButtonCheck = millis();
  }

  // ✅ CRITICAL FIX: REST OF MAIN LOOP - Run MUCH less frequently to speed up button response
  static unsigned long lastSlowOperations = 0;
  if (millis() - lastSlowOperations > 200) { // Increased frequency from 500ms to 200ms
    
    checkWiFiConnection();

    if (wifiConnected && !mqttClient.connected()) {
      connectMQTT();
    }

    // Update offline queue system
    updateOfflineQueue();

    lastSlowOperations = millis();
  }

  // ✅ CRITICAL FIX: BLE SCANNING - Run MUCH less frequently (major performance fix)
  static unsigned long lastBLEScan = 0;
  if (millis() - lastBLEScan > 8000) { // Increased from 1000ms to 8000ms (8 seconds)
    adaptiveScanner.update();
    lastBLEScan = millis();
  }

  // Update time every 10 seconds (increased from 5)
  static unsigned long lastTimeUpdate = 0;
  if (millis() - lastTimeUpdate > 10000) { // Increased frequency
    updateTimeAndDate();
    lastTimeUpdate = millis();
  }

  // Update system status every 15 seconds (increased from 10)
  static unsigned long lastStatusUpdate = 0;
  if (millis() - lastStatusUpdate > 15000) { // Increased frequency
    updateSystemStatus();
    lastStatusUpdate = millis();
  }

  // Heartbeat every 5 minutes (unchanged)
  static unsigned long lastHeartbeatTime = 0;
  if (millis() - lastHeartbeatTime > HEARTBEAT_INTERVAL) {
    publishHeartbeat();
    lastHeartbeatTime = millis();
  }

  // Periodic time sync check - less frequent
  static unsigned long lastTimeSyncCheck = 0;
  if (millis() - lastTimeSyncCheck > 60000) { // Increased from 30 seconds to 60 seconds
    checkPeriodicTimeSync();
    lastTimeSyncCheck = millis();
  }

  // Simple animation toggle every 1000ms (reduced frequency)
  static unsigned long lastIndicatorUpdate = 0;
  if (millis() - lastIndicatorUpdate > 1000) { // Increased from 800ms
    animationState = !animationState;
    if (presenceDetector.getPresence() && !messageDisplayed) {
      drawStatusIndicator(STATUS_CENTER_X, STATUS_CENTER_Y + 50, true);
    }
    lastIndicatorUpdate = millis();
  }

  // Loop timing analysis
  unsigned long loopTime = millis() - loopStart;
  loopCount++;
  
  if (loopTime > maxLoopTime) {
    maxLoopTime = loopTime;
  }
  
  // Log slow loops that could interfere with button processing
  if (loopTime > 50) {  // Keep threshold at 50ms
    DEBUG_PRINTF("⚠️ Slow loop detected: %lu ms (could affect button response)\n", loopTime);
  }
  
  // Report loop performance every 60 seconds (increased from 30)
  static unsigned long lastLoopReport = 0;
  if (millis() - lastLoopReport > 60000) {
    DEBUG_PRINTF("🔧 Loop Performance: Max=%lu ms, Avg=%.1f ms, Count=%lu\n", 
                maxLoopTime, 
                (float)(millis() - lastLoopTime) / loopCount,
                loopCount);
    maxLoopTime = 0;  // Reset max
    loopCount = 0;    // Reset count
    lastLoopTime = millis();
    lastLoopReport = millis();
  }

  delay(5); // Keep at 5ms for fast button response
}

// ================================
// END OF GRACE PERIOD ENHANCED SYSTEM
// ================================