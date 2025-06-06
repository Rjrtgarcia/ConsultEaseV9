#!/usr/bin/env python3
"""
Full Consultation Flow Test

This script tests the complete consultation flow:
1. Creates a consultation in the database
2. Sends consultation message to ESP32
3. Simulates ESP32 button response
4. Verifies central system processes the response

Usage:
    python scripts/test_full_consultation_flow.py
"""

import sys
import os
import time
import json
import logging
import socket
import paho.mqtt.client as mqtt
from datetime import datetime

# Add the central_system directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'central_system'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MQTT Configuration - Try multiple possible broker addresses
POSSIBLE_BROKERS = [
    "172.20.10.8",      # From your test
    "192.168.1.100",    # ESP32 configured address
    "localhost",        # Default central system
    "127.0.0.1",        # Localhost IP
]
PORT = 1883
FACULTY_ID = 1
STUDENT_ID = 1  # Test student

# Topics
RESPONSES_TOPIC = f"consultease/faculty/{FACULTY_ID}/responses"
MESSAGES_TOPIC = f"consultease/faculty/{FACULTY_ID}/messages"

def find_mqtt_broker():
    """Find an accessible MQTT broker from the list."""
    logger.info("🔍 Searching for accessible MQTT brokers...")
    
    for broker in POSSIBLE_BROKERS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((broker, PORT))
            sock.close()
            if result == 0:
                logger.info(f"✅ Found accessible broker: {broker}:{PORT}")
                return broker
            else:
                logger.info(f"❌ Cannot reach {broker}:{PORT}")
        except Exception as e:
            logger.debug(f"Connection test failed for {broker}:{PORT} - {e}")
    
    logger.error("❌ No accessible MQTT brokers found!")
    return None

def create_test_consultation():
    """Create a test consultation in the database."""
    logger.info("📝 Creating test consultation in database...")
    
    try:
        # Import database models
        from models.base import get_db, init_db
        from models.consultation import Consultation, ConsultationStatus
        from models.student import Student
        from models.faculty import Faculty
        
        # Initialize database
        init_db()
        db = get_db()
        
        try:
            # Check if test student exists, create if not
            student = db.query(Student).filter(Student.id == STUDENT_ID).first()
            if not student:
                student = Student(
                    id=STUDENT_ID,
                    student_id="TEST123",
                    name="Test Student",
                    email="test@student.com",
                    course="Computer Science",
                    year_level="4th Year"
                )
                db.add(student)
                logger.info("➕ Created test student")
            
            # Check if test faculty exists
            faculty = db.query(Faculty).filter(Faculty.id == FACULTY_ID).first()
            if not faculty:
                faculty = Faculty(
                    id=FACULTY_ID,
                    name="Dave Jomillo",
                    department="Helpdesk",
                    email="djo@hd.com"
                )
                db.add(faculty)
                logger.info("➕ Created test faculty")
            
            # Create a new consultation
            consultation = Consultation(
                student_id=STUDENT_ID,
                faculty_id=FACULTY_ID,
                message="Please help me with my project - this is a test consultation",
                status=ConsultationStatus.PENDING,
                created_at=datetime.now()
            )
            
            db.add(consultation)
            db.commit()
            
            consultation_id = consultation.id
            logger.info(f"✅ Created test consultation with ID: {consultation_id}")
            
            return consultation_id
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Failed to create test consultation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

