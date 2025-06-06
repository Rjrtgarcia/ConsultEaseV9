#!/usr/bin/env python3
"""
Complete MQTT Flow Test for ConsultEase
Tests the entire consultation flow from creation to ESP32 response

This script:
1. Creates a test consultation 
2. Publishes it to the ESP32 topic
3. Simulates ESP32 response in the exact format expected
4. Verifies the central system receives and processes the response

Usage: python3 scripts/test_complete_mqtt_flow.py
"""

import paho.mqtt.client as mqtt
import json
import time
import threading
import sys
from datetime import datetime

# MQTT Configuration
MQTT_SERVER = "localhost"  # Change to your Raspberry Pi IP if running remotely
MQTT_PORT = 1883
FACULTY_ID = 1

class CompleteMQTTFlowTester:
    def __init__(self):
        self.messages_received = []
        self.responses_received = []
        self.test_consultation_id = 12345
        
    def create_client(self, client_id):
        """Create and configure MQTT client"""
        client = mqtt.Client(client_id)
        # No authentication needed with current anonymous setup
        client.on_connect = lambda c, u, f, rc: self.on_connect(c, u, f, rc, client_id)
        client.on_message = lambda c, u, msg: self.on_message(c, u, msg, client_id)
        client.on_publish = lambda c, u, mid: self.on_publish(c, u, mid, client_id)
        return client
        
    def on_connect(self, client, userdata, flags, rc, client_id):
        """Connection callback"""
        if rc == 0:
            print(f"✅ {client_id} connected successfully")
        else:
            print(f"❌ {client_id} connection failed (RC: {rc})")
            
    def on_message(self, client, userdata, msg, client_id):
        """Message received callback"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            print(f"\n📨 {client_id} received message:")
            print(f"   Topic: {topic}")
            print(f"   Payload: {payload}")
            print(f"   Time: {timestamp}")
            
            if "messages" in topic:
                self.messages_received.append({
                    'topic': topic,
                    'payload': payload,
                    'client': client_id,
                    'timestamp': timestamp
                })
                    
            elif "responses" in topic:
                self.responses_received.append({
                    'topic': topic,
                    'payload': payload,
                    'client': client_id,
                    'timestamp': timestamp
                })
                    
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            
    def on_publish(self, client, userdata, mid, client_id):
        """Message published callback"""
        print(f"✅ {client_id} published message (MID: {mid})")
        
    def test_complete_flow(self):
        """Test the complete consultation flow"""
        print("🚀 Starting Complete MQTT Flow Test")
        print("=" * 80)
        
        # Create clients
        print("🔧 Creating MQTT clients...")
        central_client = self.create_client("central_system_test")
        esp32_client = self.create_client("esp32_simulator")
        
        try:
            # Connect clients
            print(f"\n🔌 Connecting to MQTT broker at {MQTT_SERVER}:{MQTT_PORT}...")
            central_client.connect(MQTT_SERVER, MQTT_PORT, 60)
            esp32_client.connect(MQTT_SERVER, MQTT_PORT, 60)
            
            # Start network loops
            central_client.loop_start()
            esp32_client.loop_start()
            
            # Wait for connections
            time.sleep(2)
            
            # Subscribe to response topic (central system should listen here)
            print(f"\n📡 Central system subscribing to response topic...")
            response_topic = f"consultease/faculty/{FACULTY_ID}/responses"
            central_client.subscribe(response_topic, qos=1)
            
            # Subscribe to message topic (ESP32 should listen here)
            print(f"📡 ESP32 subscribing to message topic...")
            message_topic = f"consultease/faculty/{FACULTY_ID}/messages"
            esp32_client.subscribe(message_topic, qos=1)
            
            time.sleep(1)
            
            # Step 1: Central system sends consultation to ESP32
            print(f"\n📤 Step 1: Central system sending consultation to ESP32...")
            consultation_message = {
                "id": self.test_consultation_id,
                "student_id": 1,
                "student_name": "John Doe",
                "student_department": "Computer Science",
                "faculty_id": FACULTY_ID,
                "faculty_name": "Dr. Smith",
                "request_message": "Complete flow test consultation",
                "course_code": "CS101",
                "status": "PENDING",
                "requested_at": datetime.now().isoformat()
            }
            
            result = central_client.publish(message_topic, json.dumps(consultation_message), qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"   ✅ Consultation sent to ESP32")
            else:
                print(f"   ❌ Failed to send consultation (RC: {result.rc})")
                
            time.sleep(2)
            
            # Step 2: ESP32 simulates ACKNOWLEDGE response
            print(f"\n📤 Step 2: ESP32 sending ACKNOWLEDGE response...")
            
            # This is the EXACT format the central system expects
            esp32_response = {
                "faculty_id": FACULTY_ID,                    # INTEGER - matches ESP32 ID
                "response_type": "ACKNOWLEDGE",             # EXACT string expected
                "message_id": self.test_consultation_id,    # INTEGER - consultation ID
                "faculty_name": "Dr. Smith",                # Optional but helpful
                "timestamp": datetime.now().isoformat()     # Optional
            }
            
            result = esp32_client.publish(response_topic, json.dumps(esp32_response), qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"   ✅ ESP32 response sent")
                print(f"   📋 Response format: {esp32_response}")
            else:
                print(f"   ❌ ESP32 failed to send response (RC: {result.rc})")
                
            time.sleep(3)
            
            # Step 3: Test BUSY response
            print(f"\n📤 Step 3: ESP32 sending BUSY response...")
            
            busy_response = {
                "faculty_id": FACULTY_ID,
                "response_type": "BUSY",
                "message_id": self.test_consultation_id,
                "faculty_name": "Dr. Smith",
                "timestamp": datetime.now().isoformat()
            }
            
            result = esp32_client.publish(response_topic, json.dumps(busy_response), qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"   ✅ ESP32 BUSY response sent")
            else:
                print(f"   ❌ ESP32 failed to send BUSY response (RC: {result.rc})")
                
            time.sleep(2)
            
            # Step 4: Test with string values (common ESP32 issue)
            print(f"\n📤 Step 4: Testing with string values (common ESP32 format)...")
            
            string_response = {
                "faculty_id": str(FACULTY_ID),              # STRING instead of int
                "response_type": "ACKNOWLEDGE",
                "message_id": str(self.test_consultation_id), # STRING instead of int
                "faculty_name": "Dr. Smith",
                "timestamp": datetime.now().isoformat()
            }
            
            result = esp32_client.publish(response_topic, json.dumps(string_response), qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"   ✅ ESP32 string response sent")
                print(f"   📋 String format: {string_response}")
            else:
                print(f"   ❌ ESP32 failed to send string response (RC: {result.rc})")
                
            time.sleep(3)
            
        except Exception as e:
            print(f"❌ Test error: {e}")
            
        finally:
            # Cleanup
            print(f"\n🧹 Cleaning up...")
            central_client.loop_stop()
            esp32_client.loop_stop()
            central_client.disconnect()
            esp32_client.disconnect()
            
        # Display results
        self.display_test_results()
        
    def display_test_results(self):
        """Display comprehensive test results"""
        print(f"\n📊 Complete MQTT Flow Test Results")
        print("=" * 80)
        
        print(f"📨 Messages Received: {len(self.messages_received)}")
        for i, msg in enumerate(self.messages_received, 1):
            print(f"   {i}. Topic: {msg['topic']}")
            print(f"      Time: {msg['timestamp']}")
            print(f"      Client: {msg['client']}")
            
        print(f"\n📤 Responses Received: {len(self.responses_received)}")
        for i, resp in enumerate(self.responses_received, 1):
            print(f"   {i}. Topic: {resp['topic']}")
            print(f"      Time: {resp['timestamp']}")
            print(f"      Client: {resp['client']}")
            print(f"      Payload: {resp['payload']}")
            
        # Analyze results
        print(f"\n🔍 Analysis:")
        
        esp32_received_consultation = any(msg['client'] == 'esp32_simulator' and 'messages' in msg['topic'] 
                                        for msg in self.messages_received)
        central_received_response = any(resp['client'] == 'central_system_test' and 'responses' in resp['topic'] 
                                      for resp in self.responses_received)
        
        if esp32_received_consultation:
            print(f"   ✅ ESP32 can receive consultations")
        else:
            print(f"   ❌ ESP32 did NOT receive consultations")
            
        if central_received_response:
            print(f"   ✅ Central system can receive ESP32 responses")
        else:
            print(f"   ❌ Central system did NOT receive ESP32 responses")
            
        if esp32_received_consultation and central_received_response:
            print(f"\n🎉 SUCCESS: Full MQTT flow is working!")
            print(f"   Your ESP32 should be able to communicate properly.")
        else:
            print(f"\n⚠️  ISSUES DETECTED:")
            if not esp32_received_consultation:
                print(f"   - ESP32 cannot receive consultation messages")
                print(f"   - Check ESP32 MQTT topic subscription")
            if not central_received_response:
                print(f"   - Central system cannot receive ESP32 responses") 
                print(f"   - Check central system MQTT subscription")
                
        print(f"\n💡 For ESP32 Code:")
        print(f"   Topic to subscribe: consultease/faculty/{FACULTY_ID}/messages")
        print(f"   Topic to publish: consultease/faculty/{FACULTY_ID}/responses")
        print(f"   Required response format:")
        print(f"   {{")
        print(f"     \"faculty_id\": {FACULTY_ID},")
        print(f"     \"response_type\": \"ACKNOWLEDGE\",")
        print(f"     \"message_id\": consultation_id")
        print(f"   }}")

def main():
    """Main function"""
    print("🔧 ConsultEase Complete MQTT Flow Tester")
    print("Testing end-to-end MQTT communication")
    print(f"Broker: {MQTT_SERVER}:{MQTT_PORT}")
    print()
    
    tester = CompleteMQTTFlowTester()
    tester.test_complete_flow()

if __name__ == "__main__":
    main() 