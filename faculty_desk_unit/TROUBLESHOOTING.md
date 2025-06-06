# Faculty Desk Unit - Troubleshooting Guide

## Compilation Issues

### 1. BLE Compilation Error: "conversion from 'BLEScanResults*' to non-scalar type 'BLEScanResults' requested"

**Problem**: The BLE scanning code was trying to assign a pointer to a non-pointer variable.

**Solution**: ✅ **FIXED** - Updated the code to properly handle the pointer:
```cpp
// OLD (incorrect):
BLEScanResults foundDevices = pBLEScan->start(BLE_SCAN_DURATION, false);

// NEW (correct):
BLEScanResults* foundDevices = pBLEScan->start(BLE_SCAN_DURATION, false);
```

### 2. Missing Variable Declarations

**Problem**: References to undefined variables like `deviceConnected`, `pCharacteristic`, `lastBleSignalTime`.

**Solution**: ✅ **FIXED** - Removed references to BLE server variables that were eliminated during the MAC address detection refactoring.

### 3. Missing Color Definitions

**Problem**: Compilation errors for undefined color constants like `ST77XX_GREEN`, `ST77XX_ORANGE`.

**Solution**: ✅ **FIXED** - Added missing color definitions:
```cpp
#define ST77XX_GREEN 0x07E0      // Green for success indicators
#define ST77XX_RED   0xF800      // Red for error indicators
#define ST77XX_ORANGE 0xFD20     // Orange for warning indicators
#define ST77XX_YELLOW 0xFFE0     // Yellow for warning indicators
```

### 4. Library Dependencies

