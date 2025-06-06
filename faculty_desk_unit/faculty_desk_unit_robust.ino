// ================================
// ROBUST FACULTY DESK UNIT - ESP32
// ================================
// Enterprise-grade connectivity with NetworkManager
// Comprehensive error handling and automatic recovery
// Production-ready with watchdog monitoring and diagnostics

#include <WiFi.h>
#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <SPI.h>
#include <time.h>
#include <ArduinoJson.h>

// Local includes
#include "network_manager.h"
#include "config_robust.h"

// ================================
// GLOBAL OBJECTS AND STATE
// ================================
NetworkManager networkManager;
Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_RST);
BLEScan* pBLEScan;

// System state
bool systemInitialized = false;
bool displayInitialized = false;
bool bleInitialized = false;
unsigned long systemStartTime;

// Faculty presence detection
bool facultyPresent = false;
bool lastFacultyPresent = false;
unsigned long lastPresenceChange = 0;
unsigned long gracePeriodStart = 0;
bool inGracePeriod = false;

// Message handling
String currentMessage = "";
String currentConsultationId = "";
bool messageDisplayed = false;
unsigned long messageDisplayStart = 0;

// Button state
bool buttonAPressed = false;
bool buttonBPressed = false;
unsigned long buttonALastDebounce = 0;
unsigned long buttonBLastDebounce = 0;
bool buttonALastState = HIGH;
bool buttonBLastState = HIGH;

// UI state
String lastDisplayedTime = "";
String lastDisplayedDate = "";
unsigned long lastUIUpdate = 0;
unsigned long lastStatusUpdate = 0;
unsigned long lastHeartbeat = 0;

// NTP state
bool timeInitialized = false;
String ntpSyncStatus = "PENDING";
unsigned long lastNtpSync = 0;

// ================================
// BLE CALLBACK CLASS
// ================================
class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) {
        String deviceAddress = advertisedDevice.getAddress().toString().c_str();
        deviceAddress.toUpperCase();
        
        if (deviceAddress == FACULTY_BEACON_MAC) {
            int rssi = advertisedDevice.getRSSI();
            DEBUG_PRINTF("🔵 Faculty beacon detected: %s (RSSI: %d)\n", deviceAddress.c_str(), rssi);
            
            if (rssi >= BLE_SIGNAL_THRESHOLD) {
                facultyPresent = true;
                if (inGracePeriod) {
                    DEBUG_PRINTLN("✅ Faculty returned during grace period");
                    inGracePeriod = false;
                }
            }
        }
    }
};

// ================================
// NETWORK EVENT CALLBACKS
// ================================
void onWiFiEvent(NetworkManager::WiFiState state, NetworkManager::ConnectionError error) {
    DEBUG_PRINTF("📡 WiFi State Changed: %s", getWiFiStateString(state).c_str());
    if (error != NetworkManager::ERROR_NONE) {
        DEBUG_PRINTF(" (Error: %s)", getErrorString(error).c_str());
    }
    DEBUG_PRINTLN();
    
    // Update UI immediately on state changes
    updateSystemStatus();
}

void onMQTTEvent(NetworkManager::MQTTState state, NetworkManager::ConnectionError error) {
    DEBUG_PRINTF("📡 MQTT State Changed: %s", getMQTTStateString(state).c_str());
    if (error != NetworkManager::ERROR_NONE) {
        DEBUG_PRINTF(" (Error: %s)", getErrorString(error).c_str());
    }
    DEBUG_PRINTLN();
    
    // Subscribe to consultation messages when connected
    if (state == NetworkManager::MQTT_CONNECTED) {
        networkManager.subscribe(MQTT_TOPIC_MESSAGES);
        publishPresenceUpdate();
    }
    
    // Update UI immediately on state changes
    updateSystemStatus();
}

void onMQTTMessage(char* topic, byte* payload, unsigned int length) {
    DEBUG_PRINTF("📨 MQTT Message: Topic=%s, Length=%d\n", topic, length);
    
    // Bounds checking
    if (length > MAX_MESSAGE_LENGTH) {
        DEBUG_PRINTF("⚠️ Message too long (%d bytes), truncating\n", length);
        length = MAX_MESSAGE_LENGTH;
    }
    
    // Convert payload to string
    String message = "";
    message.reserve(length + 1);
    for (unsigned int i = 0; i < length; i++) {
        message += (char)payload[i];
    }
    
    DEBUG_PRINTF("📨 Message Content: %s\n", message.c_str());
    
    // Parse consultation ID
    parseConsultationMessage(message);
    
    // Only display if faculty is present
    if (facultyPresent && !inGracePeriod) {
        displayConsultationMessage(message);
    } else {
        DEBUG_PRINTLN("📭 Message ignored - Faculty not present");
    }
}

