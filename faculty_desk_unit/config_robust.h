#ifndef CONFIG_ROBUST_H
#define CONFIG_ROBUST_H

// ================================
// ROBUST FACULTY DESK UNIT CONFIGURATION
// ================================
// Enhanced configuration for production deployment with NetworkManager

// ===== FACULTY INFORMATION =====
#define FACULTY_ID 1
#define FACULTY_NAME "Dave Jomillo"
#define FACULTY_DEPARTMENT "Helpdesk"

// ===== NETWORK CONFIGURATION =====
// WiFi Settings
#define WIFI_SSID "HUAWEI-2.4G-37Pf"
#define WIFI_PASSWORD "7981526rtg"
#define WIFI_TIMEOUT_MS 30000           // 30 seconds for initial connection
#define WIFI_RETRY_INTERVAL_MS 10000    // 10 seconds between retry attempts
#define WIFI_MAX_RETRIES 5              // Maximum retry attempts before escalation
#define WIFI_POWER_SAVE_ENABLED false   // Disable for maximum reliability

// MQTT Settings
#define MQTT_SERVER "192.168.100.3"
#define MQTT_PORT 1883
#define MQTT_USERNAME ""                // Empty for anonymous
#define MQTT_PASSWORD ""                // Empty for anonymous
#define MQTT_CLIENT_ID_PREFIX "FacultyDesk_"
#define MQTT_KEEPALIVE 60               // 60 seconds keepalive
#define MQTT_TIMEOUT_MS 15000           // 15 seconds connection timeout
#define MQTT_RETRY_INTERVAL_MS 8000     // 8 seconds between retry attempts
#define MQTT_MAX_RETRIES 3              // Maximum retry attempts
#define MQTT_BUFFER_SIZE 1024           // Increased buffer for large messages

// Connection Quality Thresholds
#define WIFI_MIN_RSSI -75               // Minimum acceptable signal strength
#define CONNECTION_QUALITY_THRESHOLD 70  // Minimum connection quality percentage
#define HEALTH_CHECK_INTERVAL_MS 30000  // 30 seconds between health checks

// ===== BLE BEACON SETTINGS =====
#define FACULTY_BEACON_MAC "51:00:25:04:02:A2"
#define BLE_SCAN_INTERVAL_FAST 3000     // Fast scan when transitioning (3s)
#define BLE_SCAN_INTERVAL_SLOW 10000    // Slow scan when stable (10s)
#define BLE_GRACE_PERIOD_MS 60000       // 1 minute grace period for disconnections
#define BLE_SIGNAL_THRESHOLD -80        // Minimum signal strength for detection

// ===== HARDWARE CONFIGURATION =====
// Display pins (ST7789 2.4" 320x240)
#define TFT_CS 5
#define TFT_RST 22
#define TFT_DC 21

// Button pins
#define BUTTON_A_PIN 16  // Blue button (Acknowledge)
#define BUTTON_B_PIN 4   // Red button (Busy)

// ===== SYSTEM SETTINGS =====
#define ENABLE_SERIAL_DEBUG true
#define SERIAL_BAUD_RATE 115200
#define ENABLE_DIAGNOSTICS true
#define ENABLE_WATCHDOG true
#define WATCHDOG_TIMEOUT_SECONDS 30
#define MAX_MESSAGE_LENGTH 512

// Time synchronization
#define TIME_ZONE_OFFSET 8              // GMT+8 Philippines
#define NTP_SERVER_PRIMARY "pool.ntp.org"
#define NTP_SERVER_SECONDARY "time.nist.gov"
#define NTP_SYNC_TIMEOUT 10000
#define NTP_UPDATE_INTERVAL 3600000     // 1 hour

// ===== MQTT TOPICS =====
#define MQTT_TOPIC_STATUS "consultease/faculty/" TOSTRING(FACULTY_ID) "/status"
#define MQTT_TOPIC_MESSAGES "consultease/faculty/" TOSTRING(FACULTY_ID) "/messages"
#define MQTT_TOPIC_RESPONSES "consultease/faculty/" TOSTRING(FACULTY_ID) "/responses"
#define MQTT_TOPIC_HEARTBEAT "consultease/faculty/" TOSTRING(FACULTY_ID) "/heartbeat"
#define MQTT_TOPIC_DIAGNOSTICS "consultease/faculty/" TOSTRING(FACULTY_ID) "/diagnostics"

// Legacy compatibility
#define MQTT_LEGACY_STATUS "faculty/" TOSTRING(FACULTY_ID) "/status"

// ===== DISPLAY CONFIGURATION =====
#define SCREEN_WIDTH 320
#define SCREEN_HEIGHT 240

// Color scheme
#define COLOR_WHITE      0x0000
#define COLOR_BLACK      0xFFFF
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

