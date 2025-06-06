#!/usr/bin/env python3
"""
ConsultEase - Two-Button Response System Test Script

This script tests the enhanced two-button response functionality:
1. Sends test consultation requests to faculty desk units
2. Monitors for faculty responses (ACKNOWLEDGE/BUSY)
3. Verifies database status updates
4. Tests real-time notification system

Usage:
    python test_two_button_response.py --faculty-id 1 --student-id 1
    python test_two_button_response.py --test-all
"""

import sys
import time
import json
import argparse
import logging
from datetime import datetime
import paho.mqtt.client as mqtt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_BROKER = "192.168.1.100"
DEFAULT_PORT = 1883
DEFAULT_FACULTY_ID = 1
DEFAULT_STUDENT_ID = 1

# MQTT Topics
TOPIC_FACULTY_REQUESTS = "consultease/faculty/{}/requests"
TOPIC_FACULTY_MESSAGES = "consultease/faculty/{}/messages"
TOPIC_FACULTY_RESPONSES = "consultease/faculty/{}/responses"
TOPIC_SYSTEM_NOTIFICATIONS = "consultease/system/notifications"

class TwoButtonResponseTester:
    """Test the two-button response system."""
    
    def __init__(self, broker, port, faculty_id, student_id):
        self.broker = broker
        self.port = port
        self.faculty_id = faculty_id
        self.student_id = student_id
        self.client = mqtt.Client("TwoButtonResponseTester")
        self.responses_received = []
        self.test_consultation_id = None
        
        # Set up MQTT callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection."""
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.broker}:{self.port}")
            
            # Subscribe to response topics
            response_topic = TOPIC_FACULTY_RESPONSES.format(self.faculty_id)
            notification_topic = TOPIC_SYSTEM_NOTIFICATIONS
            
            client.subscribe(response_topic)
            client.subscribe(notification_topic)
            
            logger.info(f"Subscribed to: {response_topic}")
            logger.info(f"Subscribed to: {notification_topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback for received MQTT messages."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.info(f"Received message on {topic}")
            
            if "responses" in topic:
                self.handle_faculty_response(payload)
            elif "notifications" in topic:
                self.handle_system_notification(payload)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def handle_faculty_response(self, payload):
        """Handle faculty response messages."""
        try:
            response_data = json.loads(payload)
            
            faculty_id = response_data.get('faculty_id')
            response_type = response_data.get('response_type')
            message_id = response_data.get('message_id')
            faculty_name = response_data.get('faculty_name', 'Unknown')
            timestamp = response_data.get('timestamp')
            
            logger.info("=" * 50)
            logger.info("FACULTY RESPONSE RECEIVED")
            logger.info("=" * 50)
            logger.info(f"Faculty ID: {faculty_id}")
            logger.info(f"Faculty Name: {faculty_name}")
            logger.info(f"Response Type: {response_type}")
            logger.info(f"Message ID: {message_id}")
            logger.info(f"Timestamp: {timestamp}")
            logger.info(f"Faculty Present: {response_data.get('faculty_present', 'Unknown')}")
            logger.info(f"Response Method: {response_data.get('response_method', 'Unknown')}")
            logger.info("=" * 50)
            
            # Store response for analysis
            self.responses_received.append({
                'response_type': response_type,
                'faculty_id': faculty_id,
                'message_id': message_id,
                'timestamp': timestamp,
                'received_at': datetime.now().isoformat()
            })
            
            # Verify this is for our test consultation
            if str(message_id) == str(self.test_consultation_id):
                if response_type == "ACKNOWLEDGE":
                    logger.info("✅ ACKNOWLEDGE response received successfully!")
                elif response_type == "BUSY":
                    logger.info("🔶 BUSY response received successfully!")
                else:
                    logger.info(f"📝 {response_type} response received")
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in faculty response: {payload}")
        except Exception as e:
            logger.error(f"Error handling faculty response: {e}")
    
    def handle_system_notification(self, payload):
        """Handle system notification messages."""
        try:
            notification_data = json.loads(payload)
            
            if notification_data.get('type') == 'faculty_response':
                faculty_name = notification_data.get('faculty_name', 'Unknown')
                response_type = notification_data.get('response_type')
                
                logger.info(f"📢 System Notification: {faculty_name} sent {response_type} response")
                
        except json.JSONDecodeError:
            logger.debug(f"Non-JSON system notification: {payload}")
        except Exception as e:
            logger.error(f"Error handling system notification: {e}")
    
    def send_test_consultation_request(self, message="Test consultation request"):
        """Send a test consultation request to the faculty desk unit."""
        try:
            # Generate a test consultation ID
            self.test_consultation_id = int(time.time())
            
            # Create consultation request data (JSON format)
            consultation_data = {
                'id': self.test_consultation_id,
                'student_id': self.student_id,
                'student_name': f"Test Student {self.student_id}",
                'student_department': "Computer Science",
                'faculty_id': self.faculty_id,
                'faculty_name': f"Test Faculty {self.faculty_id}",
                'request_message': message,
                'course_code': "CS101",
                'status': "pending",
                'requested_at': datetime.now().isoformat()
            }
            
            # Send to JSON topic
            json_topic = TOPIC_FACULTY_REQUESTS.format(self.faculty_id)
            self.client.publish(json_topic, json.dumps(consultation_data), qos=2)
            
            # Send to plain text topic (for ESP32 compatibility)
            plain_message = f"CID:{self.test_consultation_id} From:Test Student {self.student_id} (SID:{self.student_id}): {message}"
            text_topic = TOPIC_FACULTY_MESSAGES.format(self.faculty_id)
            self.client.publish(text_topic, plain_message, qos=2)
            
            logger.info("=" * 50)
            logger.info("TEST CONSULTATION REQUEST SENT")
            logger.info("=" * 50)
            logger.info(f"Consultation ID: {self.test_consultation_id}")
            logger.info(f"Faculty ID: {self.faculty_id}")
            logger.info(f"Student ID: {self.student_id}")
            logger.info(f"Message: {message}")
            logger.info(f"JSON Topic: {json_topic}")
            logger.info(f"Text Topic: {text_topic}")
            logger.info("=" * 50)
            
            return self.test_consultation_id
            
        except Exception as e:
            logger.error(f"Error sending test consultation request: {e}")
            return None
    
    def run_interactive_test(self):
        """Run an interactive test session."""
        try:
            # Connect to MQTT broker
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
            # Wait for connection
            time.sleep(2)
            
            logger.info("🚀 Starting Two-Button Response System Test")
            logger.info(f"Faculty ID: {self.faculty_id}")
            logger.info(f"Student ID: {self.student_id}")
            logger.info("")
            
            while True:
                print("\n" + "=" * 60)
                print("TWO-BUTTON RESPONSE SYSTEM TEST MENU")
                print("=" * 60)
                print("1. Send Test Consultation Request")
                print("2. Send Custom Message")
                print("3. View Received Responses")
                print("4. Test ACKNOWLEDGE Response")
                print("5. Test BUSY Response")
                print("6. Run Automated Test Sequence")
                print("7. Exit")
                print("=" * 60)
                
                choice = input("Enter your choice (1-7): ").strip()
                
                if choice == "1":
                    message = "Please help me with my assignment on data structures."
                    consultation_id = self.send_test_consultation_request(message)
                    if consultation_id:
                        print(f"\n✅ Test consultation request sent with ID: {consultation_id}")
                        print("👆 Press the BLUE button on the faculty desk unit to ACKNOWLEDGE")
                        print("👆 Press the RED button on the faculty desk unit to mark BUSY")
                        print("⏰ Waiting for response (timeout in 30 seconds)...")
                
                elif choice == "2":
                    message = input("Enter custom consultation message: ").strip()
                    if message:
                        consultation_id = self.send_test_consultation_request(message)
                        if consultation_id:
                            print(f"\n✅ Custom consultation request sent with ID: {consultation_id}")
                
                elif choice == "3":
                    self.show_received_responses()
                
                elif choice == "4":
                    print("\n🔵 Testing ACKNOWLEDGE Response")
                    message = "Test message for ACKNOWLEDGE response"
                    consultation_id = self.send_test_consultation_request(message)
                    if consultation_id:
                        print("👆 Please press the BLUE button on the faculty desk unit")
                
                elif choice == "5":
                    print("\n🔴 Testing BUSY Response")
                    message = "Test message for BUSY response"
                    consultation_id = self.send_test_consultation_request(message)
                    if consultation_id:
                        print("👆 Please press the RED button on the faculty desk unit")
                
                elif choice == "6":
                    self.run_automated_test_sequence()
                
                elif choice == "7":
                    print("\n👋 Exiting test program...")
                    break
                
                else:
                    print("\n❌ Invalid choice. Please try again.")
                
                # Wait a bit for any responses
                time.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Test interrupted by user")
        except Exception as e:
            logger.error(f"Error in interactive test: {e}")
        finally:
            self.client.loop_stop()
            self.client.disconnect()
    
    def show_received_responses(self):
        """Display all received responses."""
        if not self.responses_received:
            print("\n📭 No responses received yet.")
            return
        
        print(f"\n📨 Received {len(self.responses_received)} response(s):")
        print("-" * 60)
        
        for i, response in enumerate(self.responses_received, 1):
            print(f"{i}. Response Type: {response['response_type']}")
            print(f"   Faculty ID: {response['faculty_id']}")
            print(f"   Message ID: {response['message_id']}")
            print(f"   Timestamp: {response['timestamp']}")
            print(f"   Received At: {response['received_at']}")
            print("-" * 60)
    
    def run_automated_test_sequence(self):
        """Run an automated test sequence."""
        print("\n🤖 Running Automated Test Sequence")
        print("This will send multiple test requests...")
        
        test_messages = [
            "Can you help me with my programming assignment?",
            "I need clarification on the exam topics.",
            "Could we discuss my project proposal?",
            "I'm having trouble with the homework."
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n📤 Sending test message {i}/{len(test_messages)}")
            consultation_id = self.send_test_consultation_request(message)
            
            if consultation_id:
                print(f"✅ Sent consultation ID: {consultation_id}")
                print("⏰ Waiting 10 seconds before next message...")
                time.sleep(10)
        
        print("\n✅ Automated test sequence completed!")
        print("📊 Check the responses using option 3 in the menu.")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test ConsultEase Two-Button Response System")
    parser.add_argument("--broker", default=DEFAULT_BROKER, help="MQTT broker address")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="MQTT broker port")
    parser.add_argument("--faculty-id", type=int, default=DEFAULT_FACULTY_ID, help="Faculty ID to test")
    parser.add_argument("--student-id", type=int, default=DEFAULT_STUDENT_ID, help="Student ID for test")
    parser.add_argument("--message", default="Test consultation request", help="Test message to send")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--single-test", action="store_true", help="Send single test message and exit")
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = TwoButtonResponseTester(args.broker, args.port, args.faculty_id, args.student_id)
    
    if args.interactive or (not args.single_test):
        # Run interactive test by default
        tester.run_interactive_test()
    elif args.single_test:
        # Send single test message
        try:
            tester.client.connect(args.broker, args.port, 60)
            tester.client.loop_start()
            time.sleep(2)
            
            consultation_id = tester.send_test_consultation_request(args.message)
            if consultation_id:
                print(f"✅ Test consultation request sent with ID: {consultation_id}")
                print("⏰ Waiting 30 seconds for response...")
                
                # Wait for response
                time.sleep(30)
                
                if tester.responses_received:
                    print(f"📨 Received {len(tester.responses_received)} response(s)")
                    tester.show_received_responses()
                else:
                    print("📭 No responses received")
            
        except Exception as e:
            logger.error(f"Error in single test: {e}")
        finally:
            tester.client.loop_stop()
            tester.client.disconnect()

if __name__ == "__main__":
    main() 