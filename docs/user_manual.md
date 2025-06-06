# ConsultEase User Manual

## Introduction

ConsultEase is a comprehensive system designed to streamline student-faculty consultations. It consists of a Central System running on a Raspberry Pi with a touchscreen interface, and Faculty Desk Units installed at each faculty member's desk. The system uses RFID for student authentication, displays real-time faculty availability, and manages consultation requests efficiently.

This manual provides instructions for students, faculty members, and administrators on how to use the ConsultEase system. This version has been updated to reflect recent improvements to the system, including enhanced UI transitions, improved consultation panel, and updated BLE functionality.

## Quick Start Guide

### For Students
1. **Authentication**: Scan your RFID card at the Central System
2. **View Faculty**: Browse available faculty members (green cards indicate availability)
3. **Request Consultation**: Tap "Request Consultation" on a faculty card
4. **Enter Details**: Provide your consultation details and submit

### For Faculty
1. **Status Management**: Keep your BLE beacon with you - your status updates automatically
2. **View Requests**: Check your Desk Unit for incoming student consultation requests
3. **Request Notifications**: The display will flash when new requests arrive
4. **Availability**: Your status is determined by your proximity to your desk

### For Administrators
1. **Admin Access**: Tap "Admin Login" on the login screen
2. **Default Credentials**: Username: `admin`, Password: `admin123` (change after first login)
3. **Faculty Management**: Add/edit faculty details and assign BLE IDs
4. **Student Management**: Register student RFID cards in the system

## Table of Contents