void onDiagnostics(const NetworkManager::ConnectionStats& stats) {
    if (ENABLE_DIAGNOSTICS) {
        DEBUG_PRINTLN("📊 Network Diagnostics:");
        DEBUG_PRINTF("   WiFi Uptime: %lu ms\n", stats.wifi_uptime_ms);
        DEBUG_PRINTF("   MQTT Uptime: %lu ms\n", stats.mqtt_uptime_ms);
        DEBUG_PRINTF("   WiFi Reconnects: %lu\n", stats.wifi_reconnect_count);
        DEBUG_PRINTF("   MQTT Reconnects: %lu\n", stats.mqtt_reconnect_count);
        DEBUG_PRINTF("   Messages Sent: %lu\n", stats.messages_sent);
        DEBUG_PRINTF("   Messages Failed: %lu\n", stats.messages_failed);
        DEBUG_PRINTF("   Last RSSI: %d dBm\n", stats.last_wifi_rssi);
        
        // Publish diagnostics to central system
        publishDiagnostics(stats);
    }
}

// ================================
// SETUP FUNCTIONS
// ================================
void setup() {
    systemStartTime = millis();
    
    // Initialize serial communication
    if (ENABLE_SERIAL_DEBUG) {
        Serial.begin(SERIAL_BAUD_RATE);
        while (!Serial && millis() < 3000); // Wait up to 3 seconds
    }
    
    DEBUG_PRINTLN("================================");
    DEBUG_PRINTLN("ROBUST FACULTY DESK UNIT v2.0");
    DEBUG_PRINTLN("Enterprise-Grade Connectivity");
    DEBUG_PRINTLN("================================");
    
    // Validate configuration
    if (!validateRobustConfiguration()) {
        DEBUG_PRINTLN("❌ Configuration validation failed - System halted");
        while(true) {
            delay(5000);
            DEBUG_PRINTLN("❌ Fix configuration and restart");
        }
    }
    
    // Initialize hardware
    initializeDisplay();
    initializeButtons();
    initializeBLE();
    
    // Initialize network manager
    initializeNetworkManager();
    
    // Initialize time
    initializeTimeSync();
    
    systemInitialized = true;
    DEBUG_PRINTLN("✅ System initialization complete");
    
    // Draw initial UI
    drawCompleteUI();
}

void initializeDisplay() {
    DEBUG_PRINTLN("🖥️ Initializing display...");
    
    tft.init(240, 320);
    tft.setRotation(3);
    tft.fillScreen(COLOR_BACKGROUND);
    
    // Show startup screen
    tft.setCursor(10, 50);
    tft.setTextColor(COLOR_ACCENT);
    tft.setTextSize(2);
    tft.print("FACULTY DESK UNIT");
    
    tft.setCursor(10, 80);
    tft.setTextColor(COLOR_TEXT);
    tft.setTextSize(1);
    tft.print("Initializing robust connectivity...");
    
    displayInitialized = true;
    DEBUG_PRINTLN("✅ Display initialized");
}

void initializeButtons() {
    DEBUG_PRINTLN("🔘 Initializing buttons...");
    
    pinMode(BUTTON_A_PIN, INPUT_PULLUP);
    pinMode(BUTTON_B_PIN, INPUT_PULLUP);
    
    // Initialize button states
    buttonALastState = digitalRead(BUTTON_A_PIN);
    buttonBLastState = digitalRead(BUTTON_B_PIN);
    
    DEBUG_PRINTLN("✅ Buttons initialized");
}

void initializeBLE() {
    DEBUG_PRINTLN("🔵 Initializing BLE...");
    
    try {
        BLEDevice::init("");
        pBLEScan = BLEDevice::getScan();
        pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
        pBLEScan->setActiveScan(true);
        pBLEScan->setInterval(100);
        pBLEScan->setWindow(99);
        
        bleInitialized = true;
        DEBUG_PRINTLN("✅ BLE initialized");
    } catch (const std::exception& e) {
        DEBUG_PRINTF("❌ BLE initialization failed: %s\n", e.what());
        bleInitialized = false;
    }
}

void initializeNetworkManager() {
    DEBUG_PRINTLN("🌐 Initializing NetworkManager...");
    
    // Build configuration
    NetworkManager::NetworkConfig config = buildNetworkConfig();
    
    // Set event callbacks
    networkManager.setWiFiEventCallback(onWiFiEvent);
    networkManager.setMQTTEventCallback(onMQTTEvent);
    networkManager.setMessageCallback(onMQTTMessage);
    networkManager.setDiagnosticsCallback(onDiagnostics);
    
    // Initialize network manager
    if (!networkManager.begin(config)) {
        DEBUG_PRINTLN("❌ NetworkManager initialization failed");
        return;
    }
    
    // Start connections
    DEBUG_PRINTLN("📡 Starting WiFi connection...");
    networkManager.connectWiFi();
    
    DEBUG_PRINTLN("✅ NetworkManager initialized");
}

