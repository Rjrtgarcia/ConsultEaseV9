#!/usr/bin/env python3
"""
Production readiness test suite for ConsultEase.
Tests all critical functionality and security features.
"""
import sys
import os
import unittest
import logging
import tempfile
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Configure test logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestSecurityFeatures(unittest.TestCase):
    """Test security-related features."""
    
    def setUp(self):
        """Set up test environment."""
        # Use test database
        os.environ['DB_TYPE'] = 'sqlite'
        os.environ['DB_PATH'] = ':memory:'
        
    def test_admin_password_validation(self):
        """Test admin password strength validation."""
        from central_system.models.admin import Admin
        
        # Test weak passwords
        weak_passwords = [
            "123456",
            "password",
            "admin",
            "12345678",
            "Password",
            "Password123"
        ]
        
        for password in weak_passwords:
            is_valid, message = Admin.validate_password_strength(password)
            self.assertFalse(is_valid, f"Weak password '{password}' should be rejected")
            
        # Test strong passwords
        strong_passwords = [
            "TempPass123!",
            "MySecure@Pass2024",
            "Complex#Password1",
            "Strong$Pass456"
        ]
        
        for password in strong_passwords:
            is_valid, message = Admin.validate_password_strength(password)
            self.assertTrue(is_valid, f"Strong password '{password}' should be accepted: {message}")
            
    def test_password_hashing(self):
        """Test password hashing functionality."""
        from central_system.models.admin import Admin
        
        password = "TestPassword123!"
        hash1, salt1 = Admin.hash_password(password)
        hash2, salt2 = Admin.hash_password(password)
        
        # Hashes should be different (due to different salts)
        self.assertNotEqual(hash1, hash2)
        self.assertNotEqual(salt1, salt2)
        
        # But verification should work for both
        self.assertTrue(Admin.verify_password(password, hash1, salt1))
        self.assertTrue(Admin.verify_password(password, hash2, salt2))
        
        # Wrong password should fail
        self.assertFalse(Admin.verify_password("WrongPassword", hash1, salt1))
        
    def test_forced_password_change(self):
        """Test forced password change functionality."""
        from central_system.models.admin import Admin
        from central_system.models.base import init_db, get_db
        
        # Initialize test database
        init_db()
        
        db = get_db()
        
        # Create admin with forced password change
        password_hash, salt = Admin.hash_password("TempPass123!")
        admin = Admin(
            username="testadmin",
            password_hash=password_hash,
            salt=salt,
            email="test@example.com",
            is_active=True,
            force_password_change=True
        )
        
        db.add(admin)
        db.commit()
        
        # Test that password change is required
        self.assertTrue(admin.needs_password_change())
        
        # Update password
        success = admin.update_password("NewSecurePass123!")
        self.assertTrue(success)
        
        # Password change should no longer be required
        self.assertFalse(admin.needs_password_change())
        
        db.close()


class TestDatabaseResilience(unittest.TestCase):
    """Test database connection resilience."""
    
    def test_database_connection_retry(self):
        """Test database connection retry logic."""
        from central_system.models.base import get_db_with_health_check
        
        # This should work with in-memory database
        os.environ['DB_TYPE'] = 'sqlite'
        os.environ['DB_PATH'] = ':memory:'
        
        try:
            db = get_db_with_health_check()
            self.assertIsNotNone(db)
            db.close()
        except Exception as e:
            self.fail(f"Database connection should succeed: {e}")
            
    def test_database_health_check(self):
        """Test database health check functionality."""
        from central_system.models.base import get_db_with_health_check
        
        os.environ['DB_TYPE'] = 'sqlite'
        os.environ['DB_PATH'] = ':memory:'
        
        db = get_db_with_health_check()
        
        # Test health check query
        result = db.execute("SELECT 1 as health_check")
        health_check = result.fetchone()
        
        self.assertIsNotNone(health_check)
        self.assertEqual(health_check[0], 1)
        
        db.close()


class TestMQTTPerformance(unittest.TestCase):
    """Test MQTT service performance features."""
    
    def test_mqtt_queue_management(self):
        """Test MQTT queue size management."""
        from central_system.services.async_mqtt_service import AsyncMQTTService
        
        # Create service with small queue size for testing
        service = AsyncMQTTService(max_queue_size=5)
        
        # Fill queue beyond capacity
        for i in range(10):
            service.publish_async(f"test/topic/{i}", {"data": i})
            
        # Check that queue size is limited
        self.assertLessEqual(service.publish_queue.qsize(), 5)
        
        # Check that messages were dropped
        self.assertGreater(service.dropped_messages, 0)
        
    def test_mqtt_statistics(self):
        """Test MQTT service statistics."""
        from central_system.services.async_mqtt_service import AsyncMQTTService
        
        service = AsyncMQTTService()
        stats = service.get_stats()
        
        # Check that all expected statistics are present
        expected_keys = [
            'connected', 'messages_published', 'messages_received',
            'publish_errors', 'dropped_messages', 'queue_size',
            'max_queue_size', 'last_error', 'last_ping'
        ]
        
        for key in expected_keys:
            self.assertIn(key, stats)


class TestHardwareValidation(unittest.TestCase):
    """Test hardware validation functionality."""
    
    def test_hardware_validator(self):
        """Test hardware validation system."""
        from central_system.utils.hardware_validator import HardwareValidator
        
        validator = HardwareValidator()
        results = validator.validate_all()
        
        # Check that all expected components are validated
        expected_components = [
            'rfid_reader', 'display', 'network', 'storage',
            'touch_input', 'keyboard', 'system_resources'
        ]
        
        for component in expected_components:
            self.assertIn(component, results)
            self.assertIsInstance(results[component], bool)
            
        # Test deployment readiness check
        is_ready = validator.is_deployment_ready()
        self.assertIsInstance(is_ready, bool)
        
    def test_hardware_validation_summary(self):
        """Test hardware validation summary."""
        from central_system.utils.hardware_validator import HardwareValidator
        
        validator = HardwareValidator()
        validator.validate_all()
        
        passed, warnings, failed = validator.get_validation_summary()
        
        self.assertIsInstance(passed, list)
        self.assertIsInstance(warnings, list)
        self.assertIsInstance(failed, list)


