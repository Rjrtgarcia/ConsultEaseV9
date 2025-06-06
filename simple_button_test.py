#!/usr/bin/env python3
"""
Simple ESP32 Button Response Test

This script sends MQTT messages simulating ESP32 button responses
to test if the central system receives and processes them.

Usage: python simple_button_test.py
"""

import time
import json
import logging
import paho.mqtt.client as mqtt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BROKER = "172.20.10.8"  # Use the broker that worked in your previous test
PORT = 1883
FACULTY_ID = 1

# MQTT Topics
RESPONSE_TOPIC = f"consultease/faculty/{FACULTY_ID}/responses"

class SimpleButtonTester:
    def __init__(self):
        self.client = mqtt.Client("SimpleButtonTester")
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            logger.info(f"✅ Connected to MQTT broker at {BROKER}:{PORT}")
            # Subscribe to notifications to see responses
            client.subscribe("consultease/system/notifications")
            logger.info("📬 Subscribed to system notifications")
        else:
            logger.error(f"❌ Failed to connect, return code: {rc}")
    
    def on_publish(self, client, userdata, mid):
        logger.info(f"📤 Message published (MID: {mid})")
    
    def on_message(self, client, userdata, msg):
        logger.info(f"📥 Received: {msg.topic} - {msg.payload.decode()}")
    
    def connect(self):
        try:
            logger.info(f"🔌 Connecting to {BROKER}:{PORT}...")
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_start()
            
            # Wait for connection
            for i in range(50):  # 5 second timeout
                if self.connected:
                    return True
                time.sleep(0.1)
            
            logger.error("❌ Connection timeout")
            return False
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def send_button_response(self, consultation_id, response_type):
        """Send a button response like ESP32 would."""
        logger.info("=" * 50)
        logger.info(f"🔘 SENDING {response_type} BUTTON RESPONSE")
        logger.info("=" * 50)
        
        # Create response data exactly like ESP32 sends
        response_data = {
            "faculty_id": FACULTY_ID,
            "faculty_name": "Dave Jomillo", 
            "response_type": response_type,
            "message_id": str(consultation_id),
            "original_message": "Test consultation request",
            "timestamp": str(int(time.time() * 1000)),
            "faculty_present": True,
            "response_method": "physical_button",
            "status": f"Professor {response_type.lower()}s the request"
        }
        
        logger.info(f"📨 Sending to: {RESPONSE_TOPIC}")
        logger.info(f"📄 Data: {json.dumps(response_data, indent=2)}")
        
        result = self.client.publish(RESPONSE_TOPIC, json.dumps(response_data), qos=2)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"✅ {response_type} response sent successfully")
            return True
        else:
            logger.error(f"❌ Failed to send {response_type} response")
            return False
    
    def run_test(self):
        """Run the button response test."""
        logger.info("🚀 Starting Simple Button Response Test")
        logger.info("=" * 60)
        
        if not self.connect():
            return False
        
        # Test with some consultation IDs
        test_cases = [
            (123, "ACKNOWLEDGE"),
            (124, "BUSY"),
            (125, "ACKNOWLEDGE") 
        ]
        
        logger.info("📋 This test will send ESP32-style button responses.")
        logger.info("📋 Watch your central system logs for:")
        logger.info("   🔥 FACULTY RESPONSE HANDLER TRIGGERED")
        logger.info("   ✅ Successfully updated consultation")
        logger.info("")
        
        for consultation_id, response_type in test_cases:
            logger.info(f"🧪 Test {consultation_id}: {response_type}")
            
            if self.send_button_response(consultation_id, response_type):
                logger.info("⏳ Waiting 3 seconds...")
                time.sleep(3)
            else:
                logger.error(f"❌ Failed to send {response_type} for consultation {consultation_id}")
            
            logger.info("")  # Empty line for readability
        
        logger.info("🏁 Test completed!")
        logger.info("🔍 Check your central system logs to see if Faculty Response Controller")
        logger.info("   received and processed these button responses.")
        
        # Wait a bit to see any responses
        logger.info("⏳ Waiting 10 seconds for any system responses...")
        time.sleep(10)
        
        return True
    
    def cleanup(self):
        self.client.loop_stop()
        self.client.disconnect()

def main():
    logger.info("🔧 Simple ESP32 Button Response Test")
    logger.info("This sends MQTT messages like ESP32 button presses")
    logger.info("=" * 60)
    
    tester = SimpleButtonTester()
    
    try:
        success = tester.run_test()
        if success:
            logger.info("✅ Test messages sent successfully!")
        else:
            logger.error("❌ Test failed")
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main() 