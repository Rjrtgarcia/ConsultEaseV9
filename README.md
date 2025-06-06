# ConsultEase

A comprehensive system for enhanced student-faculty interaction, featuring RFID-based authentication, real-time faculty availability, and streamlined consultation requests.

## Components

### Central System (Raspberry Pi)
- PyQt5 user interface for student interaction
- RFID-based authentication
- Real-time faculty availability display
- Consultation request management with improved UI
- Secure admin interface with automatic login account management
- Touch-optimized UI with on-screen keyboard support (squeekboard preferred)
- Smooth UI transitions and animations
- Integrated admin account creation and repair
- Real-time system monitoring and health checks
- Comprehensive audit logging for security compliance

### Faculty Desk Unit (ESP32)
- 2.4" TFT Display for consultation requests
- BLE-based presence detection (configurable always-available mode)
- MQTT communication with Central System
- Real-time status updates
- Improved reliability and error handling

## Requirements

### Central System
- Raspberry Pi 4 (Bookworm 64-bit)
- 10.1-inch touchscreen (1024x600 resolution)
- USB RFID IC Reader
- Python 3.9+
- PostgreSQL database

### Faculty Desk Unit
- ESP32 microcontroller
- 2.4-inch TFT SPI Screen (ST7789)
- Arduino IDE 2.0+

## Installation

### Central System

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL database:
```bash
# Create database and user
sudo -u postgres psql -c "CREATE DATABASE consultease;"
sudo -u postgres psql -c "CREATE USER piuser WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE consultease TO piuser;"
```

3. Install touchscreen utilities (for Raspberry Pi):
```bash
sudo chmod +x scripts/keyboard_setup.sh
sudo ./scripts/keyboard_setup.sh
```

Note: The system now uses a unified keyboard setup script that supports both squeekboard and onboard, with automatic fallback. Squeekboard is preferred for mobile-friendly environments, while onboard is used as a fallback. You can also install squeekboard directly:

```bash
sudo chmod +x scripts/install_squeekboard.sh
./scripts/install_squeekboard.sh
```

4. Calibrate the touchscreen (if needed):
```bash
sudo chmod +x scripts/calibrate_touch.sh
sudo ./scripts/calibrate_touch.sh
```

5. Enable fullscreen mode (for deployment):
```bash
python scripts/enable_fullscreen.py
```

6. Run the application:
```bash
python central_system/main.py
```

## Admin Access

ConsultEase includes an enhanced admin account management system that ensures users can always gain admin access through multiple fallback mechanisms.

### Enhanced Admin Account Management

The system provides **multiple layers** of admin account management:

1. **Automatic Database Creation** - Creates default admin during database initialization
2. **First-Time Setup Dialog** - User-friendly account creation if no accounts exist
3. **Manual Login** - Traditional login with enhanced error handling
4. **Emergency Repair** - Automatic repair of corrupted accounts

### First-Time Setup Experience

When no admin accounts exist, the system automatically displays a **user-friendly setup dialog**:

#### Features:
- 🖥️ **Touch-Optimized Interface** - Designed for Raspberry Pi touchscreen
- 🔒 **Real-Time Password Validation** - Visual feedback on password requirements
- ✅ **Instant Verification** - Username uniqueness and strength checking
- 🎯 **Auto-Login** - Automatic login after successful account creation
- 📱 **On-Screen Keyboard** - Automatic keyboard display for input fields

