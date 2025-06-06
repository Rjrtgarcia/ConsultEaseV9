/**
 * ConsultEase - Faculty Desk Unit Configuration
 * Unit 3 Configuration Template
 * 
 * Copy this file to config.h and update with actual values
 * Update these values to match your specific setup.
 */

#ifndef CONFIG_H
#define CONFIG_H

// WiFi Configuration
#define WIFI_SSID "ConsultEase"
#define WIFI_PASSWORD "Admin123"

// MQTT Configuration
#define MQTT_SERVER "172.20.10.8"  // Update with your MQTT broker IP
#define MQTT_PORT 1883
#define MQTT_USERNAME ""  // Leave empty if not using authentication
#define MQTT_PASSWORD ""  // Leave empty if not using authentication

// Faculty Configuration - Unit 3
#define FACULTY_ID 3  // This should match the faculty ID in the database
#define FACULTY_NAME "Prof. Robert Chen"  // REPLACE WITH ACTUAL FACULTY NAME
#define FACULTY_DEPARTMENT "Computer Science"  // REPLACE WITH ACTUAL DEPARTMENT

// BLE Configuration - MAC Address Detection for nRF51822 Beacons
#define BLE_SCAN_INTERVAL 3000  // Scan interval in milliseconds (optimized for nRF51822)
#define BLE_SCAN_DURATION 5     // Scan duration in seconds (longer for better beacon detection)
#define BLE_RSSI_THRESHOLD -85  // RSSI threshold for presence detection (adjusted for beacon range)

// Faculty BLE Beacon Configuration - nRF51822 Beacon
// Each ESP32 unit is configured with only its assigned faculty member's beacon MAC address
// Format: "XX:XX:XX:XX:XX:XX" (case insensitive)
// IMPORTANT: Update this with the actual nRF51822 beacon MAC address for this specific faculty member
#define FACULTY_BEACON_MAC "AA:BB:CC:DD:EE:03"  // REPLACE WITH ACTUAL BEACON MAC ADDRESS

// MAC Address Detection Settings - Optimized for nRF51822 Beacons
#define MAC_DETECTION_TIMEOUT 45000    // Time in ms to consider faculty absent (increased for beacon reliability)
#define MAC_SCAN_ACTIVE true           // Use active scanning (better for beacon detection)
#define MAC_DETECTION_DEBOUNCE 2       // Number of consecutive scans needed (reduced for faster response)

// Display Configuration
#define TFT_ROTATION 1  // 0=Portrait, 1=Landscape, 2=Inverted Portrait, 3=Inverted Landscape

// Color Scheme - National University Philippines
#define NU_BLUE      0x0015      // Dark blue (navy) - Primary color
#define NU_GOLD      0xFE60      // Gold/Yellow - Secondary color
#define NU_DARKBLUE  0x000B      // Darker blue for contrasts
#define NU_LIGHTGOLD 0xF710      // Lighter gold for highlights
#define TFT_WHITE    0xFFFF      // White for text
#define TFT_BLACK    0x0000      // Black for backgrounds

// UI Colors
#define TFT_BG       NU_BLUE         // Background color
#define TFT_TEXT     TFT_WHITE       // Text color
#define TFT_HEADER   NU_DARKBLUE     // Header color
#define TFT_ACCENT   NU_GOLD         // Accent color
#define TFT_HIGHLIGHT NU_LIGHTGOLD   // Highlight color

// MQTT Topics - Standardized format
#define MQTT_TOPIC_STATUS "consultease/faculty/%d/status"  // %d will be replaced with FACULTY_ID
#define MQTT_TOPIC_MAC_STATUS "consultease/faculty/%d/mac_status"  // %d will be replaced with FACULTY_ID
#define MQTT_TOPIC_REQUESTS "consultease/faculty/%d/requests"  // %d will be replaced with FACULTY_ID
#define MQTT_TOPIC_MESSAGES "consultease/faculty/%d/messages"  // %d will be replaced with FACULTY_ID
#define MQTT_TOPIC_NOTIFICATIONS "consultease/system/notifications"

// Legacy MQTT Topics - For backward compatibility
#define MQTT_LEGACY_STATUS "professor/status"
#define MQTT_LEGACY_MESSAGES "professor/messages"

// Debug Configuration
#define DEBUG_ENABLED true  // Set to false to disable debug output

#endif // CONFIG_H
