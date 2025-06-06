# ESP32 Faculty Desk Unit Configuration Guide

## One-to-One Beacon Mapping Configuration

Each ESP32 faculty desk unit is now configured to detect only its assigned faculty member's nRF51822 beacon MAC address. This creates a clean one-to-one mapping between units and faculty members.

## Configuration Steps for Each Unit

### Unit 1 - Faculty Member 1
**File:** `config.h`
```cpp
// Faculty Configuration - Unit 1
#define FACULTY_ID 1
#define FACULTY_NAME "Dr. John Smith"  // Replace with actual name
#define FACULTY_DEPARTMENT "Computer Science"  // Replace with actual department

// Faculty BLE Beacon Configuration - nRF51822 Beacon
#define FACULTY_BEACON_MAC "AA:BB:CC:DD:EE:01"  // Replace with actual beacon MAC
```

### Unit 2 - Faculty Member 2
**File:** `config.h`
```cpp
// Faculty Configuration - Unit 2
#define FACULTY_ID 2
#define FACULTY_NAME "Dr. Jane Doe"  // Replace with actual name
#define FACULTY_DEPARTMENT "Mathematics"  // Replace with actual department

// Faculty BLE Beacon Configuration - nRF51822 Beacon
#define FACULTY_BEACON_MAC "AA:BB:CC:DD:EE:02"  // Replace with actual beacon MAC
```

### Unit 3 - Faculty Member 3
**File:** `config.h`
```cpp
// Faculty Configuration - Unit 3
#define FACULTY_ID 3
#define FACULTY_NAME "Prof. Robert Chen"  // Replace with actual name
#define FACULTY_DEPARTMENT "Computer Science"  // Replace with actual department

// Faculty BLE Beacon Configuration - nRF51822 Beacon
#define FACULTY_BEACON_MAC "AA:BB:CC:DD:EE:03"  // Replace with actual beacon MAC
```

### Unit 4 - Faculty Member 4
**File:** `config.h`
```cpp
// Faculty Configuration - Unit 4
#define FACULTY_ID 4
#define FACULTY_NAME "Jeysibn"  // Replace with actual name
#define FACULTY_DEPARTMENT "Computer Science"  // Replace with actual department

// Faculty BLE Beacon Configuration - nRF51822 Beacon
#define FACULTY_BEACON_MAC "AA:BB:CC:DD:EE:04"  // Replace with actual beacon MAC
```

### Unit 5 - Faculty Member 5
**File:** `config.h`
```cpp
// Faculty Configuration - Unit 5
#define FACULTY_ID 5
#define FACULTY_NAME "Dr. Maria Santos"  // Replace with actual name
#define FACULTY_DEPARTMENT "Information Technology"  // Replace with actual department

// Faculty BLE Beacon Configuration - nRF51822 Beacon
#define FACULTY_BEACON_MAC "AA:BB:CC:DD:EE:05"  // Replace with actual beacon MAC
```

## Upload Process for Each Unit

### Step 1: Configure Unit-Specific Settings
1. Open `config.h` in Arduino IDE
2. Update `FACULTY_ID` with the unit number (1-5)
3. Update `FACULTY_NAME` with the actual faculty member's name
4. Update `FACULTY_DEPARTMENT` with the actual department
5. Update `FACULTY_BEACON_MAC` with the actual nRF51822 beacon MAC address

### Step 2: Verify Configuration
- Ensure each unit has a unique `FACULTY_ID`
- Ensure each unit has a unique `FACULTY_BEACON_MAC`
- Verify faculty names match the database records
- Check WiFi and MQTT settings are correct

### Step 3: Upload Firmware
1. Select correct ESP32 board in Arduino IDE
2. Select correct COM port
3. Upload firmware
4. Monitor Serial output for successful initialization

## Expected Serial Output

### Successful Initialization
```
Initializing BLE Scanner for nRF51822 beacon detection...
Assigned Faculty: Dr. John Smith (ID: 1)
Target Beacon MAC: AA:BB:CC:DD:EE:01
BLE Scanner initialized for single beacon detection
WiFi connected
MQTT connected
```

### Beacon Detection
```
Starting BLE scan for Dr. John Smith's beacon...
Assigned faculty beacon detected: AA:BB:CC:DD:EE:01 (Dr. John Smith)
Dr. John Smith presence changed: PRESENT
Published Dr. John Smith present status
```

### Beacon Not Detected
```
Starting BLE scan for Dr. John Smith's beacon...
Assigned faculty beacon not detected (AA:BB:CC:DD:EE:01)
Dr. John Smith presence changed: ABSENT
Published Dr. John Smith absent status
```

## Benefits of One-to-One Mapping

### Performance Benefits
- **Faster Scanning:** Only scans for one specific MAC address
- **Lower Memory Usage:** No need to store array of MAC addresses
- **Reduced Processing:** Simplified detection logic
- **Better Reliability:** Less chance of false positives

### Configuration Benefits
- **Simpler Setup:** Each unit only needs its own beacon MAC
- **Clear Mapping:** One unit = one faculty = one beacon
- **Easy Troubleshooting:** Clear identification of which unit detects which faculty
- **Scalable:** Easy to add more units without affecting existing ones

### Maintenance Benefits
- **Independent Units:** Each unit operates independently
- **Isolated Issues:** Problems with one beacon don't affect others
- **Clear Responsibility:** Each unit has a single purpose
- **Easy Replacement:** Can replace individual units without reconfiguration

## Troubleshooting

### Unit Not Detecting Beacon
1. **Check MAC Address:** Verify `FACULTY_BEACON_MAC` matches actual beacon
2. **Check Beacon Power:** Ensure beacon is powered on and advertising
3. **Check Range:** Place beacon within 2-3 meters of ESP32
4. **Check Serial Output:** Look for detection messages

### Wrong Faculty Detected
1. **Check Faculty ID:** Verify `FACULTY_ID` matches database
2. **Check Faculty Name:** Verify `FACULTY_NAME` matches database
3. **Check Beacon Assignment:** Ensure correct beacon is assigned to faculty

### MQTT Issues
1. **Check WiFi:** Verify WiFi connection is successful
2. **Check MQTT Server:** Verify `MQTT_SERVER` IP address is correct
3. **Check Topics:** Verify MQTT topics are being published correctly

## Testing Checklist

### For Each Unit:
- [ ] Correct `FACULTY_ID` configured
- [ ] Correct `FACULTY_NAME` configured
- [ ] Correct `FACULTY_DEPARTMENT` configured
- [ ] Correct `FACULTY_BEACON_MAC` configured
- [ ] WiFi connection successful
- [ ] MQTT connection successful
- [ ] Beacon detection working
- [ ] Status messages published correctly
- [ ] Display showing correct faculty name
- [ ] Serial output shows correct faculty information

## Deployment Verification

### System-Wide Testing:
- [ ] All 5 units configured with unique settings
- [ ] All 5 units detecting their assigned beacons
- [ ] No cross-detection between units
- [ ] All units publishing to correct MQTT topics
- [ ] Admin dashboard showing correct status for each faculty
- [ ] Each unit displays correct faculty name and status

This one-to-one mapping approach provides a cleaner, more efficient, and more maintainable solution for your nRF51822 beacon-based faculty presence detection system.
