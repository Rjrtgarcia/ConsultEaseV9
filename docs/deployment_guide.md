# ConsultEase Deployment Guide

This guide provides comprehensive instructions for deploying the complete ConsultEase system, including both the Central System (Raspberry Pi) and the Faculty Desk Units (ESP32). This guide incorporates all recent improvements to the system.

## 🚀 Production Readiness Status

**Current Version**: Production Ready ✅
**Security Level**: Enhanced with audit logging and forced password changes
**Performance**: Optimized with queue management and system monitoring
**Reliability**: Hardware validation and error recovery implemented

## ⚠️ CRITICAL SECURITY NOTICE

**Default Admin Credentials**: The system creates a default admin account with temporary credentials that MUST be changed on first login:
- Username: `admin`
- Password: `TempPass123!`

**This password MUST be changed immediately after first login for security.**

## 🔧 New Features in This Release

### Security Enhancements
- **Forced Password Changes**: Admins must change default/expired passwords
- **Password Strength Validation**: Enforced strong password requirements
- **Audit Logging**: Complete audit trail for all security events
- **Enhanced Authentication**: Improved login security with session management

### Performance Improvements
- **MQTT Queue Management**: Prevents memory exhaustion during network issues
- **Database Resilience**: Enhanced connection retry logic with exponential backoff
- **System Monitoring**: Real-time performance monitoring and alerting
- **Hardware Validation**: Startup validation of all required components

### User Interface
- **Enhanced Password Change Dialog**: Modern, user-friendly password change interface
- **System Monitoring Dashboard**: Real-time system health monitoring in admin panel
- **Improved Error Handling**: Better error messages and recovery mechanisms

## Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [Central System Setup](#central-system-setup)
3. [Faculty Desk Unit Setup](#faculty-desk-unit-setup)
4. [BLE Beacon Setup](#ble-beacon-setup)
5. [Network Configuration](#network-configuration)
6. [Database Setup](#database-setup)
7. [System Testing](#system-testing)
8. [Troubleshooting](#troubleshooting)
9. [Touch Interface Setup](#touch-interface-setup)
10. [Performance Optimization](#performance-optimization)

## Hardware Requirements

### Central System (Raspberry Pi)
- Raspberry Pi 4 (4GB RAM recommended)
- 10.1-inch touchscreen (1024x600 resolution)
- USB RFID IC Reader
- 32GB+ microSD card
- Power supply (5V, 3A recommended)
- Case or mounting solution

### Faculty Desk Unit (per faculty member)
- ESP32 development board
- 2.4-inch TFT SPI Display (ST7789)
- Power supply (USB or wall adapter)
- Case or enclosure

### BLE Beacon (per faculty member)
- ESP32 development board (smaller form factor recommended)
- Small LiPo battery (optional for portable use)
- Case or enclosure

### Additional Requirements
- Local network with Wi-Fi access
- Ethernet cable (optional for Raspberry Pi)
- RFID cards for students

## Central System Setup

### 1. Operating System Installation
1. Download Raspberry Pi OS (64-bit, Bookworm) from the [official website](https://www.raspberrypi.org/software/operating-systems/)
2. Flash the OS to the microSD card using [Raspberry Pi Imager](https://www.raspberrypi.org/software/)
3. Insert the microSD card into the Raspberry Pi and connect the display, keyboard, and mouse
4. Power on the Raspberry Pi and complete the initial setup

### 2. Touchscreen Configuration
1. Connect the touchscreen to the Raspberry Pi
2. Update the system:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
3. Configure the display resolution if needed:
   ```bash
   sudo nano /boot/config.txt
   ```
   Add these lines at the end:
   ```
   hdmi_group=2
   hdmi_mode=87
   hdmi_cvt=1024 600 60 6 0 0 0
   ```
4. Save and reboot the Raspberry Pi:
   ```bash
   sudo reboot
   ```

### 3. PostgreSQL Installation
1. Install PostgreSQL:
   ```bash
   sudo apt install postgresql postgresql-contrib -y
   ```
2. Start the PostgreSQL service:
   ```bash
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

### 4. MQTT Broker Setup
1. Install Mosquitto MQTT broker:
   ```bash
   sudo apt install mosquitto mosquitto-clients -y
   ```
2. Configure Mosquitto with authentication:
   ```bash
   # Create password file
   sudo mosquitto_passwd -c /etc/mosquitto/passwd consultease_user

   # Configure Mosquitto
   sudo nano /etc/mosquitto/mosquitto.conf
   ```
   Add these lines:
   ```
   listener 1883
   allow_anonymous false
   password_file /etc/mosquitto/passwd
   ```
3. Start and enable the Mosquitto service:
   ```bash
   sudo systemctl start mosquitto
   sudo systemctl enable mosquitto
   ```

### 5. Python Dependencies Installation
1. Install required packages:
   ```bash
   sudo apt install python3-pip python3-pyqt5 python3-evdev -y
   ```
2. Install PyQt5 WebEngine:
   ```bash
   sudo apt install python3-pyqt5.qtwebengine -y
   ```
3. Install Python libraries:
   ```bash
   pip3 install paho-mqtt sqlalchemy psycopg2-binary
   ```

### 6. ConsultEase Application Setup
1. Clone the ConsultEase repository:
   ```bash
   git clone https://github.com/yourusername/ConsultEase.git
   cd ConsultEase
   ```
2. Set up the database:
   ```bash
   sudo -u postgres psql -c "CREATE DATABASE consultease;"
   sudo -u postgres psql -c "CREATE USER piuser WITH PASSWORD 'password';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE consultease TO piuser;"
   ```
3. Configure environment variables (create a `.env` file):
   ```bash
   DB_USER=piuser
   DB_PASSWORD=password
   DB_HOST=localhost
   DB_NAME=consultease
   MQTT_BROKER_HOST=localhost
   MQTT_BROKER_PORT=1883
   ```
4. Run the application for testing:
   ```bash
   python3 central_system/main.py
   ```

### 7. Auto-start Configuration
1. Create a service file:
   ```bash
   sudo nano /etc/systemd/system/consultease.service
   ```
2. Add the following content:
   ```
   [Unit]
   Description=ConsultEase Central System
   After=network.target postgresql.service mosquitto.service

   [Service]
   ExecStart=/usr/bin/python3 /home/pi/ConsultEase/central_system/main.py
   WorkingDirectory=/home/pi/ConsultEase
   StandardOutput=inherit
   StandardError=inherit
   Restart=always
   User=pi
   Environment=DISPLAY=:0
   Environment=XAUTHORITY=/home/pi/.Xauthority
   Environment=CONSULTEASE_KEYBOARD=squeekboard
   Environment=PYTHONUNBUFFERED=1
   Environment=MQTT_USERNAME=consultease_user
   Environment=MQTT_PASSWORD=consultease_secure_password
   Environment=CONSULTEASE_FULLSCREEN=true

   [Install]
   WantedBy=multi-user.target
   ```
3. Enable and start the service:
   ```bash
   sudo systemctl enable consultease.service
   sudo systemctl start consultease.service
   ```

## Faculty Desk Unit Setup

### 1. Arduino IDE Installation
1. Download and install the Arduino IDE from the [official website](https://www.arduino.cc/en/software)
2. Install the ESP32 board package:
   - In Arduino IDE, go to File > Preferences
   - Add this URL to the "Additional Boards Manager URLs" field:
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to Tools > Board > Boards Manager
   - Search for ESP32 and install the latest version

### 2. Required Libraries Installation
Install the following libraries via the Arduino Library Manager (Tools > Manage Libraries):
- TFT_eSPI by Bodmer
- PubSubClient by Nick O'Leary
- ArduinoJson by Benoit Blanchon
- NimBLE-Arduino by h2zero

### 3. TFT_eSPI Configuration
1. Navigate to your Arduino libraries folder (usually in Documents/Arduino/libraries)
2. Find the TFT_eSPI folder
3. Replace the User_Setup.h file with the one from the ConsultEase repository
4. Alternatively, edit the file to match your display configuration

### 4. Faculty Desk Unit Firmware Upload
1. Open the `faculty_desk_unit.ino` file in Arduino IDE
2. Update the configuration section with your settings:
   - WiFi credentials
   - MQTT broker address (Raspberry Pi IP)
   - Faculty ID (matching database record)
   - Faculty name
   - BLE settings (including always-on option)
3. Connect the ESP32 to your computer via USB
4. Select the correct board and port in Arduino IDE
5. Click the Upload button
6. Monitor the serial output to verify the connection

Note: The faculty desk unit now supports an always-on BLE option, which keeps the faculty status as "Available" even when no BLE beacon is detected. This is configured in the `config.h` file.

## BLE Beacon Setup

### 1. Testing BLE Functionality
Before deploying the BLE beacons, you can test the BLE functionality using the provided test script:
```bash
cd /path/to/consultease
python scripts/test_ble_connection.py test
```

This script will:
- Simulate a BLE beacon
- Simulate a faculty desk unit
- Test MQTT communication between components
- Verify proper status updates

### 2. BLE Beacon Firmware Upload
1. Open the `faculty_desk_unit/ble_beacon/ble_beacon.ino` file in Arduino IDE
2. Update the configuration in `ble_beacon/config.h`:
   - Faculty ID (matching database record)
   - Faculty name
   - Device name
   - Advertising interval
3. Connect the ESP32 to your computer via USB
4. Select the correct board and port in Arduino IDE
5. Click the Upload button
6. Monitor the serial output to get the MAC address of the beacon
7. Note this MAC address for use in the Faculty Desk Unit configuration

### 3. Beacon Configuration
1. Optionally, customize the beacon settings:
   - Device name
   - Advertising interval
   - LED behavior
2. For battery-powered operation, configure power management settings

### 4. MQTT Communication Testing
Test the MQTT communication between components:
```bash
# Subscribe to faculty status topic
mosquitto_sub -t "consultease/faculty/+/status"

# Subscribe to consultation requests topic
mosquitto_sub -t "consultease/faculty/+/requests"

# Publish a test message
mosquitto_pub -t "consultease/faculty/1/status" -m "keychain_connected"
```

## Network Configuration

### 1. Static IP for Raspberry Pi (Recommended)
1. Edit the DHCP configuration:
   ```bash
   sudo nano /etc/dhcpcd.conf
   ```
2. Add these lines (adjust based on your network):
   ```
   interface eth0  # or wlan0 for WiFi
   static ip_address=192.168.1.100/24
   static routers=192.168.1.1
   static domain_name_servers=192.168.1.1 8.8.8.8
   ```
3. Restart networking:
   ```bash
   sudo systemctl restart dhcpcd
   ```

### 2. Port Forwarding (Optional for Remote Access)
Configure your router to forward the necessary ports if remote access is required:
- Port 1883 for MQTT
- Port 5432 for PostgreSQL (not recommended for direct internet exposure)

## Database Setup

### 1. Initial Data Setup
1. Create a script to add initial admin user:
   ```bash
   sudo nano add_admin.py
   ```
2. Add the following content:
   ```python
   from central_system.models import Admin, init_db
   from central_system.controllers import AdminController

   # Initialize database
   init_db()

   # Create admin controller
   admin_controller = AdminController()

   # Ensure default admin exists
   admin_controller.ensure_default_admin()

   print("Default admin created with username 'admin' and password 'admin123'")
   print("Please change this password immediately!")
   ```
3. Run the script:
   ```bash
   python3 add_admin.py
   ```

### 2. Sample Data (Optional)
1. Create a script to add sample data for testing:
   ```bash
   sudo nano add_sample_data.py
   ```
2. Add faculty and student records as needed
3. Run the script:
   ```bash
   python3 add_sample_data.py
   ```

## System Testing

### 1. UI Improvements Testing
Test the improved UI components:
```bash
cd /path/to/consultease
python scripts/test_ui_improvements.py
```

This script will:
- Test the improved UI transitions
- Test the enhanced consultation panel
- Verify smooth animations and proper user feedback

### 2. Central System Testing
1. Verify RFID scanning works:
   - Scan an RFID card at the login screen
   - Check the logs for detection
2. Test faculty status display:
   - Verify faculty cards show the correct status
3. Test consultation requests:
   - Submit a test consultation request
   - Verify it appears in the database
   - Verify MQTT message is sent
4. Test UI improvements:
   - Verify smooth transitions between screens
   - Test the improved consultation panel
   - Check that the logout button is properly sized

### 3. Faculty Desk Unit Testing
1. Verify connectivity:
   - Check WiFi connection
   - Verify MQTT connection to Raspberry Pi
2. Test BLE detection:
   - Bring the BLE beacon near the unit
   - Verify status changes to "Available"
   - Move the beacon away
   - If not using always-on mode, verify status changes to "Unavailable" after timeout
   - If using always-on mode, verify status remains "Available"
3. Test consultation display:
   - Submit a consultation request from the Central System
   - Verify it appears on the Faculty Desk Unit display
4. Test BLE functionality with the test script:
   ```bash
   python scripts/test_ble_connection.py test
   ```

## Troubleshooting

### Central System Issues
- **RFID reader not detected**: Check USB connection and device permissions
- **Database connection errors**: Verify PostgreSQL is running and credentials are correct
- **UI scaling issues**: Adjust Qt screen scaling or resolution settings
- **On-screen keyboard not appearing**: Run `~/keyboard-show.sh` or press F5 to toggle keyboard

### Faculty Desk Unit Issues
- **WiFi connection problems**: Check network credentials and signal strength
- **Display not working**: Verify SPI connections and TFT_eSPI configuration
- **BLE detection issues**: Check beacon MAC address and RSSI threshold
- **Always showing Available**: This is expected if using the always-on BLE option in config.h

### MQTT Communication Issues
- **Connection failures**: Verify Mosquitto is running and accessible
- **Message not received**: Check topic names and subscription status
- **Delayed updates**: Check network latency and MQTT QoS settings
- **Reconnection issues**: The system now uses exponential backoff for reconnection attempts

### UI Issues
- **Transitions not working**: Some platforms may not support opacity-based transitions
- **Consultation panel not refreshing**: Check auto-refresh timer settings
- **Keyboard not appearing**: Try different keyboard types (squeekboard, onboard)

### For Additional Help
- Check the logs:
  ```bash
  journalctl -u consultease.service
  ```
- Review MQTT messages:
  ```bash
  mosquitto_sub -t "consultease/#" -v
  ```
- Monitor database:
  ```bash
  sudo -u postgres psql -d consultease
  ```

## Touch Interface Setup

ConsultEase is designed to work with a touchscreen interface on the Raspberry Pi. Follow these steps to ensure optimal touch functionality:

### 1. Install On-Screen Keyboard

ConsultEase supports automatic pop-up of an on-screen keyboard when text fields receive focus. To enable this functionality, you need to install one of the supported virtual keyboards:

```bash
# Run the installation script
cd /path/to/consultease
chmod +x scripts/install_squeekboard.sh
./scripts/install_squeekboard.sh
```

The script will attempt to install one of the following keyboards (in order of preference):
- squeekboard (preferred)
- onboard (alternative)
- matchbox-keyboard (fallback)

Note: The system now prefers squeekboard over onboard for better touch input support and integration with the Raspberry Pi environment.

### 2. Enable Fullscreen Mode

To utilize the full touchscreen area, uncomment the following line in `central_system/views/base_window.py`:

```python
# Uncomment this line when deploying on Raspberry Pi
self.showFullScreen()
```

### 3. Adjust Touch Calibration (if needed)

If the touch input is not aligned correctly with the display:

```bash
# Install the calibration tool
sudo apt install -y xinput-calibrator

# Run the calibration
DISPLAY=:0 xinput_calibrator
```

Follow the on-screen instructions to calibrate your touchscreen.

### 4. Testing the Touch Interface

To test the touch interface and keyboard functionality:

1. Start the ConsultEase application
2. Tap on any text input field (like the Admin Login username field)
3. The on-screen keyboard should automatically appear
4. When you tap outside the text field, the keyboard should close

If the keyboard doesn't appear automatically, you can:
- Press F5 to toggle the keyboard visibility
- Run `~/keyboard-show.sh` to manually show the keyboard
- Run `./scripts/fix_keyboard.sh` to troubleshoot keyboard issues

## Performance Optimization

### 1. Database Optimization

For optimal database performance:

1. **PostgreSQL Configuration**:
   ```bash
   sudo nano /etc/postgresql/13/main/postgresql.conf
   ```

   Adjust the following settings based on your Raspberry Pi's resources:
   ```
   shared_buffers = 128MB
   work_mem = 8MB
   maintenance_work_mem = 64MB
   effective_cache_size = 512MB
   ```

2. **Regular Maintenance**:
   ```bash
   # Create a maintenance script
   sudo nano /etc/cron.weekly/consultease-maintenance.sh
   ```

   Add the following content:
   ```bash
   #!/bin/bash
   echo "Running ConsultEase database maintenance..."
   sudo -u postgres psql -d consultease -c "VACUUM ANALYZE;"
   echo "Maintenance complete."
   ```

   Make it executable:
   ```bash
   sudo chmod +x /etc/cron.weekly/consultease-maintenance.sh
   ```

### 2. Application Optimization

1. **Memory Usage**:
   - Monitor memory usage with `htop`
   - If memory usage is high, consider increasing swap space:
     ```bash
     sudo dphys-swapfile swapoff
     sudo nano /etc/dphys-swapfile
     # Set CONF_SWAPSIZE=1024
     sudo dphys-swapfile setup
     sudo dphys-swapfile swapon
     ```

2. **CPU Usage**:
   - The application is optimized to use minimal CPU resources
   - If CPU usage is consistently high, check for background processes

## Recent Improvements

The ConsultEase system has undergone significant improvements to enhance stability, security, and functionality:

### Security Enhancements

1. **Password Security**:
   - Implemented bcrypt password hashing for admin accounts
   - Added fallback mechanism for backward compatibility
   - Improved validation of user input

2. **Database Security**:
   - Enhanced database connection security
   - Added proper error handling for database operations
   - Implemented secure backup and restore functionality

### Functionality Improvements

1. **RFID Service**:
   - Improved callback management to prevent memory leaks
   - Enhanced error handling for different card types
   - Added manual input fallback for RFID scanning

2. **MQTT Communication**:
   - Added exponential backoff for reconnection attempts
   - Improved error handling for network disconnections
   - Enhanced message delivery reliability
   - Added keep-alive mechanism to detect disconnections

3. **BLE Functionality**:
   - Added always-on BLE option for faculty desk unit
   - Improved BLE connection detection and reporting
   - Created test script to verify BLE functionality
   - Enhanced status reporting for more reliable faculty status updates

4. **Admin Dashboard**:
   - Fixed CRUD operations for faculty and student management
   - Added proper resource cleanup to prevent memory leaks
   - Improved UI consistency and user experience

5. **Database Management**:
   - Added backup and restore functionality
   - Implemented proper error handling for database operations
   - Added default data creation for easier setup

### UI Improvements

1. **Theme Consistency**:
   - Set the theme to light as specified in the technical context
   - Improved UI element styling and layout
   - Enhanced touch interface usability

2. **Transitions and Animations**:
   - Added smooth transitions between screens
   - Improved platform detection for transition effects
   - Enhanced fade and slide animations
   - Added tab highlighting for better visual cues

3. **Consultation Panel Improvements**:
   - Enhanced readability and user feedback
   - Added auto-refresh for consultation history
   - Improved tab change animations
   - Better visual feedback for user actions

4. **Dashboard Improvements**:
   - Made the logout button smaller in the dashboard
   - Improved faculty status display
   - Enhanced overall layout and spacing

5. **Error Handling**:
   - Added informative error messages
   - Implemented fallback mechanisms for error recovery
   - Improved logging for debugging

## Maintenance and Updates

### Regular System Updates

It's important to keep the system updated:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update ConsultEase from repository (if applicable)
cd /path/to/consultease
git pull
```

### Database Backups

Regular database backups are essential:

1. **Automated Backups**:
   ```bash
   # Create a backup script
   sudo nano /etc/cron.daily/consultease-backup.sh
   ```

   Add the following content:
   ```bash
   #!/bin/bash
   BACKUP_DIR="/home/pi/consultease_backups"
   mkdir -p $BACKUP_DIR
   DATE=$(date +%Y-%m-%d)
   sudo -u postgres pg_dump consultease > $BACKUP_DIR/consultease_$DATE.sql
   # Keep only the last 7 backups
   ls -t $BACKUP_DIR/consultease_*.sql | tail -n +8 | xargs rm -f
   ```

   Make it executable:
   ```bash
   sudo chmod +x /etc/cron.daily/consultease-backup.sh
   ```

2. **Manual Backups**:
   - Use the admin interface to create manual backups
   - Store backups in a secure location
   - Test restore functionality periodically