void initializeTimeSync() {
    DEBUG_PRINTLN("🕐 Initializing time synchronization...");
    
    // Time will be synchronized automatically when WiFi connects
    // via NetworkManager's built-in NTP handling
    ntpSyncStatus = "WAITING_FOR_WIFI";
    
    DEBUG_PRINTLN("✅ Time sync initialization complete");
}

// ================================
// MAIN LOOP
// ================================
void loop() {
    unsigned long loopStart = millis();
    
    // Critical: Update network manager first
    networkManager.update();
    
    // Feed watchdog
    if (ENABLE_WATCHDOG) {
        networkManager.feedWatchdog();
    }
    
    // High-priority operations (run every loop)
    updateButtons();
    handleButtonPresses();
    
    // Medium-priority operations (run every 1 second)
    static unsigned long lastMediumUpdate = 0;
    if (millis() - lastMediumUpdate > 1000) {
        updatePresenceDetection();
        lastMediumUpdate = millis();
    }
    
    // Low-priority operations (run every 5 seconds)
    static unsigned long lastLowUpdate = 0;
    if (millis() - lastLowUpdate > 5000) {
        updateTimeDisplay();
        checkTimeSync();
        lastLowUpdate = millis();
    }
    
    // UI updates (run every 10 seconds)
    if (millis() - lastStatusUpdate > STATUS_UPDATE_INTERVAL) {
        updateSystemStatus();
        lastStatusUpdate = millis();
    }
    
    // Heartbeat (run every 5 minutes)
    if (millis() - lastHeartbeat > HEARTBEAT_INTERVAL) {
        publishHeartbeat();
        lastHeartbeat = millis();
    }
    
    // Performance monitoring
    unsigned long loopTime = millis() - loopStart;
    if (loopTime > 100) {
        DEBUG_PRINTF("⚠️ Slow loop detected: %lu ms\n", loopTime);
    }
    
    // Small delay to prevent overwhelming
    delay(10);
}

// ================================
// PRESENCE DETECTION
// ================================
void updatePresenceDetection() {
    if (!bleInitialized) return;
    
    // Reset faculty present flag before scan
    bool previousPresent = facultyPresent;
    facultyPresent = false;
    
    // Quick BLE scan
    BLEScanResults foundDevices = pBLEScan->start(1, false);
    pBLEScan->clearResults();
    
    // Handle presence changes
    if (facultyPresent != previousPresent) {
        handlePresenceChange(facultyPresent);
    }
    
    // Handle grace period
    if (!facultyPresent && !inGracePeriod && previousPresent) {
        DEBUG_PRINTLN("⏳ Starting grace period for faculty absence");
        inGracePeriod = true;
        gracePeriodStart = millis();
    }
    
    // Check grace period expiration
    if (inGracePeriod && (millis() - gracePeriodStart > BLE_GRACE_PERIOD_MS)) {
        DEBUG_PRINTLN("⏰ Grace period expired - Faculty confirmed away");
        inGracePeriod = false;
        handlePresenceChange(false);
    }
}

void handlePresenceChange(bool present) {
    DEBUG_PRINTF("👤 Faculty presence changed: %s\n", present ? "PRESENT" : "AWAY");
    
    lastFacultyPresent = facultyPresent;
    lastPresenceChange = millis();
    
    // Clear any displayed message if faculty goes away
    if (!present && messageDisplayed) {
        clearCurrentMessage();
    }
    
    // Update UI
    updateMainDisplay();
    
    // Publish presence update
    publishPresenceUpdate();
}

// ================================
// BUTTON HANDLING
// ================================
void updateButtons() {
    // Read current button states
    bool buttonACurrentState = digitalRead(BUTTON_A_PIN);
    bool buttonBCurrentState = digitalRead(BUTTON_B_PIN);
    
    // Button A debouncing
    if (buttonACurrentState != buttonALastState) {
        buttonALastDebounce = millis();
    }
    
    if ((millis() - buttonALastDebounce) > BUTTON_DEBOUNCE_DELAY) {
        if (buttonACurrentState != buttonAPressed) {
            buttonAPressed = buttonACurrentState;
            if (!buttonAPressed) { // Button released (LOW to HIGH transition)
                DEBUG_PRINTLN("🔵 Button A pressed (Acknowledge)");
            }
        }
    }
    buttonALastState = buttonACurrentState;
    
    // Button B debouncing
    if (buttonBCurrentState != buttonBLastState) {
        buttonBLastDebounce = millis();
    }
    
    if ((millis() - buttonBLastDebounce) > BUTTON_DEBOUNCE_DELAY) {
        if (buttonBCurrentState != buttonBPressed) {
            buttonBPressed = buttonBCurrentState;
            if (!buttonBPressed) { // Button released (LOW to HIGH transition)
                DEBUG_PRINTLN("🔴 Button B pressed (Busy)");
            }
        }
    }
    buttonBLastState = buttonBCurrentState;
}

