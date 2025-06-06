// Enhanced MQTT Debugging for Faculty Desk Unit
// Add this to your faculty_desk_unit.ino for better error diagnosis

// Enhanced MQTT publish with detailed error reporting
bool publishWithDetailedDebug(const char* topic, const char* payload, bool retained = false) {
  if (!client.connected()) {
    DEBUG_PRINTLN("❌ MQTT not connected - cannot publish");
    return false;
  }

  // Pre-publish diagnostics
  DEBUG_PRINTF("🔍 MQTT Debug Info:\n");
  DEBUG_PRINTF("   Topic: %s\n", topic);
  DEBUG_PRINTF("   Payload size: %d bytes\n", strlen(payload));
  DEBUG_PRINTF("   Retained: %s\n", retained ? "YES" : "NO");
  DEBUG_PRINTF("   Client state: %d\n", client.state());
  DEBUG_PRINTF("   Buffer size: %d bytes\n", client.getBufferSize());
  DEBUG_PRINTF("   WiFi RSSI: %d dBm\n", WiFi.RSSI());
  DEBUG_PRINTF("   Free heap: %d bytes\n", ESP.getFreeHeap());

  // Check if payload is too large
  if (strlen(payload) > client.getBufferSize() - strlen(topic) - 10) {
    DEBUG_PRINTF("❌ Payload too large! %d bytes > %d available\n", 
                 strlen(payload), client.getBufferSize() - strlen(topic) - 10);
    return false;
  }

  // Attempt publish with detailed error handling
  DEBUG_PRINTLN("🚀 Attempting MQTT publish...");
  bool result = client.publish(topic, payload, retained);
  
  // Post-publish diagnostics
  if (result) {
    DEBUG_PRINTLN("✅ MQTT publish reported SUCCESS");
  } else {
    DEBUG_PRINTLN("❌ MQTT publish reported FAILURE");
    DEBUG_PRINTF("   Error state: %d\n", client.state());
    
    // Detailed error analysis
    switch (client.state()) {
      case MQTT_CONNECTION_TIMEOUT:
        DEBUG_PRINTLN("   → Connection timeout");
        break;
      case MQTT_CONNECTION_LOST:
        DEBUG_PRINTLN("   → Connection lost");
        break;
      case MQTT_CONNECT_FAILED:
        DEBUG_PRINTLN("   → Connect failed");
        break;
      case MQTT_DISCONNECTED:
        DEBUG_PRINTLN("   → Disconnected");
        break;
      case MQTT_CONNECT_BAD_PROTOCOL:
        DEBUG_PRINTLN("   → Bad protocol");
        break;
      case MQTT_CONNECT_BAD_CLIENT_ID:
        DEBUG_PRINTLN("   → Bad client ID");
        break;
      case MQTT_CONNECT_UNAVAILABLE:
        DEBUG_PRINTLN("   → Server unavailable");
        break;
      case MQTT_CONNECT_BAD_CREDENTIALS:
        DEBUG_PRINTLN("   → Bad credentials");
        break;
      case MQTT_CONNECT_UNAUTHORIZED:
        DEBUG_PRINTLN("   → Unauthorized");
        break;
      default:
        DEBUG_PRINTF("   → Unknown error: %d\n", client.state());
    }
  }

  // Network connectivity check
  if (WiFi.status() != WL_CONNECTED) {
    DEBUG_PRINTLN("❌ WiFi disconnected during publish!");
  }

  return result;
}

// Enhanced MQTT connection test
bool testMQTTConnection() {
  DEBUG_PRINTLN("🧪 Testing MQTT connection...");
  
  // Test 1: Basic connectivity
  bool connected = client.connected();
  DEBUG_PRINTF("Test 1 - Connected: %s\n", connected ? "PASS" : "FAIL");
  
  // Test 2: State check
  int state = client.state();
  DEBUG_PRINTF("Test 2 - State: %d (%s)\n", state, state == 0 ? "CONNECTED" : "ERROR");
  
  // Test 3: Simple publish test
  DEBUG_PRINTLN("Test 3 - Simple publish test...");
  String testTopic = "consultease/faculty/" + String(FACULTY_ID) + "/test";
  String testPayload = "{\"test\":\"connection\",\"timestamp\":\"" + String(millis()) + "\"}";
  
  bool testResult = publishWithDetailedDebug(testTopic.c_str(), testPayload.c_str());
  DEBUG_PRINTF("Test 3 - Publish: %s\n", testResult ? "PASS" : "FAIL");
  
  // Test 4: Topic permission test
  DEBUG_PRINTLN("Test 4 - Testing different topics...");
  String statusTopic = "consultease/faculty/" + String(FACULTY_ID) + "/status";
  String statusPayload = "{\"test\":\"status\",\"present\":true}";
  bool statusResult = publishWithDetailedDebug(statusTopic.c_str(), statusPayload.c_str());
  DEBUG_PRINTF("Test 4a - Status topic: %s\n", statusResult ? "PASS" : "FAIL");
  
  String responseTopic = "consultease/faculty/" + String(FACULTY_ID) + "/responses";
  String responsePayload = "{\"test\":\"response\",\"faculty_id\":" + String(FACULTY_ID) + "}";
  bool responseResult = publishWithDetailedDebug(responseTopic.c_str(), responsePayload.c_str());
  DEBUG_PRINTF("Test 4b - Response topic: %s\n", responseResult ? "PASS" : "FAIL");
  
  DEBUG_PRINTLN("🧪 MQTT connection test completed");
  return connected && (state == 0) && testResult;
}

// Call this in your setup() function for detailed MQTT diagnosis
void runMQTTDiagnostics() {
  DEBUG_PRINTLN("🔍 Running comprehensive MQTT diagnostics...");
  
  DEBUG_PRINTF("MQTT Server: %s:%d\n", MQTT_SERVER, MQTT_PORT);
  DEBUG_PRINTF("MQTT Username: %s\n", MQTT_USERNAME);
  DEBUG_PRINTF("MQTT Client ID: %s\n", MQTT_CLIENT_ID);
  DEBUG_PRINTF("WiFi Status: %d\n", WiFi.status());
  DEBUG_PRINTF("WiFi SSID: %s\n", WiFi.SSID().c_str());
  DEBUG_PRINTF("WiFi IP: %s\n", WiFi.localIP().toString().c_str());
  
  testMQTTConnection();
} 