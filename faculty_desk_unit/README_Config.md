# Faculty Desk Unit - Configuration Setup

## Quick Setup Guide

### 1. Configure Your Unit

Copy `config_simple_template.h` to `config.h` and edit these essential settings:

```cpp
// ===== CHANGE THESE FOR EACH FACULTY UNIT =====
#define FACULTY_ID 1                           // Unique ID (1, 2, 3, etc.)
#define FACULTY_NAME "Your Name"               // Professor's name  
#define FACULTY_DEPARTMENT "Your Department"   // Department name
#define FACULTY_BEACON_MAC "XX:XX:XX:XX:XX:XX" // Your iBeacon MAC address

// ===== CHANGE THESE FOR YOUR NETWORK =====
#define WIFI_SSID "Your_WiFi_Name"             // WiFi network name
#define WIFI_PASSWORD "Your_WiFi_Password"     // WiFi password
#define MQTT_SERVER "192.168.1.100"           // MQTT broker IP address
```

### 2. Hardware Setup

Default pin configuration (change in config.h if different):
- **Blue Button (Acknowledge)**: Pin 15
- **Red Button (Busy)**: Pin 4  
- **Display CS**: Pin 5
- **Display RST**: Pin 22
- **Display DC**: Pin 21

### 3. Features

✅ **Simplified Configuration** - Only 8 essential settings to change
✅ **Auto-Generated MQTT Topics** - Based on FACULTY_ID
✅ **Built-in Validation** - Checks configuration on startup
✅ **Grace Period BLE** - 1-minute reconnection window
✅ **Enhanced MQTT Diagnostics** - Better error reporting

### 4. MQTT Topics (Auto-Generated)

For FACULTY_ID = 1:
- Status: `consultease/faculty/1/status`
- Messages: `consultease/faculty/1/messages`  
- Responses: `consultease/faculty/1/responses`
- Heartbeat: `consultease/faculty/1/heartbeat`

### 5. Configuration Validation

The system validates your configuration on startup:
- Faculty ID must be >= 1
- Beacon MAC must be 17 characters (XX:XX:XX:XX:XX:XX format)
- WiFi SSID cannot be empty
- MQTT server cannot be empty
- Button pins must be different

### 6. Multiple Faculty Units

For additional units, just change:
1. `FACULTY_ID` (increment: 1, 2, 3, etc.)
2. `FACULTY_NAME` 
3. `FACULTY_DEPARTMENT`
4. `FACULTY_BEACON_MAC` (each professor's unique beacon)

MQTT topics will automatically update based on the Faculty ID.

### 7. Advanced Settings

Most settings use sensible defaults and don't need changes:
- **BLE Grace Period**: 60 seconds
- **Scan Intervals**: 2s (searching) / 8s (monitoring)
- **WiFi Timeout**: 20 seconds
- **Button Debounce**: 20ms
- **Heartbeat**: Every 5 minutes

### 8. Troubleshooting

Check the Serial Monitor (115200 baud) for:
- ✅ Configuration validation results
- 🔍 Detailed MQTT connection diagnostics  
- 📡 Enhanced BLE scanning status
- 🌐 Network connectivity information

---

## Simplified vs Original Config

**Before**: 283 lines with complex settings
**After**: ~140 lines with clear sections

**Benefits**:
- Easier deployment of multiple units
- Reduced configuration errors
- Better organization with clear "CHANGE" vs "DO NOT CHANGE" sections
- Auto-generated MQTT topics prevent conflicts 