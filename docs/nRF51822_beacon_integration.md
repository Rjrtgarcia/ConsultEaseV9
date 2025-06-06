# nRF51822 BLE Beacon Integration Guide

This guide provides step-by-step instructions for integrating 5 nRF51822 BLE beacons with the ConsultEase faculty presence detection system for your capstone research defense.

## Overview

The ConsultEase system has been configured to use MAC address-based BLE scanning to detect faculty presence using nRF51822 beacons. Each beacon will be assigned to a specific faculty member, and the ESP32 faculty desk units will scan for these beacons to determine faculty availability.

## Hardware Requirements

- 5 × nRF51822 BLE beacons (your existing beacons)
- 5 × ESP32 faculty desk units (already configured)
- 1 × Central system (Raspberry Pi or computer)
- BLE scanner app (nRF Connect, BLE Scanner, or LightBlue)

## System Architecture

```
nRF51822 Beacon → ESP32 Faculty Desk Unit → MQTT → Central System → Database
     (BLE)              (BLE Scanner)        (WiFi)    (Faculty Status)
```

## Step-by-Step Integration Process

### Phase 1: Beacon MAC Address Discovery

#### 1.1 Prepare Your Environment
```bash
cd /path/to/ConsultEase
python scripts/configure_nrf51822_beacons.py discover
```

#### 1.2 Discover Beacon MAC Addresses
1. **Power on ONE beacon at a time**
2. **Use a BLE scanner app:**
   - **Android:** nRF Connect, BLE Scanner
   - **iOS:** nRF Connect, LightBlue
   - **Windows:** Bluetooth LE Explorer
3. **Look for your beacon** (may appear as "nRF51822" or custom name)
4. **Record the MAC address** (format: XX:XX:XX:XX:XX:XX)
5. **Repeat for all 5 beacons**

#### 1.3 Document Beacon Assignments
Create a mapping like this:
```
Beacon #1: AA:BB:CC:DD:EE:01 → Faculty 1 (Dr. John Smith)
Beacon #2: AA:BB:CC:DD:EE:02 → Faculty 2 (Dr. Jane Doe)
Beacon #3: AA:BB:CC:DD:EE:03 → Faculty 3 (Prof. Robert Chen)
Beacon #4: AA:BB:CC:DD:EE:04 → Faculty 4 (Jeysibn)
Beacon #5: AA:BB:CC:DD:EE:05 → Faculty 5 (Additional Faculty)
```

### Phase 2: System Configuration

#### 2.1 Update Database
```bash
python scripts/configure_nrf51822_beacons.py configure
```

This will:
- Update faculty records with beacon MAC addresses
- Generate ESP32 configuration code
- Validate MAC address formats

#### 2.2 Update ESP32 Faculty Desk Units

**For each ESP32 unit:**

1. **Open Arduino IDE**
2. **Open `faculty_desk_unit/faculty_desk_unit.ino`**
3. **Replace the FACULTY_MAC_ADDRESSES array** with the generated configuration:

```cpp
// Faculty MAC Addresses Definition - nRF51822 BLE Beacons
const char* FACULTY_MAC_ADDRESSES[MAX_FACULTY_MAC_ADDRESSES] = {
  "AA:BB:CC:DD:EE:01",  // Dr. John Smith - Beacon #1
  "AA:BB:CC:DD:EE:02",  // Dr. Jane Doe - Beacon #2
  "AA:BB:CC:DD:EE:03",  // Prof. Robert Chen - Beacon #3
  "AA:BB:CC:DD:EE:04",  // Jeysibn - Beacon #4
  "AA:BB:CC:DD:EE:05"   // Additional Faculty - Beacon #5
};
```

4. **Update config.h for each unit:**
   - Set the correct `FACULTY_ID` for each desk unit
   - Set the correct `FACULTY_NAME` for each desk unit
   - Verify WiFi and MQTT settings

5. **Upload firmware to each ESP32**

### Phase 3: Testing and Validation

#### 3.1 Individual Beacon Testing

**For each beacon:**
1. **Power on the beacon**
2. **Place it near the corresponding ESP32 unit**
3. **Monitor ESP32 serial output:**
   ```
   Starting BLE scan for faculty devices...
   Faculty device detected: AA:BB:CC:DD:EE:01 RSSI: -65
   Faculty presence changed: PRESENT
   Published faculty present status
   ```
4. **Verify MQTT messages** in central system logs
5. **Check faculty status** in admin dashboard

#### 3.2 System Integration Testing

1. **Start central system**
2. **Power on all ESP32 units**
3. **Test each beacon individually:**
   - Place beacon near desk unit
   - Verify presence detection
   - Move beacon away
   - Verify absence detection
4. **Test multiple beacons simultaneously**
5. **Verify admin dashboard updates**

## Configuration Parameters

### BLE Scanning Parameters (Optimized for nRF51822)

```cpp
#define BLE_SCAN_INTERVAL 3000  // Scan every 3 seconds
#define BLE_SCAN_DURATION 5     // Scan for 5 seconds
#define BLE_RSSI_THRESHOLD -85  // Detection range threshold
#define MAC_DETECTION_TIMEOUT 45000  // 45 seconds timeout
#define MAC_DETECTION_DEBOUNCE 2     // 2 consecutive scans needed
```

### MQTT Topics