1. [For Students](#for-students)
   - [Authentication](#student-authentication)
   - [Viewing Faculty Availability](#viewing-faculty-availability)
   - [Requesting Consultations](#requesting-consultations)
   - [Checking Request Status](#checking-request-status)

2. [For Faculty](#for-faculty)
   - [Understanding the Faculty Desk Unit](#understanding-the-faculty-desk-unit)
   - [Viewing Consultation Requests](#viewing-consultation-requests)
   - [Status Updates](#faculty-status-updates)
   - [Using the BLE Beacon](#using-the-ble-beacon)

3. [For Administrators](#for-administrators)
   - [Accessing the Admin Interface](#accessing-the-admin-interface)
   - [Managing Faculty](#managing-faculty)
   - [Managing Students](#managing-students)
   - [System Maintenance](#system-maintenance)

4. [Troubleshooting](#troubleshooting)
   - [Common Issues](#common-issues)
   - [Contact Support](#contact-support)

---

## For Students

### Student Authentication

To use the ConsultEase system:

1. Approach the Central System touchscreen display.
2. Scan your RFID student ID card over the reader when prompted.
3. The system will validate your credentials and display the main dashboard.
4. If your card is not recognized, please see an administrator to register your card.

### Viewing Faculty Availability

After authentication, you will see the faculty availability dashboard:

- **Green cards**: Faculty members who are currently available for consultation.
- **Red cards**: Faculty members who are currently unavailable.
- **Search bar**: Use this to search for a specific faculty member by name or department.
- **Filter dropdown**: Use this to filter faculty by availability status or department.

### Requesting Consultations

To request a consultation with a faculty member:

1. Locate the faculty member on the dashboard.
2. Tap the "Request Consultation" button on their card (note: this button is only active if they are available).
3. The improved consultation panel will open with a smooth transition animation.
4. Fill in the consultation details:
   - **Course Code** (optional): Enter the relevant course code if applicable.
   - **Consultation Details**: Describe the purpose of your consultation.
5. Tap "Submit Request" to send your request.
6. You will receive a confirmation message when your request is successfully submitted.
7. The system will automatically switch to the consultation history tab with a smooth transition.

### Checking Request Status

The system will notify the faculty member of your request. You will be notified when:

- Your request is submitted successfully.
- The faculty member accepts your request.
- The consultation is marked as completed.

To check the status of your previous requests:
1. Navigate to the consultation panel
2. Select the "Consultation History" tab
3. View a list of all your previous consultation requests
4. The history automatically refreshes periodically to show the latest status
5. You can manually refresh by switching tabs or clicking the refresh button
6. For pending consultations, you can cancel them by clicking the "Cancel" button

---

## For Faculty

### Understanding the Faculty Desk Unit

Each faculty member has a Faculty Desk Unit installed at their desk. This unit:

- Displays your availability status
- Shows pending consultation requests
- Automatically detects your presence via BLE beacon

### Viewing Consultation Requests

When a student submits a consultation request:

1. The display will flash briefly to notify you of the new request.
2. The request will appear on your Faculty Desk Unit display with:
   - Student name
   - Course code (if provided)
   - Consultation details
   - Request time

Requests are displayed in chronological order, with the most recent at the top.

### Faculty Status Updates

Your status is automatically updated based on your presence:

- **Available**: When the BLE beacon is detected near your desk
- **Unavailable**: When the BLE beacon is not detected for more than 15 seconds

Alternatively, if your Faculty Desk Unit is configured with the always-on BLE option, your status will always show as "Available" regardless of the BLE beacon's presence. This is useful for faculty members who want to be always available for consultations.

Your status is displayed both on your Faculty Desk Unit and on the Central System for students to see.

### Using the BLE Beacon

Each faculty member is provided with a BLE beacon:

1. The beacon should be kept with you at all times during working hours.
2. Ensure the beacon has sufficient battery power (check the LED indicator).
3. The beacon automatically broadcasts your presence to the Faculty Desk Unit.
4. No manual action is required to update your status.

### BLE Beacon Maintenance

To ensure reliable operation of your BLE beacon:

1. **Charging**: Recharge your beacon when the LED flashes rapidly (indicating low battery).
   - Connect the beacon to a USB charger using the provided cable
   - A solid red LED indicates charging in progress
   - A solid green LED indicates charging complete

2. **Battery Life**: A fully charged beacon typically lasts 2-3 weeks with normal use.

3. **Troubleshooting**:
   - If the beacon is not being detected, check that it is powered on (LED blinks occasionally)
   - If the LED does not light up at all, the battery may be completely discharged
   - If problems persist after charging, contact IT support for a replacement

4. **Care and Handling**:
   - Keep the beacon dry and avoid exposure to extreme temperatures
   - The beacon contains a lithium battery - do not crush, puncture, or dispose of in fire
   - If the beacon is damaged, stop using it and contact IT support

---

## For Administrators

### Accessing the Admin Interface

To access the admin interface:

1. On the Central System login screen, tap "Admin Login."
2. Enter your administrator username and password.
3. If this is your first login, use the default credentials:
   - Username: `admin`
   - Password: `admin123`
4. You will be prompted to change your password on first login.

### Managing Faculty

In the admin interface, you can manage faculty members:

1. To view all faculty, select "Faculty Management" from the admin menu.
2. **Add a new faculty member**:
   - Click "Add Faculty"
   - Fill in the required information:
     - Name
     - Department
     - Email
     - BLE ID (from the faculty member's BLE beacon)
   - Click "Save"

3. **Edit a faculty member**:
   - Locate the faculty member in the list
   - Click "Edit" on their row
   - Modify the information as needed
   - Click "Save"

4. **Delete a faculty member**:
   - Locate the faculty member in the list
   - Click "Delete" on their row
   - Confirm the deletion

### Managing Students

In the admin interface, you can also manage students:

1. To view all students, select "Student Management" from the admin menu.
2. **Add a new student**:
   - Click "Add Student"
   - Fill in the required information:
     - Name
     - Department
     - RFID UID (scan their RFID card when prompted)
   - Click "Save"

3. **Edit a student**:
   - Locate the student in the list
   - Click "Edit" on their row
   - Modify the information as needed
   - Click "Save"

4. **Delete a student**:
   - Locate the student in the list
   - Click "Delete" on their row
   - Confirm the deletion

### System Maintenance

As an administrator, you may need to perform system maintenance:

1. **Backup Database**:
   - Select "System Maintenance" from the admin menu
   - Click "Backup Database"
   - Choose a location to save the backup file
   - The system supports both PostgreSQL and SQLite database formats
   - For PostgreSQL (default), the backup will be saved as a .sql file
   - Regular backups are recommended to prevent data loss

2. **Restore Database**:
   - Select "System Maintenance" from the admin menu
   - Click "Restore Database"
   - Select a previously created backup file
   - Confirm the restore operation (this will overwrite the current database)
   - The system will automatically restart after the restore is complete
   - Note: Always create a backup before performing a restore

3. **System Logs**:
   - Select "System Maintenance" from the admin menu
   - Click "View Logs" to see system activity
   - Use filters to narrow down the log entries
   - You can clear logs if they become too large
   - Log files are also stored in the application directory for advanced troubleshooting

4. **System Settings**:
   - Select "System Settings" from the admin menu
   - Configure MQTT settings, database connection, and other parameters
   - Changes to system settings require a restart to take effect
   - Default settings are optimized for most deployments

---

## Troubleshooting

### Common Issues

#### RFID Card Not Recognized
- Ensure you are holding the card close to the reader
- Try scanning the card again, more slowly
- Try using the manual RFID input option if available
- If using a 13.56 MHz reader, ensure it's configured correctly
- If the problem persists, see an administrator to verify your card registration

#### Faculty Status Not Updating
- Check if the BLE beacon is functioning (LED indicator)
- Ensure the beacon has sufficient battery power
- Verify the BLE ID is correctly registered in the system
- Check if the ESP32 is properly connected to the network
- Restart the Faculty Desk Unit if necessary
- Check the MQTT broker status on the server
- If using the always-on BLE option, verify it's properly configured in the Faculty Desk Unit's config.h file
- Run the BLE test script to verify functionality: `python scripts/test_ble_connection.py test`

#### Central System Unresponsive
- Wait a few moments for the system to respond
- If the touchscreen remains unresponsive, notify an administrator
- Press F11 to toggle fullscreen mode if the display is cut off
- Press F5 to toggle the on-screen keyboard if needed
- The system may require a restart
- Check system logs for any error messages
- If transitions between screens are not working properly, try restarting the application
- If the consultation panel is not refreshing, check the auto-refresh timer settings

#### Faculty Desk Unit Display Issues
- Check the power connection
- Verify WiFi connectivity (indicator on the screen)
- Restart the unit if necessary
- Check if the MQTT connection is established
- Verify the ESP32 is properly configured

#### Database Issues
- If you can't access student or faculty data, the database may be unavailable
- Administrators should check if PostgreSQL is running
- Verify the database credentials in the environment variables
- Try restoring from a backup if the database is corrupted
- Regular database backups are recommended to prevent data loss

#### Admin Dashboard Issues
- If CRUD operations are not working, check database permissions
- Ensure you're logged in with an admin account
- Check the system logs for any error messages
- Try clearing browser cache if using a web interface
- Restart the application if the dashboard is unresponsive

### Contact Support

If you encounter issues that cannot be resolved using this manual:

- **For students**: Contact your department administrator
- **For faculty**: Contact the IT support department
- **For administrators**: Contact the system vendor

Technical support contact:
- Email: support@consultease.com
- Phone: (123) 456-7890

---

## Technical Appendix

### System Architecture

ConsultEase consists of two main hardware components:

1. **Central System** (Raspberry Pi)
   - Hardware: Raspberry Pi 4 (Bookworm 64-bit), 10.1-inch touchscreen, USB RFID reader
   - Software: Python 3.9+, PyQt5, PostgreSQL, Paho MQTT
   - Communication: MQTT broker for messaging between components

2. **Faculty Desk Unit** (ESP32)
   - Hardware: ESP32 microcontroller, 2.4-inch TFT SPI Screen (ST7789)
   - Software: Arduino framework, TFT_eSPI, NimBLE-Arduino, PubSubClient
   - Communication: BLE for presence detection, MQTT for data exchange

### Technical Specifications

#### Central System Requirements
- **Operating System**: Raspberry Pi OS (Bookworm 64-bit)
- **CPU**: Quad-core Cortex-A72 (ARM v8) 64-bit SoC @ 1.5GHz or better
- **Memory**: 2GB RAM minimum (4GB recommended)
- **Storage**: 16GB microSD card minimum
- **Display**: 10.1-inch touchscreen (1024x600 resolution)
- **Network**: Wi-Fi or Ethernet connection
- **Ports**: USB port for RFID reader

#### Faculty Desk Unit Requirements
- **Microcontroller**: ESP32 dual-core processor
- **Display**: 2.4-inch TFT SPI Screen (ST7789)
- **Network**: Wi-Fi connection to local network
- **Power**: USB or wall adapter (5V)

#### Network Requirements
- Local Wi-Fi network with DHCP
- Network ports open for MQTT communication (default: 1883)
- All devices must be on the same local network

### Database Schema

The system uses a PostgreSQL database with the following main tables:

- **faculty**: Stores faculty information and status
- **students**: Stores student information and RFID identifiers
- **consultations**: Tracks consultation requests and their status
- **admins**: Manages administrator accounts

### Software Dependencies

The Central System requires the following software packages:
- Python 3.9+
- PyQt5
- PostgreSQL (primary database)
- SQLite (supported for development)
- Paho MQTT client
- SQLAlchemy
- evdev (for RFID reader)
- bcrypt (for secure password hashing)
- squeekboard (preferred on-screen keyboard)

The Faculty Desk Unit requires the following libraries:
- TFT_eSPI by Bodmer
- PubSubClient by Nick O'Leary
- ArduinoJson by Benoit Blanchon
- NimBLE-Arduino by h2zero

### Security Features

The ConsultEase system includes several security features:

1. **Password Security**:
   - Admin passwords are hashed using bcrypt, a secure password-hashing function
   - Password complexity requirements are enforced
   - Failed login attempts are logged

2. **Database Security**:
   - Database connections use secure authentication
   - Sensitive data is properly handled
   - Regular backups protect against data loss

3. **Input Validation**:
   - All user inputs are validated to prevent injection attacks
   - RFID data is sanitized before processing
   - Form submissions include CSRF protection

### Backup and Recovery

To backup the system:
1. Go to the Admin interface
2. Select "System Maintenance"
3. Click "Backup Database"
4. Choose a location to save the backup file
5. The system will create a backup of the PostgreSQL database

To restore from a backup:
1. Go to the Admin interface
2. Select "System Maintenance"
3. Click "Restore Database"
4. Select the backup file to restore
5. Confirm the restore operation
6. The system will restart automatically after the restore is complete

### Error Handling

The system includes comprehensive error handling:

1. **User-Friendly Messages**:
   - Clear error messages are displayed to users
   - Technical details are logged for administrators
   - Suggestions for resolution are provided when possible

2. **Automatic Recovery**:
   - The system attempts to recover from common errors
   - Services automatically reconnect after network interruptions
   - Database connections are retried with exponential backoff

### Performance Considerations

For optimal performance:
- Limit the number of simultaneous users to 50
- Perform database maintenance weekly
- Restart the Central System once per week
- Check BLE beacon batteries monthly

---

© 2024 ConsultEase System - All Rights Reserved