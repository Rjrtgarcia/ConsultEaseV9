// ================================
// FACULTY DESK UNIT - SIMPLE SETUP TEMPLATE
// ================================
// Copy this to 'config.h' and fill in your details

#ifndef CONFIG_H
#define CONFIG_H

// ===== CHANGE THESE FOR EACH FACULTY UNIT =====
#define FACULTY_ID 1                           // Unique ID (1, 2, 3, etc.)
#define FACULTY_NAME "Your Name"               // Professor's name
#define FACULTY_DEPARTMENT "Your Department"   // Department name
#define FACULTY_BEACON_MAC "XX:XX:XX:XX:XX:XX" // Your iBeacon MAC address

// ===== CHANGE THESE FOR YOUR NETWORK =====
#define WIFI_SSID "Your_WiFi_Name"             // WiFi network name
#define WIFI_PASSWORD "Your_WiFi_Password"     // WiFi password
#define MQTT_SERVER "192.168.1.100"           // MQTT broker IP address
#define MQTT_USERNAME "faculty_desk"           // MQTT username
#define MQTT_PASSWORD "desk_password"          // MQTT password

// ===== HARDWARE PINS (CHANGE IF DIFFERENT) =====
#define BUTTON_A_PIN 15  // Blue button (Acknowledge)
#define BUTTON_B_PIN 4   // Red button (Busy)
#define TFT_CS 5         // Display CS pin
#define TFT_RST 22       // Display RST pin  
#define TFT_DC 21        // Display DC pin

// ===== DEFAULT SETTINGS (USUALLY NO NEED TO CHANGE) =====
#define MQTT_PORT 1883
#define MQTT_KEEPALIVE 60
#define MQTT_QOS 1
#define MQTT_CLIENT_ID "Faculty_Desk_Unit_" TOSTRING(FACULTY_ID)

// BLE timing
#define BLE_SCAN_INTERVAL_SEARCHING 2000    // Fast scan when away (2s)
#define BLE_SCAN_INTERVAL_MONITORING 8000   // Slow scan when present (8s) 
#define BLE_SCAN_INTERVAL_VERIFICATION 1000 // Quick scan during transitions
#define BLE_GRACE_PERIOD_MS 60000           // 1 minute grace period

// Network timeouts
#define WIFI_CONNECT_TIMEOUT 20000          // 20 seconds
#define WIFI_RECONNECT_INTERVAL 5000        // 5 seconds between WiFi reconnect attempts

// UI timing
#define BUTTON_DEBOUNCE_DELAY 20            // 20ms button debounce
#define CONFIRMATION_DISPLAY_TIME 2000      // 2s confirmation display

// System settings
#define ENABLE_SERIAL_DEBUG true
#define SERIAL_BAUD_RATE 115200
#define MAX_MESSAGE_LENGTH 512
#define HEARTBEAT_INTERVAL 300000           // 5 minutes
#define TIME_ZONE_OFFSET 8                  // GMT+8 Philippines

// ===== AUTO-GENERATED TOPICS (DO NOT CHANGE) =====
#define MQTT_TOPIC_STATUS "consultease/faculty/" TOSTRING(FACULTY_ID) "/status"
#define MQTT_TOPIC_MESSAGES "consultease/faculty/" TOSTRING(FACULTY_ID) "/messages"
#define MQTT_TOPIC_RESPONSES "consultease/faculty/" TOSTRING(FACULTY_ID) "/responses"
#define MQTT_TOPIC_HEARTBEAT "consultease/faculty/" TOSTRING(FACULTY_ID) "/heartbeat"
#define MQTT_LEGACY_STATUS "faculty/" TOSTRING(FACULTY_ID) "/status"

// ===== DISPLAY SETTINGS (DO NOT CHANGE) =====
#define SCREEN_WIDTH 320
#define SCREEN_HEIGHT 240
#define MAIN_AREA_Y 35
#define MAIN_AREA_HEIGHT 140
#define STATUS_CENTER_X 160
#define STATUS_CENTER_Y 105

// Panel layout
#define TOP_PANEL_HEIGHT 30
#define TOP_PANEL_Y 0
#define STATUS_PANEL_HEIGHT 25
#define STATUS_PANEL_Y 180
#define BOTTOM_PANEL_HEIGHT 30
#define BOTTOM_PANEL_Y 210

// Text positions
#define PROFESSOR_NAME_X 10
#define PROFESSOR_NAME_Y 8
#define DEPARTMENT_X 10
#define DEPARTMENT_Y 18
#define TIME_X 10
#define TIME_Y 220
#define DATE_X 250
#define DATE_Y 220