void handleButtonPresses() {
    // Handle acknowledge button
    static bool buttonAProcessed = false;
    if (!buttonAPressed && !buttonAProcessed && messageDisplayed) {
        handleAcknowledgeResponse();
        buttonAProcessed = true;
    } else if (buttonAPressed) {
        buttonAProcessed = false;
    }
    
    // Handle busy button
    static bool buttonBProcessed = false;
    if (!buttonBPressed && !buttonBProcessed && messageDisplayed) {
        handleBusyResponse();
        buttonBProcessed = true;
    } else if (buttonBPressed) {
        buttonBProcessed = false;
    }
}

void handleAcknowledgeResponse() {
    DEBUG_PRINTLN("🔵 Processing ACKNOWLEDGE response");
    
    if (!messageDisplayed || currentConsultationId.isEmpty()) {
        DEBUG_PRINTLN("❌ No message to acknowledge");
        showResponseConfirmation("NO MESSAGE", COLOR_ERROR);
        return;
    }
    
    if (!facultyPresent || inGracePeriod) {
        DEBUG_PRINTLN("❌ Cannot acknowledge - Faculty not present");
        showResponseConfirmation("NOT PRESENT", COLOR_ERROR);
        return;
    }
    
    // Create response JSON
    DynamicJsonDocument response(512);
    response["faculty_id"] = FACULTY_ID;
    response["faculty_name"] = FACULTY_NAME;
    response["response_type"] = "ACKNOWLEDGE";
    response["message_id"] = currentConsultationId;
    response["timestamp"] = millis();
    response["faculty_present"] = true;
    response["response_method"] = "physical_button";
    
    String responseStr;
    serializeJson(response, responseStr);
    
    DEBUG_PRINTF("📤 Sending ACKNOWLEDGE: %s\n", responseStr.c_str());
    
    // Send response with automatic retry
    bool success = networkManager.publish(MQTT_TOPIC_RESPONSES, responseStr.c_str());
    
    if (success) {
        DEBUG_PRINTLN("✅ ACKNOWLEDGE sent successfully");
        showResponseConfirmation("ACKNOWLEDGED", COLOR_SUCCESS);
    } else {
        DEBUG_PRINTLN("📥 ACKNOWLEDGE queued for retry");
        showResponseConfirmation("QUEUED", COLOR_WARNING);
    }
    
    clearCurrentMessage();
}

void handleBusyResponse() {
    DEBUG_PRINTLN("🔴 Processing BUSY response");
    
    if (!messageDisplayed || currentConsultationId.isEmpty()) {
        DEBUG_PRINTLN("❌ No message to mark as busy");
        showResponseConfirmation("NO MESSAGE", COLOR_ERROR);
        return;
    }
    
    if (!facultyPresent || inGracePeriod) {
        DEBUG_PRINTLN("❌ Cannot respond busy - Faculty not present");
        showResponseConfirmation("NOT PRESENT", COLOR_ERROR);
        return;
    }
    
    // Create response JSON
    DynamicJsonDocument response(512);
    response["faculty_id"] = FACULTY_ID;
    response["faculty_name"] = FACULTY_NAME;
    response["response_type"] = "BUSY";
    response["message_id"] = currentConsultationId;
    response["timestamp"] = millis();
    response["faculty_present"] = true;
    response["response_method"] = "physical_button";
    
    String responseStr;
    serializeJson(response, responseStr);
    
    DEBUG_PRINTF("📤 Sending BUSY: %s\n", responseStr.c_str());
    
    // Send response with automatic retry
    bool success = networkManager.publish(MQTT_TOPIC_RESPONSES, responseStr.c_str());
    
    if (success) {
        DEBUG_PRINTLN("✅ BUSY sent successfully");
        showResponseConfirmation("MARKED BUSY", COLOR_WARNING);
    } else {
        DEBUG_PRINTLN("📥 BUSY queued for retry");
        showResponseConfirmation("QUEUED", COLOR_WARNING);
    }
    
    clearCurrentMessage();
}

