#!/usr/bin/env python3
"""
MQTT Faculty Status Synchronization Diagnostic Tool

This script helps diagnose MQTT message flow and database update issues
between ESP32 faculty desk units and the central Raspberry Pi system.
"""

import json
import logging
import time
import threading
from datetime import datetime
from typing import Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MQTTDiagnostics:
    """Diagnostic tool for MQTT faculty status synchronization."""
    
    def __init__(self):
        self.message_count = 0
        self.messages_by_topic = {}
        self.faculty_status_updates = {}
        self.database_updates = {}
        self.errors = []
        self.start_time = datetime.now()
        
    def start_diagnostics(self, duration_minutes=5):
        """
        Start comprehensive MQTT diagnostics.
        
        Args:
            duration_minutes: How long to run diagnostics
        """
        logger.info(f"🔍 Starting MQTT Faculty Status Diagnostics for {duration_minutes} minutes...")
        
        # Test 1: Check MQTT service connectivity
        self._test_mqtt_connectivity()
        
        # Test 2: Check database connectivity
        self._test_database_connectivity()
        
        # Test 3: Check faculty records in database
        self._check_faculty_records()
        
        # Test 4: Monitor MQTT messages
        self._monitor_mqtt_messages(duration_minutes)
        
        # Test 5: Generate diagnostic report
        self._generate_report()
        
    def _test_mqtt_connectivity(self):
        """Test MQTT service connectivity."""
        logger.info("🔌 Testing MQTT connectivity...")
        
        try:
            from ..services.async_mqtt_service import get_async_mqtt_service
            mqtt_service = get_async_mqtt_service()
            
            if mqtt_service.is_connected:
                logger.info("✅ MQTT service is connected")
                logger.info(f"📊 MQTT Stats - Received: {mqtt_service.messages_received}, Published: {mqtt_service.messages_published}")
            else:
                logger.error("❌ MQTT service is not connected")
                self.errors.append("MQTT service not connected")
                
        except Exception as e:
            logger.error(f"❌ Error testing MQTT connectivity: {e}")
            self.errors.append(f"MQTT connectivity error: {e}")
            
    def _test_database_connectivity(self):
        """Test database connectivity."""
        logger.info("🗄️ Testing database connectivity...")
        
        try:
            from ..services.database_manager import get_database_manager
            db_manager = get_database_manager()
            
            # Test database connection
            with db_manager.get_session_context() as db:
                # Simple query to test connection
                result = db.execute("SELECT 1").fetchone()
                if result:
                    logger.info("✅ Database connection successful")
                else:
                    logger.error("❌ Database query failed")
                    self.errors.append("Database query failed")
                    
        except Exception as e:
            logger.error(f"❌ Database connectivity error: {e}")
            self.errors.append(f"Database connectivity error: {e}")
            
    def _check_faculty_records(self):
        """Check faculty records in database."""
        logger.info("👥 Checking faculty records...")
        
        try:
            from ..models import Faculty, get_db
            
            db = get_db()
            faculties = db.query(Faculty).all()
            
            logger.info(f"📊 Found {len(faculties)} faculty records:")
            for faculty in faculties:
                logger.info(f"  - ID: {faculty.id}, Name: {faculty.name}, Status: {faculty.status}, BLE ID: {faculty.ble_id}")
                
            # Check for faculty ID 1 specifically (ESP32 default)
            faculty_1 = db.query(Faculty).filter(Faculty.id == 1).first()
            if faculty_1:
                logger.info(f"✅ Faculty ID 1 found: {faculty_1.name} (Status: {faculty_1.status})")
            else:
                logger.warning("⚠️ Faculty ID 1 not found - ESP32 may be configured for non-existent faculty")
                self.errors.append("Faculty ID 1 not found in database")
                
        except Exception as e:
            logger.error(f"❌ Error checking faculty records: {e}")
            self.errors.append(f"Faculty records error: {e}")
            
    def _monitor_mqtt_messages(self, duration_minutes):
        """Monitor MQTT messages for the specified duration."""
        logger.info(f"📡 Monitoring MQTT messages for {duration_minutes} minutes...")
        
        try:
            from ..services.async_mqtt_service import get_async_mqtt_service
            mqtt_service = get_async_mqtt_service()
            
            # Register diagnostic handler
            original_handlers = mqtt_service.message_handlers.copy()
            
            # Add our diagnostic handler
            mqtt_service.register_topic_handler("consultease/faculty/+/status", self._diagnostic_message_handler)
            mqtt_service.register_topic_handler("faculty/+/status", self._diagnostic_message_handler)
            mqtt_service.register_topic_handler("professor/status", self._diagnostic_message_handler)
            
            # Monitor for specified duration
            end_time = time.time() + (duration_minutes * 60)
            
            logger.info("🎧 Listening for MQTT messages...")
            logger.info("📝 Expected ESP32 topics:")
            logger.info("  - consultease/faculty/1/status")
            logger.info("  - faculty/1/status (legacy)")
            
            while time.time() < end_time:
                time.sleep(1)
                
            logger.info("⏰ Monitoring period completed")
            
        except Exception as e:
            logger.error(f"❌ Error monitoring MQTT messages: {e}")
            self.errors.append(f"MQTT monitoring error: {e}")
            
    def _diagnostic_message_handler(self, topic: str, data: Any):
        """Handle MQTT messages for diagnostics."""
        self.message_count += 1
        timestamp = datetime.now().isoformat()
        
        # Track messages by topic
        if topic not in self.messages_by_topic:
            self.messages_by_topic[topic] = []
        self.messages_by_topic[topic].append({
            'timestamp': timestamp,
            'data': data,
            'data_type': type(data).__name__
        })
        
        logger.info(f"📨 MQTT Message #{self.message_count}")
        logger.info(f"  📍 Topic: {topic}")
        logger.info(f"  📄 Data: {data}")
        logger.info(f"  🏷️ Type: {type(data).__name__}")
        
        # Analyze faculty status messages
        if 'faculty' in topic and 'status' in topic:
            self._analyze_faculty_status_message(topic, data, timestamp)
            
    def _analyze_faculty_status_message(self, topic: str, data: Any, timestamp: str):
        """Analyze faculty status messages."""
        logger.info("🔍 Analyzing faculty status message...")
        
        # Extract faculty ID from topic
        faculty_id = None
        if 'consultease/faculty/' in topic:
            parts = topic.split('/')
            if len(parts) >= 3:
                try:
                    faculty_id = int(parts[2])
                except ValueError:
                    pass
        elif topic == 'professor/status':
            faculty_id = 1  # Legacy topic typically for faculty ID 1
            
        logger.info(f"  👤 Faculty ID: {faculty_id}")
        
        # Analyze data content
        if isinstance(data, dict):
            logger.info("  📊 Data analysis:")
            for key, value in data.items():
                logger.info(f"    - {key}: {value}")
                
            # Check for presence indicators
            if 'present' in data:
                status = bool(data['present'])
                logger.info(f"  ✅ Found 'present' field: {status}")
            elif 'status' in data:
                status = data['status']
                logger.info(f"  📝 Found 'status' field: {status}")
            else:
                logger.warning("  ⚠️ No clear status indicator found")
                
        # Track this update
        if faculty_id:
            if faculty_id not in self.faculty_status_updates:
                self.faculty_status_updates[faculty_id] = []
            self.faculty_status_updates[faculty_id].append({
                'timestamp': timestamp,
                'topic': topic,
                'data': data
            })
            
    def _generate_report(self):
        """Generate comprehensive diagnostic report."""
        logger.info("📋 Generating diagnostic report...")
        
        duration = datetime.now() - self.start_time
        
        print("\n" + "="*80)
        print("🔍 MQTT FACULTY STATUS SYNCHRONIZATION DIAGNOSTIC REPORT")
        print("="*80)
        print(f"📅 Report generated: {datetime.now().isoformat()}")
        print(f"⏱️ Monitoring duration: {duration}")
        print(f"📨 Total messages received: {self.message_count}")
        print()
        
        # Messages by topic
        print("📡 MESSAGES BY TOPIC:")
        for topic, messages in self.messages_by_topic.items():
            print(f"  📍 {topic}: {len(messages)} messages")
            if messages:
                latest = messages[-1]
                print(f"    🕐 Latest: {latest['timestamp']}")
                print(f"    📄 Data: {latest['data']}")
        print()
        
        # Faculty status updates
        print("👥 FACULTY STATUS UPDATES:")
        if self.faculty_status_updates:
            for faculty_id, updates in self.faculty_status_updates.items():
                print(f"  👤 Faculty {faculty_id}: {len(updates)} updates")
                for update in updates[-3:]:  # Show last 3 updates
                    print(f"    🕐 {update['timestamp']}: {update['data']}")
        else:
            print("  ⚠️ No faculty status updates received")
        print()
        
        # Errors
        if self.errors:
            print("❌ ERRORS DETECTED:")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print("✅ No errors detected")
        print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS:")
        if self.message_count == 0:
            print("  1. Check ESP32 MQTT connection and publishing")
            print("  2. Verify MQTT broker is running and accessible")
            print("  3. Check ESP32 configuration (MQTT_SERVER, topics)")
        elif not self.faculty_status_updates:
            print("  1. Verify ESP32 is publishing to correct topics")
            print("  2. Check faculty ID configuration in ESP32")
            print("  3. Verify message format matches expected structure")
        else:
            print("  ✅ MQTT messages are being received successfully")
            print("  📝 Check central system logs for database update issues")
        
        print("="*80)


def run_diagnostics(duration_minutes=5):
    """Run MQTT diagnostics for the specified duration."""
    diagnostics = MQTTDiagnostics()
    diagnostics.start_diagnostics(duration_minutes)


if __name__ == "__main__":
    # Run diagnostics for 5 minutes
    run_diagnostics(5)
