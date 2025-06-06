#!/usr/bin/env python3
"""
ConsultEase - BLE Connection Test Script

This script tests the BLE connection between the central system and the faculty desk unit.
It simulates both the BLE beacon and the faculty desk unit to verify proper communication.

Usage:
    python test_ble_connection.py [mode] [faculty_id]

Modes:
    beacon - Simulate a BLE beacon
    desk - Simulate a faculty desk unit
    test - Test both beacon and desk unit communication

Example:
    python test_ble_connection.py beacon 1
    python test_ble_connection.py desk 1
    python test_ble_connection.py test 1
"""

import sys
import time
import json
import logging
import threading
import paho.mqtt.client as mqtt
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default values
DEFAULT_FACULTY_ID = 1
DEFAULT_FACULTY_NAME = "Jeysibn"

# MQTT Configuration
MQTT_BROKER = "localhost"  # Replace with your MQTT broker IP address
MQTT_PORT = 1883
MQTT_TOPIC_REQUESTS = "consultease/faculty/%d/requests"
MQTT_TOPIC_STATUS = "consultease/faculty/%d/status"
MQTT_ALT_TOPIC_REQUESTS = "professor/messages"
MQTT_ALT_TOPIC_STATUS = "professor/status"
MQTT_CLIENT_ID = "ConsultEase_BLE_Test"