class FullConsultationFlowTester:
    """Test the complete consultation flow."""
    
    def __init__(self, broker_host):
        self.broker_host = broker_host
        self.client = mqtt.Client("Full_Consultation_Flow_Tester")
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message
        self.connected = False
        self.received_messages = []
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection."""
        if rc == 0:
            self.connected = True
            logger.info(f"✅ Connected to MQTT broker at {self.broker_host}:{PORT}")
            
            # Subscribe to all relevant topics
            topics = [
                "consultease/system/notifications",
                "consultease/#",
                f"consultease/faculty/{FACULTY_ID}/#"
            ]
            
            for topic in topics:
                client.subscribe(topic)
                logger.info(f"📬 Subscribed to: {topic}")
        else:
            self.connected = False
            logger.error(f"❌ Failed to connect to MQTT broker, return code: {rc}")
    
    def on_publish(self, client, userdata, mid):
        """Callback for published messages."""
        logger.info(f"📤 Message published successfully (MID: {mid})")
    
    def on_message(self, client, userdata, msg):
        """Callback for received messages."""
        message_info = {
            'topic': msg.topic,
            'payload': msg.payload.decode(),
            'timestamp': datetime.now()
        }
        self.received_messages.append(message_info)
        logger.info(f"📥 Received: {msg.topic} - {msg.payload.decode()}")
    
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
    
    def send_consultation_message(self, consultation_id, message):
        """Send consultation message to ESP32."""
        logger.info("=" * 60)
        logger.info("SENDING CONSULTATION MESSAGE TO ESP32")
        logger.info("=" * 60)
        
        # Format: "CID:{consultation_id} From:{student_name} (SID:{student_id}): {message}"
        formatted_message = f"CID:{consultation_id} From:Test Student (SID:{STUDENT_ID}): {message}"
        
        logger.info(f"📨 Sending to topic: {MESSAGES_TOPIC}")
        logger.info(f"📨 Message: {formatted_message}")
        
        result = self.client.publish(MESSAGES_TOPIC, formatted_message, qos=2)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info("✅ Consultation message sent successfully")
            return True
        else:
            logger.error(f"❌ Failed to send message, error code: {result.rc}")
            return False
    
    def send_button_response(self, consultation_id, response_type="ACKNOWLEDGE"):
        """Send button response (simulating ESP32)."""
        logger.info("=" * 60)
        logger.info(f"SENDING {response_type} BUTTON RESPONSE")
        logger.info("=" * 60)
        
        # Create ESP32 button response
        response_data = {
            "faculty_id": FACULTY_ID,
            "faculty_name": "Dave Jomillo",
            "response_type": response_type,
            "message_id": str(consultation_id),  # This is the critical field!
            "original_message": "Test consultation request",
            "timestamp": str(int(time.time() * 1000)),
            "faculty_present": True,
            "response_method": "physical_button",
            "status": f"Professor {response_type.lower()}s the request"
        }
        
        logger.info(f"📨 Sending to topic: {RESPONSES_TOPIC}")
        logger.info(f"📨 Response data: {json.dumps(response_data, indent=2)}")
        
        result = self.client.publish(RESPONSES_TOPIC, json.dumps(response_data), qos=2)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"✅ {response_type} response sent successfully")
            return True
        else:
            logger.error(f"❌ Failed to send {response_type} response, error code: {result.rc}")
            return False
    
    def verify_consultation_status(self, consultation_id, expected_status):
        """Verify the consultation status in the database."""
        logger.info(f"🔍 Verifying consultation {consultation_id} status...")
        
        try:
            from models.base import get_db
            from models.consultation import Consultation, ConsultationStatus
            
            db = get_db()
            try:
                consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
                
                if not consultation:
                    logger.error(f"❌ Consultation {consultation_id} not found in database")
                    return False
                
                actual_status = consultation.status.value
                logger.info(f"📊 Consultation {consultation_id} status: {actual_status}")
                
                if actual_status == expected_status:
                    logger.info(f"✅ Status verification successful: {actual_status}")
                    return True
                else:
                    logger.warning(f"⚠️ Status mismatch - Expected: {expected_status}, Actual: {actual_status}")
                    return False
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Failed to verify consultation status: {e}")
            return False
    
    def run_full_test(self):
        """Run the complete consultation flow test."""
        logger.info("🚀 Starting Full Consultation Flow Test...")
        
        # Step 1: Create consultation in database
        consultation_id = create_test_consultation()
        if not consultation_id:
            logger.error("❌ Failed to create test consultation")
            return False
        
        # Step 2: Connect to MQTT
        if not self.connect():
            logger.error("❌ Failed to connect to MQTT broker")
            return False
        
        # Step 3: Send consultation message to ESP32
        message = "Please help me with my project - this is a test consultation"
        if not self.send_consultation_message(consultation_id, message):
            logger.error("❌ Failed to send consultation message")
            return False
        
        # Wait for ESP32 to receive
        time.sleep(3)
        
        # Step 4: Send ACKNOWLEDGE response (simulating ESP32 button press)
        if not self.send_button_response(consultation_id, "ACKNOWLEDGE"):
            logger.error("❌ Failed to send ACKNOWLEDGE response")
            return False
        
        # Wait for central system to process
        logger.info("⏳ Waiting for central system to process ACKNOWLEDGE response...")
        time.sleep(5)
        
        # Step 5: Verify consultation status changed to ACCEPTED
        if self.verify_consultation_status(consultation_id, "ACCEPTED"):
            logger.info("✅ ACKNOWLEDGE response processed successfully!")
        else:
            logger.warning("⚠️ ACKNOWLEDGE response may not have been processed")
        
        # Step 6: Test BUSY response with new consultation
        consultation_id_2 = create_test_consultation()
        if consultation_id_2:
            time.sleep(2)
            self.send_consultation_message(consultation_id_2, "Another test consultation")
            time.sleep(2)
            self.send_button_response(consultation_id_2, "BUSY")
            time.sleep(3)
            self.verify_consultation_status(consultation_id_2, "BUSY")
        
        # Final summary
        logger.info("📋 Test Summary:")
        logger.info(f"   Messages received: {len(self.received_messages)}")
        logger.info("   Check central system logs for Faculty Response Handler messages")
        
        return True
    
    def cleanup(self):
        """Clean up MQTT connection."""
        self.client.loop_stop()
        self.client.disconnect()

def main():
    """Main function."""
    logger.info("🔧 Full Consultation Flow Test")
    logger.info("=" * 50)
    
    # Find accessible broker
    broker_host = find_mqtt_broker()
    if not broker_host:
        logger.error("❌ Cannot proceed without an accessible MQTT broker")
        return False
    
    # Run the test
    tester = FullConsultationFlowTester(broker_host)
    
    try:
        success = tester.run_full_test()
        if success:
            logger.info("🎉 Full consultation flow test completed!")
            logger.info("🔍 Check central system logs for:")
            logger.info("   - 🔥 FACULTY RESPONSE HANDLER TRIGGERED")
            logger.info("   - ✅ Successfully updated consultation")
        else:
            logger.error("❌ Test failed")
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main() 