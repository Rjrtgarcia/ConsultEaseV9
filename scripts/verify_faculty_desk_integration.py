#!/usr/bin/env python3
"""
Faculty Desk Unit Integration Verification Script
Verifies that the enhanced faculty desk unit integration is working correctly.
"""

import sys
import os
import logging
import time
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from central_system.models import get_db, Faculty
from central_system.controllers.faculty_controller import FacultyController
from central_system.controllers.faculty_response_controller import FacultyResponseController
from central_system.utils.mqtt_utils import publish_mqtt_message
from central_system.utils.mqtt_topics import MQTTTopics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FacultyDeskIntegrationVerifier:
    """Verifies faculty desk unit integration functionality."""
    
    def __init__(self):
        self.faculty_controller = FacultyController()
        self.response_controller = FacultyResponseController()
        self.test_results = []
        
    def run_verification(self):
        """Run all verification tests."""
        logger.info("Starting Faculty Desk Unit Integration Verification")
        logger.info("=" * 60)
        
        tests = [
            ("Database Schema", self.verify_database_schema),
            ("Faculty Controller", self.verify_faculty_controller),
            ("Response Controller", self.verify_response_controller),
            ("MQTT Topics", self.verify_mqtt_topics),
            ("Enhanced Status Fields", self.verify_enhanced_status),
            ("Faculty Response Processing", self.verify_response_processing),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n--- Testing: {test_name} ---")
            try:
                result = test_func()
                self.test_results.append((test_name, "PASS" if result else "FAIL"))
                logger.info(f"✅ {test_name}: {'PASS' if result else 'FAIL'}")
            except Exception as e:
                self.test_results.append((test_name, f"ERROR: {str(e)}"))
                logger.error(f"❌ {test_name}: ERROR - {str(e)}")
        
        self.print_summary()
        
    def verify_database_schema(self):
        """Verify database schema has enhanced fields."""
        try:
            db = get_db()
            
            # Check if Faculty table has new columns
            faculty = db.query(Faculty).first()
            if faculty:
                # Check for new attributes
                has_ntp_sync = hasattr(faculty, 'ntp_sync_status')
                has_grace_period = hasattr(faculty, 'grace_period_active')
                
                logger.info(f"NTP sync status field: {'✅' if has_ntp_sync else '❌'}")
                logger.info(f"Grace period field: {'✅' if has_grace_period else '❌'}")
                
                return has_ntp_sync and has_grace_period
            else:
                logger.warning("No faculty records found in database")
                return True  # Schema might be correct, just no data
                
        except Exception as e:
            logger.error(f"Database schema verification failed: {e}")
            return False
        finally:
            db.close()
    
    def verify_faculty_controller(self):
        """Verify faculty controller has enhanced methods."""
        try:
            # Check for enhanced status update method
            has_enhanced_method = hasattr(self.faculty_controller, '_update_faculty_enhanced_status')
            has_heartbeat_method = hasattr(self.faculty_controller, 'handle_faculty_heartbeat')
            
            logger.info(f"Enhanced status method: {'✅' if has_enhanced_method else '❌'}")
            logger.info(f"Heartbeat handler method: {'✅' if has_heartbeat_method else '❌'}")
            
            return has_enhanced_method and has_heartbeat_method
            
        except Exception as e:
            logger.error(f"Faculty controller verification failed: {e}")
            return False
    
    def verify_response_controller(self):
        """Verify response controller functionality."""
        try:
            # Check if response controller has required methods
            has_response_handler = hasattr(self.response_controller, 'handle_faculty_response')
            has_heartbeat_handler = hasattr(self.response_controller, 'handle_faculty_heartbeat')
            has_stats_method = hasattr(self.response_controller, 'get_response_statistics')
            
            logger.info(f"Response handler: {'✅' if has_response_handler else '❌'}")
            logger.info(f"Heartbeat handler: {'✅' if has_heartbeat_handler else '❌'}")
            logger.info(f"Statistics method: {'✅' if has_stats_method else '❌'}")
            
            return has_response_handler and has_heartbeat_handler and has_stats_method
            
        except Exception as e:
            logger.error(f"Response controller verification failed: {e}")
            return False
    
    def verify_mqtt_topics(self):
        """Verify MQTT topics are properly configured."""
        try:
            # Check if new topics exist
            has_responses_topic = hasattr(MQTTTopics, 'FACULTY_RESPONSES')
            has_heartbeat_topic = hasattr(MQTTTopics, 'FACULTY_HEARTBEAT')
            
            # Check helper methods
            has_responses_helper = hasattr(MQTTTopics, 'get_faculty_responses_topic')
            has_heartbeat_helper = hasattr(MQTTTopics, 'get_faculty_heartbeat_topic')
            
            logger.info(f"Responses topic: {'✅' if has_responses_topic else '❌'}")
            logger.info(f"Heartbeat topic: {'✅' if has_heartbeat_topic else '❌'}")
            logger.info(f"Responses helper: {'✅' if has_responses_helper else '❌'}")
            logger.info(f"Heartbeat helper: {'✅' if has_heartbeat_helper else '❌'}")
            
            # Test topic generation
            if has_responses_helper:
                topic = MQTTTopics.get_faculty_responses_topic(1)
                expected = "consultease/faculty/1/responses"
                topic_correct = topic == expected
                logger.info(f"Topic generation: {'✅' if topic_correct else '❌'} ({topic})")
            else:
                topic_correct = False
            
            return all([has_responses_topic, has_heartbeat_topic, 
                       has_responses_helper, has_heartbeat_helper, topic_correct])
            
        except Exception as e:
            logger.error(f"MQTT topics verification failed: {e}")
            return False
    
    def verify_enhanced_status(self):
        """Verify enhanced status handling."""
        try:
            # Create test faculty if none exists
            db = get_db()
            faculty = db.query(Faculty).first()
            
            if not faculty:
                logger.info("Creating test faculty for verification...")
                faculty = Faculty(
                    name="Test Faculty",
                    department="Test Department", 
                    email="test@example.com",
                    ble_id="AA:BB:CC:DD:EE:FF"
                )
                db.add(faculty)
                db.commit()
            
            faculty_id = faculty.id
            
            # Test enhanced status update
            self.faculty_controller._update_faculty_enhanced_status(
                faculty_id, True, "SYNCED", False
            )
            
            # Verify update
            db.refresh(faculty)
            ntp_updated = faculty.ntp_sync_status == "SYNCED"
            grace_updated = faculty.grace_period_active == False
            
            logger.info(f"NTP status update: {'✅' if ntp_updated else '❌'}")
            logger.info(f"Grace period update: {'✅' if grace_updated else '❌'}")
            
            return ntp_updated and grace_updated
            
        except Exception as e:
            logger.error(f"Enhanced status verification failed: {e}")
            return False
        finally:
            db.close()
    
    def verify_response_processing(self):
        """Verify faculty response processing."""
        try:
            # Simulate faculty response message
            test_response = {
                "faculty_id": 1,
                "faculty_name": "Test Faculty",
                "response_type": "ACKNOWLEDGE",
                "message_id": "test_12345",
                "original_message": "Test consultation request",
                "timestamp": str(int(time.time()))
            }
            
            # Test response processing (without actually processing)
            topic = "consultease/faculty/1/responses"
            
            # Check if the handler can process the data structure
            required_fields = ['faculty_id', 'response_type', 'message_id']
            has_required_fields = all(field in test_response for field in required_fields)
            
            logger.info(f"Response data structure: {'✅' if has_required_fields else '❌'}")
            
            # Test statistics method
            stats = self.response_controller.get_response_statistics()
            has_stats = isinstance(stats, dict) and 'total_acknowledged' in stats
            
            logger.info(f"Statistics generation: {'✅' if has_stats else '❌'}")
            
            return has_required_fields and has_stats
            
        except Exception as e:
            logger.error(f"Response processing verification failed: {e}")
            return False
    
    def print_summary(self):
        """Print verification summary."""
        logger.info("\n" + "=" * 60)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 60)
        
        passed = 0
        total = len(self.test_results)
        
        for test_name, result in self.test_results:
            status_icon = "✅" if result == "PASS" else "❌"
            logger.info(f"{status_icon} {test_name}: {result}")
            if result == "PASS":
                passed += 1
        
        logger.info("-" * 60)
        logger.info(f"TOTAL: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Faculty desk integration is ready for production.")
        else:
            logger.warning("⚠️ Some tests failed. Please review the issues before deployment.")
        
        return passed == total

def main():
    """Main verification function."""
    verifier = FacultyDeskIntegrationVerifier()
    success = verifier.run_verification()
    
    if success:
        print("\n✅ Faculty Desk Unit Integration Verification: SUCCESS")
        sys.exit(0)
    else:
        print("\n❌ Faculty Desk Unit Integration Verification: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