// UI Layout
#define MAIN_AREA_Y 35
#define MAIN_AREA_HEIGHT 140
#define STATUS_CENTER_X 160
#define STATUS_CENTER_Y 105
#define TOP_PANEL_HEIGHT 30
#define STATUS_PANEL_HEIGHT 25
#define STATUS_PANEL_Y 180
#define BOTTOM_PANEL_HEIGHT 30
#define BOTTOM_PANEL_Y 210

// ===== TIMING SETTINGS =====
#define BUTTON_DEBOUNCE_DELAY 20        // 20ms button debounce
#define CONFIRMATION_DISPLAY_TIME 3000  // 3s confirmation display
#define HEARTBEAT_INTERVAL 300000       // 5 minutes
#define UI_UPDATE_INTERVAL 5000         // 5 seconds
#define STATUS_UPDATE_INTERVAL 10000    // 10 seconds

// ===== HELPER MACROS =====
#define STRINGIFY(x) #x
#define TOSTRING(x) STRINGIFY(x)
#define DEBUG_PRINT(x) if(ENABLE_SERIAL_DEBUG) Serial.print(x)
#define DEBUG_PRINTLN(x) if(ENABLE_SERIAL_DEBUG) Serial.println(x)
#define DEBUG_PRINTF(format, ...) if(ENABLE_SERIAL_DEBUG) Serial.printf(format, ##__VA_ARGS__)

// ===== NETWORKMANAGER CONFIGURATION BUILDER =====
inline NetworkManager::NetworkConfig buildNetworkConfig() {
    NetworkManager::NetworkConfig config;
    
    // WiFi settings
    config.wifi_ssid = WIFI_SSID;
    config.wifi_password = WIFI_PASSWORD;
    config.wifi_timeout_ms = WIFI_TIMEOUT_MS;
    config.wifi_retry_interval_ms = WIFI_RETRY_INTERVAL_MS;
    config.wifi_max_retries = WIFI_MAX_RETRIES;
    config.wifi_power_save_enabled = WIFI_POWER_SAVE_ENABLED;
    
    // MQTT settings
    config.mqtt_server = MQTT_SERVER;
    config.mqtt_port = MQTT_PORT;
    config.mqtt_username = MQTT_USERNAME;
    config.mqtt_password = MQTT_PASSWORD;
    config.mqtt_client_id = String(MQTT_CLIENT_ID_PREFIX + String(FACULTY_ID) + "_" + String(random(0xffff), HEX)).c_str();
    config.mqtt_keepalive = MQTT_KEEPALIVE;
    config.mqtt_timeout_ms = MQTT_TIMEOUT_MS;
    config.mqtt_retry_interval_ms = MQTT_RETRY_INTERVAL_MS;
    config.mqtt_max_retries = MQTT_MAX_RETRIES;
    config.mqtt_buffer_size = MQTT_BUFFER_SIZE;
    
    // Advanced settings
    config.enable_diagnostics = ENABLE_DIAGNOSTICS;
    config.enable_watchdog = ENABLE_WATCHDOG;
    config.health_check_interval_ms = HEALTH_CHECK_INTERVAL_MS;
    config.connection_quality_threshold = CONNECTION_QUALITY_THRESHOLD;
    
    return config;
}

// ===== CONFIGURATION VALIDATION =====
inline bool validateRobustConfiguration() {
    bool valid = true;
    
    DEBUG_PRINTLN("🔍 Validating robust configuration...");
    
    // Check required settings
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
    
    // Check network timeouts
    if (WIFI_TIMEOUT_MS < 10000) {
        DEBUG_PRINTLN("⚠️ WARNING: WIFI_TIMEOUT_MS might be too short for reliable connection");
    }
    
    if (MQTT_BUFFER_SIZE < 512) {
        DEBUG_PRINTLN("⚠️ WARNING: MQTT_BUFFER_SIZE might be too small for consultation messages");
    }
    
    if (valid) {
        DEBUG_PRINTLN("✅ Robust configuration validation passed");
        DEBUG_PRINTF("   Faculty: %s (ID: %d)\n", FACULTY_NAME, FACULTY_ID);
        DEBUG_PRINTF("   Department: %s\n", FACULTY_DEPARTMENT);
        DEBUG_PRINTF("   WiFi: %s (Timeout: %ds)\n", WIFI_SSID, WIFI_TIMEOUT_MS/1000);
        DEBUG_PRINTF("   MQTT: %s:%d (Buffer: %d bytes)\n", MQTT_SERVER, MQTT_PORT, MQTT_BUFFER_SIZE);
        DEBUG_PRINTF("   Watchdog: %s\n", ENABLE_WATCHDOG ? "ENABLED" : "DISABLED");
        DEBUG_PRINTF("   Diagnostics: %s\n", ENABLE_DIAGNOSTICS ? "ENABLED" : "DISABLED");
    } else {
        DEBUG_PRINTLN("❌ Robust configuration validation FAILED");
    }
    
    return valid;
}

#endif // CONFIG_ROBUST_H 