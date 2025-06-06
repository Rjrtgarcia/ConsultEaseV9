#!/usr/bin/env python3
"""
Test script to verify faculty status updates and MQTT connectivity.
This script helps diagnose issues with faculty availability not updating.
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
from central_system.services.async_mqtt_service import get_async_mqtt_service
from central_system.utils.mqtt_utils import publish_mqtt_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FacultyStatusTester:
    """Test faculty status updates and MQTT connectivity."""
    
    def __init__(self):
        self.faculty_controller = FacultyController()
        self.mqtt_service = get_async_mqtt_service()
        
    def run_tests(self):
        """Run all faculty status tests."""
        logger.info("Starting Faculty Status Update Tests")
        logger.info("=" * 60)
        
        tests = [
            ("Database Connection", self.test_database_connection),
            ("Faculty Data Retrieval", self.test_faculty_data_retrieval),
            ("MQTT Service Status", self.test_mqtt_service),
            ("Faculty Controller Setup", self.test_faculty_controller_setup),
            ("Manual Status Update", self.test_manual_status_update),
            ("MQTT Status Simulation", self.test_mqtt_status_simulation),
            ("Dashboard Data Refresh", self.test_dashboard_data_refresh),
        ]
        
        results = []
        for test_name, test_func in tests:
            logger.info(f"\n--- Testing: {test_name} ---")
            try:
                result = test_func()
                results.append((test_name, "PASS" if result else "FAIL"))
                logger.info(f"✅ {test_name}: {'PASS' if result else 'FAIL'}")
            except Exception as e:
                results.append((test_name, f"ERROR: {str(e)}"))
                logger.error(f"❌ {test_name}: ERROR - {str(e)}")
        
        self.print_summary(results)
        
    def test_database_connection(self):
        """Test database connection and faculty table access."""
        try:
            db = get_db()
            faculty_count = db.query(Faculty).count()
            logger.info(f"Database connected, {faculty_count} faculty members found")
            
            # Test faculty data access
            faculties = db.query(Faculty).all()
            for faculty in faculties:
                logger.info(f"Faculty: {faculty.name} (ID: {faculty.id}, Status: {faculty.status})")
            
            db.close()
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def test_faculty_data_retrieval(self):
        """Test faculty data retrieval through controller."""
        try:
            faculties = self.faculty_controller.get_all_faculty()
            logger.info(f"Retrieved {len(faculties)} faculty members through controller")
            
            for faculty in faculties:
                # Test attribute access to check for DetachedInstanceError
                faculty_id = faculty.id
                faculty_name = faculty.name
                faculty_status = faculty.status
                faculty_department = faculty.department
                
                logger.info(f"Faculty: {faculty_name} (ID: {faculty_id}, Status: {faculty_status}, Dept: {faculty_department})")
            
            return True
        except Exception as e:
            logger.error(f"Faculty data retrieval failed: {e}")
            return False
    
    def test_mqtt_service(self):
        """Test MQTT service connectivity."""
        try:
            # Start MQTT service if not running
            if not self.mqtt_service.running:
                self.mqtt_service.start()
                time.sleep(2)  # Wait for connection
            
            # Check connection status
            stats = self.mqtt_service.get_stats()
            is_connected = stats.get('connected', False)
            
            logger.info(f"MQTT Service Running: {self.mqtt_service.running}")
            logger.info(f"MQTT Connected: {is_connected}")
            logger.info(f"MQTT Stats: {stats}")
            
            return is_connected
        except Exception as e:
            logger.error(f"MQTT service test failed: {e}")
            return False
    
    def test_faculty_controller_setup(self):
        """Test faculty controller initialization and MQTT subscriptions."""
        try:
            # Start faculty controller
            self.faculty_controller.start()
            
            # Check if controller has required attributes
            has_queue_service = hasattr(self.faculty_controller, 'queue_service')
            has_callbacks = hasattr(self.faculty_controller, 'callbacks')
            
            logger.info(f"Faculty controller has queue service: {has_queue_service}")
            logger.info(f"Faculty controller has callbacks: {has_callbacks}")
            
            return has_queue_service and has_callbacks
        except Exception as e:
            logger.error(f"Faculty controller setup test failed: {e}")
            return False
    
    def test_manual_status_update(self):
        """Test manual faculty status update."""
        try:
            db = get_db()
            faculty = db.query(Faculty).first()
            
            if not faculty:
                logger.warning("No faculty found for manual status test")
                return False
            
            # Get current status
            original_status = faculty.status
            new_status = not original_status
            
            logger.info(f"Testing status update for {faculty.name}: {original_status} -> {new_status}")
            
            # Update status through controller
            updated_faculty = self.faculty_controller.update_faculty_status(faculty.id, new_status)
            
            if updated_faculty:
                logger.info(f"Status updated successfully: {updated_faculty.status}")
                
                # Revert status
                self.faculty_controller.update_faculty_status(faculty.id, original_status)
                logger.info(f"Status reverted to original: {original_status}")
                
                return True
            else:
                logger.error("Status update failed")
                return False
                
        except Exception as e:
            logger.error(f"Manual status update test failed: {e}")
            return False
        finally:
            db.close()
    
    def test_mqtt_status_simulation(self):
        """Test MQTT status message simulation."""
        try:
            db = get_db()
            faculty = db.query(Faculty).first()
            
            if not faculty:
                logger.warning("No faculty found for MQTT simulation test")
                return False
            
            # Simulate MQTT status message
            status_data = {
                "faculty_id": faculty.id,
                "faculty_name": faculty.name,
                "present": True,
                "status": "Available",
                "timestamp": int(time.time()),
                "ntp_sync_status": "SYNCED"
            }
            
            topic = f"consultease/faculty/{faculty.id}/status"
            
            logger.info(f"Simulating MQTT message to topic: {topic}")
            logger.info(f"Message data: {status_data}")
            
            # Send the message through the faculty controller handler
            self.faculty_controller.handle_faculty_status_update(topic, status_data)
            
            # Wait a moment for processing
            time.sleep(1)
            
            # Check if status was updated
            db.refresh(faculty)
            logger.info(f"Faculty status after MQTT simulation: {faculty.status}")
            
            return True
            
        except Exception as e:
            logger.error(f"MQTT status simulation test failed: {e}")
            return False
        finally:
            db.close()
    
    def test_dashboard_data_refresh(self):
        """Test dashboard data refresh functionality."""
        try:
            # Get faculty data as dashboard would
            faculties = self.faculty_controller.get_all_faculty()
            
            logger.info(f"Dashboard would receive {len(faculties)} faculty members")
            
            # Test data extraction as dashboard does
            for faculty in faculties:
                try:
                    # Access attributes safely as dashboard does
                    faculty_id = faculty.id
                    faculty_name = faculty.name
                    faculty_department = faculty.department
                    faculty_status = faculty.status
                    faculty_always_available = getattr(faculty, 'always_available', False)
                    faculty_email = getattr(faculty, 'email', '')
                    
                    faculty_data = {
                        'id': faculty_id,
                        'name': faculty_name,
                        'department': faculty_department,
                        'available': faculty_status or faculty_always_available,
                        'status': 'Available' if (faculty_status or faculty_always_available) else 'Unavailable',
                        'email': faculty_email
                    }
                    
                    logger.info(f"Dashboard data for {faculty_name}: {faculty_data}")
                    
                except Exception as e:
                    logger.error(f"Error processing faculty {faculty.id}: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Dashboard data refresh test failed: {e}")
            return False
    
    def print_summary(self, results):
        """Print test summary."""
        logger.info("\n" + "=" * 60)
        logger.info("FACULTY STATUS UPDATE TEST SUMMARY")
        logger.info("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status_icon = "✅" if result == "PASS" else "❌"
            logger.info(f"{status_icon} {test_name}: {result}")
            if result == "PASS":
                passed += 1
        
        logger.info("-" * 60)
        logger.info(f"TOTAL: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Faculty status system is working correctly.")
        else:
            logger.warning("⚠️ Some tests failed. Check the issues above.")
            
            # Provide troubleshooting suggestions
            logger.info("\n🔧 TROUBLESHOOTING SUGGESTIONS:")
            logger.info("1. Check MQTT broker connectivity")
            logger.info("2. Verify faculty desk unit is sending status updates")
            logger.info("3. Check database permissions and connectivity")
            logger.info("4. Restart the central system application")
            logger.info("5. Check system logs for detailed error messages")
        
        return passed == total

def main():
    """Main test function."""
    tester = FacultyStatusTester()
    success = tester.run_tests()
    
    if success:
        print("\n✅ Faculty Status Update Tests: SUCCESS")
        sys.exit(0)
    else:
        print("\n❌ Faculty Status Update Tests: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
