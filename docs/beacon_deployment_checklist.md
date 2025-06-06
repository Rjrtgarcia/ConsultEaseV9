# nRF51822 Beacon Deployment Checklist

## Pre-Deployment Preparation

### ✅ Hardware Verification
- [ ] 5 × nRF51822 BLE beacons are functional and powered
- [ ] 5 × ESP32 faculty desk units are assembled and tested
- [ ] Central system (Raspberry Pi) is operational
- [ ] WiFi network "ConsultEase" is configured and accessible
- [ ] MQTT broker is running on central system

### ✅ Software Preparation
- [ ] ConsultEase central system is updated with beacon support
- [ ] Database schema supports MAC address storage
- [ ] Faculty records are created in database
- [ ] ESP32 firmware is compiled and ready for upload

## Phase 1: Beacon Discovery and Configuration

### Step 1: Discover Beacon MAC Addresses
**Via Admin Dashboard:**
1. Launch ConsultEase central system
2. Log in to admin dashboard
3. Go to **Faculty Management** → **"Beacon Management"**
4. Switch to **"Beacon Discovery"** tab

**Tasks:**
- [ ] Power on each beacon individually
- [ ] Use BLE scanner app to find MAC addresses
- [ ] Enter MAC addresses in the discovery interface
- [ ] Validate all MAC addresses
- [ ] Save configuration via the interface

**Expected Output:**
```
Beacon #1: AA:BB:CC:DD:EE:01 → Dr. John Smith
Beacon #2: AA:BB:CC:DD:EE:02 → Dr. Jane Doe
Beacon #3: AA:BB:CC:DD:EE:03 → Prof. Robert Chen
Beacon #4: AA:BB:CC:DD:EE:04 → Jeysibn
Beacon #5: AA:BB:CC:DD:EE:05 → Dr. Maria Santos
```

### Step 2: Configure System Database
**Via Admin Dashboard:**
1. Switch to **"Faculty Assignment"** tab
2. Use "Auto-Assign to Faculty" or manually assign each beacon
3. Save assignments to update the database

**Tasks:**
- [ ] Assign beacons to faculty members
- [ ] Verify database updates are successful
- [ ] Confirm all faculty have assigned beacons

## Phase 2: ESP32 Configuration

### Step 3: Generate Individual Unit Configurations
**Via Admin Dashboard:**
1. Switch to **"ESP32 Configuration"** tab
2. Click "Generate All Configurations"
3. Preview configurations
4. Export configuration files to local directory

**Tasks:**
- [ ] Generate configuration for all 5 units
- [ ] Review unit-specific config.h files
- [ ] Verify MAC address arrays are correct
- [ ] Check faculty ID assignments

### Step 4: Configure Each ESP32 Unit

**For Unit #1 (Dr. John Smith):**
- [ ] Copy `esp32_configs/unit_1_Dr._John_Smith/config.h` to `faculty_desk_unit/config.h`
- [ ] Update `FACULTY_ID` to match Dr. John Smith's database ID
- [ ] Update `FACULTY_NAME` to "Dr. John Smith"
- [ ] Verify WiFi and MQTT settings
- [ ] Upload firmware to ESP32
- [ ] Test serial output for successful connection

**For Unit #2 (Dr. Jane Doe):**
- [ ] Copy `esp32_configs/unit_2_Dr._Jane_Doe/config.h` to `faculty_desk_unit/config.h`
- [ ] Update `FACULTY_ID` to match Dr. Jane Doe's database ID
- [ ] Update `FACULTY_NAME` to "Dr. Jane Doe"
- [ ] Verify WiFi and MQTT settings
- [ ] Upload firmware to ESP32
- [ ] Test serial output for successful connection

**For Unit #3 (Prof. Robert Chen):**
- [ ] Copy `esp32_configs/unit_3_Prof._Robert_Chen/config.h` to `faculty_desk_unit/config.h`
- [ ] Update `FACULTY_ID` to match Prof. Robert Chen's database ID
- [ ] Update `FACULTY_NAME` to "Prof. Robert Chen"
- [ ] Verify WiFi and MQTT settings
- [ ] Upload firmware to ESP32
- [ ] Test serial output for successful connection

**For Unit #4 (Jeysibn):**
- [ ] Copy `esp32_configs/unit_4_Jeysibn/config.h` to `faculty_desk_unit/config.h`
- [ ] Update `FACULTY_ID` to match Jeysibn's database ID
- [ ] Update `FACULTY_NAME` to "Jeysibn"
- [ ] Verify WiFi and MQTT settings
- [ ] Upload firmware to ESP32
- [ ] Test serial output for successful connection

**For Unit #5 (Dr. Maria Santos):**
- [ ] Copy `esp32_configs/unit_5_Dr._Maria_Santos/config.h` to `faculty_desk_unit/config.h`
- [ ] Update `FACULTY_ID` to match Dr. Maria Santos's database ID
- [ ] Update `FACULTY_NAME` to "Dr. Maria Santos"
- [ ] Verify WiFi and MQTT settings
- [ ] Upload firmware to ESP32
- [ ] Test serial output for successful connection

## Phase 3: System Testing