// ===== COLORS (DO NOT CHANGE) =====
#define COLOR_WHITE      0x0000  // White
#define COLOR_BLACK      0xFFFF  // Black
#define COLOR_SUCCESS    0xF81F  // Green
#define COLOR_ERROR      0x07FF  // Red
#define COLOR_WARNING    0xFE60  // Gold
#define COLOR_BLUE       0xF800  // Blue
#define COLOR_ACCENT     0xFE60  // Gold accent
#define COLOR_PANEL      0x001F  // Navy blue
#define COLOR_PANEL_DARK 0x000B  // Dark navy
#define COLOR_BACKGROUND COLOR_BLACK
#define COLOR_TEXT       COLOR_WHITE
#define COLOR_GRAY_LIGHT 0x7BEF

// ===== NTP SERVERS (DO NOT CHANGE) =====
#define NTP_SERVER_PRIMARY "pool.ntp.org"
#define NTP_SERVER_SECONDARY "time.nist.gov" 
#define NTP_SERVER_TERTIARY "time.google.com"
#define NTP_SYNC_TIMEOUT 10000        // 10 seconds
#define NTP_UPDATE_INTERVAL 7200000   // 2 hours
#define NTP_RETRY_INTERVAL 30000      // 30 seconds
#define NTP_MAX_RETRIES 3             // Maximum retries

// ===== ADVANCED BLE SETTINGS (DO NOT CHANGE) =====
#define BLE_SCAN_DURATION_QUICK 1
#define BLE_SCAN_DURATION_FULL 3
#define BLE_SIGNAL_STRENGTH_THRESHOLD -80
#define BLE_RECONNECT_ATTEMPT_INTERVAL 5000
#define BLE_RECONNECT_MAX_ATTEMPTS 12
#define PRESENCE_CONFIRM_TIME 6000            // Time to confirm presence change
#define BLE_STATS_REPORT_INTERVAL 60000      // Report stats every minute

// ===== HELPER MACROS (DO NOT CHANGE) =====
#define STRINGIFY(x) #x
#define TOSTRING(x) STRINGIFY(x)
#define DEBUG_PRINT(x) if(ENABLE_SERIAL_DEBUG) Serial.print(x)
#define DEBUG_PRINTLN(x) if(ENABLE_SERIAL_DEBUG) Serial.println(x)
#define DEBUG_PRINTF(format, ...) if(ENABLE_SERIAL_DEBUG) Serial.printf(format, ##__VA_ARGS__)

// ===== VALIDATION (DO NOT CHANGE) =====
inline bool validateConfiguration() {
  bool valid = true;

  if (FACULTY_ID < 1) {
    DEBUG_PRINTLN("❌ ERROR: FACULTY_ID must be >= 1");
    valid = false;
  }

  if (strlen(FACULTY_BEACON_MAC) != 17) {
    DEBUG_PRINTLN("❌ ERROR: FACULTY_BEACON_MAC must be 17 characters (XX:XX:XX:XX:XX:XX)");
    valid = false;
  }

  if (strlen(WIFI_SSID) == 0) {
    DEBUG_PRINTLN("❌ ERROR: WIFI_SSID cannot be empty");
    valid = false;
  }

  if (strlen(MQTT_SERVER) == 0) {
    DEBUG_PRINTLN("❌ ERROR: MQTT_SERVER cannot be empty");
    valid = false;
  }

  if (BUTTON_A_PIN == BUTTON_B_PIN) {
    DEBUG_PRINTLN("❌ ERROR: Button pins cannot be the same");
    valid = false;
  }

  if (valid) {
    DEBUG_PRINTLN("✅ Configuration validation passed");
    DEBUG_PRINTF("   Faculty: %s (ID: %d)\n", FACULTY_NAME, FACULTY_ID);
    DEBUG_PRINTF("   Department: %s\n", FACULTY_DEPARTMENT);
    DEBUG_PRINTF("   Beacon MAC: %s\n", FACULTY_BEACON_MAC);
    DEBUG_PRINTF("   Grace Period: %d seconds\n", BLE_GRACE_PERIOD_MS / 1000);
    DEBUG_PRINTF("   MQTT Topics: consultease/faculty/%d/*\n", FACULTY_ID);
  } else {
    DEBUG_PRINTLN("❌ Configuration validation FAILED - Check settings above");
  }

  return valid;
}

#endif // CONFIG_H 