- **Status Updates:** `consultease/faculty/{faculty_id}/status`
- **MAC Status:** `consultease/faculty/{faculty_id}/mac_status`
- **Requests:** `consultease/faculty/{faculty_id}/requests`

## Troubleshooting

### Common Issues

#### 1. Beacon Not Detected
**Symptoms:** No detection messages in ESP32 serial output
**Solutions:**
- Verify beacon is powered on and advertising
- Check MAC address in configuration
- Reduce RSSI threshold: `#define BLE_RSSI_THRESHOLD -90`
- Increase scan duration: `#define BLE_SCAN_DURATION 10`

#### 2. Frequent Status Changes
**Symptoms:** Faculty status rapidly switching between present/absent
**Solutions:**
- Increase debounce count: `#define MAC_DETECTION_DEBOUNCE 3`
- Adjust RSSI threshold for more stable detection
- Check for BLE interference

#### 3. MQTT Connection Issues
**Symptoms:** ESP32 can't publish status updates
**Solutions:**
- Verify WiFi connection
- Check MQTT broker IP address in config.h
- Verify MQTT broker is running on central system

#### 4. Database Not Updating
**Symptoms:** Admin dashboard doesn't show status changes
**Solutions:**
- Check central system logs for MQTT message reception
- Verify faculty ID mapping in database
- Restart central system services

## Performance Optimization

### Battery Life (for Battery-Powered Beacons)
- Use lower advertising intervals on beacons
- Increase scan intervals on ESP32: `#define BLE_SCAN_INTERVAL 5000`
- Use passive scanning: `#define MAC_SCAN_ACTIVE false`

### Detection Reliability
- Place beacons at optimal height (desk level)
- Avoid metal obstacles between beacon and ESP32
- Use consistent beacon placement for each faculty member

## Deployment Checklist

### Pre-Deployment
- [ ] All 5 beacon MAC addresses discovered and documented
- [ ] Database updated with beacon-to-faculty mappings
- [ ] All 5 ESP32 units configured with correct MAC addresses
- [ ] Each ESP32 unit configured with correct faculty ID
- [ ] Firmware uploaded to all ESP32 units
- [ ] Central system running and MQTT broker active

### Testing Phase
- [ ] Individual beacon detection tested for each unit
- [ ] MQTT communication verified for all units
- [ ] Admin dashboard updates confirmed
- [ ] Range testing completed for deployment environment
- [ ] Interference testing completed

### Production Deployment
- [ ] Beacons distributed to faculty members
- [ ] ESP32 units installed at faculty desks
- [ ] System monitoring configured
- [ ] Faculty members trained on beacon usage
- [ ] Backup procedures documented

## Quick Start - Integrated Admin Dashboard

### Complete Setup Process via Admin Dashboard

1. **Launch ConsultEase Admin Dashboard**
   - Start the central system
   - Log in to the admin dashboard

2. **Access Beacon Management**
   - Go to **Faculty Management** tab → Click **"Beacon Management"** button
   - OR go to **System Maintenance** tab → Click **"Open Beacon Management"** button

3. **Discover Beacon MAC Addresses**
   - Switch to **"Beacon Discovery"** tab
   - Follow the on-screen instructions to discover your 5 nRF51822 beacon MAC addresses
   - Enter each MAC address and validate
   - Save the configuration

4. **Assign Beacons to Faculty**
   - Switch to **"Faculty Assignment"** tab
   - Use "Auto-Assign to Faculty" or manually assign each beacon
   - Save assignments to update the database

5. **Generate ESP32 Configurations**
   - Switch to **"ESP32 Configuration"** tab
   - Click "Generate All Configurations"
   - Preview configurations and export to files

6. **Test and Monitor**
   - Switch to **"Testing & Monitoring"** tab
   - Test MQTT connection
   - Start real-time monitoring of beacon detection

### Integrated Features
- **Beacon Management Dialog** - Comprehensive beacon configuration interface
- **Faculty Assignment** - Direct database integration for beacon-to-faculty mapping
- **ESP32 Configuration Generator** - Automated config file generation
- **Real-time Testing** - Built-in MQTT monitoring and testing tools
- **System Integration** - Seamless integration with existing admin dashboard

## Support and Maintenance

### Monitoring
- Monitor ESP32 serial output for detection issues
- Check central system logs for MQTT communication
- Use admin dashboard to verify faculty status updates

### Maintenance
- Replace beacon batteries as needed
- Update firmware if issues arise
- Adjust detection parameters based on environment

## Research Defense Preparation

### Demonstration Points
1. **Real-time presence detection** using nRF51822 beacons
2. **Automatic faculty status updates** in admin dashboard
3. **MQTT communication** between ESP32 units and central system
4. **Scalable architecture** supporting multiple faculty members
5. **Reliable BLE scanning** with optimized parameters

### Technical Highlights
- MAC address-based detection for reliable identification
- Debouncing logic to prevent false positives
- MQTT integration for real-time communication
- Database integration for persistent status tracking
- Configurable parameters for different environments

### System Architecture Benefits
- **Scalable:** Easily add more beacons and faculty members
- **Reliable:** Robust detection with debouncing and timeout handling
- **Real-time:** Immediate status updates via MQTT
- **Configurable:** Adjustable parameters for different environments
- **Maintainable:** Clear separation of concerns and modular design
