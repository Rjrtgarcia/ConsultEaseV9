#!/usr/bin/env python3
"""
Test ESP32 Communication Script

This script simulates ESP32 communication to test if the central system
can receive and process faculty response messages properly.

Usage:
    python scripts/test_esp32_communication.py
"""

import sys
import time
import json
import logging
import socket
import paho.mqtt.client as mqtt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MQTT Configuration - Try multiple possible broker addresses
POSSIBLE_BROKERS = [
    "192.168.1.100",    # ESP32 configured address
    "localhost",        # Default central system
    "127.0.0.1",        # Localhost IP
    "172.20.10.8",      # Alternative from templates
]
PORT = 1883
FACULTY_ID = 1

# Topics
RESPONSES_TOPIC = f"consultease/faculty/{FACULTY_ID}/responses"
MESSAGES_TOPIC = f"consultease/faculty/{FACULTY_ID}/messages"

def test_broker_connectivity(host, port, timeout=3):
    """Test if a broker is accessible."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        logger.debug(f"Connection test failed for {host}:{port} - {e}")
        return False

def find_mqtt_broker():
    """Find an accessible MQTT broker from the list."""
    logger.info("🔍 Searching for accessible MQTT brokers...")
    
    for broker in POSSIBLE_BROKERS:
        logger.info(f"   Testing {broker}:{PORT}...")
        if test_broker_connectivity(broker, PORT):
            logger.info(f"✅ Found accessible broker: {broker}:{PORT}")
            return broker
        else:
            logger.info(f"❌ Cannot reach {broker}:{PORT}")
    
    logger.error("❌ No accessible MQTT brokers found!")
    logger.info("💡 Tips:")
    logger.info("   1. Make sure MQTT broker is running")
    logger.info("   2. Check firewall settings")
    logger.info("   3. Verify the broker IP address")
    logger.info("   4. Try running: mosquitto_pub -h <broker_ip> -t test -m 'hello'")
    return None

class ESP32CommunicationTester:
    """Test ESP32 communication with central system."""
    
    def __init__(self, broker_host):
        self.broker_host = broker_host
        self.client = mqtt.Client("ESP32_Communication_Tester")
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message
        self.connected = False
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection."""
        if rc == 0:
            self.connected = True
            logger.info(f"✅ Connected to MQTT broker at {self.broker_host}:{PORT}")
            
            # Subscribe to see if we get anything back
            client.subscribe("consultease/system/notifications")
            client.subscribe("consultease/#")  # Subscribe to all ConsultEase topics
            logger.info("📬 Subscribed to system notifications and all topics")
        else:
            self.connected = False
            logger.error(f"❌ Failed to connect to MQTT broker, return code: {rc}")
    
    def on_publish(self, client, userdata, mid):
        """Callback for published messages."""
        logger.info(f"📤 Message published successfully (MID: {mid})")
    
    def on_message(self, client, userdata, msg):
        """Callback for received messages."""
        logger.info(f"📥 Received response: {msg.topic} - {msg.payload.decode()}")
    
    def connect(self):
        """Connect to MQTT broker."""
        try:
            logger.info(f"🔌 Connecting to MQTT broker at {self.broker_host}:{PORT}...")
            self.client.connect(self.broker_host, PORT, 60)
            self.client.loop_start()
            
            # Wait for connection with timeout
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.connected:
                logger.info("✅ MQTT connection established successfully")
                return True
            else:
                logger.error("❌ MQTT connection timeout")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
    
    def send_test_consultation_message(self):
        """Send a test consultation message to ESP32."""
        logger.info("=" * 60)
        logger.info("SENDING TEST CONSULTATION MESSAGE")
        logger.info("=" * 60)
        
        # Create test consultation message (simulating central system)
        consultation_id = int(time.time())
        message = f"CID:{consultation_id} From:Test Student (SID:123): Please help me with my project"
        
        logger.info(f"📨 Sending to topic: {MESSAGES_TOPIC}")
        logger.info(f"📨 Message: {message}")
        
        result = self.client.publish(MESSAGES_TOPIC, message, qos=2)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info("✅ Test consultation message sent successfully")
            return consultation_id
        else:
            logger.error(f"❌ Failed to send message, error code: {result.rc}")
            return None
    
    def send_test_button_response(self, consultation_id):
        """Send a test button response (simulating ESP32)."""
        logger.info("=" * 60)
        logger.info("SENDING TEST BUTTON RESPONSE")
        logger.info("=" * 60)
        
        # Create ESP32 button response
        response_data = {
            "faculty_id": FACULTY_ID,
            "faculty_name": "Dave Jomillo",
            "response_type": "ACKNOWLEDGE",
            "message_id": str(consultation_id),
            "original_message": "Test consultation request",
            "timestamp": str(int(time.time() * 1000)),
            "faculty_present": True,
            "response_method": "physical_button",
            "status": "Professor acknowledges the request and will respond accordingly"
        }
        
        logger.info(f"📨 Sending to topic: {RESPONSES_TOPIC}")
        logger.info(f"📨 Response data: {json.dumps(response_data, indent=2)}")
        
        result = self.client.publish(RESPONSES_TOPIC, json.dumps(response_data), qos=2)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info("✅ Test button response sent successfully")
            return True
        else:
            logger.error(f"❌ Failed to send response, error code: {result.rc}")
            return False
    
    def run_test(self):
        """Run the complete communication test."""
        logger.info("🚀 Starting ESP32 communication test...")
        
        if not self.connect():
            return False
        
        # Step 1: Send consultation message (central system → ESP32)
        consultation_id = self.send_test_consultation_message()
        if not consultation_id:
            return False
        
        # Wait a bit
        time.sleep(3)
        
        # Step 2: Send button response (ESP32 → central system)
        success = self.send_test_button_response(consultation_id)
        if not success:
            return False
        
        # Wait for any responses
        logger.info("⏳ Waiting for central system to process the response...")
        time.sleep(10)
        
        # Step 3: Send BUSY response as well
        response_data = {
            "faculty_id": FACULTY_ID,
            "faculty_name": "Dave Jomillo",
            "response_type": "BUSY",
            "message_id": str(consultation_id + 1),
            "original_message": "Another test consultation request",
            "timestamp": str(int(time.time() * 1000)),
            "faculty_present": True,
            "response_method": "physical_button",
            "status": "Professor is currently busy and cannot cater to this request"
        }
        
        logger.info("📨 Sending BUSY response test...")
        self.client.publish(RESPONSES_TOPIC, json.dumps(response_data), qos=2)
        
        # Final wait
        time.sleep(5)
        
        logger.info("✅ ESP32 communication test completed!")
        logger.info("🔍 Check central system logs for faculty response handling")
        
        return True
    
    def cleanup(self):
        """Clean up MQTT connection."""
        self.client.loop_stop()
        self.client.disconnect()

def main():
    """Main function."""
    logger.info("🔍 ESP32 Communication Test - Broker Discovery & Testing")
    logger.info("=" * 70)
    
    # Find accessible broker
    broker_host = find_mqtt_broker()
    if not broker_host:
        logger.error("❌ Cannot proceed without an accessible MQTT broker")
        logger.info("📋 To set up a local MQTT broker:")
        logger.info("   sudo apt-get install mosquitto mosquitto-clients")
        logger.info("   sudo systemctl start mosquitto")
        logger.info("   sudo systemctl enable mosquitto")
        return False
    
    # Run the test
    tester = ESP32CommunicationTester(broker_host)
    
    try:
        success = tester.run_test()
        if success:
            logger.info("🎉 Test completed successfully")
            logger.info("🔍 If ESP32 is connected, it should:")
            logger.info("   1. Display the test consultation message")
            logger.info("   2. Allow button responses")
            logger.info("🔍 If central system is running, it should:")
            logger.info("   1. Log faculty response handling")
            logger.info("   2. Update consultation status in database")
        else:
            logger.error("❌ Test failed")
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main() 