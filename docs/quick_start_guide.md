# ConsultEase Quick Start Guide

This guide provides the essential steps to quickly set up and run the ConsultEase system. For a more comprehensive setup, refer to the full [Deployment Guide](deployment_guide.md).

## Central System Setup (Raspberry Pi)

### 1. Install Required Software
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y git python3-pip python3-pyqt5 python3-dev libpq-dev postgresql postgresql-contrib mosquitto mosquitto-clients

# Start services
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

### 2. Get ConsultEase
```bash
# Clone repository
git clone https://github.com/yourusername/ConsultEase.git
cd ConsultEase

# Install Python dependencies
pip3 install -r requirements.txt
```

### 3. Set Up Database
```bash
# Create database and user
sudo -u postgres psql -c "CREATE DATABASE consultease;"
sudo -u postgres psql -c "CREATE USER piuser WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE consultease TO piuser;"

# Create .env file
cat > .env << EOF
DB_USER=piuser
DB_PASSWORD=password
DB_HOST=localhost
DB_NAME=consultease
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
CONSULTEASE_KEYBOARD=squeekboard
EOF
```

### 4. Install On-Screen Keyboard
```bash
# Install and configure squeekboard (preferred keyboard)
chmod +x scripts/install_squeekboard.sh
./scripts/install_squeekboard.sh
```

### 5. Initialize Database
```bash
# Create initial admin user
python3 -c "
from central_system.models import Admin, init_db
from central_system.controllers import AdminController
init_db()
admin_controller = AdminController()
admin_controller.ensure_default_admin()
print('Default admin created with username \"admin\" and password \"admin123\"')
"
```

### 6. Run ConsultEase
```bash
# Start the application
python3 central_system/main.py
```

## Faculty Desk Unit Setup (ESP32)

### 1. Prepare Arduino IDE
- Install Arduino IDE from [arduino.cc](https://www.arduino.cc/en/software)
- Add ESP32 board support:
  - Go to File > Preferences
  - Add `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json` to Additional Boards Manager URLs
  - Go to Tools > Board > Boards Manager
  - Search for ESP32 and install

### 2. Install Required Libraries
- Open Tools > Manage Libraries
- Install the following libraries:
  - TFT_eSPI by Bodmer
  - PubSubClient by Nick O'Leary
  - ArduinoJson by Benoit Blanchon
  - NimBLE-Arduino by h2zero

### 3. Configure TFT_eSPI
- Find the TFT_eSPI library folder (usually in Documents/Arduino/libraries)
- Replace User_Setup.h with the one from ConsultEase/faculty_desk_unit/config/

### 4. Configure Faculty Desk Unit
- Open faculty_desk_unit/config.h in Arduino IDE
- Update the following settings:
  - WiFi credentials (WIFI_SSID and WIFI_PASSWORD)
  - MQTT broker IP address (MQTT_SERVER)
  - Faculty ID and name (FACULTY_ID and FACULTY_NAME)
  - BLE settings (including always-on option if desired)

### 5. Upload Firmware
- Open faculty_desk_unit/faculty_desk_unit.ino in Arduino IDE
- Select your ESP32 board from Tools > Board
- Connect ESP32 via USB and select the correct port
- Click Upload

## Testing the System

### 1. Test MQTT Communication
```bash
# Subscribe to faculty status topic
mosquitto_sub -t "consultease/faculty/+/status"

# In another terminal, publish a test message
mosquitto_pub -t "consultease/faculty/1/status" -m "keychain_connected"
```

### 2. Test BLE Functionality
```bash
# Run the BLE test script
python3 scripts/test_ble_connection.py test
```

### 3. Test UI Improvements
```bash
# Run the UI test script
python3 scripts/test_ui_improvements.py
```

## Common Issues and Solutions

### On-Screen Keyboard Not Appearing
```bash
# Show keyboard manually
~/keyboard-show.sh

# Fix keyboard issues
./scripts/fix_keyboard.sh
```

### RFID Reader Not Working
```bash
# List input devices
python3 scripts/debug_rfid.py list

# Test RFID reader
python3 scripts/debug_rfid.py test

# Fix RFID issues
sudo ./scripts/fix_rfid.sh
```

### Database Connection Errors
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
psql -U piuser -d consultease -c "SELECT 1;"
```

### MQTT Connection Issues
```bash
# Check Mosquitto status
sudo systemctl status mosquitto

# Test MQTT broker
mosquitto_sub -t "test" &
mosquitto_pub -t "test" -m "hello"
```

## Auto-Start Configuration

To make ConsultEase start automatically on boot:

```bash
# Create service file
sudo nano /etc/systemd/system/consultease.service

# Add the following content:
# [Unit]
# Description=ConsultEase Central System
# After=network.target postgresql.service mosquitto.service
#
# [Service]
# ExecStart=/usr/bin/python3 /path/to/consultease/central_system/main.py
# WorkingDirectory=/path/to/consultease
# StandardOutput=inherit
# StandardError=inherit
# Restart=always
# User=pi
#
# [Install]
# WantedBy=multi-user.target

# Enable and start the service
sudo systemctl enable consultease.service
sudo systemctl start consultease.service
```

## Next Steps

After completing this quick setup:

1. **Change Default Password**: Log in to the admin interface with username "admin" and password "admin123", then change the password immediately.

2. **Add Faculty and Students**: Use the admin interface to add faculty members and students to the system.

3. **Configure BLE Beacons**: Set up BLE beacons for faculty members to enable presence detection.

4. **Test Full System**: Test the complete system with RFID cards, consultation requests, and faculty desk units.

5. **Optimize Performance**: Refer to the full deployment guide for performance optimization tips.

For more detailed instructions and troubleshooting, refer to the full [Deployment Guide](deployment_guide.md), [User Manual](user_manual.md), and [Recent Improvements](recent_improvements.md) documentation.
