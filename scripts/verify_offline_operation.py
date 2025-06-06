#!/usr/bin/env python3
"""
Offline Operation Verification Script
Tests the offline operation capabilities and message queuing system.
"""

import sys
import os
import logging
import time
import json
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from central_system.models import get_db, Faculty, Consultation, ConsultationStatus
from central_system.controllers.consultation_controller import ConsultationController
from central_system.controllers.faculty_controller import FacultyController
from central_system.services.consultation_queue_service import get_consultation_queue_service, MessagePriority
from central_system.utils.mqtt_utils import publish_mqtt_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OfflineOperationVerifier:
    """Verifies offline operation and message queuing functionality."""
    
    def __init__(self):
        self.consultation_controller = ConsultationController()
        self.faculty_controller = FacultyController()
        self.queue_service = get_consultation_queue_service()
        self.test_results = []
        
    def run_verification(self):
        """Run all offline operation verification tests."""
        logger.info("Starting Offline Operation Verification")
        logger.info("=" * 60)
        
        tests = [
            ("Queue Service Initialization", self.verify_queue_service),
            ("Faculty Status Tracking", self.verify_faculty_status_tracking),
            ("Consultation Request Queuing", self.verify_consultation_queuing),
            ("Message Priority Handling", self.verify_message_priority),
            ("Queue Processing", self.verify_queue_processing),
            ("Recovery Simulation", self.verify_recovery_simulation),
            ("Database Persistence", self.verify_database_persistence),
            ("Queue Statistics", self.verify_queue_statistics),
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
        
    def verify_queue_service(self):
        """Verify queue service initialization and basic functionality."""
        try:
            # Check if queue service is properly initialized
            has_start_method = hasattr(self.queue_service, 'start')
            has_queue_method = hasattr(self.queue_service, 'queue_consultation_request')
            has_status_method = hasattr(self.queue_service, 'update_faculty_status')
            
            logger.info(f"Start method: {'✅' if has_start_method else '❌'}")
            logger.info(f"Queue method: {'✅' if has_queue_method else '❌'}")
            logger.info(f"Status method: {'✅' if has_status_method else '❌'}")
            
            # Test database initialization
            db_exists = os.path.exists(self.queue_service.db_path)
            logger.info(f"Database exists: {'✅' if db_exists else '❌'}")
            
            return has_start_method and has_queue_method and has_status_method
            
        except Exception as e:
            logger.error(f"Queue service verification failed: {e}")
            return False
    
    def verify_faculty_status_tracking(self):
        """Verify faculty online/offline status tracking."""
        try:
            # Test faculty status updates
            test_faculty_id = 1
            
            # Set faculty offline
            self.queue_service.update_faculty_status(test_faculty_id, False)
            is_offline = not self.queue_service.is_faculty_online(test_faculty_id)
            
            # Set faculty online
            self.queue_service.update_faculty_status(test_faculty_id, True)
            is_online = self.queue_service.is_faculty_online(test_faculty_id)
            
            logger.info(f"Offline status tracking: {'✅' if is_offline else '❌'}")
            logger.info(f"Online status tracking: {'✅' if is_online else '❌'}")
            
            return is_offline and is_online
            
        except Exception as e:
            logger.error(f"Faculty status tracking verification failed: {e}")
            return False
    
    def verify_consultation_queuing(self):
        """Verify consultation request queuing for offline faculty."""
        try:
            db = get_db()
            
            # Create or get test faculty
            faculty = db.query(Faculty).first()
            if not faculty:
                faculty = Faculty(
                    name="Test Faculty",
                    department="Test Department",
                    email="test@example.com",
                    ble_id="AA:BB:CC:DD:EE:FF"
                )
                db.add(faculty)
                db.commit()
            
            # Set faculty offline
            self.queue_service.update_faculty_status(faculty.id, False)
            
            # Create test consultation
            consultation = Consultation(
                student_id=1,
                faculty_id=faculty.id,
                request_message="Test consultation request for offline queuing",
                course_code="TEST101",
                status=ConsultationStatus.PENDING,
                requested_at=datetime.now()
            )
            db.add(consultation)
            db.commit()
            
            # Test queuing
            queue_success = self.queue_service.queue_consultation_request(
                consultation, MessagePriority.NORMAL
            )
            
            logger.info(f"Consultation queuing: {'✅' if queue_success else '❌'}")
            
            # Check queue statistics
            stats = self.queue_service.get_queue_statistics()
            has_pending = stats.get('faculty_pending', {}).get(faculty.id, 0) > 0
            
            logger.info(f"Queue statistics: {'✅' if has_pending else '❌'}")
            
            return queue_success and has_pending
            
        except Exception as e:
            logger.error(f"Consultation queuing verification failed: {e}")
            return False
        finally:
            db.close()
    
    def verify_message_priority(self):
        """Verify message priority handling."""
        try:
            db = get_db()
            faculty = db.query(Faculty).first()
            
            if not faculty:
                logger.warning("No faculty found for priority testing")
                return False
            
            # Set faculty offline
            self.queue_service.update_faculty_status(faculty.id, False)
            
            # Create consultations with different priorities
            priorities = [MessagePriority.LOW, MessagePriority.HIGH, MessagePriority.CRITICAL]
            queued_count = 0
            
            for i, priority in enumerate(priorities):
                consultation = Consultation(
                    student_id=1,
                    faculty_id=faculty.id,
                    request_message=f"Priority test message {priority.name}",
                    course_code="PRIORITY",
                    status=ConsultationStatus.PENDING,
                    requested_at=datetime.now()
                )
                db.add(consultation)
                db.commit()
                
                success = self.queue_service.queue_consultation_request(consultation, priority)
                if success:
                    queued_count += 1
            
            logger.info(f"Priority queuing: {queued_count}/{len(priorities)} messages queued")
            
            return queued_count == len(priorities)
            
        except Exception as e:
            logger.error(f"Message priority verification failed: {e}")
            return False
        finally:
            db.close()
    
    def verify_queue_processing(self):
        """Verify queue processing when faculty comes online."""
        try:
            db = get_db()
            faculty = db.query(Faculty).first()
            
            if not faculty:
                logger.warning("No faculty found for processing testing")
                return False
            
            # Get initial queue stats
            initial_stats = self.queue_service.get_queue_statistics()
            initial_pending = initial_stats.get('faculty_pending', {}).get(faculty.id, 0)
            
            logger.info(f"Initial pending messages: {initial_pending}")
            
            # Simulate faculty coming online
            self.queue_service.update_faculty_status(faculty.id, True)
            
            # Wait a moment for processing
            time.sleep(2)
            
            # Check if messages were processed
            final_stats = self.queue_service.get_queue_statistics()
            final_pending = final_stats.get('faculty_pending', {}).get(faculty.id, 0)
            
            logger.info(f"Final pending messages: {final_pending}")
            
            # Messages should be processed (reduced)
            processed = initial_pending > final_pending
            logger.info(f"Queue processing: {'✅' if processed else '❌'}")
            
            return processed or initial_pending == 0  # Pass if no messages or processed
            
        except Exception as e:
            logger.error(f"Queue processing verification failed: {e}")
            return False
        finally:
            db.close()
    
    def verify_recovery_simulation(self):
        """Verify recovery simulation functionality."""
        try:
            # Test consultation controller integration
            has_queue_service = hasattr(self.consultation_controller, 'queue_service')
            
            # Test faculty controller integration
            has_faculty_queue = hasattr(self.faculty_controller, 'queue_service')
            
            logger.info(f"Consultation controller integration: {'✅' if has_queue_service else '❌'}")
            logger.info(f"Faculty controller integration: {'✅' if has_faculty_queue else '❌'}")
            
            return has_queue_service and has_faculty_queue
            
        except Exception as e:
            logger.error(f"Recovery simulation verification failed: {e}")
            return False
    
    def verify_database_persistence(self):
        """Verify database persistence functionality."""
        try:
            import sqlite3
            
            # Check if database file exists
            db_exists = os.path.exists(self.queue_service.db_path)
            
            if db_exists:
                # Check database structure
                with sqlite3.connect(self.queue_service.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='queued_requests'
                    """)
                    table_exists = cursor.fetchone() is not None
                    
                    if table_exists:
                        # Check if we can query the table
                        cursor = conn.execute("SELECT COUNT(*) FROM queued_requests")
                        count = cursor.fetchone()[0]
                        logger.info(f"Queued requests in database: {count}")
                        
                        # Check for required columns
                        cursor = conn.execute("PRAGMA table_info(queued_requests)")
                        columns = [row[1] for row in cursor.fetchall()]
                        required_columns = ['id', 'consultation_id', 'faculty_id', 'status', 'priority']
                        has_columns = all(col in columns for col in required_columns)
                        
                        logger.info(f"Database structure: {'✅' if has_columns else '❌'}")
                        return has_columns
            
            logger.warning("Database file not found")
            return False
            
        except Exception as e:
            logger.error(f"Database persistence verification failed: {e}")
            return False
    
    def verify_queue_statistics(self):
        """Verify queue statistics functionality."""
        try:
            stats = self.queue_service.get_queue_statistics()
            
            # Check if statistics contain expected keys
            expected_keys = ['status_breakdown', 'faculty_pending', 'total_online_faculty']
            has_keys = all(key in stats for key in expected_keys)
            
            logger.info(f"Statistics structure: {'✅' if has_keys else '❌'}")
            logger.info(f"Statistics content: {json.dumps(stats, indent=2)}")
            
            return has_keys
            
        except Exception as e:
            logger.error(f"Queue statistics verification failed: {e}")
            return False
    
    def print_summary(self):
        """Print verification summary."""
        logger.info("\n" + "=" * 60)
        logger.info("OFFLINE OPERATION VERIFICATION SUMMARY")
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
            logger.info("🎉 All tests passed! Offline operation system is ready for production.")
        else:
            logger.warning("⚠️ Some tests failed. Please review the issues before deployment.")
        
        return passed == total

def main():
    """Main verification function."""
    verifier = OfflineOperationVerifier()
    success = verifier.run_verification()
    
    if success:
        print("\n✅ Offline Operation Verification: SUCCESS")
        sys.exit(0)
    else:
        print("\n❌ Offline Operation Verification: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
