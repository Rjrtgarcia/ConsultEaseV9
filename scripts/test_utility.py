#!/usr/bin/env python3
"""
ConsultEase - Unified Testing Utility

This script provides a unified interface for testing various components of the ConsultEase system:
1. Faculty Desk Unit testing via MQTT
2. BLE beacon simulation for faculty presence detection
3. MQTT monitoring and message publishing

Usage:
    python test_utility.py [command] [options]

Commands:
    mqtt-test       - Test MQTT communication with faculty desk unit
    faculty-desk    - Send test messages to faculty desk unit
    ble-beacon      - Simulate a BLE beacon for faculty presence detection
    monitor         - Monitor all MQTT messages on the broker

Examples:
    python test_utility.py mqtt-test --broker 192.168.1.100
    python test_utility.py faculty-desk --faculty-id 3 --message "Test message"
    python test_utility.py ble-beacon --faculty-id 2
    python test_utility.py monitor --broker 192.168.1.100
"""

import sys
import time
import json
import random
import argparse
import logging
import paho.mqtt.client as mqtt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default values
DEFAULT_BROKER = "192.168.1.100"
DEFAULT_PORT = 1883
DEFAULT_FACULTY_ID = 1
DEFAULT_FACULTY_NAME = "Jeysibn"
DEFAULT_MESSAGE = "Test consultation request from a student. Please check your schedule for availability."

# MQTT Topics
TOPIC_REQUESTS_JSON = "consultease/faculty/{}/requests"
TOPIC_REQUESTS_TEXT = "professor/messages"
TOPIC_FACULTY_MESSAGES = "consultease/faculty/{}/messages"
TOPIC_STATUS = "consultease/faculty/{}/status"
TOPIC_SYSTEM_PING = "consultease/system/ping"

