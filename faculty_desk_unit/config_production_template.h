/**
 * ConsultEase - Faculty Desk Unit Production Configuration Template
 *
 * SECURITY NOTICE: This is a template for production deployment.
 * Copy this file to config.h and update all values marked with ⚠️
 * 
 * NEVER commit actual credentials to version control!
 */

#ifndef CONFIG_H
#define CONFIG_H

// ============================================================================
// SECURITY CONFIGURATION - MUST BE UPDATED FOR PRODUCTION
// ============================================================================

// WiFi Configuration
// ⚠️ CRITICAL: Update these credentials before production deployment!
#define WIFI_SSID "YOUR_PRODUCTION_WIFI_NETWORK"  // ⚠️ REQUIRED: Replace with actual WiFi SSID
#define WIFI_PASSWORD "YOUR_STRONG_WIFI_PASSWORD"  // ⚠️ REQUIRED: Use strong WiFi password (min 12 chars)

// MQTT Configuration with Authentication
#define MQTT_SERVER "192.168.1.100"  // ⚠️ REQUIRED: Replace with your MQTT broker IP
#define MQTT_PORT 1883
#define MQTT_USERNAME "esp32_faculty_unit"  // ⚠️ REQUIRED: Unique MQTT username per unit
#define MQTT_PASSWORD "STRONG_MQTT_PASSWORD_HERE"  // ⚠️ REQUIRED: Strong password (min 16 chars)

// Faculty Configuration
#define FACULTY_ID 1  // ⚠️ REQUIRED: Update with actual faculty ID from database
#define FACULTY_NAME "Dr. Faculty Name"  // ⚠️ REQUIRED: Update with actual faculty name
#define FACULTY_DEPARTMENT "Department Name"  // ⚠️ REQUIRED: Update with actual department

// BLE Beacon Configuration
#define FACULTY_BEACON_MAC "AA:BB:CC:DD:EE:FF"  // ⚠️ REQUIRED: Replace with actual beacon MAC

// ============================================================================
// SYSTEM CONFIGURATION - Review and adjust as needed
// ============================================================================

// BLE Configuration - Optimized for nRF51822 Beacon Detection
#define BLE_SCAN_INTERVAL 5000  // Scan interval in milliseconds
#define BLE_SCAN_DURATION 3     // Scan duration in seconds
#define BLE_RSSI_THRESHOLD -75  // RSSI threshold for presence detection

// Beacon Discovery Mode - Set to false for production
#define BEACON_DISCOVERY_MODE false  // Must be false in production

// MAC Address Detection Settings
#define MAC_DETECTION_TIMEOUT 30000   // Time in ms to consider faculty absent
#define MAC_SCAN_ACTIVE true          // Use active scanning
#define MAC_DETECTION_DEBOUNCE 2      // Consecutive scans needed for state change

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
#define MQTT_TOPIC_STATUS "consultease/faculty/%d/status"
#define MQTT_TOPIC_MAC_STATUS "consultease/faculty/%d/mac_status"
#define MQTT_TOPIC_REQUESTS "consultease/faculty/%d/requests"
#define MQTT_TOPIC_MESSAGES "consultease/faculty/%d/messages"
#define MQTT_TOPIC_NOTIFICATIONS "consultease/system/notifications"

// Legacy MQTT Topics - For backward compatibility
#define MQTT_LEGACY_STATUS "professor/status"
#define MQTT_LEGACY_MESSAGES "professor/messages"

// NTP Time Synchronization Configuration
#define NTP_SERVER_1 "pool.ntp.org"
#define NTP_SERVER_2 "time.nist.gov"
#define NTP_SERVER_3 "time.google.com"
#define TIMEZONE_OFFSET_HOURS 8  // Philippines timezone UTC+8
#define NTP_SYNC_INTERVAL_HOURS 1  // Sync every 1 hour
#define NTP_RETRY_INTERVAL_MINUTES 5  // Retry every 5 minutes if failed
#define NTP_MAX_RETRY_ATTEMPTS 3  // Maximum retry attempts

// Security Configuration
#define ENABLE_WATCHDOG true  // Enable hardware watchdog
#define ENABLE_SECURE_BOOT false  // Enable if ESP32 supports secure boot
#define ENABLE_FLASH_ENCRYPTION false  // Enable if ESP32 supports flash encryption

// Debug Configuration - DISABLE IN PRODUCTION
#define DEBUG_ENABLED false  // ⚠️ MUST BE FALSE IN PRODUCTION
#define SERIAL_DEBUG false   // ⚠️ MUST BE FALSE IN PRODUCTION

// ============================================================================
// PRODUCTION DEPLOYMENT CHECKLIST
// ============================================================================
/*
Before deploying to production, ensure:

1. ✅ WiFi credentials updated (WIFI_SSID, WIFI_PASSWORD)
2. ✅ MQTT broker IP and credentials updated (MQTT_SERVER, MQTT_USERNAME, MQTT_PASSWORD)
3. ✅ Faculty information updated (FACULTY_ID, FACULTY_NAME, FACULTY_DEPARTMENT)
4. ✅ Beacon MAC address updated (FACULTY_BEACON_MAC)
5. ✅ Debug mode disabled (DEBUG_ENABLED = false, SERIAL_DEBUG = false)
6. ✅ Beacon discovery mode disabled (BEACON_DISCOVERY_MODE = false)
7. ✅ Strong passwords used (min 12 chars for WiFi, min 16 chars for MQTT)
8. ✅ Unique MQTT username per unit
9. ✅ Network security configured (WPA2/WPA3 for WiFi, TLS for MQTT if available)
10. ✅ Physical security measures in place

SECURITY REMINDERS:
- Never commit actual credentials to version control
- Use environment-specific configuration files
- Regularly rotate passwords
- Monitor for unauthorized access
- Keep firmware updated
*/

#endif // CONFIG_H