### Step 5: Individual Unit Testing

**For Each Unit:**
- [ ] Power on corresponding beacon
- [ ] Place beacon within 2 meters of ESP32 unit
- [ ] Monitor ESP32 serial output for detection messages:
  ```
  Faculty device detected: AA:BB:CC:DD:EE:01 RSSI: -65
  Faculty presence changed: PRESENT
  Published faculty present status
  ```
- [ ] Verify MQTT messages in central system logs
- [ ] Check admin dashboard for status update
- [ ] Move beacon away and verify absence detection
- [ ] Test detection range (optimal: 1-3 meters)

### Step 6: System Integration Testing
**Via Admin Dashboard:**
1. Go to **System Maintenance** → **"Test Beacon Detection"**
2. OR go to **Faculty Management** → **"Beacon Management"** → **"Testing & Monitoring"** tab
3. Test MQTT connection
4. Run system integration tests

**Tasks:**
- [ ] Test MQTT communication
- [ ] Test database operations
- [ ] Test faculty controller functionality
- [ ] Verify all components work together

### Step 7: Real-Time Monitoring
**Via Admin Dashboard:**
1. In the **"Testing & Monitoring"** tab
2. Click "Start Monitoring"
3. Monitor real-time beacon detection messages

**Tasks:**
- [ ] Monitor real-time beacon detection
- [ ] Verify status changes appear in admin dashboard
- [ ] Test multiple beacons simultaneously
- [ ] Check for interference or conflicts

## Phase 4: Production Deployment

### Step 8: Physical Installation
- [ ] Install ESP32 units at faculty desks
- [ ] Ensure power supply for each unit
- [ ] Verify WiFi signal strength at each location
- [ ] Test display visibility and orientation

### Step 9: Beacon Distribution
- [ ] Distribute beacons to faculty members
- [ ] Provide usage instructions
- [ ] Test beacon detection at actual desk locations
- [ ] Adjust RSSI thresholds if needed

### Step 10: Final System Verification
- [ ] All 5 units connect to WiFi successfully
- [ ] All 5 units connect to MQTT broker
- [ ] All 5 beacons are detected by their respective units
- [ ] Admin dashboard shows real-time status updates
- [ ] Faculty can request consultations successfully
- [ ] System handles multiple simultaneous detections

## Troubleshooting Guide

### Common Issues and Solutions

**Issue: Beacon not detected**
- [ ] Verify beacon is powered and advertising
- [ ] Check MAC address in configuration
- [ ] Reduce RSSI threshold: `#define BLE_RSSI_THRESHOLD -90`
- [ ] Increase scan duration: `#define BLE_SCAN_DURATION 10`

**Issue: Frequent status changes**
- [ ] Increase debounce count: `#define MAC_DETECTION_DEBOUNCE 3`
- [ ] Adjust RSSI threshold for stability
- [ ] Check for BLE interference

**Issue: MQTT connection failed**
- [ ] Verify WiFi credentials in config.h
- [ ] Check MQTT broker IP address
- [ ] Ensure MQTT broker is running
- [ ] Test network connectivity

**Issue: Database not updating**
- [ ] Check central system logs
- [ ] Verify faculty ID mapping
- [ ] Restart central system services
- [ ] Check MQTT message format

## Performance Optimization

### For Better Detection Reliability
- [ ] Optimal beacon placement (desk level, unobstructed)
- [ ] Consistent beacon positioning
- [ ] Regular beacon battery checks
- [ ] Environmental interference assessment

### For Better System Performance
- [ ] Monitor MQTT message frequency
- [ ] Optimize scan intervals based on usage patterns
- [ ] Regular database maintenance
- [ ] System resource monitoring

## Research Defense Preparation

### Demonstration Points
- [ ] Real-time presence detection using nRF51822 beacons
- [ ] Automatic faculty status updates in admin dashboard
- [ ] MQTT communication between ESP32 units and central system
- [ ] Scalable architecture supporting multiple faculty members
- [ ] Reliable BLE scanning with optimized parameters

### Technical Documentation
- [ ] System architecture diagram
- [ ] BLE detection algorithm explanation
- [ ] MQTT message flow documentation
- [ ] Database schema documentation
- [ ] Performance metrics and testing results

### Backup Plans
- [ ] Alternative detection methods if beacons fail
- [ ] Manual status override capabilities
- [ ] System recovery procedures
- [ ] Troubleshooting documentation

## Post-Deployment Monitoring

### Daily Checks
- [ ] Verify all units are online
- [ ] Check beacon battery levels
- [ ] Monitor detection accuracy
- [ ] Review system logs for errors

### Weekly Maintenance
- [ ] Database backup
- [ ] System performance review
- [ ] Faculty feedback collection
- [ ] Configuration optimization

## Success Criteria

### Technical Success
- [ ] 95%+ beacon detection accuracy
- [ ] < 5 second response time for status changes
- [ ] 99%+ system uptime during demonstration
- [ ] All 5 faculty members successfully tracked

### Research Success
- [ ] Demonstrates practical IoT implementation
- [ ] Shows real-world BLE beacon integration
- [ ] Proves system scalability and reliability
- [ ] Validates presence detection methodology
