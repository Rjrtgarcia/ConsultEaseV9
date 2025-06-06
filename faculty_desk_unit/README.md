# ConsultEase - Faculty Desk Unit

This is the firmware for the Faculty Desk Unit component of the ConsultEase system. This unit is installed at each faculty member's desk and shows consultation requests from students while automatically detecting the faculty's presence via MAC address-based BLE scanning.

## Hardware Requirements

- ESP32 Development Board (ESP32-WROOM-32 or similar)
- 2.4" TFT Display (ST7789 SPI interface)
- Faculty member's BLE device (smartphone, smartwatch, or dedicated BLE beacon)
- Power supply (USB or wall adapter)

## Pin Connections

### Display Connections (SPI)
| TFT Display Pin | ESP32 Pin |
|-----------------|-----------|
| MOSI/SDA        | GPIO 23   |
| MISO            | GPIO 19   |
| SCK/CLK         | GPIO 18   |
| CS              | GPIO 5    |
| DC              | GPIO 21   |
| RST             | GPIO 22   |
| VCC             | 3.3V      |
| GND             | GND       |

## Software Dependencies

The following libraries need to be installed via the Arduino Library Manager:

- WiFi
- PubSubClient (by Nick O'Leary)
- BLEDevice
- BLEServer
- BLEUtils
- BLE2902
- SPI
- Adafruit_GFX
- Adafruit_ST7789
- time
- WiFiUdp (built-in ESP32 library)
- NTPClient (by Fabrice Weinberg) - **NEW: For automatic time synchronization**
- NimBLE-Arduino (for BLE beacon)

## Setup and Configuration

1. Install the required libraries in Arduino IDE
2. Open `faculty_desk_unit.ino` in Arduino IDE
3. Update the configuration in `config.h`:
   - WiFi credentials (`WIFI_SSID` and `WIFI_PASSWORD`)
   - MQTT broker IP address (`MQTT_SERVER`)
   - Faculty ID and name (`FACULTY_ID` and `FACULTY_NAME`)
   - Faculty MAC addresses in the `FACULTY_MAC_ADDRESSES` array
   - NTP settings (optional - defaults to Philippines timezone)
4. Compile and upload to your ESP32

### NTP Time Synchronization Configuration

The faculty desk unit now includes automatic internet time synchronization. Configure these settings in `config.h`:

```cpp
// NTP Time Synchronization Configuration
#define NTP_SERVER_1 "pool.ntp.org"
#define NTP_SERVER_2 "time.nist.gov"
#define NTP_SERVER_3 "time.google.com"
#define TIMEZONE_OFFSET_HOURS 8  // Philippines timezone UTC+8
#define NTP_SYNC_INTERVAL_HOURS 1  // Sync every 1 hour
#define NTP_RETRY_INTERVAL_MINUTES 5  // Retry every 5 minutes if failed
#define NTP_MAX_RETRY_ATTEMPTS 3  // Maximum retry attempts before giving up
```

**Features:**
- Automatic time synchronization on startup
- Periodic sync every 1-2 hours to maintain accuracy
- Multiple NTP server fallback for reliability
- Visual indicators for sync status (green dot = synced, orange dot = fallback)
- Graceful fallback to ESP32 internal clock if NTP fails

### nRF51822 BLE Beacon Detection Configuration

The faculty desk unit uses **passive scanning** to detect nRF51822 BLE beacons for faculty presence detection. No pairing or connection is required.

#### Step 1: Find Your Beacon's MAC Address

**Option A: Use Beacon Discovery Utility (Recommended)**
1. Upload `beacon_discovery.ino` to your ESP32
2. Open Serial Monitor at 115200 baud
3. Power on your nRF51822 beacon near the ESP32
4. Look for devices marked with "🎯 LIKELY nRF51822 BEACON"
5. Copy the MAC address shown

**Option B: Use Discovery Mode in Main Firmware**
1. Set `#define BEACON_DISCOVERY_MODE true` in `config.h`
2. Upload main firmware and check serial output
3. Find your beacon in the detected devices list
4. Set `#define BEACON_DISCOVERY_MODE false` after finding MAC

#### Step 2: Configure Beacon Detection

Update `config.h` with your beacon's MAC address:

```cpp
// Replace with your actual nRF51822 beacon MAC address
#define FACULTY_BEACON_MAC "AA:BB:CC:DD:EE:FF"

// Adjust detection parameters if needed
#define BLE_RSSI_THRESHOLD -75  // Signal strength threshold (-75 dBm ≈ 5-10 meters)
#define BLE_SCAN_INTERVAL 5000  // Scan every 5 seconds
#define BLE_SCAN_DURATION 3     // Scan for 3 seconds each time
```

#### Detection Features:
- **No Pairing Required**: Uses passive BLE scanning
- **Automatic Detection**: Scans every 5 seconds for assigned beacon
- **Range Control**: Configurable RSSI threshold for detection range
- **Comprehensive Debugging**: Detailed serial output for troubleshooting
- **Reliable Detection**: Debouncing and timeout mechanisms for stable presence detection

#### Troubleshooting:
- See `BLE_BEACON_TROUBLESHOOTING.md` for detailed troubleshooting guide
- Use `beacon_discovery.ino` to verify beacon is advertising
- Check serial output for detection logs and error messages
- Adjust RSSI threshold for different detection ranges

## Testing

### NTP Time Synchronization Testing

To test the NTP functionality independently:

1. Upload the `test_ntp.ino` sketch to your ESP32
2. Open the Serial Monitor at 115200 baud
3. Observe the NTP synchronization process and results
4. The test will verify:
   - Primary NTP server connectivity
   - Alternative server fallback
   - Time formatting functions
   - Fallback mechanisms

### Full System Testing

To test the complete faculty desk unit, you can use the new BLE test script:

1. Make sure the central system is running
2. Make sure the MQTT broker is running
3. Run the BLE test script:
   ```bash
   python scripts/test_ble_connection.py test
   ```

This script will:
1. Simulate a BLE beacon
2. Simulate a faculty desk unit
3. Test MQTT communication between components
4. Verify proper status updates

You can also use the older test scripts in the `test_scripts` directory:
- On Windows: `test_scripts\test_faculty_desk_unit.bat`
- On Linux/macOS: `bash test_scripts/test_faculty_desk_unit.sh`

## Usage

1. The unit will automatically connect to WiFi and the MQTT broker
2. It will act as a BLE server waiting for BLE client connections
3. When a BLE client (faculty keychain) connects, the faculty status is set to "Available"
4. When the BLE client disconnects, the faculty status is set to "Unavailable"
5. Consultation requests from students will appear on the display

### BLE Always-Available Feature (Optional)

The faculty desk unit includes an optional "Always Available" mode that can be enabled in the config.h file:

```cpp
// Set to true to make faculty always appear as available regardless of BLE connection
#define ALWAYS_AVAILABLE true
```

When this feature is enabled:
- The faculty status is always shown as "Available" in the central system regardless of BLE connection
- The unit will still accept real BLE client connections, but won't change status when they disconnect
- Every 5 minutes, the unit sends a "keychain_connected" message to ensure the faculty remains available
- This feature is useful for faculty members who want to be always available for consultations

By default, this feature is disabled (set to `false`), meaning the faculty status will accurately reflect the actual BLE connection status.

### Database Integration

The central system has been updated to support the always-on BLE client feature:
- A new "always_available" field has been added to the Faculty model
- Faculty members with this flag set will always be shown as available
- The admin dashboard has been updated to allow setting this flag
- The Jeysibn faculty member is set to always available by default

To update an existing database with the new schema, run:
```
python scripts/update_faculty_schema.py
python scripts/update_jeysibn_faculty.py
```

## Manual Testing

You can also test the faculty desk unit manually:

1. Create a faculty member:
   ```
   python test_scripts/create_jeysibn_faculty.py
   ```

2. Simulate BLE beacon connected event:
   ```
   python test_scripts/simulate_ble_connection.py --broker <mqtt_broker_ip> --connect
   ```

3. Send a consultation request:
   ```
   python test_scripts/send_consultation_request.py
   ```

4. Simulate BLE beacon disconnected event:
   ```
   python test_scripts/simulate_ble_connection.py --broker <mqtt_broker_ip> --disconnect
   ```

Replace `<mqtt_broker_ip>` with the IP address of your MQTT broker.

## Troubleshooting

### MQTT Connection Issues

If the faculty desk unit is not connecting to the MQTT broker:
- Make sure the MQTT broker IP address is correct
- Make sure the MQTT broker is running
- Make sure the ESP32 is connected to the WiFi network

### BLE Issues

The faculty desk unit uses MAC address-based detection:
- Make sure the faculty member's BLE device (smartphone, smartwatch, etc.) is powered on
- Make sure the device is within range of the ESP32 (adjust `BLE_RSSI_THRESHOLD` if needed)
- Check the serial output for BLE scanning messages
- Verify the faculty member's device MAC address is correctly added to the `FACULTY_MAC_ADDRESSES` array
- The device will be detected even if it's not actively advertising (passive scanning)

### Display Issues

If the display is not working:
- Check the wiring connections
- Make sure the display is powered on
- Try running the test screen function to verify the display is working

## Integration with Central System

The Faculty Desk Unit communicates with the central system via MQTT. The central system publishes consultation requests to the following topics:

- `consultease/faculty/{faculty_id}/requests` - Main topic for consultation requests
- `professor/messages` - Alternative topic for backward compatibility

The Faculty Desk Unit publishes faculty status updates to:

- `consultease/faculty/{faculty_id}/status` - Faculty status updates
- `professor/status` - Alternative topic for backward compatibility

When the BLE client connects or disconnects, the Faculty Desk Unit publishes a status update with `keychain_connected` or `keychain_disconnected` message, which the central system uses to update the faculty status in the database.

## MQTT Message Format

### Consultation Request (from Central System to Faculty Desk Unit)
```
Student: Alice Johnson
Course: CS101
Request: Need help with assignment
```

### Status Update (from Faculty Desk Unit to Central System)
```
keychain_connected
```

or

```
keychain_disconnected
```

## UI Features

The faculty desk unit features a modern UI with the following elements:

- Gold accent bar on the left side
- Header with synchronized date and time display
- Time sync status indicator (green dot = NTP synced, orange dot = fallback time)
- Message area with title and content
- Status bar at the bottom
- National University Philippines color scheme (blue and gold)
- Smooth transitions between screens

### Time Display Features

- **Accurate Time**: Displays internet-synchronized time (Philippines timezone UTC+8)
- **Visual Sync Status**: Small colored dot indicates synchronization status
- **Automatic Updates**: Time display refreshes every minute
- **Fallback Support**: Gracefully handles network issues with fallback time sources
- **Format**: 12-hour format (HH:MM) with MM/DD/YYYY date format