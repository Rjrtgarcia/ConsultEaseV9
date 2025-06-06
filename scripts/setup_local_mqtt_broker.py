#!/usr/bin/env python3
"""
Setup Local MQTT Broker Script

This script helps set up a local MQTT broker for testing ConsultEase communication.

Usage:
    python scripts/setup_local_mqtt_broker.py
"""

import sys
import subprocess
import logging
import platform
import socket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(command, description):
    """Run a system command and log the result."""
    try:
        logger.info(f"🔧 {description}...")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ {description} - Success")
            if result.stdout.strip():
                logger.info(f"   Output: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"❌ {description} - Failed")
            if result.stderr.strip():
                logger.error(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"❌ {description} - Exception: {e}")
        return False

def check_mqtt_broker():
    """Check if MQTT broker is running."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 1883))
        sock.close()
        return result == 0
    except:
        return False

def get_local_ip():
    """Get the local IP address."""
    try:
        # Connect to a remote address to determine local IP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        local_ip = sock.getsockname()[0]
        sock.close()
        return local_ip
    except:
        return "127.0.0.1"

def setup_mqtt_broker():
    """Set up MQTT broker based on the operating system."""
    system = platform.system().lower()
    
    logger.info("🚀 Setting up local MQTT broker...")
    logger.info(f"   Detected OS: {system}")
    
    if check_mqtt_broker():
        logger.info("✅ MQTT broker is already running on port 1883")
        return True
    
    if system == "linux":
        # Linux/Raspberry Pi setup
        logger.info("🐧 Setting up MQTT broker for Linux...")
        
        commands = [
            ("sudo apt-get update", "Updating package list"),
            ("sudo apt-get install -y mosquitto mosquitto-clients", "Installing Mosquitto MQTT broker"),
            ("sudo systemctl start mosquitto", "Starting Mosquitto service"),
            ("sudo systemctl enable mosquitto", "Enabling Mosquitto to start on boot"),
        ]
        
        for command, description in commands:
            if not run_command(command, description):
                logger.error(f"❌ Failed to execute: {command}")
                return False
                
    elif system == "darwin":  # macOS
        logger.info("🍎 Setting up MQTT broker for macOS...")
        
        # Check if Homebrew is installed
        if run_command("which brew", "Checking Homebrew installation"):
            commands = [
                ("brew install mosquitto", "Installing Mosquitto via Homebrew"),
                ("brew services start mosquitto", "Starting Mosquitto service"),
            ]
        else:
            logger.error("❌ Homebrew not found. Please install Homebrew first:")
            logger.info("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            return False
        
        for command, description in commands:
            if not run_command(command, description):
                logger.error(f"❌ Failed to execute: {command}")
                return False
                
    elif system == "windows":
        logger.info("🪟 For Windows, please:")
        logger.info("   1. Download Mosquitto from: https://mosquitto.org/download/")
        logger.info("   2. Install and start the service")
        logger.info("   3. Or use Docker: docker run -it -p 1883:1883 eclipse-mosquitto")
        return False
        
    else:
        logger.error(f"❌ Unsupported operating system: {system}")
        return False
    
    # Wait a moment and check if broker is running
    import time
    time.sleep(3)
    
    if check_mqtt_broker():
        logger.info("✅ MQTT broker setup completed successfully!")
        return True
    else:
        logger.error("❌ MQTT broker setup failed - broker not responding")
        return False

def test_mqtt_broker():
    """Test MQTT broker functionality."""
    logger.info("🧪 Testing MQTT broker functionality...")
    
    test_commands = [
        ("mosquitto_pub -h localhost -t test/topic -m 'Hello MQTT'", "Testing MQTT publish"),
        ("timeout 2 mosquitto_sub -h localhost -t test/topic -C 1", "Testing MQTT subscribe"),
    ]
    
    for command, description in test_commands:
        run_command(command, description)

def display_connection_info():
    """Display connection information."""
    local_ip = get_local_ip()
    
    logger.info("📋 MQTT Broker Connection Information:")
    logger.info("=" * 50)
    logger.info(f"   Local IP: {local_ip}")
    logger.info(f"   Localhost: 127.0.0.1")
    logger.info(f"   Port: 1883")
    logger.info("")
    logger.info("📝 For ESP32 Configuration (config.h):")
    logger.info(f'   #define MQTT_SERVER "{local_ip}"')
    logger.info("   #define MQTT_PORT 1883")
    logger.info("")
    logger.info("📝 For Central System Configuration:")
    logger.info("   Set MQTT_BROKER_HOST environment variable or config file")
    logger.info(f"   MQTT_BROKER_HOST={local_ip}")

def main():
    """Main function."""
    logger.info("🔧 ConsultEase MQTT Broker Setup")
    logger.info("=" * 40)
    
    # Check if broker is already running
    if check_mqtt_broker():
        logger.info("✅ MQTT broker is already running!")
        display_connection_info()
        return True
    
    # Set up broker
    success = setup_mqtt_broker()
    
    if success:
        # Test broker
        test_mqtt_broker()
        
        # Display connection info
        display_connection_info()
        
        logger.info("🎉 MQTT broker setup completed!")
        logger.info("🔍 You can now run the ESP32 communication test:")
        logger.info("   python scripts/test_esp32_communication.py")
        
    else:
        logger.error("❌ MQTT broker setup failed")
        logger.info("💡 Alternative options:")
        logger.info("   1. Use Docker: docker run -it -p 1883:1883 eclipse-mosquitto")
        logger.info("   2. Use online broker (for testing only): test.mosquitto.org")
        logger.info("   3. Install manually from: https://mosquitto.org/download/")
    
    return success

if __name__ == "__main__":
    main() 