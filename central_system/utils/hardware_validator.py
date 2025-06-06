"""
Hardware validation utilities for ConsultEase Raspberry Pi deployment.
Validates required hardware components on startup.
"""
import logging
import os
import shutil
import socket
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class HardwareValidator:
    """Hardware validation for Raspberry Pi deployment."""
    
    def __init__(self):
        self.validation_results = {}
        
    def validate_all(self) -> Dict[str, bool]:
        """
        Validate all required hardware components.
        
        Returns:
            Dict mapping component names to validation status
        """
        self.validation_results = {
            'rfid_reader': self._validate_rfid_reader(),
            'display': self._validate_display(),
            'network': self._validate_network(),
            'storage': self._validate_storage(),
            'touch_input': self._validate_touch_input(),
            'keyboard': self._validate_keyboard(),
            'system_resources': self._validate_system_resources()
        }
        
        return self.validation_results
    
    def _validate_rfid_reader(self) -> bool:
        """Validate RFID reader availability."""
        try:
            import evdev
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            rfid_devices = [device for device in devices if 'rfid' in device.name.lower()]
            
            if rfid_devices:
                logger.info(f"✓ RFID reader found: {rfid_devices[0].name}")
                return True
            else:
                # Check for generic input devices that might be RFID readers
                input_devices = [device for device in devices if 'input' in device.name.lower()]
                if input_devices:
                    logger.warning(f"⚠ No RFID reader found, but input devices available: {len(input_devices)}")
                    return True
                else:
                    logger.error("✗ No RFID reader or input devices found")
                    return False
                    
        except ImportError:
            logger.error("✗ evdev library not available for RFID validation")
            return False
        except Exception as e:
            logger.error(f"✗ Error validating RFID reader: {e}")
            return False
    
    def _validate_display(self) -> bool:
        """Validate display availability."""
        try:
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if not app:
                # Create temporary application for testing
                app = QApplication([])
                
            screen = app.primaryScreen()
            if screen:
                geometry = screen.geometry()
                logger.info(f"✓ Display found: {geometry.width()}x{geometry.height()}")
                return True
            else:
                logger.error("✗ No display found")
                return False
                
        except ImportError:
            logger.error("✗ PyQt5 not available for display validation")
            return False
        except Exception as e:
            logger.error(f"✗ Error validating display: {e}")
            return False
    
    def _validate_network(self) -> bool:
        """Validate network connectivity."""
        try:
            # Test internet connectivity
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            logger.info("✓ Internet connectivity available")
            
            # Test local network
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            logger.info(f"✓ Local network available: {local_ip}")
            
            return True
            
        except OSError as e:
            logger.warning(f"⚠ Network connectivity limited: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Error validating network: {e}")
            return False
    
    def _validate_storage(self) -> bool:
        """Validate storage space."""
        try:
            total, used, free = shutil.disk_usage("/")
            free_gb = free // (1024**3)
            total_gb = total // (1024**3)
            
            if free_gb >= 2:  # At least 2GB free
                logger.info(f"✓ Storage space adequate: {free_gb}GB free of {total_gb}GB total")
                return True
            elif free_gb >= 1:  # 1-2GB free
                logger.warning(f"⚠ Storage space low: {free_gb}GB free of {total_gb}GB total")
                return True
            else:
                logger.error(f"✗ Storage space critical: {free_gb}GB free of {total_gb}GB total")
                return False
                
        except Exception as e:
            logger.error(f"✗ Error validating storage: {e}")
            return False
    
    def _validate_touch_input(self) -> bool:
        """Validate touch input capability."""
        try:
            import evdev
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            touch_devices = [
                device for device in devices 
                if any(keyword in device.name.lower() for keyword in ['touch', 'screen', 'pointer'])
            ]
            
            if touch_devices:
                logger.info(f"✓ Touch input devices found: {len(touch_devices)}")
                return True
            else:
                logger.warning("⚠ No touch input devices found")
                return False
                
        except ImportError:
            logger.warning("⚠ evdev library not available for touch validation")
            return False
        except Exception as e:
            logger.error(f"✗ Error validating touch input: {e}")
            return False
    
    def _validate_keyboard(self) -> bool:
        """Validate on-screen keyboard availability."""
        try:
            # Check for squeekboard
            if shutil.which('squeekboard'):
                logger.info("✓ Squeekboard on-screen keyboard available")
                return True
            
            # Check for onboard
            if shutil.which('onboard'):
                logger.info("✓ Onboard on-screen keyboard available")
                return True
            
            # Check for matchbox-keyboard
            if shutil.which('matchbox-keyboard'):
                logger.info("✓ Matchbox on-screen keyboard available")
                return True
            
            logger.warning("⚠ No on-screen keyboard found")
            return False
            
        except Exception as e:
            logger.error(f"✗ Error validating keyboard: {e}")
            return False
    
    def _validate_system_resources(self) -> bool:
        """Validate system resources (CPU, memory)."""
        try:
            # Check memory
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                
            for line in meminfo.split('\n'):
                if line.startswith('MemTotal:'):
                    total_mem_kb = int(line.split()[1])
                    total_mem_gb = total_mem_kb / (1024 * 1024)
                    
                    if total_mem_gb >= 2:  # At least 2GB RAM
                        logger.info(f"✓ Memory adequate: {total_mem_gb:.1f}GB")
                        return True
                    elif total_mem_gb >= 1:  # 1-2GB RAM
                        logger.warning(f"⚠ Memory limited: {total_mem_gb:.1f}GB")
                        return True
                    else:
                        logger.error(f"✗ Memory insufficient: {total_mem_gb:.1f}GB")
                        return False
            
            logger.warning("⚠ Could not determine memory size")
            return False
            
        except Exception as e:
            logger.error(f"✗ Error validating system resources: {e}")
            return False
    
    def get_validation_summary(self) -> Tuple[List[str], List[str], List[str]]:
        """
        Get validation summary.
        
        Returns:
            Tuple of (passed, warnings, failed) component lists
        """
        passed = []
        warnings = []
        failed = []
        
        for component, status in self.validation_results.items():
            if status:
                passed.append(component)
            else:
                failed.append(component)
        
        return passed, warnings, failed
    
    def is_deployment_ready(self) -> bool:
        """
        Check if system is ready for deployment.
        
        Returns:
            True if critical components are available
        """
        critical_components = ['display', 'storage', 'system_resources']
        
        for component in critical_components:
            if not self.validation_results.get(component, False):
                return False
        
        return True


def validate_hardware() -> Dict[str, bool]:
    """
    Convenience function to validate hardware.
    
    Returns:
        Dictionary mapping component names to validation status
    """
    validator = HardwareValidator()
    return validator.validate_all()


def log_hardware_status():
    """Log hardware validation status."""
    validator = HardwareValidator()
    results = validator.validate_all()
    
    passed, warnings, failed = validator.get_validation_summary()
    
    logger.info("=== Hardware Validation Summary ===")
    
    if passed:
        logger.info(f"✓ Passed: {', '.join(passed)}")
    
    if warnings:
        logger.warning(f"⚠ Warnings: {', '.join(warnings)}")
    
    if failed:
        logger.error(f"✗ Failed: {', '.join(failed)}")
    
    if validator.is_deployment_ready():
        logger.info("✓ System ready for deployment")
    else:
        logger.error("✗ System NOT ready for deployment - critical components missing")
    
    return results
