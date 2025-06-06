#!/usr/bin/env python3
"""
MQTT Broker Test Script for ConsultEase
Tests MQTT connectivity, topic permissions, and message flow
"""

import paho.mqtt.client as mqtt
import json
import time
import threading
import sys

# MQTT Configuration (update these to match your setup)
MQTT_SERVER = "172.20.10.8"
MQTT_PORT = 1883
MQTT_USERNAME = "faculty_desk"
MQTT_PASSWORD = "desk_password"
FACULTY_ID = 1

class MQTTTester:
    def __init__(self):
        self.received_messages = []
        self.client = mqtt.Client()
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        # Set up callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.on_publish = self.on_publish
        self.client.on_disconnect = self.on_disconnect
        
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Connected to MQTT broker (RC: {rc})")
            self.connected = True
        else:
            print(f"❌ Failed to connect to MQTT broker (RC: {rc})")
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable", 
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorised"
            }
            print(f"   Error: {error_messages.get(rc, 'Unknown error')}")
            
    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8')
            print(f"📨 Received message:")
            print(f"   Topic: {msg.topic}")
            print(f"   Payload: {payload}")
            print(f"   QoS: {msg.qos}")
            print(f"   Retained: {msg.retain}")
            
            self.received_messages.append({
                'topic': msg.topic,
                'payload': payload,
                'timestamp': time.time()
            })
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            
    def on_subscribe(self, client, userdata, mid, granted_qos):
        print(f"✅ Subscription successful (QoS: {granted_qos})")
        
    def on_publish(self, client, userdata, mid):
        print(f"✅ Message published (MID: {mid})")
        
    def on_disconnect(self, client, userdata, rc):
        print(f"🔌 Disconnected from MQTT broker (RC: {rc})")
        self.connected = False
        
    def connect(self):
        print(f"🔌 Connecting to MQTT broker {MQTT_SERVER}:{MQTT_PORT}...")
        try:
            self.client.connect(MQTT_SERVER, MQTT_PORT, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
                
            if not self.connected:
                print("❌ Connection timeout")
                return False
                
            return True
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
            
    def test_faculty_topics(self):
        """Test faculty-specific topics"""
        print(f"\n🧪 Testing Faculty {FACULTY_ID} Topics...")
        
        # Topics to test
        topics = [
            f"consultease/faculty/{FACULTY_ID}/status",
            f"consultease/faculty/{FACULTY_ID}/messages", 
            f"consultease/faculty/{FACULTY_ID}/responses",
            f"consultease/faculty/{FACULTY_ID}/heartbeat",
            f"faculty/{FACULTY_ID}/status",  # Legacy topic
        ]
        
        # Subscribe to response topic to catch ESP32 messages
        response_topic = f"consultease/faculty/{FACULTY_ID}/responses"
        print(f"📡 Subscribing to {response_topic}...")
        self.client.subscribe(response_topic, qos=1)
        time.sleep(1)
        
        # Test publishing to each topic
        for topic in topics:
            print(f"\n📤 Testing publish to: {topic}")
            
            test_payload = {
                "test": "broker_connectivity",
                "timestamp": int(time.time()),
                "topic": topic,
                "faculty_id": FACULTY_ID
            }
            
            try:
                result = self.client.publish(topic, json.dumps(test_payload), qos=1)
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(f"   ✅ Publish SUCCESS (MID: {result.mid})")
                else:
                    print(f"   ❌ Publish FAILED (RC: {result.rc})")
            except Exception as e:
                print(f"   ❌ Publish ERROR: {e}")
                
        # Wait for any responses
        print(f"\n⏳ Waiting 5 seconds for ESP32 responses...")
        time.sleep(5)
        
    def test_consultation_flow(self):
        """Test a complete consultation message flow"""
        print(f"\n🔄 Testing Consultation Flow...")
        
        # Subscribe to response topic
        response_topic = f"consultease/faculty/{FACULTY_ID}/responses"
        self.client.subscribe(response_topic, qos=1)
        
        # Send a test consultation
        message_topic = f"consultease/faculty/{FACULTY_ID}/messages"
        consultation_data = {
            "id": 999,
            "student_id": 1,
            "student_name": "Test Student",
            "student_department": "Test Department",
            "faculty_id": FACULTY_ID,
            "faculty_name": "Test Faculty",
            "request_message": "This is a test consultation message",
            "course_code": "TEST101",
            "status": "PENDING",
            "requested_at": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        print(f"📤 Sending test consultation to {message_topic}...")
        result = self.client.publish(message_topic, json.dumps(consultation_data), qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"   ✅ Consultation sent successfully")
            print(f"   💡 ESP32 should display: 'Test Student: This is a test consultation message'")
            print(f"   💡 Press ACKNOWLEDGE or BUSY button on ESP32 to test response")
            
            # Wait for faculty response
            print(f"⏳ Waiting 30 seconds for faculty button response...")
            start_time = time.time()
            initial_count = len(self.received_messages)
            
            while (time.time() - start_time) < 30:
                if len(self.received_messages) > initial_count:
                    print(f"🎉 Received faculty response!")
                    break
                time.sleep(1)
            else:
                print(f"⚠️  No response received - check ESP32 and button press")
        else:
            print(f"   ❌ Failed to send consultation (RC: {result.rc})")
            
    def run_full_test(self):
        """Run complete MQTT test suite"""
        print("🚀 Starting MQTT Broker Test Suite")
        print("=" * 50)
        
        if not self.connect():
            print("❌ Cannot connect to MQTT broker - check configuration")
            return False
            
        # Test topics
        self.test_faculty_topics()
        
        # Test consultation flow  
        self.test_consultation_flow()
        
        # Show summary
        print(f"\n📊 Test Summary:")
        print(f"   Messages received: {len(self.received_messages)}")
        for msg in self.received_messages:
            print(f"   - {msg['topic']}: {msg['payload'][:50]}...")
            
        print(f"\n🔌 Disconnecting...")
        self.client.loop_stop()
        self.client.disconnect()
        
        return True

def main():
    print("MQTT Broker Test for ConsultEase")
    print("This script tests MQTT connectivity and topic permissions")
    print(f"Broker: {MQTT_SERVER}:{MQTT_PORT}")
    print(f"Username: {MQTT_USERNAME}")
    print(f"Faculty ID: {FACULTY_ID}")
    print()
    
    input("Press Enter to start testing... ")
    
    tester = MQTTTester()
    success = tester.run_full_test()
    
    if success:
        print("\n✅ MQTT test completed - check results above")
    else:
        print("\n❌ MQTT test failed - check broker configuration")
        
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 