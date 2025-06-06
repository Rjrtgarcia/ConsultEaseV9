/*
 * nRF51822 Beacon Discovery Utility for ESP32
 * 
 * This utility helps you find the MAC address of your nRF51822 beacon
 * by scanning for all BLE devices and displaying detailed information.
 * 
 * INSTRUCTIONS:
 * 1. Upload this sketch to your ESP32
 * 2. Open Serial Monitor at 115200 baud
 * 3. Power on your nRF51822 beacon near the ESP32
 * 4. Look for your beacon in the device list
 * 5. Note the MAC address and update config.h in main firmware
 * 
 * Author: ConsultEase Development Team
 * Version: 1.0
 */

#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

// Scan configuration
#define SCAN_DURATION 10        // Scan for 10 seconds
#define SCAN_INTERVAL 1000      // Scan every 1 second
#define MIN_RSSI -100           // Show all devices (no RSSI filtering)

BLEScan* pBLEScan;
int scanCount = 0;
unsigned long lastScanTime = 0;

// Device tracking
struct BLEDeviceInfo {
  String mac;
  String name;
  int rssi;
  bool hasServiceUUID;
  String serviceUUID;
  bool hasManufacturerData;
  int detectionCount;
  unsigned long lastSeen;
};

std::vector<BLEDeviceInfo> detectedDevices;

class BeaconDiscoveryCallbacks: public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) {
      String deviceMac = advertisedDevice.getAddress().toString().c_str();
      String deviceName = "";
      int rssi = advertisedDevice.getRSSI();
      
      // Get device name if available
      if (advertisedDevice.haveName()) {
        deviceName = advertisedDevice.getName().c_str();
      }
      
      // Get service UUID if available
      String serviceUUID = "";
      bool hasServiceUUID = false;
      if (advertisedDevice.haveServiceUUID()) {
        serviceUUID = advertisedDevice.getServiceUUID().toString().c_str();
        hasServiceUUID = true;
      }
      
      // Check for manufacturer data
      bool hasManufacturerData = advertisedDevice.haveManufacturerData();
      
      // Update or add device to list
      updateDeviceList(deviceMac, deviceName, rssi, hasServiceUUID, serviceUUID, hasManufacturerData);
      
      // Real-time device detection output
      Serial.print("📱 ");
      Serial.print(deviceMac);
      Serial.print(" | ");
      Serial.print(rssi);
      Serial.print(" dBm | ");
      Serial.print(deviceName.length() > 0 ? deviceName : "Unknown");
      
      if (hasServiceUUID) {
        Serial.print(" | Service: ");
        Serial.print(serviceUUID);
      }
      
      if (hasManufacturerData) {
        Serial.print(" | MfgData: Yes");
      }
      
      // Highlight potential nRF51822 beacons
      if (deviceName.indexOf("nRF") >= 0 || 
          deviceName.indexOf("Nordic") >= 0 || 
          deviceName.indexOf("Beacon") >= 0 ||
          (deviceName.length() == 0 && hasManufacturerData)) {
        Serial.print(" ⭐ POTENTIAL BEACON");
      }
      
      Serial.println();
    }
};

void updateDeviceList(String mac, String name, int rssi, bool hasServiceUUID, String serviceUUID, bool hasManufacturerData) {
  // Find existing device or add new one
  for (auto& device : detectedDevices) {
    if (device.mac == mac) {
      // Update existing device
      device.rssi = rssi;
      device.detectionCount++;
      device.lastSeen = millis();
      if (name.length() > 0 && device.name.length() == 0) {
        device.name = name; // Update name if we didn't have it before
      }
      return;
    }
  }
  
  // Add new device
  BLEDeviceInfo newDevice;
  newDevice.mac = mac;
  newDevice.name = name;
  newDevice.rssi = rssi;
  newDevice.hasServiceUUID = hasServiceUUID;
  newDevice.serviceUUID = serviceUUID;
  newDevice.hasManufacturerData = hasManufacturerData;
  newDevice.detectionCount = 1;
  newDevice.lastSeen = millis();
  
  detectedDevices.push_back(newDevice);
}

void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println("🔍 nRF51822 Beacon Discovery Utility");
  Serial.println("=====================================");
  Serial.println();
  Serial.println("This utility will help you find your nRF51822 beacon's MAC address.");
  Serial.println("Make sure your beacon is powered on and nearby.");
  Serial.println();
  
  // Initialize BLE
  Serial.println("Initializing BLE...");
  BLEDevice::init("BeaconDiscovery");
  
  // Create BLE Scanner
  pBLEScan = BLEDevice::getScan();
  pBLEScan->setAdvertisedDeviceCallbacks(new BeaconDiscoveryCallbacks());
  pBLEScan->setActiveScan(true);  // Active scan for more information
  pBLEScan->setInterval(80);      // Fast scanning
  pBLEScan->setWindow(80);
  
  Serial.println("✅ BLE Scanner initialized");
  Serial.println();
  Serial.println("Starting continuous BLE scanning...");
  Serial.println("Look for devices marked with ⭐ POTENTIAL BEACON");
  Serial.println();
  
  lastScanTime = millis();
}