// ================================
// MESSAGE HANDLING
// ================================
void parseConsultationMessage(const String& message) {
    DEBUG_PRINTF("🔍 Parsing consultation message: %s\n", message.c_str());
    
    // Parse consultation ID from message
    // Expected format: "CID:{id} From:{name} (SID:{sid}): {message}"
    int cidIndex = message.indexOf("CID:");
    if (cidIndex != -1) {
        int cidStart = cidIndex + 4;
        int cidEnd = message.indexOf(" ", cidStart);
        if (cidEnd != -1) {
            currentConsultationId = message.substring(cidStart, cidEnd);
            DEBUG_PRINTF("🔑 Extracted consultation ID: %s\n", currentConsultationId.c_str());
        } else {
            DEBUG_PRINTLN("⚠️ Could not parse consultation ID");
            currentConsultationId = "";
        }
    } else {
        DEBUG_PRINTLN("⚠️ No consultation ID found in message");
        currentConsultationId = "";
    }
}

void displayConsultationMessage(const String& message) {
    DEBUG_PRINTLN("📱 Displaying consultation message");
    
    currentMessage = message;
    messageDisplayed = true;
    messageDisplayStart = millis();
    
    // Clear main area
    tft.fillRect(0, MAIN_AREA_Y, SCREEN_WIDTH, MAIN_AREA_HEIGHT, COLOR_WHITE);
    
    // Display message header
    tft.fillRect(10, MAIN_AREA_Y + 5, SCREEN_WIDTH - 20, 20, COLOR_ACCENT);
    tft.setCursor(15, MAIN_AREA_Y + 10);
    tft.setTextColor(COLOR_BACKGROUND);
    tft.setTextSize(1);
    tft.print("CONSULTATION REQUEST");
    
    if (!currentConsultationId.isEmpty()) {
        tft.setCursor(15, MAIN_AREA_Y + 20);
        tft.setTextColor(COLOR_BACKGROUND);
        tft.setTextSize(1);
        tft.print("ID: " + currentConsultationId);
    }
    
    // Display message content with word wrapping
    int yPos = MAIN_AREA_Y + 35;
    int maxCharsPerLine = 25;
    int lineHeight = 18;
    
    // Parse student info if available
    int fromIndex = message.indexOf("From:");
    int sidIndex = message.indexOf("(SID:");
    int messageIndex = message.indexOf("): ");
    
    if (fromIndex != -1 && sidIndex != -1 && messageIndex != -1) {
        // Extract student name
        String studentName = message.substring(fromIndex + 5, sidIndex);
        studentName.trim();
        
        // Display student info
        tft.setCursor(15, yPos);
        tft.setTextColor(COLOR_ACCENT);
        tft.setTextSize(2);
        tft.print("Student: ");
        tft.setTextColor(COLOR_BLACK);
        tft.print(studentName);
        yPos += lineHeight + 4;
        
        // Extract and display the consultation message
        String consultationMsg = message.substring(messageIndex + 3);
        consultationMsg.trim();
        
        tft.setCursor(15, yPos);
        tft.setTextColor(COLOR_ACCENT);
        tft.setTextSize(2);
        tft.print("Request:");
        yPos += lineHeight;
        
        // Display with word wrapping
        for (int i = 0; i < consultationMsg.length(); i += maxCharsPerLine) {
            String line = consultationMsg.substring(i, min(i + maxCharsPerLine, (int)consultationMsg.length()));
            tft.setCursor(15, yPos);
            tft.setTextColor(COLOR_BLACK);
            tft.setTextSize(2);
            tft.print(line);
            yPos += lineHeight;
        }
    } else {
        // Fallback: display raw message with word wrapping
        for (int i = 0; i < message.length(); i += maxCharsPerLine) {
            String line = message.substring(i, min(i + maxCharsPerLine, (int)message.length()));
            tft.setCursor(15, yPos);
            tft.setTextColor(COLOR_BLACK);
            tft.setTextSize(2);
            tft.print(line);
            yPos += lineHeight;
        }
    }
    
    // Instructions
    tft.setCursor(15, MAIN_AREA_Y + 120);
    tft.setTextColor(COLOR_ACCENT);
    tft.setTextSize(1);
    tft.print("BLUE=Accept | RED=Busy");
    
    DEBUG_PRINTF("📱 Message displayed. ID: %s\n", currentConsultationId.c_str());
}

void clearCurrentMessage() {
    DEBUG_PRINTLN("🧹 Clearing current message");
    
    currentMessage = "";
    currentConsultationId = "";
    messageDisplayed = false;
    messageDisplayStart = 0;
    
    // Redraw main display
    updateMainDisplay();
}

