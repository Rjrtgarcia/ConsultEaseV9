#!/usr/bin/env python3
"""
MQTT Permission Testing Script for ConsultEase
Tests the MQTT broker permissions after applying the fix

This script simulates:
1. Central system sending consultation messages
2. ESP32 faculty desk receiving messages
3. ESP32 publishing responses (the key test)
4. Central system receiving responses

Usage: python3 scripts/test_mqtt_permissions.py
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
FACULTY_USER = "faculty_desk"
FACULTY_PASSWORD = "desk_password"
CENTRAL_USER = "central_system"
CENTRAL_PASSWORD = "central_secure_password"
FACULTY_ID = 1

class MQTTPermissionTester:
    def __init__(self):
        self.test_results = {
            'central_connect': False,
            'faculty_connect': False,
            'central_can_send': False,
            'faculty_can_receive': False,
            'faculty_can_publish_response': False,
            'central_can_receive_response': False
        }
        self.messages_received = []
        self.responses_received = []
        
    def create_client(self, client_id, username, password):
        """Create and configure MQTT client"""
        client = mqtt.Client(client_id)
        client.username_pw_set(username, password)
        client.on_connect = lambda c, u, f, rc: self.on_connect(c, u, f, rc, client_id)
        client.on_message = lambda c, u, msg: self.on_message(c, u, msg, client_id)
        client.on_publish = lambda c, u, mid: self.on_publish(c, u, mid, client_id)
        return client
        
    def on_connect(self, client, userdata, flags, rc, client_id):
        """Connection callback"""
        if rc == 0:
            print(f"✅ {client_id} connected successfully")
            if client_id == "central_system":
                self.test_results['central_connect'] = True
            elif client_id == "faculty_desk":
                self.test_results['faculty_connect'] = True
        else:
            print(f"❌ {client_id} connection failed (RC: {rc})")
            
    def on_message(self, client, userdata, msg, client_id):
        """Message received callback"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            print(f"📨 {client_id} received message:")
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
                if client_id == "faculty_desk":
                    self.test_results['faculty_can_receive'] = True
                    
            elif "responses" in topic:
                self.responses_received.append({
                    'topic': topic,
                    'payload': payload,
                    'client': client_id,
                    'timestamp': timestamp
                })
                if client_id == "central_system":
                    self.test_results['central_can_receive_response'] = True
                    
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            
    def on_publish(self, client, userdata, mid, client_id):
        """Message published callback"""
        print(f"✅ {client_id} published message (MID: {mid})")
        
    def test_permissions(self):
        """Run comprehensive permission tests"""
        print("🚀 Starting MQTT Permission Test Suite")
        print("=" * 60)
        
        # Create clients
        print("🔧 Creating MQTT clients...")
        central_client = self.create_client("central_system", CENTRAL_USER, CENTRAL_PASSWORD)
        faculty_client = self.create_client("faculty_desk", FACULTY_USER, FACULTY_PASSWORD)
        
        try:
            # Connect clients
            print(f"\n🔌 Connecting to MQTT broker at {MQTT_SERVER}:{MQTT_PORT}...")
            central_client.connect(MQTT_SERVER, MQTT_PORT, 60)
            faculty_client.connect(MQTT_SERVER, MQTT_PORT, 60)
            
            # Start network loops
            central_client.loop_start()
            faculty_client.loop_start()
            
            # Wait for connections
            time.sleep(2)
            
            # Test 1: Subscribe to topics
            print(f"\n📡 Setting up subscriptions...")
            
            # Faculty subscribes to messages (should work)
            faculty_client.subscribe(f"consultease/faculty/{FACULTY_ID}/messages", qos=1)
            
            # Central subscribes to responses (should work) 
            central_client.subscribe(f"consultease/faculty/{FACULTY_ID}/responses", qos=1)
            central_client.subscribe(f"consultease/faculty/{FACULTY_ID}/status", qos=1)
            
            time.sleep(1)
            
            # Test 2: Central system sends consultation message
            print(f"\n📤 Test 2: Central system sending consultation...")
            consultation_message = {
                "id": 12345,
                "student_id": 1,
                "student_name": "John Doe",
                "student_department": "Computer Science",
                "faculty_id": FACULTY_ID,
                "faculty_name": "Dr. Smith",
                "request_message": "Permission test consultation message",
                "course_code": "CS101",
                "status": "PENDING",
                "requested_at": datetime.now().isoformat()
            }
            
            message_topic = f"consultease/faculty/{FACULTY_ID}/messages"
            result = central_client.publish(message_topic, json.dumps(consultation_message), qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"   ✅ Central system sent consultation message")
                self.test_results['central_can_send'] = True
            else:
                print(f"   ❌ Central system failed to send message (RC: {result.rc})")
                
            time.sleep(2)
            
            # Test 3: Faculty publishes response (THE KEY TEST)
            print(f"\n📤 Test 3: Faculty publishing response (KEY TEST)...")
            response_message = {
                "consultation_id": 12345,
                "faculty_id": FACULTY_ID,
                "response": "ACKNOWLEDGED",
                "status": "BUSY",
                "timestamp": datetime.now().isoformat(),
                "test": "permission_verification"
            }
            
            response_topic = f"consultease/faculty/{FACULTY_ID}/responses"
            result = faculty_client.publish(response_topic, json.dumps(response_message), qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"   ✅ Faculty desk published response successfully!")
                print(f"   🎉 PERMISSION ISSUE FIXED!")
                self.test_results['faculty_can_publish_response'] = True
            else:
                print(f"   ❌ Faculty desk failed to publish response (RC: {result.rc})")
                print(f"   ⚠️  Permission issue still exists")
                
            time.sleep(2)
            
            # Test 4: Faculty publishes status
            print(f"\n📤 Test 4: Faculty publishing status...")
            status_message = {
                "faculty_id": FACULTY_ID,
                "status": "available",
                "timestamp": datetime.now().isoformat(),
                "test": "status_update"
            }
            
            status_topic = f"consultease/faculty/{FACULTY_ID}/status"
            result = faculty_client.publish(status_topic, json.dumps(status_message), qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"   ✅ Faculty desk published status update")
            else:
                print(f"   ❌ Faculty desk failed to publish status (RC: {result.rc})")
                
            time.sleep(2)
            
            # Test 5: Test legacy topics
            print(f"\n📤 Test 5: Testing legacy topic support...")
            legacy_topic = f"faculty/{FACULTY_ID}/responses"
            result = faculty_client.publish(legacy_topic, json.dumps(response_message), qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"   ✅ Legacy topic publishing works")
            else:
                print(f"   ❌ Legacy topic publishing failed (RC: {result.rc})")
            
            time.sleep(3)
            
        except Exception as e:
            print(f"❌ Test error: {e}")
            
        finally:
            # Cleanup
            print(f"\n🧹 Cleaning up...")
            central_client.loop_stop()
            faculty_client.loop_stop()
            central_client.disconnect()
            faculty_client.disconnect()
            
        # Display results
        self.display_test_results()
        
    def display_test_results(self):
        """Display comprehensive test results"""
        print(f"\n📊 MQTT Permission Test Results")
        print("=" * 60)
        
        tests = [
            ("Central System Connection", self.test_results['central_connect']),
            ("Faculty Desk Connection", self.test_results['faculty_connect']),
            ("Central Can Send Messages", self.test_results['central_can_send']),
            ("Faculty Can Receive Messages", self.test_results['faculty_can_receive']),
            ("Faculty Can Publish Responses", self.test_results['faculty_can_publish_response']),
            ("Central Can Receive Responses", self.test_results['central_can_receive_response'])
        ]
        
        all_passed = True
        for test_name, result in tests:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name:<30} {status}")
            if not result:
                all_passed = False
                
        print(f"\n📈 Summary:")
        print(f"   Messages Received: {len(self.messages_received)}")
        print(f"   Responses Received: {len(self.responses_received)}")
        
        if self.test_results['faculty_can_publish_response']:
            print(f"\n🎉 SUCCESS: Faculty desk can now publish responses!")
            print(f"   The MQTT permission issue has been FIXED!")
        else:
            print(f"\n⚠️  ISSUE: Faculty desk still cannot publish responses")
            print(f"   The permission fix may need additional work")
            
        print(f"\n💡 Key Test Result:")
        key_test_status = "FIXED ✅" if self.test_results['faculty_can_publish_response'] else "BROKEN ❌"
        print(f"   ESP32 → Central System: {key_test_status}")
        
        if all_passed:
            print(f"\n🚀 All tests passed! The ESP32 should now work correctly.")
        else:
            print(f"\n🔧 Some tests failed. Check the MQTT broker configuration.")
            
        return all_passed

def main():
    """Main function"""
    print("🔧 ConsultEase MQTT Permission Tester")
    print("Testing MQTT broker permissions for faculty desk units")
    print(f"Broker: {MQTT_SERVER}:{MQTT_PORT}")
    print()
    
    tester = MQTTPermissionTester()
    success = tester.test_permissions()
    
    if success:
        print(f"\n✅ All MQTT permissions are working correctly!")
        print(f"🎯 Your ESP32 faculty desk unit should now be able to:")
        print(f"   - Receive consultation messages")
        print(f"   - Send button responses")
        print(f"   - Update faculty status")
        sys.exit(0)
    else:
        print(f"\n❌ Some MQTT permissions are not working.")
        print(f"🔧 Run the permission fix script:")
        print(f"   sudo bash scripts/fix_mqtt_permissions.sh")
        sys.exit(1)

if __name__ == "__main__":
    main() 