void loop() {
  unsigned long currentTime = millis();
  
  // Perform scan every SCAN_INTERVAL
  if (currentTime - lastScanTime >= SCAN_INTERVAL) {
    lastScanTime = currentTime;
    scanCount++;
    
    Serial.println();
    Serial.print("=== SCAN #");
    Serial.print(scanCount);
    Serial.println(" ===");
    
    // Perform scan
    BLEScanResults* foundDevices = pBLEScan->start(SCAN_DURATION, false);
    
    Serial.print("Scan completed. Found ");
    Serial.print(foundDevices ? foundDevices->getCount() : 0);
    Serial.println(" devices in this scan.");
    
    // Clear scan results to free memory
    pBLEScan->clearResults();
    
    // Display summary every 5 scans
    if (scanCount % 5 == 0) {
      displayDeviceSummary();
    }
    
    Serial.println();
  }
  
  delay(100);
}

void displayDeviceSummary() {
  Serial.println();
  Serial.println("📊 DEVICE SUMMARY");
  Serial.println("=================");
  
  if (detectedDevices.empty()) {
    Serial.println("No BLE devices detected yet.");
    Serial.println("Make sure your beacon is powered on and advertising.");
    return;
  }
  
  // Sort devices by detection count (most frequently seen first)
  std::sort(detectedDevices.begin(), detectedDevices.end(), 
    [](const BLEDeviceInfo& a, const BLEDeviceInfo& b) {
      return a.detectionCount > b.detectionCount;
    });
  
  Serial.println("Devices sorted by detection frequency:");
  Serial.println();
  
  for (const auto& device : detectedDevices) {
    Serial.print("MAC: ");
    Serial.print(device.mac);
    Serial.print(" | RSSI: ");
    Serial.print(device.rssi);
    Serial.print(" dBm | Name: ");
    Serial.print(device.name.length() > 0 ? device.name : "Unknown");
    Serial.print(" | Seen: ");
    Serial.print(device.detectionCount);
    Serial.print(" times");
    
    // Highlight likely beacons
    bool likelyBeacon = false;
    
    if (device.name.indexOf("nRF") >= 0 || 
        device.name.indexOf("Nordic") >= 0 || 
        device.name.indexOf("Beacon") >= 0) {
      Serial.print(" | 🎯 LIKELY nRF51822 BEACON");
      likelyBeacon = true;
    } else if (device.name.length() == 0 && device.hasManufacturerData) {
      Serial.print(" | ⭐ POTENTIAL BEACON (unnamed with mfg data)");
      likelyBeacon = true;
    } else if (device.detectionCount >= 10 && device.name.length() == 0) {
      Serial.print(" | 🔄 CONSISTENT UNKNOWN DEVICE (could be beacon)");
      likelyBeacon = true;
    }
    
    Serial.println();
    
    if (likelyBeacon) {
      Serial.println("   👆 COPY THIS MAC ADDRESS TO config.h");
      Serial.print("   #define FACULTY_BEACON_MAC \"");
      Serial.print(device.mac);
      Serial.println("\"");
      Serial.println();
    }
  }
  
  Serial.println();
  Serial.println("🔧 NEXT STEPS:");
  Serial.println("1. Identify your nRF51822 beacon from the list above");
  Serial.println("2. Copy the MAC address of your beacon");
  Serial.println("3. Update FACULTY_BEACON_MAC in config.h of main firmware");
  Serial.println("4. Upload the main faculty_desk_unit.ino firmware");
  Serial.println();
  
  // Provide troubleshooting hints
  if (detectedDevices.size() == 0) {
    Serial.println("⚠️ TROUBLESHOOTING:");
    Serial.println("- Ensure beacon is powered on");
    Serial.println("- Check beacon battery level");
    Serial.println("- Move beacon closer to ESP32");
    Serial.println("- Verify beacon is in advertising mode");
  } else {
    Serial.println("✅ BLE devices detected successfully!");
    Serial.println("If you don't see your beacon, try:");
    Serial.println("- Moving it closer to the ESP32");
    Serial.println("- Checking if it's properly programmed");
    Serial.println("- Verifying it's not in sleep mode");
  }
  
  Serial.println();
}