void showResponseConfirmation(const String& message, uint16_t color) {
    DEBUG_PRINTF("✅ Showing confirmation: %s\n", message.c_str());
    
    // Temporarily show confirmation
    int centerX = (SCREEN_WIDTH - message.length() * 12) / 2;
    
    tft.fillRect(20, STATUS_CENTER_Y - 10, SCREEN_WIDTH - 40, 40, color);
    tft.setCursor(centerX, STATUS_CENTER_Y);
    tft.setTextColor(COLOR_WHITE);
    tft.setTextSize(2);
    tft.print(message);
    
    delay(CONFIRMATION_DISPLAY_TIME);
    
    // Restore display
    updateMainDisplay();
}

// ================================
// DISPLAY FUNCTIONS
// ================================
void drawCompleteUI() {
    DEBUG_PRINTLN("🖥️ Drawing complete UI");
    
    tft.fillScreen(COLOR_BACKGROUND);
    
    // Top panel
    tft.fillRect(0, 0, SCREEN_WIDTH, TOP_PANEL_HEIGHT, COLOR_PANEL);
    
    tft.setCursor(10, 8);
    tft.setTextColor(COLOR_ACCENT);
    tft.setTextSize(1);
    tft.print("PROFESSOR: ");
    tft.print(FACULTY_NAME);
    
    tft.setCursor(10, 18);
    tft.setTextColor(COLOR_ACCENT);
    tft.setTextSize(1);
    tft.print("DEPARTMENT: ");
    tft.print(FACULTY_DEPARTMENT);
    
    // Status panel
    tft.fillRect(0, STATUS_PANEL_Y, SCREEN_WIDTH, STATUS_PANEL_HEIGHT, COLOR_PANEL_DARK);
    
    // Bottom panel
    tft.fillRect(0, BOTTOM_PANEL_Y, SCREEN_WIDTH, BOTTOM_PANEL_HEIGHT, COLOR_PANEL);
    
    updateMainDisplay();
    updateSystemStatus();
    updateTimeDisplay();
}

void updateMainDisplay() {
    // Clear main area
    tft.fillRect(0, MAIN_AREA_Y, SCREEN_WIDTH, MAIN_AREA_HEIGHT, COLOR_WHITE);
    
    if (messageDisplayed) {
        // Message is already displayed by displayConsultationMessage
        return;
    }
    
    // Show availability status
    if (facultyPresent && !inGracePeriod) {
        // Available
        tft.fillRect(20, STATUS_CENTER_Y - 40, 280, 70, COLOR_PANEL);
        
        int availableX = (SCREEN_WIDTH - 9 * 24) / 2; // Center "AVAILABLE"
        tft.setCursor(availableX, STATUS_CENTER_Y - 25);
        tft.setTextSize(4);
        tft.setTextColor(COLOR_SUCCESS);
        tft.print("AVAILABLE");
        
        int subtitleX = (SCREEN_WIDTH - 21 * 12) / 2; // Center subtitle
        tft.setCursor(subtitleX, STATUS_CENTER_Y + 5);
        tft.setTextSize(2);
        tft.setTextColor(COLOR_ACCENT);
        tft.print("Ready for Consultation");
        
    } else {
        // Away or in grace period
        tft.fillRect(20, STATUS_CENTER_Y - 40, 280, 70, COLOR_GRAY_LIGHT);
        
        int awayX = (SCREEN_WIDTH - 4 * 24) / 2; // Center "AWAY"
        tft.setCursor(awayX, STATUS_CENTER_Y - 25);
        tft.setTextSize(4);
        tft.setTextColor(COLOR_ERROR);
        tft.print("AWAY");
        
        String subtitle = inGracePeriod ? "Grace Period" : "Not Available";
        int subtitleX = (SCREEN_WIDTH - subtitle.length() * 12) / 2;
        tft.setCursor(subtitleX, STATUS_CENTER_Y + 5);
        tft.setTextSize(2);
        tft.setTextColor(COLOR_WHITE);
        tft.print(subtitle);
    }
}

