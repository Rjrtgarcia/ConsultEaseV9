# MAC Address-Based Faculty Detection

This document describes the implementation of MAC address-based faculty detection for the ConsultEase Faculty Desk Unit.

## Overview

The faculty desk unit has been modified to detect faculty presence using Bluetooth Low Energy (BLE) MAC address scanning instead of the previous connection-based approach. This provides more reliable detection and supports multiple faculty members.

## Key Changes

### 1. Configuration (config.h)
- Added `BLE_DETECTION_MODE_MAC_ADDRESS` flag to enable MAC address detection
- Added `FACULTY_MAC_ADDRESSES` array to store known faculty device MAC addresses
- Added MAC detection settings for timeout, scanning parameters, and debouncing

### 2. Faculty Desk Unit Code (faculty_desk_unit.ino)
- **BLE Scanner Mode**: Converted from BLE server to BLE scanner
- **MAC Address Detection**: Scans for known faculty MAC addresses
- **Debouncing Logic**: Requires multiple consecutive detections to confirm presence/absence
- **MQTT Communication**: Publishes detailed MAC status information
- **Backward Compatibility**: Maintains legacy BLE server mode when MAC detection is disabled

### 3. Central System Updates
- **Enhanced Validators**: Updated BLE ID validation to accept both UUID and MAC address formats
- **Faculty Model**: Added MAC address normalization and validation methods
- **MQTT Topics**: Added new `mac_status` topic for detailed MAC address information
- **Faculty Controller**: Added handler for MAC address status updates with automatic BLE ID updating

## Configuration

### Faculty MAC Addresses
Edit the `FACULTY_MAC_ADDRESSES` array in `faculty_desk_unit.ino`:

```cpp
const char* FACULTY_MAC_ADDRESSES[MAX_FACULTY_MAC_ADDRESSES] = {
  "11:22:33:44:55:66",  // Dr. John Smith's device
  "AA:BB:CC:DD:EE:FF",  // Dr. Jane Doe's device  
  "4F:AF:C2:01:1F:B5",  // Prof. Robert Chen's device
  "12:34:56:78:9A:BC",  // Jeysibn's device (matches FACULTY_ID 3)
  ""                    // Empty slot for additional faculty
};
```

### Detection Parameters
Adjust these settings in `config.h`:

- `BLE_SCAN_INTERVAL`: How often to scan (default: 5000ms)
- `BLE_SCAN_DURATION`: How long each scan lasts (default: 3 seconds)
- `BLE_RSSI_THRESHOLD`: Minimum signal strength (default: -80 dBm)
- `MAC_DETECTION_TIMEOUT`: Timeout for faculty absence (default: 30 seconds)
- `MAC_DETECTION_DEBOUNCE`: Required consecutive detections (default: 3)

## MQTT Communication

### New Topics
- `consultease/faculty/{faculty_id}/mac_status`: Detailed MAC address status updates

### Message Format
```json
{
  "status": "faculty_present|faculty_absent",
  "mac": "12:34:56:78:9A:BC",
  "timestamp": 1234567890
}
```

### Legacy Compatibility
The system continues to publish to legacy topics:
- `professor/status`: "keychain_connected"/"keychain_disconnected"
- `consultease/faculty/{faculty_id}/status`: Same legacy messages

## Database Integration

### Faculty Table
The `ble_id` field now stores MAC addresses in normalized format (uppercase with colons).

### Sample Data
The system creates sample faculty with MAC addresses:
- Dr. John Smith: `11:22:33:44:55:66`
- Dr. Jane Doe: `AA:BB:CC:DD:EE:FF`
- Prof. Robert Chen: `4F:AF:C2:01:1F:B5`
- Jeysibn: `12:34:56:78:9A:BC`

## Testing

### 1. Enable MAC Detection
Set `BLE_DETECTION_MODE_MAC_ADDRESS` to `true` in `config.h`

### 2. Configure Faculty MAC
Add your device's MAC address to the `FACULTY_MAC_ADDRESSES` array

### 3. Monitor Serial Output
The ESP32 will log:
- BLE scan results
- Faculty device detections
- Status changes
- MQTT publications

### 4. Check Central System
Monitor the central system logs for:
- MAC status message reception
- Faculty status updates
- Database BLE ID updates

## Troubleshooting

### Common Issues

1. **No Faculty Detected**
   - Verify MAC address format (XX:XX:XX:XX:XX:XX)
   - Check RSSI threshold (device might be too far)
   - Ensure device is advertising BLE

2. **Frequent Status Changes**
   - Increase `MAC_DETECTION_DEBOUNCE` value
   - Adjust `BLE_RSSI_THRESHOLD` for more stable detection
   - Check for interference

3. **Legacy Mode Fallback**
   - Set `BLE_DETECTION_MODE_MAC_ADDRESS` to `false`
   - System will revert to connection-based detection

### Debug Information
Enable debug output by monitoring the serial console at 115200 baud. The system provides detailed logging of:
- BLE scanning operations
- MAC address matching
- Status change decisions
- MQTT message publishing

## Benefits

1. **Multi-Faculty Support**: Can detect multiple faculty members
2. **No Pairing Required**: Works with any BLE-enabled device
3. **Reliable Detection**: Less prone to connection issues
4. **Automatic Configuration**: Updates faculty BLE IDs automatically
5. **Backward Compatible**: Maintains existing functionality

## Security Considerations

- MAC addresses are transmitted in plain text over MQTT
- Consider implementing encryption for sensitive deployments
- MAC addresses can be randomized by modern devices (iOS/Android privacy features)
- For production use, consider using dedicated BLE beacons with fixed MAC addresses
