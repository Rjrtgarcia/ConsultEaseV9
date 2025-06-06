/*
ESP32 MQTT Template for ConsultEase - CORRECTED VERSION
This template shows the exact format expected by the central system

Key Fixes:
1. Correct topic format: consultease/faculty/{faculty_id}/messages (subscribe)
2. Correct topic format: consultease/faculty/{faculty_id}/responses (publish)  
3. Correct message format with required fields
4. No authentication needed (anonymous mode)

Based on central system code analysis in faculty_response_controller.py
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WiFi Configuration
const char* ssid = "YourWiFiSSID";
const char* password = "YourWiFiPassword";

// MQTT Configuration - CORRECTED
const char* mqtt_server = "192.168.1.100";  // Your Raspberry Pi IP
const int mqtt_port = 1883;
// NO USERNAME/PASSWORD needed with current anonymous setup

// Faculty Configuration
const int FACULTY_ID = 1;  // Your faculty ID

// MQTT Topics - CORRECTED FORMAT
String subscribe_topic = "consultease/faculty/" + String(FACULTY_ID) + "/messages";
String publish_topic = "consultease/faculty/" + String(FACULTY_ID) + "/responses";

// Hardware
const int ACKNOWLEDGE_BUTTON = 2;
const int BUSY_BUTTON = 4;

WiFiClient espClient;
PubSubClient client(espClient);

// Current consultation data
int current_consultation_id = -1;
String current_student_name = "";
String current_message = "";

void setup() {
  Serial.begin(115200);
  
  // Initialize buttons
  pinMode(ACKNOWLEDGE_BUTTON, INPUT_PULLUP);
  pinMode(BUSY_BUTTON, INPUT_PULLUP);
  
  // Connect to WiFi
  setup_wifi();
  
  // Configure MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  
  // Connect to MQTT
  connect_mqtt();
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void connect_mqtt() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    // Generate client ID
    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX);
    
    // Connect WITHOUT credentials (anonymous mode)
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      
      // Subscribe to consultation messages
      client.subscribe(subscribe_topic.c_str());
      Serial.println("Subscribed to: " + subscribe_topic);
      
      // Send test message to verify publishing works
      test_publish();
      
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void test_publish() {
  // Send a test message to verify the topic works
  DynamicJsonDocument testDoc(200);
  testDoc["faculty_id"] = FACULTY_ID;
  testDoc["response_type"] = "TEST";
  testDoc["message_id"] = 0;
  testDoc["faculty_name"] = "Dr. Test";
  testDoc["timestamp"] = "test_startup";
  
  String testMessage;
  serializeJson(testDoc, testMessage);
  
  bool result = client.publish(publish_topic.c_str(), testMessage.c_str());
  Serial.println("Test publish result: " + String(result ? "SUCCESS" : "FAILED"));
  Serial.println("Published to: " + publish_topic);
  Serial.println("Test message: " + testMessage);
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  
  // Convert payload to string
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);
  
  // Parse JSON message
  DynamicJsonDocument doc(1024);
  deserializeJson(doc, message);
  
  // Extract consultation data - CORRECTED field names
  current_consultation_id = doc["id"];  // Note: "id" not "consultation_id"
  current_student_name = doc["student_name"].as<String>();
  current_message = doc["request_message"].as<String>();
  
  Serial.println("=== NEW CONSULTATION ===");
  Serial.println("ID: " + String(current_consultation_id));
  Serial.println("Student: " + current_student_name);
  Serial.println("Message: " + current_message);
  Serial.println("Press ACKNOWLEDGE or BUSY button");
  Serial.println("=======================");
}

void send_response(String response_type) {
  if (current_consultation_id == -1) {
    Serial.println("No consultation to respond to");
    return;
  }
  
  // Create response in EXACT format expected by central system
  DynamicJsonDocument doc(300);
  doc["faculty_id"] = FACULTY_ID;           // INTEGER - required
  doc["response_type"] = response_type;     // STRING - required ("ACKNOWLEDGE" or "BUSY")
  doc["message_id"] = current_consultation_id;  // INTEGER - required (consultation ID)
  doc["faculty_name"] = "Dr. Faculty";      // STRING - optional but helpful
  doc["timestamp"] = millis();              // LONG - optional
  
  String responseJson;
  serializeJson(doc, responseJson);
  
  // Publish response
  bool result = client.publish(publish_topic.c_str(), responseJson.c_str());
  
  if (result) {
    Serial.println("✅ MQTT publish reported SUCCESS");
    Serial.println("📤 Response sent: " + responseJson);
    Serial.println("📍 Published to: " + publish_topic);
  } else {
    Serial.println("❌ MQTT publish FAILED");
    Serial.println("💀 Failed to send: " + responseJson);
  }
  
  // Clear current consultation
  current_consultation_id = -1;
  current_student_name = "";
  current_message = "";
}

void loop() {
  if (!client.connected()) {
    connect_mqtt();
  }
  client.loop();
  
  // Check buttons
  if (digitalRead(ACKNOWLEDGE_BUTTON) == LOW) {
    delay(50); // Debounce
    if (digitalRead(ACKNOWLEDGE_BUTTON) == LOW) {
      send_response("ACKNOWLEDGE");
      delay(1000); // Prevent multiple presses
    }
  }
  
  if (digitalRead(BUSY_BUTTON) == LOW) {
    delay(50); // Debounce
    if (digitalRead(BUSY_BUTTON) == LOW) {
      send_response("BUSY");
      delay(1000); // Prevent multiple presses
    }
  }
}

/*
TROUBLESHOOTING CHECKLIST:

1. Topics MUST match exactly:
   - Subscribe: consultease/faculty/1/messages
   - Publish: consultease/faculty/1/responses

2. Response format MUST include:
   - faculty_id (integer)
   - response_type ("ACKNOWLEDGE" or "BUSY") 
   - message_id (integer - the consultation id)

3. MQTT broker should be in anonymous mode (no auth)

4. Check IP address of Raspberry Pi

5. Verify ESP32 can connect to WiFi

6. Use Serial Monitor to see debug messages
*/ 