void updateSystemStatus() {
    // Clear status area
    tft.fillRect(2, STATUS_PANEL_Y + 1, SCREEN_WIDTH - 4, STATUS_PANEL_HEIGHT - 2, COLOR_PANEL_DARK);
    
    int topLineY = STATUS_PANEL_Y + 3;
    
    // WiFi status
    tft.setCursor(10, topLineY);
    tft.setTextColor(COLOR_ACCENT);
    tft.setTextSize(1);
    tft.print("WiFi:");
    if (networkManager.isWiFiConnected()) {
        tft.setTextColor(COLOR_SUCCESS);
        tft.print("CONNECTED");
    } else {
        tft.setTextColor(COLOR_ERROR);
        tft.print("FAILED");
    }
    
    // MQTT status
    tft.setCursor(120, topLineY);
    tft.setTextColor(COLOR_ACCENT);
    tft.print("MQTT:");
    if (networkManager.isMQTTConnected()) {
        tft.setTextColor(COLOR_SUCCESS);
        tft.print("ONLINE");
    } else {
        tft.setTextColor(COLOR_ERROR);
        tft.print("OFFLINE");
    }
    
    // BLE status
    tft.setCursor(230, topLineY);
    tft.setTextColor(COLOR_ACCENT);
    tft.print("BLE:");
    if (bleInitialized) {
        tft.setTextColor(COLOR_SUCCESS);
        tft.print("ACTIVE");
    } else {
        tft.setTextColor(COLOR_ERROR);
        tft.print("FAILED");
    }
    
    int bottomLineY = STATUS_PANEL_Y + 15;
    
    // Time status
    tft.setCursor(10, bottomLineY);
    tft.setTextColor(COLOR_ACCENT);
    tft.print("TIME:");
    if (timeInitialized) {
        tft.setTextColor(COLOR_SUCCESS);
        tft.print("SYNCED");
    } else {
        tft.setTextColor(COLOR_WARNING);
        tft.print(ntpSyncStatus.c_str());
    }
    
    // Memory status
    tft.setCursor(120, bottomLineY);
    tft.setTextColor(COLOR_ACCENT);
    tft.print("RAM:");
    int freeHeapKB = ESP.getFreeHeap() / 1024;
    tft.printf("%dKB", freeHeapKB);
    
    // Connection quality
    if (networkManager.isWiFiConnected()) {
        tft.setCursor(200, bottomLineY);
        tft.setTextColor(COLOR_ACCENT);
        tft.print("RSSI:");
        int rssi = networkManager.getWiFiRSSI();
        if (rssi > -50) {
            tft.setTextColor(COLOR_SUCCESS);
        } else if (rssi > -70) {
            tft.setTextColor(COLOR_WARNING);
        } else {
            tft.setTextColor(COLOR_ERROR);
        }
        tft.printf("%ddBm", rssi);
    }
}

void updateTimeDisplay() {
    if (!networkManager.isWiFiConnected()) {
        if (lastDisplayedTime != "OFFLINE") {
            lastDisplayedTime = "OFFLINE";
            lastDisplayedDate = "NO WIFI";
            
            tft.fillRect(10, BOTTOM_PANEL_Y + 5, 120, 15, COLOR_PANEL);
            tft.setCursor(10, BOTTOM_PANEL_Y + 8);
            tft.setTextColor(COLOR_ERROR);
            tft.setTextSize(1);
            tft.print("TIME: OFFLINE");
            
            tft.fillRect(200, BOTTOM_PANEL_Y + 5, 110, 15, COLOR_PANEL);
            tft.setCursor(200, BOTTOM_PANEL_Y + 8);
            tft.setTextColor(COLOR_ERROR);
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
            
            tft.fillRect(10, BOTTOM_PANEL_Y + 5, 120, 15, COLOR_PANEL);
            tft.setCursor(10, BOTTOM_PANEL_Y + 8);
            tft.setTextColor(COLOR_ACCENT);
            tft.setTextSize(1);
            tft.print("TIME: ");
            tft.print(timeStr);
        }
        
        if (currentDateStr != lastDisplayedDate) {
            lastDisplayedDate = currentDateStr;
            
            tft.fillRect(200, BOTTOM_PANEL_Y + 5, 110, 15, COLOR_PANEL);
            tft.setCursor(200, BOTTOM_PANEL_Y + 8);
            tft.setTextColor(COLOR_ACCENT);
            tft.setTextSize(1);
            tft.print(dateStr);
        }
    } else {
        if (lastDisplayedTime != "SYNCING") {
            lastDisplayedTime = "SYNCING";
            lastDisplayedDate = "SYNCING";
            
            tft.fillRect(10, BOTTOM_PANEL_Y + 5, 120, 15, COLOR_PANEL);
            tft.setCursor(10, BOTTOM_PANEL_Y + 8);
            tft.setTextColor(COLOR_WARNING);
            tft.setTextSize(1);
            tft.print("TIME: SYNCING...");
            
            tft.fillRect(200, BOTTOM_PANEL_Y + 5, 110, 15, COLOR_PANEL);
            tft.setCursor(200, BOTTOM_PANEL_Y + 8);
            tft.setTextColor(COLOR_WARNING);
            tft.print("PLEASE WAIT");
        }
    }
}