# Message received counter
messages_received = 0

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the MQTT broker."""
    if rc == 0:
        logger.info(f"Connected to MQTT broker at {userdata['broker']}:{userdata['port']}")
        
        # Subscribe to topics if needed
        if userdata.get('subscribe_all', False):
            topics = [
                TOPIC_REQUESTS_JSON.format(userdata['faculty_id']),
                TOPIC_REQUESTS_TEXT,
                TOPIC_FACULTY_MESSAGES.format(userdata['faculty_id']),
                TOPIC_STATUS.format(userdata['faculty_id']),
                TOPIC_SYSTEM_PING,
                # Add wildcard subscription to catch all messages
                "consultease/#",
                "professor/#"
            ]
            
            for topic in topics:
                client.subscribe(topic)
                logger.info(f"Subscribed to topic: {topic}")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code: {rc}")

def on_message(client, userdata, msg):
    """Callback for when a message is received from the MQTT broker."""
    global messages_received
    messages_received += 1
    
    topic = msg.topic
    try:
        payload = msg.payload.decode('utf-8')
        logger.info(f"Received message #{messages_received} on topic {topic}")
        logger.info(f"Payload: {payload}")
        
        # Try to parse as JSON for better display
        try:
            json_payload = json.loads(payload)
            logger.info(f"JSON content: {json.dumps(json_payload, indent=2)}")
        except json.JSONDecodeError:
            # Not JSON, which is fine for text messages
            pass
    except Exception as e:
        logger.error(f"Error processing message on {topic}: {e}")

def on_publish(client, userdata, mid):
    """Callback for when a message is published to the MQTT broker."""
    logger.info(f"Message published with ID: {mid}")

def on_disconnect(client, userdata, rc):
    """Callback for when the client disconnects from the MQTT broker."""
    if rc != 0:
        logger.warning(f"Unexpected disconnection from MQTT broker, code: {rc}")
    else:
        logger.info("Disconnected from MQTT broker")

# Command Functions
def mqtt_test(args):
    """Run comprehensive MQTT tests with the faculty desk unit."""
    logger.info("Starting comprehensive MQTT test...")
    
    # Create MQTT client
    client_id = f"ConsultEase_MQTT_Test_{int(time.time())}"
    client = mqtt.Client(client_id)
    
    # Set user data for callbacks
    userdata = {
        'broker': args.broker,
        'port': args.port,
        'faculty_id': args.faculty_id,
        'subscribe_all': True
    }
    client.user_data_set(userdata)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    
    try:
        # Connect to MQTT broker
        logger.info(f"Connecting to MQTT broker at {args.broker}:{args.port}")
        client.connect(args.broker, args.port, 60)
        
        # Start the MQTT client loop in a separate thread
        client.loop_start()
        
        # Wait for connection to establish
        time.sleep(2)
        
        if not args.monitor_only:
            # Send test messages
            send_test_messages(client, args.faculty_id, args.faculty_name)
            
            # Wait for messages to be processed
            logger.info("Waiting for messages to be processed...")
            time.sleep(5)
            
            # Send another round of test messages
            logger.info("Sending another round of test messages...")
            send_test_messages(client, args.faculty_id, args.faculty_name)
        
        # Keep the script running to monitor messages
        logger.info("Monitoring MQTT messages. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Exiting...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Disconnect from MQTT broker
        client.loop_stop()
        client.disconnect()
        logger.info("Disconnected from MQTT broker")

def faculty_desk(args):
    """Send a test message to the faculty desk unit."""
    logger.info(f"Sending test message to faculty ID {args.faculty_id}...")
    
    # Create MQTT client
    client_id = f"ConsultEase_FacultyDesk_Test_{int(time.time())}"
    client = mqtt.Client(client_id)
    
    # Set user data for callbacks
    userdata = {
        'broker': args.broker,
        'port': args.port,
        'faculty_id': args.faculty_id,
        'subscribe_all': False
    }
    client.user_data_set(userdata)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    
    # Connect to MQTT broker
    try:
        client.connect(args.broker, args.port, 60)
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {e}")
        return
    
    # Start the MQTT client loop in a separate thread
    client.loop_start()
    
    # Wait for connection to establish
    time.sleep(1)
    
    # Subscribe to status topic to see if the faculty desk unit is connected
    status_topic = TOPIC_STATUS.format(args.faculty_id)
    client.subscribe(status_topic)
    logger.info(f"Subscribed to topic: {status_topic}")
    
    # Publish a test message to the faculty desk unit
    requests_topic = TOPIC_REQUESTS_JSON.format(args.faculty_id)
    logger.info(f"Sending message to faculty ID {args.faculty_id} on topic: {requests_topic}")
    logger.info(f"Message: {args.message}")
    
    # Create a JSON message if requested
    if args.json:
        payload = json.dumps({
            'message': args.message,
            'student_name': "Test Student",
            'course_code': "TEST101",
            'consultation_id': random.randint(1000, 9999),
            'timestamp': time.time()
        })
    else:
        payload = args.message
    
    result = client.publish(requests_topic, payload)
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        logger.info("Message sent successfully")
    else:
        logger.error(f"Failed to send message, return code: {result.rc}")
    
    # Wait for a moment to see if we get any status updates
    logger.info("Waiting for status updates (5 seconds)...")
    time.sleep(5)
    
    # Disconnect from MQTT broker
    client.loop_stop()
    client.disconnect()
    logger.info("Disconnected from MQTT broker")

def ble_beacon(args):
    """Simulate a BLE beacon for faculty presence detection."""
    logger.info(f"Simulating BLE beacon for faculty ID {args.faculty_id}...")
    
    try:
        # Try to import bluepy
        from bluepy.btle import UUID, Peripheral, DefaultDelegate, ADDR_TYPE_RANDOM
        
        # BLE Configuration
        SERVICE_UUID = "91BAD35B-F3CB-4FC1-8603-88D5137892A6"
        CHARACTERISTIC_UUID = "D9473AA3-E6F4-424B-B6E7-A5F94FDDA285"
        
        class BLEBeaconSimulator:
            """Class to simulate a BLE beacon for the faculty desk unit."""
            
            def __init__(self, faculty_id, device_name):
                """Initialize the BLE beacon simulator."""
                self.faculty_id = faculty_id
                self.device_name = device_name
                self.peripheral = None
                
            def start_advertising(self):
                """Start advertising as a BLE beacon."""
                try:
                    # Create a peripheral device
                    self.peripheral = Peripheral()
                    
                    # Set up the service
                    service = self.peripheral.addService(UUID(SERVICE_UUID))
                    
                    # Add a characteristic
                    char = service.addCharacteristic(
                        UUID(CHARACTERISTIC_UUID),
                        ["read", "notify"]
                    )
                    
                    # Set the initial value
                    faculty_id_bytes = self.faculty_id.to_bytes(4, byteorder='big')
                    char.setValue(faculty_id_bytes)
                    
                    # Start advertising
                    self.peripheral.advertise(self.device_name, [SERVICE_UUID])
                    
                    logger.info(f"Started advertising as '{self.device_name}' with faculty ID {self.faculty_id}")
                    logger.info(f"Service UUID: {SERVICE_UUID}")
                    logger.info(f"Characteristic UUID: {CHARACTERISTIC_UUID}")
                    
                    # Keep advertising until interrupted
                    try:
                        while True:
                            # Update the characteristic value occasionally
                            if random.random() < 0.1:  # 10% chance each second
                                # Add some random data to simulate updates
                                random_data = random.randint(0, 255).to_bytes(1, byteorder='big')
                                new_value = faculty_id_bytes + random_data
                                char.setValue(new_value)
                                logger.info(f"Updated characteristic value: {new_value.hex()}")
                            
                            time.sleep(1)
                    except KeyboardInterrupt:
                        logger.info("Stopping advertising...")
                        self.peripheral.stopAdvertising()
                        
                except Exception as e:
                    logger.error(f"Error starting BLE advertising: {e}")
                    if self.peripheral:
                        self.peripheral.stopAdvertising()
        
        # Create and start the BLE beacon simulator
        simulator = BLEBeaconSimulator(args.faculty_id, args.device_name)
        simulator.start_advertising()
        
    except ImportError:
        logger.error("bluepy library not found. Please install it with: pip install bluepy")
        logger.error("Note: bluepy only works on Linux systems with Bluetooth support.")
        sys.exit(1)

def monitor(args):
    """Monitor all MQTT messages on the broker."""
    logger.info(f"Monitoring MQTT messages on broker {args.broker}:{args.port}...")
    
    # Create MQTT client
    client_id = f"ConsultEase_Monitor_{int(time.time())}"
    client = mqtt.Client(client_id)
    
    # Set user data for callbacks
    userdata = {
        'broker': args.broker,
        'port': args.port,
        'faculty_id': args.faculty_id,
        'subscribe_all': True
    }
    client.user_data_set(userdata)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    try:
        # Connect to MQTT broker
        logger.info(f"Connecting to MQTT broker at {args.broker}:{args.port}")
        client.connect(args.broker, args.port, 60)
        
        # Start the MQTT client loop in a separate thread
        client.loop_start()
        
        # Keep the script running to monitor messages
        logger.info("Monitoring MQTT messages. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Exiting...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Disconnect from MQTT broker
        client.loop_stop()
        client.disconnect()
        logger.info("Disconnected from MQTT broker")

def send_test_messages(client, faculty_id, faculty_name):
    """Send test messages to all relevant topics."""
    logger.info("Sending test messages to all topics...")
    
    # Create test messages
    text_message = f"Test message from MQTT test script.\nTimestamp: {time.time()}"
    json_message = {
        'id': 999,
        'student_id': 123,
        'student_name': "Test Student",
        'student_department': "Test Department",
        'faculty_id': faculty_id,
        'faculty_name': faculty_name,
        'request_message': text_message,
        'course_code': "TEST101",
        'status': "PENDING",
        'requested_at': time.time(),
        'message': text_message
    }
    
    # Simplified message format for faculty desk unit
    simplified_json = {
        'message': f"Student: Test Student\nCourse: TEST101\nRequest: {text_message}",
        'student_name': "Test Student",
        'course_code': "TEST101",
        'consultation_id': 999,
        'timestamp': time.time()
    }
    
    # Send to all topics
    topics_and_payloads = [
        (TOPIC_REQUESTS_JSON.format(faculty_id), json.dumps(json_message)),
        (TOPIC_REQUESTS_TEXT, text_message),
        (TOPIC_FACULTY_MESSAGES.format(faculty_id), text_message),
        (TOPIC_REQUESTS_JSON.format(faculty_id), json.dumps(simplified_json)),
    ]
    
    for topic, payload in topics_and_payloads:
        logger.info(f"Publishing to {topic}:")
        logger.info(f"Payload: {payload}")
        result = client.publish(topic, payload)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Successfully published to {topic}")
        else:
            logger.error(f"Failed to publish to {topic}, error code: {result.rc}")
        
        # Wait a bit between messages
        time.sleep(1)

def main():
    """Main function to parse arguments and run the appropriate command."""
    # Create the top-level parser
    parser = argparse.ArgumentParser(description='ConsultEase Unified Testing Utility')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Parser for mqtt-test command
    mqtt_parser = subparsers.add_parser('mqtt-test', help='Test MQTT communication with faculty desk unit')
    mqtt_parser.add_argument('--broker', default=DEFAULT_BROKER, help=f'MQTT broker address (default: {DEFAULT_BROKER})')
    mqtt_parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'MQTT broker port (default: {DEFAULT_PORT})')
    mqtt_parser.add_argument('--faculty-id', type=int, default=DEFAULT_FACULTY_ID, help=f'Faculty ID (default: {DEFAULT_FACULTY_ID})')
    mqtt_parser.add_argument('--faculty-name', default=DEFAULT_FACULTY_NAME, help=f'Faculty name (default: {DEFAULT_FACULTY_NAME})')
    mqtt_parser.add_argument('--monitor-only', action='store_true', help='Only monitor topics without sending test messages')
    
    # Parser for faculty-desk command
    faculty_parser = subparsers.add_parser('faculty-desk', help='Send test messages to faculty desk unit')
    faculty_parser.add_argument('--broker', default=DEFAULT_BROKER, help=f'MQTT broker address (default: {DEFAULT_BROKER})')
    faculty_parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'MQTT broker port (default: {DEFAULT_PORT})')
    faculty_parser.add_argument('--faculty-id', type=int, default=DEFAULT_FACULTY_ID, help=f'Faculty ID (default: {DEFAULT_FACULTY_ID})')
    faculty_parser.add_argument('--message', default=DEFAULT_MESSAGE, help='Message to send to the faculty desk unit')
    faculty_parser.add_argument('--json', action='store_true', help='Send message as JSON payload')
    
    # Parser for ble-beacon command
    ble_parser = subparsers.add_parser('ble-beacon', help='Simulate a BLE beacon for faculty presence detection')
    ble_parser.add_argument('--faculty-id', type=int, default=DEFAULT_FACULTY_ID, help=f'Faculty ID (default: {DEFAULT_FACULTY_ID})')
    ble_parser.add_argument('--device-name', default=f"ConsultEase-Faculty-{DEFAULT_FACULTY_ID}", help='BLE device name')
    
    # Parser for monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor all MQTT messages on the broker')
    monitor_parser.add_argument('--broker', default=DEFAULT_BROKER, help=f'MQTT broker address (default: {DEFAULT_BROKER})')
    monitor_parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'MQTT broker port (default: {DEFAULT_PORT})')
    monitor_parser.add_argument('--faculty-id', type=int, default=DEFAULT_FACULTY_ID, help=f'Faculty ID for topic filtering (default: {DEFAULT_FACULTY_ID})')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the appropriate command
    if args.command == 'mqtt-test':
        mqtt_test(args)
    elif args.command == 'faculty-desk':
        faculty_desk(args)
    elif args.command == 'ble-beacon':
        ble_beacon(args)
    elif args.command == 'monitor':
        monitor(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