class BLEBeaconSimulator:
    """Simulate a BLE beacon for the faculty desk unit."""
    
    def __init__(self, faculty_id, faculty_name):
        """Initialize the BLE beacon simulator."""
        self.faculty_id = faculty_id
        self.faculty_name = faculty_name
        self.mqtt_client = None
        self.connected = False
        self.stop_flag = False
        
    def start(self):
        """Start the BLE beacon simulator."""
        logger.info(f"Starting BLE beacon simulator for faculty {self.faculty_name} (ID: {self.faculty_id})")
        
        # Connect to MQTT broker
        self.mqtt_client = mqtt.Client(f"BLEBeacon_{self.faculty_name}")
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_disconnect = self._on_disconnect
        
        try:
            logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            
            # Start beacon simulation
            self.beacon_thread = threading.Thread(target=self._beacon_worker)
            self.beacon_thread.daemon = True
            self.beacon_thread.start()
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def stop(self):
        """Stop the BLE beacon simulator."""
        logger.info("Stopping BLE beacon simulator")
        self.stop_flag = True
        
        if self.mqtt_client:
            # Send disconnected status
            self._publish_status(False)
            time.sleep(1)  # Give time for the message to be sent
            
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            self.connected = True
            
            # Publish initial status (connected)
            self._publish_status(True)
        else:
            logger.error(f"Failed to connect to MQTT broker with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker with code {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def _publish_status(self, connected):
        """Publish BLE beacon status."""
        if not self.connected:
            logger.warning("Cannot publish status: Not connected to MQTT broker")
            return
        
        status = "keychain_connected" if connected else "keychain_disconnected"
        
        # Publish to both topics for compatibility
        topic1 = MQTT_TOPIC_STATUS % self.faculty_id
        topic2 = MQTT_ALT_TOPIC_STATUS
        
        try:
            self.mqtt_client.publish(topic1, status)
            self.mqtt_client.publish(topic2, status)
            logger.info(f"Published status: {status}")
        except Exception as e:
            logger.error(f"Error publishing status: {e}")
    
    def _beacon_worker(self):
        """Worker thread for simulating BLE beacon behavior."""
        while not self.stop_flag:
            try:
                # Publish connected status every 30 seconds
                if self.connected:
                    self._publish_status(True)
                
                # Sleep for 30 seconds
                for _ in range(30):
                    if self.stop_flag:
                        break
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Error in beacon worker: {e}")
                time.sleep(5)  # Sleep a bit to avoid tight loop if there's an error

class FacultyDeskUnitSimulator:
    """Simulate a faculty desk unit."""
    
    def __init__(self, faculty_id, faculty_name):
        """Initialize the faculty desk unit simulator."""
        self.faculty_id = faculty_id
        self.faculty_name = faculty_name
        self.mqtt_client = None
        self.connected = False
        self.stop_flag = False
        self.ble_connected = False
    
    def start(self):
        """Start the faculty desk unit simulator."""
        logger.info(f"Starting faculty desk unit simulator for {self.faculty_name} (ID: {self.faculty_id})")
        
        # Connect to MQTT broker
        self.mqtt_client = mqtt.Client(f"DeskUnit_{self.faculty_name}")
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_disconnect = self._on_disconnect
        self.mqtt_client.on_message = self._on_message
        
        try:
            logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def stop(self):
        """Stop the faculty desk unit simulator."""
        logger.info("Stopping faculty desk unit simulator")
        self.stop_flag = True
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            self.connected = True
            
            # Subscribe to topics
            topic1 = MQTT_TOPIC_REQUESTS % self.faculty_id
            topic2 = MQTT_ALT_TOPIC_REQUESTS
            topic3 = MQTT_TOPIC_STATUS % self.faculty_id
            topic4 = MQTT_ALT_TOPIC_STATUS
            
            self.mqtt_client.subscribe(topic1)
            self.mqtt_client.subscribe(topic2)
            self.mqtt_client.subscribe(topic3)
            self.mqtt_client.subscribe(topic4)
            
            logger.info(f"Subscribed to topics: {topic1}, {topic2}, {topic3}, {topic4}")
        else:
            logger.error(f"Failed to connect to MQTT broker with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker with code {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Callback when message is received."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.info(f"Received message on topic {topic}: {payload}")
            
            # Handle status updates
            if topic == MQTT_TOPIC_STATUS % self.faculty_id or topic == MQTT_ALT_TOPIC_STATUS:
                if payload == "keychain_connected":
                    self.ble_connected = True
                    logger.info("BLE beacon connected")
                elif payload == "keychain_disconnected":
                    self.ble_connected = False
                    logger.info("BLE beacon disconnected")
            
            # Handle consultation requests
            elif topic == MQTT_TOPIC_REQUESTS % self.faculty_id or topic == MQTT_ALT_TOPIC_REQUESTS:
                logger.info("Received consultation request:")
                logger.info("-" * 40)
                logger.info(payload)
                logger.info("-" * 40)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

def main():
    """Main function."""
    # Parse command line arguments
    mode = "test"
    faculty_id = DEFAULT_FACULTY_ID
    faculty_name = DEFAULT_FACULTY_NAME
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    
    if len(sys.argv) > 2:
        try:
            faculty_id = int(sys.argv[2])
        except ValueError:
            logger.error(f"Invalid faculty ID: {sys.argv[2]}. Using default: {DEFAULT_FACULTY_ID}")
    
    # Run the appropriate simulator
    if mode == "beacon":
        beacon = BLEBeaconSimulator(faculty_id, faculty_name)
        if beacon.start():
            try:
                logger.info("Press Ctrl+C to stop")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Stopping...")
            finally:
                beacon.stop()
    
    elif mode == "desk":
        desk = FacultyDeskUnitSimulator(faculty_id, faculty_name)
        if desk.start():
            try:
                logger.info("Press Ctrl+C to stop")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Stopping...")
            finally:
                desk.stop()
    
    elif mode == "test":
        # Start both simulators
        beacon = BLEBeaconSimulator(faculty_id, faculty_name)
        desk = FacultyDeskUnitSimulator(faculty_id, faculty_name)
        
        if beacon.start() and desk.start():
            try:
                logger.info("Press Ctrl+C to stop")
                
                # Simulate some consultation requests
                time.sleep(5)  # Wait for connections to establish
                
                # Create MQTT client for sending test messages
                test_client = mqtt.Client("ConsultEase_Test_Client")
                test_client.connect(MQTT_BROKER, MQTT_PORT, 60)
                
                # Send a test consultation request
                topic = MQTT_TOPIC_REQUESTS % faculty_id
                message = f"Student: Test Student\nCourse: CS101\nRequest: Test consultation request at {datetime.now().strftime('%H:%M:%S')}"
                test_client.publish(topic, message)
                logger.info(f"Sent test consultation request to {topic}")
                
                # Wait a bit
                time.sleep(5)
                
                # Send another test message
                topic = MQTT_ALT_TOPIC_REQUESTS
                message = f"Student: Another Student\nCourse: CS202\nRequest: Another test request at {datetime.now().strftime('%H:%M:%S')}"
                test_client.publish(topic, message)
                logger.info(f"Sent test consultation request to {topic}")
                
                # Disconnect test client
                test_client.disconnect()
                
                # Keep running until interrupted
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Stopping...")
            finally:
                beacon.stop()
                desk.stop()
    
    else:
        logger.error(f"Invalid mode: {mode}. Valid modes are: beacon, desk, test")
        print(__doc__)

if __name__ == "__main__":
    main()