void checkTimeSync() {
    if (!networkManager.isWiFiConnected()) {
        ntpSyncStatus = "NO_WIFI";
        return;
    }
    
    if (!timeInitialized) {
        // Attempt initial time sync
        if (millis() - lastNtpSync > 10000) { // Try every 10 seconds
            DEBUG_PRINTLN("🕐 Attempting time synchronization...");
            ntpSyncStatus = "SYNCING";
            
            configTime(TIME_ZONE_OFFSET * 3600, 0, NTP_SERVER_PRIMARY, NTP_SERVER_SECONDARY);
            
            delay(2000); // Wait for sync
            
            struct tm timeinfo;
            if (getLocalTime(&timeinfo)) {
                timeInitialized = true;
                ntpSyncStatus = "SYNCED";
                DEBUG_PRINTLN("✅ Time synchronized successfully");
            } else {
                ntpSyncStatus = "FAILED";
                DEBUG_PRINTLN("❌ Time synchronization failed");
            }
            
            lastNtpSync = millis();
        }
    } else {
        // Periodic resync
        if (millis() - lastNtpSync > NTP_UPDATE_INTERVAL) {
            DEBUG_PRINTLN("🕐 Performing periodic time sync...");
            configTime(TIME_ZONE_OFFSET * 3600, 0, NTP_SERVER_PRIMARY);
            lastNtpSync = millis();
        }
    }
}

// ================================
// MQTT PUBLISHING FUNCTIONS
// ================================
void publishPresenceUpdate() {
    DynamicJsonDocument payload(512);
    payload["faculty_id"] = FACULTY_ID;
    payload["faculty_name"] = FACULTY_NAME;
    payload["present"] = (facultyPresent && !inGracePeriod);
    payload["status"] = (facultyPresent && !inGracePeriod) ? "AVAILABLE" : "AWAY";
    payload["timestamp"] = millis();
    payload["in_grace_period"] = inGracePeriod;
    
    if (inGracePeriod) {
        payload["grace_period_remaining"] = BLE_GRACE_PERIOD_MS - (millis() - gracePeriodStart);
    }
    
    String payloadStr;
    serializeJson(payload, payloadStr);
    
    DEBUG_PRINTF("📡 Publishing presence: %s\n", payloadStr.c_str());
    
    // Publish to both topics for compatibility
    networkManager.publish(MQTT_TOPIC_STATUS, payloadStr.c_str());
    networkManager.publish(MQTT_LEGACY_STATUS, payloadStr.c_str());
}

void publishHeartbeat() {
    DynamicJsonDocument payload(512);
    payload["faculty_id"] = FACULTY_ID;
    payload["uptime"] = millis() - systemStartTime;
    payload["free_heap"] = ESP.getFreeHeap();
    payload["wifi_connected"] = networkManager.isWiFiConnected();
    payload["mqtt_connected"] = networkManager.isMQTTConnected();
    payload["time_initialized"] = timeInitialized;
    payload["faculty_present"] = (facultyPresent && !inGracePeriod);
    payload["system_healthy"] = networkManager.isSystemHealthy();
    
    if (networkManager.isWiFiConnected()) {
        payload["wifi_rssi"] = networkManager.getWiFiRSSI();
        payload["connection_quality"] = networkManager.getConnectionQuality();
    }
    
    String payloadStr;
    serializeJson(payload, payloadStr);
    
    DEBUG_PRINTF("💓 Publishing heartbeat: %s\n", payloadStr.c_str());
    networkManager.publish(MQTT_TOPIC_HEARTBEAT, payloadStr.c_str());
}

void publishDiagnostics(const NetworkManager::ConnectionStats& stats) {
    DynamicJsonDocument payload(1024);
    payload["faculty_id"] = FACULTY_ID;
    payload["timestamp"] = millis();
    
    // Connection statistics
    payload["wifi_uptime_ms"] = stats.wifi_uptime_ms;
    payload["mqtt_uptime_ms"] = stats.mqtt_uptime_ms;
    payload["wifi_reconnects"] = stats.wifi_reconnect_count;
    payload["mqtt_reconnects"] = stats.mqtt_reconnect_count;
    payload["wifi_failures"] = stats.wifi_failures;
    payload["mqtt_failures"] = stats.mqtt_failures;
    payload["messages_sent"] = stats.messages_sent;
    payload["messages_failed"] = stats.messages_failed;
    payload["messages_queued"] = stats.messages_queued;
    payload["last_wifi_rssi"] = stats.last_wifi_rssi;
    
    // System health
    payload["free_heap"] = ESP.getFreeHeap();
    payload["system_uptime"] = millis() - systemStartTime;
    payload["system_healthy"] = networkManager.isSystemHealthy();
    
    String payloadStr;
    serializeJson(payload, payloadStr);
    
    DEBUG_PRINTF("📊 Publishing diagnostics: %s\n", payloadStr.c_str());
    networkManager.publish(MQTT_TOPIC_DIAGNOSTICS, payloadStr.c_str());
}

// ================================
// END OF ROBUST FACULTY DESK UNIT
// ================================ 