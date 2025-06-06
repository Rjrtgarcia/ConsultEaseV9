/*
 * NTP Time Synchronization Test for ESP32
 * 
 * This is a simplified test sketch to verify NTP functionality
 * before integrating into the main faculty desk unit firmware.
 * 
 * Upload this sketch to test NTP synchronization independently.
 */

#include <WiFi.h>
#include <WiFiUdp.h>
#include <NTPClient.h>
#include <time.h>

// WiFi Configuration - Update these for your network
const char* ssid = "ConsultEase";
const char* password = "Admin123";

// NTP Configuration
const char* ntpServer1 = "pool.ntp.org";
const char* ntpServer2 = "time.nist.gov";
const char* ntpServer3 = "time.google.com";
const long gmtOffset_sec = 8 * 3600;  // Philippines timezone UTC+8
const int daylightOffset_sec = 0;     // No daylight saving time

// NTP Client setup
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, ntpServer1, gmtOffset_sec, 60000);

// Test variables
bool ntpSyncSuccessful = false;
int testAttempts = 0;
const int maxTestAttempts = 3;

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== ESP32 NTP Time Synchronization Test ===");
  
  // Connect to WiFi
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  
  // Test NTP synchronization
  testNTPSynchronization();
  
  // Test fallback mechanisms
  testFallbackMechanisms();
  
  Serial.println("\n=== NTP Test Complete ===");
}

void loop() {
  // Display current time every 10 seconds
  static unsigned long lastDisplay = 0;
  
  if (millis() - lastDisplay > 10000) {
    lastDisplay = millis();
    displayCurrentTime();
  }
  
  delay(100);
}

void testNTPSynchronization() {
  Serial.println("\n--- Testing NTP Synchronization ---");
  
  // Initialize NTP client
  Serial.println("Initializing NTP client...");
  timeClient.begin();
  
  // Test primary server
  Serial.print("Testing primary NTP server: ");
  Serial.println(ntpServer1);
  
  bool success = timeClient.update();
  
  if (success) {
    Serial.println("✓ Primary NTP server sync successful!");
    ntpSyncSuccessful = true;
    
    // Display synchronized time
    Serial.print("Synchronized time: ");
    Serial.println(timeClient.getFormattedTime());
    
    // Set system time
    unsigned long epochTime = timeClient.getEpochTime();
    struct timeval tv;
    tv.tv_sec = epochTime;
    tv.tv_usec = 0;
    settimeofday(&tv, NULL);
    
    // Configure timezone
    setenv("TZ", "PHT-8", 1);
    tzset();
    
    Serial.println("✓ System time updated successfully!");
    
  } else {
    Serial.println("✗ Primary NTP server sync failed");
    testAlternativeServers();
  }
}

void testAlternativeServers() {
  Serial.println("\n--- Testing Alternative NTP Servers ---");
  
  const char* servers[] = {ntpServer2, ntpServer3};
  
  for (int i = 0; i < 2 && !ntpSyncSuccessful; i++) {
    Serial.print("Testing server: ");
    Serial.println(servers[i]);
    
    // Reinitialize with different server
    timeClient.end();
    timeClient = NTPClient(ntpUDP, servers[i], gmtOffset_sec, 60000);
    timeClient.begin();
    
    delay(1000);
    
    bool success = timeClient.update();
    
    if (success) {
      Serial.print("✓ Alternative server sync successful: ");
      Serial.println(servers[i]);
      ntpSyncSuccessful = true;
      
      Serial.print("Synchronized time: ");
      Serial.println(timeClient.getFormattedTime());
      
    } else {
      Serial.print("✗ Alternative server sync failed: ");
      Serial.println(servers[i]);
    }
  }
  
  if (!ntpSyncSuccessful) {
    Serial.println("✗ All NTP servers failed");
  }
}

void testFallbackMechanisms() {
  Serial.println("\n--- Testing Fallback Mechanisms ---");
  
  // Test ESP32 internal RTC
  Serial.println("Testing ESP32 internal RTC fallback...");
  
  struct tm timeinfo;
  if (getLocalTime(&timeinfo)) {
    Serial.println("✓ ESP32 RTC is working");
    
    char timeStr[20];
    strftime(timeStr, sizeof(timeStr), "%Y-%m-%d %H:%M:%S", &timeinfo);
    Serial.print("RTC time: ");
    Serial.println(timeStr);
    
  } else {
    Serial.println("✗ ESP32 RTC failed");
    Serial.println("Would fallback to hardcoded time");
  }
  
  // Test time formatting functions
  Serial.println("\nTesting time formatting functions...");
  
  String formattedTime = getTestFormattedTime();
  String formattedDate = getTestFormattedDate();
  
  Serial.print("Formatted time: ");
  Serial.println(formattedTime);
  Serial.print("Formatted date: ");
  Serial.println(formattedDate);
}

String getTestFormattedTime() {
  if (ntpSyncSuccessful) {
    timeClient.update();
    return timeClient.getFormattedTime();
  } else {
    struct tm timeinfo;
    if (getLocalTime(&timeinfo)) {
      char timeStr[10];
      strftime(timeStr, sizeof(timeStr), "%H:%M:%S", &timeinfo);
      return String(timeStr);
    } else {
      return "12:00:00"; // Hardcoded fallback
    }
  }
}

String getTestFormattedDate() {
  if (ntpSyncSuccessful) {
    time_t epochTime = timeClient.getEpochTime();
    struct tm *ptm = gmtime(&epochTime);
    
    char dateStr[12];
    sprintf(dateStr, "%04d-%02d-%02d", 
            ptm->tm_year + 1900, 
            ptm->tm_mon + 1, 
            ptm->tm_mday);
    return String(dateStr);
  } else {
    struct tm timeinfo;
    if (getLocalTime(&timeinfo)) {
      char dateStr[12];
      strftime(dateStr, sizeof(dateStr), "%Y-%m-%d", &timeinfo);
      return String(dateStr);
    } else {
      return "2024-01-01"; // Hardcoded fallback
    }
  }
}

void displayCurrentTime() {
  Serial.println("\n--- Current Time Status ---");
  
  if (ntpSyncSuccessful) {
    Serial.println("Status: NTP Synchronized ✓");
  } else {
    Serial.println("Status: Using Fallback Time ⚠");
  }
  
  String currentTime = getTestFormattedTime();
  String currentDate = getTestFormattedDate();
  
  Serial.print("Current time: ");
  Serial.println(currentTime);
  Serial.print("Current date: ");
  Serial.println(currentDate);
  
  // Display in format used by main firmware
  String displayTime = currentTime.substring(0, 5); // HH:MM
  
  if (currentDate.length() >= 10) {
    String year = currentDate.substring(0, 4);
    String month = currentDate.substring(5, 7);
    String day = currentDate.substring(8, 10);
    String displayDate = month + "/" + day + "/" + year;
    
    Serial.print("Display format - Time: ");
    Serial.print(displayTime);
    Serial.print(", Date: ");
    Serial.println(displayDate);
  }
  
  Serial.print("WiFi Status: ");
  Serial.println(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
  
  Serial.print("Free heap: ");
  Serial.print(ESP.getFreeHeap());
  Serial.println(" bytes");
}