**Required Libraries** (install via Arduino Library Manager):
- WiFi (built-in)
- PubSubClient (by Nick O'Leary)
- BLEDevice (built-in ESP32)
- SPI (built-in)
- Adafruit_GFX
- Adafruit_ST7789
- WiFiUdp (built-in ESP32)
- **NTPClient** (by Fabrice Weinberg) - **REQUIRED FOR NTP FUNCTIONALITY**

**Installation Steps**:
1. Open Arduino IDE
2. Go to Tools → Manage Libraries
3. Search for "NTPClient" by Fabrice Weinberg
4. Click Install

## NTP Time Synchronization Issues

### 1. NTP Sync Fails on Startup

**Symptoms**:
- Orange dot indicator instead of green
- Serial output shows "NTP synchronization failed"
- Time display shows fallback time

**Troubleshooting Steps**:

1. **Check WiFi Connection**:
   ```cpp
   // Monitor serial output for:
   WiFi connected
   IP address: 192.168.x.x
   ```

2. **Verify NTP Server Accessibility**:
   - Try pinging NTP servers from your network
   - Check firewall settings
   - Verify internet connectivity

3. **Check Configuration**:
   ```cpp
   // In config.h, verify:
   #define NTP_SERVER_1 "pool.ntp.org"
   #define TIMEZONE_OFFSET_HOURS 8  // Correct for your timezone
   ```

4. **Monitor Serial Debug Output**:
   ```
   Initializing NTP client...
   Attempting NTP time synchronization...
   Primary NTP server failed, trying alternative servers...
   ```

### 2. Time Display Shows Wrong Timezone

**Problem**: Time is displayed but in wrong timezone.

**Solution**: Update timezone configuration in `config.h`:
```cpp
// For Philippines (UTC+8):
#define TIMEZONE_OFFSET_HOURS 8

// For other timezones:
// UTC-5 (Eastern US): #define TIMEZONE_OFFSET_HOURS -5
// UTC+1 (Central Europe): #define TIMEZONE_OFFSET_HOURS 1
// UTC+9 (Japan): #define TIMEZONE_OFFSET_HOURS 9
```

### 3. Periodic Sync Failures

**Symptoms**:
- Initial sync works but periodic syncs fail
- Status indicator changes from green to orange over time

**Solutions**:

1. **Adjust Sync Intervals**:
   ```cpp
   // In config.h, increase intervals:
   #define NTP_SYNC_INTERVAL_HOURS 2  // Sync every 2 hours instead of 1
   #define NTP_RETRY_INTERVAL_MINUTES 10  // Retry every 10 minutes instead of 5
   ```

2. **Check Network Stability**:
   - Monitor WiFi connection stability
   - Check for network congestion during sync times

3. **Verify Server Response**:
   - Try different NTP servers
   - Use regional NTP servers for better reliability

### 4. Memory Issues with NTP

**Symptoms**:
- ESP32 resets during NTP operations
- Compilation warnings about memory usage

**Solutions**:

1. **Optimize Memory Usage**:
   ```cpp
   // Reduce buffer sizes if needed
   char timeStringBuff[20];  // Instead of [50]
   char dateStringBuff[15];  // Instead of [50]
   ```

2. **Monitor Heap Memory**:
   ```cpp
   Serial.print("Free heap: ");
   Serial.println(ESP.getFreeHeap());
   ```

## Display Issues

### 1. Time Sync Indicator Not Visible

**Problem**: Green/orange status dot not appearing on display.

**Solutions**:

1. **Check Display Initialization**:
   ```cpp
   // Verify display is properly initialized
   tft.init(240, 320);
   tft.setRotation(1);
   ```

2. **Verify Color Definitions**:
   ```cpp
   // Ensure colors are defined
   #define ST77XX_GREEN 0x07E0
   #define ST77XX_ORANGE 0xFD20
   ```

3. **Check Indicator Position**:
   ```cpp
   // Adjust position if needed
   int statusX = tft.width() - 15;  // Move left if cut off
   int statusY = 8;                 // Adjust vertical position
   ```

### 2. Time Display Format Issues

**Problem**: Time or date not displaying correctly.

**Solutions**:

1. **Check Format Conversion**:
   ```cpp
   // Verify time format conversion
   String timeStr = getFormattedTime();
   if (timeStr.length() >= 5) {
       timeStr = timeStr.substring(0, 5); // HH:MM
   }
   ```

2. **Debug Time Values**:
   ```cpp
   // Add debug output
   Serial.print("Raw time: ");
   Serial.println(timeClient.getFormattedTime());
   Serial.print("Display time: ");
   Serial.println(timeStr);
   ```

## Testing and Validation

### 1. Use the Compilation Test

Before uploading the main firmware, test compilation with the provided test sketch:

1. Upload `compile_test.ino` to your ESP32
2. Monitor serial output for test results
3. Verify all components initialize correctly

### 2. Use the NTP Test Sketch

For isolated NTP testing:

1. Upload `test_ntp.ino` to your ESP32
2. Monitor serial output for NTP sync results
3. Verify time synchronization works independently

### 3. Monitor Serial Output

Enable detailed debugging by monitoring serial output at 115200 baud:

```
=== Expected Output ===
Starting National University Philippines Desk Unit
WiFi connected
IP address: 192.168.1.100
Initializing NTP client...
Attempting NTP time synchronization...
NTP synchronization successful!
Current time: 14:30:25
```

### 4. Visual Verification

Check the display for:
- ✅ Green dot = NTP synchronized
- ⚠️ Orange dot = Using fallback time
- 🕐 Correct time display in HH:MM format
- 📅 Correct date display in MM/DD/YYYY format

## Common Configuration Mistakes

### 1. Incorrect WiFi Credentials

```cpp
// In config.h, verify:
#define WIFI_SSID "YourNetworkName"     // Correct network name
#define WIFI_PASSWORD "YourPassword"    // Correct password
```

### 2. Wrong Timezone Setting

```cpp
// Common mistake: Using wrong sign
#define TIMEZONE_OFFSET_HOURS -8  // WRONG for Philippines
#define TIMEZONE_OFFSET_HOURS 8   // CORRECT for Philippines (UTC+8)
```

### 3. Missing NTP Library

**Error**: `'NTPClient' was not declared in this scope`

**Solution**: Install NTPClient library via Arduino Library Manager

### 4. Incorrect Pin Definitions

```cpp
// Verify TFT pins match your hardware:
#define TFT_CS    5
#define TFT_DC    21
#define TFT_RST   22
#define TFT_MOSI  23
#define TFT_SCLK  18
```

## Performance Optimization

### 1. Reduce NTP Sync Frequency

For battery-powered units or to reduce network traffic:

```cpp
#define NTP_SYNC_INTERVAL_HOURS 4  // Sync every 4 hours
#define NTP_RETRY_INTERVAL_MINUTES 15  // Retry every 15 minutes
```

### 2. Optimize Display Updates

```cpp
// Update time display less frequently if needed
if (currentMillis - lastTimeUpdate > 120000) { // Every 2 minutes
    lastTimeUpdate = currentMillis;
    updateTimeDisplay();
}
```

### 3. Memory Management

```cpp
// Monitor memory usage
if (ESP.getFreeHeap() < 10000) {
    Serial.println("Warning: Low memory");
    // Consider reducing buffer sizes or sync frequency
}
```

## Getting Help

If you continue to experience issues:

1. **Check Serial Output**: Always monitor the serial console for detailed error messages
2. **Verify Hardware**: Ensure all connections are secure and components are working
3. **Test Components**: Use the provided test sketches to isolate issues
4. **Check Network**: Verify internet connectivity and NTP server accessibility
5. **Update Libraries**: Ensure all libraries are up to date

## Success Indicators

When everything is working correctly, you should see:

- ✅ Successful compilation without errors
- ✅ WiFi connection established
- ✅ NTP synchronization successful
- ✅ Green status indicator on display
- ✅ Accurate time display
- ✅ Periodic sync working
- ✅ BLE scanning operational
- ✅ MQTT communication functional

The faculty desk unit should display accurate, synchronized time and respond to consultation requests while maintaining reliable network connectivity.
