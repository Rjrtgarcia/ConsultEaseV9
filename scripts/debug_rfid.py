#!/usr/bin/env python3
"""
RFID Reader Debugging Tool

This script helps identify and test USB RFID readers connected to the system.
It will:
1. List all input devices
2. Attempt to find devices that match common RFID reader patterns
3. Monitor a specified device for input events
4. Test RFID reading functionality

Usage:
    python debug_rfid.py list         # List all input devices
    python debug_rfid.py monitor <id> # Monitor a specific device for events
    python debug_rfid.py test <id>    # Test RFID reading using the specified device
    
    Where <id> is the device path (e.g., /dev/input/event3) or device number (e.g., 3)
"""

import sys
import os
import time
import logging
import subprocess

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('rfid_debug')

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def list_input_devices():
    """List all input devices with their capabilities."""
    try:
        # Try importing evdev
        import evdev
        
        logger.info("Listing all input devices:")
        print("\n===== INPUT DEVICES =====")
        
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        
        if not devices:
            print("No input devices found.")
            return
        
        for i, device in enumerate(devices):
            print(f"\nDevice {i}: {device.path}")
            print(f"  Name: {device.name}")
            print(f"  Physical Path: {device.phys}")
            
            # Get device info
            try:
                if hasattr(device, 'info') and device.info:
                    bustype = device.info.bustype
                    vendor = device.info.vendor
                    product = device.info.product
                    version = device.info.version
                    
                    print(f"  Bus Type: {bustype:04x}")
                    print(f"  Vendor ID: {vendor:04x}")
                    print(f"  Product ID: {product:04x}")
                    print(f"  Version: {version:04x}")
            except Exception as e:
                print(f"  Error getting device info: {e}")
            
            # List capabilities
            caps = []
            if evdev.ecodes.EV_KEY in device.capabilities():
                key_count = len(device.capabilities().get(evdev.ecodes.EV_KEY, []))
                caps.append(f"Keyboard ({key_count} keys)")
            if evdev.ecodes.EV_REL in device.capabilities():
                caps.append("Mouse/Pointer")
            if evdev.ecodes.EV_ABS in device.capabilities():
                caps.append("Touchscreen/Pad")
                
            print(f"  Capabilities: {', '.join(caps)}")
            
            # Determine if likely RFID reader
            is_rfid = False
            rfid_points = 0
            
            # RFID readers typically have keyboard capabilities with number keys
            if evdev.ecodes.EV_KEY in device.capabilities():
                key_caps = device.capabilities().get(evdev.ecodes.EV_KEY, [])
                has_numerics = any(k in key_caps for k in range(evdev.ecodes.KEY_0, evdev.ecodes.KEY_9 + 1))
                has_enter = evdev.ecodes.KEY_ENTER in key_caps
                
                if has_numerics:
                    rfid_points += 1
                if has_enter:
                    rfid_points += 1
                    
                # Most RFID readers don't have modifier keys like shift/control
                has_shift = evdev.ecodes.KEY_LEFTSHIFT in key_caps or evdev.ecodes.KEY_RIGHTSHIFT in key_caps
                has_ctrl = evdev.ecodes.KEY_LEFTCTRL in key_caps or evdev.ecodes.KEY_RIGHTCTRL in key_caps
                
                if not has_shift and not has_ctrl:
                    rfid_points += 1
                    
                # RFID readers often have limited keys (just what's needed for the card format)
                if 10 < len(key_caps) < 30:
                    rfid_points += 1
            
            # Check for RFID-related terms in device name or path
            for term in ['rfid', 'card', 'reader', 'hid']:
                if term in device.name.lower() or (device.phys and term in device.phys.lower()):
                    rfid_points += 2
                    break
            
            # Check our target VID/PID
            try:
                if hasattr(device, 'info') and device.info:
                    if device.info.vendor == 0xffff and device.info.product == 0x0035:
                        rfid_points += 5
                        print("  *** EXACT MATCH FOR TARGET RFID READER (VID:ffff PID:0035) ***")
            except:
                pass
                
            # Rate likelihood of being an RFID reader
            if rfid_points >= 5:
                print("  ASSESSMENT: Very likely an RFID reader (Score: %d/10)" % min(rfid_points, 10))
            elif rfid_points >= 3:
                print("  ASSESSMENT: Possibly an RFID reader (Score: %d/10)" % min(rfid_points, 10))
            else:
                print("  ASSESSMENT: Probably not an RFID reader (Score: %d/10)" % min(rfid_points, 10))
                
    except ImportError:
        logger.error("evdev library not installed. Please install it with: pip install evdev")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error listing input devices: {e}")
        sys.exit(1)

