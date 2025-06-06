# nRF51822 BLE Beacon Detection Troubleshooting Guide

## Overview

This guide helps resolve issues with nRF51822 BLE beacon detection in the ESP32 Faculty Desk Unit. The system uses **passive scanning** (no pairing required) to detect when faculty members carrying nRF51822 beacons are present at their desks.

## 🔍 How BLE Beacon Detection Works

### Detection Method: **Passive Scanning**
- ✅ **No pairing required** - ESP32 scans for advertising packets
- ✅ **No connection establishment** - Detection through advertisement only
- ✅ **One-way communication** - ESP32 listens, beacon advertises
- ✅ **MAC address filtering** - Only detects assigned faculty beacon

### Detection Process
1. **nRF51822 beacon** continuously advertises its presence
2. **ESP32 scans** for BLE devices every 5 seconds
3. **MAC address matching** - Compares detected MAC with configured beacon MAC
4. **RSSI filtering** - Only counts detections above threshold (-75 dBm)
5. **Debouncing** - Requires 2 consecutive detections for state change
6. **MQTT publishing** - Sends faculty presence status to central system

## 🚨 Common Issues and Solutions

### Issue 1: "Beacon MAC address not configured"

**Symptoms:**
```
*** WARNING: Beacon MAC address not configured! ***
*** Please update FACULTY_BEACON_MAC in config.h ***
```

**Solution:**
1. **Find your beacon's MAC address** using discovery mode:
   - Set `#define BEACON_DISCOVERY_MODE true` in `config.h`
   - Upload firmware and check serial output
   - Look for your nRF51822 beacon in the device list
   - Note the MAC address (format: XX:XX:XX:XX:XX:XX)

2. **Update configuration:**
   - Set `#define FACULTY_BEACON_MAC "XX:XX:XX:XX:XX:XX"` with actual MAC
   - Set `#define BEACON_DISCOVERY_MODE false`
   - Re-upload firmware

### Issue 2: "No BLE devices found"

**Symptoms:**
```
Total BLE devices found: 0
⚠️ ISSUE: No BLE devices found - check beacon is powered and advertising
```

**Possible Causes & Solutions:**

#### A. Beacon Not Powered/Advertising
- **Check beacon battery** - Replace if low
- **Verify beacon is programmed** - Should be advertising continuously
- **Check beacon LED** - Should blink indicating advertising
- **Test with phone** - Use BLE scanner app to verify beacon is visible

#### B. ESP32 BLE Issues
- **Reset ESP32** - Power cycle the device
- **Check BLE initialization** - Look for "BLE Scanner initialized successfully"
- **Verify ESP32 BLE capability** - Some ESP32 variants have BLE disabled

#### C. Range/Interference Issues
- **Move beacon closer** - Start with 1-2 meter distance
- **Check for interference** - WiFi, other BLE devices, metal objects
- **Test in open area** - Avoid obstacles between beacon and ESP32

### Issue 3: "Beacon not in range or MAC address mismatch"

**Symptoms:**
```
Total BLE devices found: 5
❌ Target beacon NOT detected
⚠️ ISSUE: Beacon not in range or MAC address mismatch
```

**Solutions:**

#### A. MAC Address Mismatch
- **Verify MAC address** - Use discovery mode to confirm beacon MAC
- **Check format** - Ensure correct format (XX:XX:XX:XX:XX:XX)
- **Case sensitivity** - MAC addresses are case-insensitive
- **Colon placement** - Must use colons as separators

#### B. RSSI Too Weak
- **Check RSSI threshold** - Default is -75 dBm
- **Move beacon closer** - Reduce distance to ESP32
- **Adjust threshold** - Lower value (e.g., -85 dBm) for longer range
- **Check beacon transmission power** - Increase if configurable

### Issue 4: "Target beacon found but RSSI too weak"

**Symptoms:**
```
*** TARGET BEACON FOUND: XX:XX:XX:XX:XX:XX | RSSI: -82 dBm | Threshold: -75 dBm | RSSI TOO WEAK
```

**Solutions:**
1. **Reduce distance** between beacon and ESP32
2. **Adjust RSSI threshold** in `config.h`:
   ```cpp
   #define BLE_RSSI_THRESHOLD -85  // Lower value = longer range
   ```
3. **Remove obstacles** between beacon and ESP32
4. **Check beacon battery** - Low battery reduces transmission power

## 🔧 Configuration Parameters

### Optimal Settings for nRF51822 Beacons

```cpp
// Scan timing - Balance between responsiveness and power consumption
#define BLE_SCAN_INTERVAL 5000  // 5 seconds between scans
#define BLE_SCAN_DURATION 3     // 3 seconds scan duration

// Detection range - Adjust based on desk/room size
#define BLE_RSSI_THRESHOLD -75  // ~5-10 meter range
// -60 dBm = ~2-3 meters (close range)
// -75 dBm = ~5-10 meters (desk range)
// -85 dBm = ~10-15 meters (room range)

// Reliability settings
#define MAC_DETECTION_DEBOUNCE 2      // 2 consecutive detections
#define MAC_DETECTION_TIMEOUT 30000   // 30 seconds timeout
```

### Range vs RSSI Guidelines

| RSSI Value | Approximate Range | Use Case |
|------------|------------------|----------|
| -40 to -60 dBm | 1-3 meters | Very close detection |
| -60 to -75 dBm | 3-8 meters | **Desk detection (recommended)** |
| -75 to -85 dBm | 8-15 meters | Room detection |
| -85 to -95 dBm | 15+ meters | Long range (unreliable) |

## 🧪 Testing Procedures

### Step 1: Discovery Mode Testing

1. **Enable discovery mode:**
   ```cpp
   #define BEACON_DISCOVERY_MODE true
   ```