#### Password Requirements:
- ✅ At least 8 characters long
- ✅ Contains uppercase letters (A-Z)
- ✅ Contains lowercase letters (a-z)
- ✅ Contains numbers (0-9)
- ✅ Contains special characters (!@#$%^&*)
- ✅ Passwords must match

### Accessing the Admin Dashboard

#### Option 1: First-Time Setup (No Admin Accounts)
1. **Start the application**
2. **Click "Admin Login"** button
3. **Follow the first-time setup dialog** (appears automatically)
4. **Create your admin account** with a secure password
5. **Automatically login** to the admin dashboard

#### Option 2: Existing Admin Account
1. **Start the application**
2. **Click "Admin Login"** button
3. **Enter your credentials**
4. **Access the admin dashboard**

#### Option 3: Default Admin (Fallback)
If automatic systems create a default admin:
```
Username: admin
Password: TempPass123!
```
**Note:** This password must be changed on first login for security.

### Admin Account Features

#### Multi-Layer Security:
- ✅ **Strong Password Requirements** - Enforced complexity rules
- ✅ **Secure Password Storage** - bcrypt hashing with salt
- ✅ **Account Validation** - Real-time username and password checking
- ✅ **Audit Logging** - Complete audit trail of all admin operations

#### User Experience:
- ✅ **Touch-Friendly Interface** - Optimized for touchscreen devices
- ✅ **Clear Visual Feedback** - Real-time validation indicators
- ✅ **Intuitive Setup Process** - Step-by-step guidance
- ✅ **Error Recovery** - Multiple fallback mechanisms

#### System Reliability:
- ✅ **Automatic Creation** - Admin accounts created automatically when needed
- ✅ **Self-Repair** - System fixes broken admin accounts during startup
- ✅ **Multiple Fallbacks** - Several methods ensure admin access is always possible
- ✅ **Zero Configuration** - Works out of the box without manual setup

### Testing the System

You can test the admin account management system:

```bash
# Run the test script
python test_admin_account_management.py
```

This will verify:
- Admin account creation and authentication
- Password validation
- First-time setup detection
- UI component functionality

The enhanced system ensures **100% reliable admin access** through multiple redundant mechanisms!

### Faculty Desk Unit

1. Install the Arduino IDE and required libraries:
   - TFT_eSPI
   - NimBLE-Arduino
   - PubSubClient
   - ArduinoJson

2. Configure TFT_eSPI for your display

3. Update the configuration in `faculty_desk_unit/config.h`:
   - Set the faculty ID and name
   - Configure WiFi credentials
   - Set MQTT broker IP address
   - Configure BLE settings (including always-on option)

4. Upload the sketch to your ESP32

5. Test the faculty desk unit using the unified test utility:
   ```bash
   # Test MQTT communication with faculty desk unit
   python scripts/test_utility.py mqtt-test --broker 192.168.1.100

   # Send a test message to faculty desk unit
   python scripts/test_utility.py faculty-desk --faculty-id 3 --message "Test message"

   # Simulate a BLE beacon for faculty presence detection
   python scripts/test_utility.py ble-beacon --faculty-id 2

   # Monitor all MQTT messages on the broker
   python scripts/test_utility.py monitor --broker 192.168.1.100
   ```

## Development

### Project Structure
```
consultease/
├── central_system/           # Raspberry Pi application
│   ├── models/               # Database models
│   ├── views/                # PyQt UI components
│   ├── controllers/          # Application logic
│   ├── services/             # External services (MQTT, RFID)
│   ├── resources/            # UI resources (icons, stylesheets)
│   └── utils/                # Utility functions
├── faculty_desk_unit/        # ESP32 firmware
│   ├── faculty_desk_unit.ino # Main firmware file
│   ├── config.h              # Configuration file
│   └── ble_beacon/           # BLE beacon firmware
├── scripts/                  # Utility scripts
│   ├── keyboard_setup.sh     # Unified on-screen keyboard setup
│   ├── calibrate_touch.sh    # Touchscreen calibration utility
│   ├── enable_fullscreen.py  # Enable fullscreen for deployment
│   ├── install_squeekboard.sh # Install and configure squeekboard
│   ├── test_utility.py       # Unified testing utility for all components
│   └── test_ui_improvements.py # Test UI improvements
├── tests/                    # Test suite
└── docs/                     # Documentation
    ├── deployment_guide.md   # Comprehensive deployment guide
    ├── quick_start_guide.md  # Quick start instructions
    ├── user_manual.md        # User manual
    ├── keyboard_setup.md     # On-screen keyboard setup guide
    └── recent_improvements.md # Documentation of recent changes
```

## Touchscreen Features

ConsultEase includes several features to enhance usability on touchscreen devices:

- **Auto-popup keyboard**: Virtual keyboard (squeekboard or onboard) appears automatically when text fields receive focus
- **Fullscreen mode**: Optimized for touchscreen deployment with full screen utilization
- **Touch calibration**: Tools to ensure accurate touch input recognition
- **Touch-friendly UI**: Larger buttons and input elements optimized for touch interaction
- **Smooth transitions**: Enhanced UI transitions between screens for better user experience
- **Improved consultation panel**: Better readability and user feedback in the consultation interface

See the user manual, deployment guide, and keyboard setup guide in the `docs/` directory for detailed instructions on touchscreen setup and optimization.

## RFID Troubleshooting

If you're experiencing issues with the RFID scanner, the following tools can help:

### Automated RFID Fix (Raspberry Pi)

Run the following command to automatically detect and configure your RFID reader:

```bash
sudo ./scripts/fix_rfid.sh
```

This script will:
1. Detect connected USB devices
2. List potential RFID readers
3. Test the selected device
4. Configure proper permissions
5. Create udev rules for persistent configuration

### Manual RFID Debugging

For more granular control, use the debug_rfid.py tool:

```bash
# List all input devices and identify potential RFID readers
python scripts/debug_rfid.py list

# Monitor a specific input device to see raw events
python scripts/debug_rfid.py monitor <device_number>

# Test RFID reading functionality with a specific device
python scripts/debug_rfid.py test <device_number>
```

### Common RFID Issues

1. **Permission denied errors**: Run `sudo chmod -R a+r /dev/input/` to ensure proper permissions
2. **Device not detected**: Ensure it's properly connected and check `lsusb` output
3. **Wrong device selected**: Use the debug tool to identify the correct device
4. **Thread-related crashes**: The latest update includes thread-safe implementations to prevent crashes

For the target RFID reader with VID:ffff PID:0035, the system should auto-detect it during startup.

## License
[MIT](LICENSE)