class TestSystemMonitoring(unittest.TestCase):
    """Test system monitoring functionality."""
    
    def test_system_monitor_creation(self):
        """Test system monitor creation and basic functionality."""
        from central_system.utils.system_monitor import SystemMonitor
        
        monitor = SystemMonitor(monitoring_interval=1)
        
        # Test metrics collection
        metrics = monitor._collect_metrics()
        
        self.assertIsNotNone(metrics)
        self.assertGreater(metrics.cpu_percent, 0)
        self.assertGreater(metrics.memory_percent, 0)
        self.assertGreater(metrics.disk_percent, 0)
        
    def test_system_health_summary(self):
        """Test system health summary."""
        from central_system.utils.system_monitor import get_system_monitor
        
        monitor = get_system_monitor()
        
        # Collect at least one metric
        metrics = monitor._collect_metrics()
        monitor.metrics_history.append(metrics)
        
        health = monitor.get_system_health_summary()
        
        self.assertIn('status', health)
        self.assertIn('message', health)
        self.assertIn('cpu_percent', health)
        self.assertIn('memory_percent', health)
        
    def test_alert_generation(self):
        """Test alert generation."""
        from central_system.utils.system_monitor import SystemMonitor, SystemMetrics
        from datetime import datetime
        
        monitor = SystemMonitor()
        
        # Create metrics that should trigger alerts
        high_cpu_metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=95.0,  # High CPU
            memory_percent=50.0,
            memory_available_gb=2.0,
            disk_percent=50.0,
            disk_free_gb=10.0,
            network_bytes_sent=1000,
            network_bytes_recv=1000,
            process_count=100,
            uptime_seconds=3600
        )
        
        initial_alert_count = len(monitor.alerts)
        monitor._check_alerts(high_cpu_metrics)
        
        # Should have generated at least one alert
        self.assertGreater(len(monitor.alerts), initial_alert_count)


class TestAuditLogging(unittest.TestCase):
    """Test audit logging functionality."""
    
    def setUp(self):
        """Set up test environment."""
        os.environ['DB_TYPE'] = 'sqlite'
        os.environ['DB_PATH'] = ':memory:'
        
    def test_audit_logger_creation(self):
        """Test audit logger creation."""
        from central_system.utils.audit_logger import AuditLogger
        
        logger = AuditLogger()
        self.assertIsNotNone(logger)
        
    def test_audit_event_logging(self):
        """Test audit event logging."""
        from central_system.utils.audit_logger import get_audit_logger
        from central_system.models.base import init_db
        
        # Initialize database
        init_db()
        
        audit_logger = get_audit_logger()
        
        # Log a test event
        audit_logger.log_event(
            action='test_action',
            username='test_user',
            resource='test_resource',
            details='Test audit event',
            success='success'
        )
        
        # Retrieve recent logs
        recent_logs = audit_logger.get_recent_logs(limit=10)
        
        self.assertGreater(len(recent_logs), 0)
        
        # Check that the test event was logged
        test_events = [log for log in recent_logs if log['action'] == 'test_action']
        self.assertGreater(len(test_events), 0)
        
    def test_authentication_logging(self):
        """Test authentication event logging."""
        from central_system.utils.audit_logger import log_authentication
        from central_system.models.base import init_db
        
        # Initialize database
        init_db()
        
        # Log successful authentication
        log_authentication('test_user', True, details='Test login')
        
        # Log failed authentication
        log_authentication('test_user', False, details='Invalid password')


class TestPasswordChangeDialog(unittest.TestCase):
    """Test password change dialog functionality."""
    
    def test_password_validation(self):
        """Test password validation in dialog."""
        # This would require PyQt5 to be available
        # For now, we'll test the underlying validation logic
        from central_system.models.admin import Admin
        
        # Test password strength validation
        weak_password = "weak"
        strong_password = "StrongPass123!"
        
        is_weak_valid, _ = Admin.validate_password_strength(weak_password)
        is_strong_valid, _ = Admin.validate_password_strength(strong_password)
        
        self.assertFalse(is_weak_valid)
        self.assertTrue(is_strong_valid)


def run_production_tests():
    """Run all production readiness tests."""
    logger.info("Starting ConsultEase Production Readiness Tests")
    logger.info("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestSecurityFeatures,
        TestDatabaseResilience,
        TestMQTTPerformance,
        TestHardwareValidation,
        TestSystemMonitoring,
        TestAuditLogging,
        TestPasswordChangeDialog
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    
    if result.failures:
        logger.error("FAILURES:")
        for test, traceback in result.failures:
            logger.error(f"  {test}: {traceback}")
    
    if result.errors:
        logger.error("ERRORS:")
        for test, traceback in result.errors:
            logger.error(f"  {test}: {traceback}")
    
    # Determine overall result
    if result.failures or result.errors:
        logger.error("❌ PRODUCTION READINESS: FAILED")
        logger.error("Critical issues found. System is NOT ready for production deployment.")
        return False
    else:
        logger.info("✅ PRODUCTION READINESS: PASSED")
        logger.info("All tests passed. System is ready for production deployment.")
        return True


if __name__ == "__main__":
    success = run_production_tests()
    sys.exit(0 if success else 1)