2. **Upload firmware and monitor serial output**

3. **Expected output:**
   ```
   BLE Device: XX:XX:XX:XX:XX:XX | RSSI: -65 dBm | Name: Unknown
   BLE Device: YY:YY:YY:YY:YY:YY | RSSI: -78 dBm | Name: iPhone
   BLE Device: ZZ:ZZ:ZZ:ZZ:ZZ:ZZ | RSSI: -45 dBm | Name: nRF51822
   ```

4. **Identify your beacon** - Look for nRF51822 or unknown devices with strong RSSI

### Step 2: Beacon Configuration Testing

1. **Configure beacon MAC:**
   ```cpp
   #define FACULTY_BEACON_MAC "ZZ:ZZ:ZZ:ZZ:ZZ:ZZ"  // Your beacon's MAC
   #define BEACON_DISCOVERY_MODE false
   ```

2. **Upload firmware and test detection**

3. **Expected output:**
   ```
   ✅ TARGET BEACON DETECTED!
      Faculty: Jeysibn
      MAC: ZZ:ZZ:ZZ:ZZ:ZZ:ZZ
      Detection Count: 1
   ```

### Step 3: Range Testing

1. **Start close** - Place beacon 1 meter from ESP32
2. **Verify detection** - Should see consistent detections
3. **Gradually increase distance** - Test at 2m, 5m, 10m
4. **Note RSSI values** - Adjust threshold as needed

### Step 4: Reliability Testing

1. **Leave beacon in position** for 10 minutes
2. **Monitor detection consistency** - Should maintain presence status
3. **Test absence detection** - Remove beacon and verify timeout
4. **Test re-detection** - Return beacon and verify quick detection

## 📊 Serial Output Analysis

### Successful Detection Example
```
=== BLE SCAN START ===
🔍 Scanning for Jeysibn's nRF51822 beacon...
Target MAC: AA:BB:CC:DD:EE:FF
RSSI Threshold: -75 dBm

BLE Device: AA:BB:CC:DD:EE:FF | RSSI: -68 dBm | Name: Unknown
*** TARGET BEACON FOUND: AA:BB:CC:DD:EE:FF | RSSI: -68 dBm | Threshold: -75 dBm | RSSI OK

--- SCAN RESULTS ---
Scan Duration: 3247 ms
Total BLE devices found: 3
✅ TARGET BEACON DETECTED!
   Faculty: Jeysibn
   MAC: AA:BB:CC:DD:EE:FF
   Detection Count: 1

--- SCAN STATISTICS ---
Current Faculty Status: PRESENT
Detection Count: 1
Absence Count: 0
Last Detection: 0 seconds ago
=== BLE SCAN END ===
```

### Failed Detection Example
```
=== BLE SCAN START ===
🔍 Scanning for Jeysibn's nRF51822 beacon...
Target MAC: AA:BB:CC:DD:EE:FF
RSSI Threshold: -75 dBm

BLE Device: 11:22:33:44:55:66 | RSSI: -45 dBm | Name: iPhone
BLE Device: 77:88:99:AA:BB:CC | RSSI: -82 dBm | Name: Unknown

--- SCAN RESULTS ---
Scan Duration: 3156 ms
Total BLE devices found: 2
❌ Target beacon NOT detected
   Looking for: AA:BB:CC:DD:EE:FF
   Absence Count: 1
   ⚠️ ISSUE: Beacon not in range or MAC address mismatch

--- SCAN STATISTICS ---
Current Faculty Status: ABSENT
Detection Count: 0
Absence Count: 1
Last Detection: Never
=== BLE SCAN END ===
```

## 🔧 Advanced Troubleshooting

### nRF51822 Beacon Verification

1. **Use smartphone BLE scanner app:**
   - Install "BLE Scanner" or "nRF Connect"
   - Scan for devices
   - Verify your beacon appears with correct MAC address

2. **Check beacon advertising parameters:**
   - Advertising interval should be 100-1000ms
   - Transmission power should be 0 dBm or higher
   - Device should be in advertising mode (not connectable mode)

3. **Verify beacon programming:**
   - Ensure beacon firmware is properly flashed
   - Check that beacon is not in sleep mode
   - Verify advertising payload is not corrupted

### ESP32 BLE Stack Issues

1. **BLE initialization problems:**
   ```cpp
   // Add to setup() for debugging
   Serial.println("ESP32 BLE MAC: " + String(BLEDevice::getAddress().toString().c_str()));
   ```

2. **Memory issues:**
   - Monitor free heap: `ESP.getFreeHeap()`
   - Restart ESP32 if heap gets too low
   - Reduce scan frequency if memory issues persist

3. **WiFi interference:**
   - BLE and WiFi share the 2.4GHz band
   - Try different WiFi channels
   - Consider using 5GHz WiFi if available

## ✅ Success Indicators

When everything is working correctly:

1. **Startup logs show:**
   ```
   ✅ BLE Scanner initialized successfully
   === Ready for nRF51822 Beacon Detection ===
   ```

2. **Detection logs show:**
   ```
   ✅ TARGET BEACON DETECTED!
   Current Faculty Status: PRESENT
   ```

3. **MQTT messages published:**
   ```
   Published Jeysibn present status
   ```

4. **Central system receives updates:**
   - Faculty status changes to "Available"
   - Admin dashboard shows faculty as present

## 📞 Getting Help

If you're still having issues:

1. **Capture serial output** - Save complete startup and scan logs
2. **Test with phone** - Verify beacon is visible to other devices
3. **Check beacon specifications** - Confirm it's an nRF51822 or compatible
4. **Verify power supply** - Ensure ESP32 has stable power
5. **Test different locations** - Try various positions and distances

The enhanced firmware now provides comprehensive debugging information to help identify and resolve any beacon detection issues.