def normalize_device_path(device_id):
    """Convert a device identifier to a full device path."""
    if device_id.startswith('/dev/input/'):
        return device_id
    
    # If just a number is provided, convert to /dev/input/eventX
    if device_id.isdigit():
        return f"/dev/input/event{device_id}"
    
    # If "eventX" is provided, add the prefix
    if device_id.startswith('event'):
        return f"/dev/input/{device_id}"
        
    return device_id

def monitor_device(device_id):
    """Monitor a specific device for input events."""
    try:
        import evdev
        from evdev import categorize, ecodes
        
        device_path = normalize_device_path(device_id)
        
        try:
            device = evdev.InputDevice(device_path)
            print(f"\nMonitoring device: {device.name} ({device_path})")
            print("Press keys or scan RFID cards. Press Ctrl+C to exit.\n")
            
            for event in device.read_loop():
                if event.type == evdev.ecodes.EV_KEY and event.value == 1:  # Key pressed
                    # Try to get the key name
                    key_name = "UNKNOWN"
                    for name, code in vars(evdev.ecodes).items():
                        if name.startswith('KEY_') and code == event.code:
                            key_name = name[4:]
                            break
                            
                    print(f"Key pressed: {key_name} (code: {event.code})")
        except Exception as e:
            logger.error(f"Error opening or reading from device {device_path}: {e}")
            sys.exit(1)
            
    except ImportError:
        logger.error("evdev library not installed. Please install it with: pip install evdev")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
    except Exception as e:
        logger.error(f"Error monitoring device: {e}")
        sys.exit(1)

def test_rfid_reading(device_id):
    """Test RFID reading functionality with the specified device."""
    try:
        # Set environment variables for testing
        os.environ['RFID_DEVICE_PATH'] = normalize_device_path(device_id)
        os.environ['RFID_SIMULATION_MODE'] = 'false'
        
        # Import RFID service from the main project
        try:
            from central_system.services.rfid_service import RFIDService
        except ImportError:
            logger.error("Cannot import RFIDService. Make sure you're running this script from the project root.")
            sys.exit(1)
            
        print(f"\nTesting RFID reading with device: {os.environ['RFID_DEVICE_PATH']}")
        print("Please scan an RFID card. Press Ctrl+C to exit.\n")
        
        # Create RFID service with callback
        rfid_service = RFIDService()
        
        def on_rfid_read(student, rfid_uid):
            print(f"\n=== RFID CARD READ SUCCESSFULLY ===")
            print(f"UID: {rfid_uid}")
            print("(Student object is None as expected in this test)")
            print("=================================\n")
        
        rfid_service.register_callback(on_rfid_read)
        rfid_service.start()
        
        # Keep the script running until Ctrl+C
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            rfid_service.stop()
            print("\nRFID testing stopped.")
            
    except Exception as e:
        logger.error(f"Error testing RFID reading: {e}")
        sys.exit(1)

def usage():
    """Print usage information."""
    print(__doc__)
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
        
    command = sys.argv[1].lower()
    
    if command == "list":
        list_input_devices()
    elif command == "monitor" and len(sys.argv) == 3:
        monitor_device(sys.argv[2])
    elif command == "test" and len(sys.argv) == 3:
        test_rfid_reading(sys.argv[2])
    else:
        usage() 