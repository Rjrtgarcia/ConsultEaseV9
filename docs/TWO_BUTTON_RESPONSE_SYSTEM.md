# ConsultEase Two-Button Response System

## Overview

The ConsultEase Two-Button Response System provides faculty members with a simple and intuitive way to respond to student consultation requests using physical buttons on their ESP32 faculty desk units. This system enhances the user experience by allowing immediate responses without complex interactions.

## Features

### Hardware Interface
- **Button 1 (Blue)**: Accept/Acknowledge consultation requests
- **Button 2 (Red)**: Mark as busy/unavailable for consultation requests
- **Physical buttons**: GPIO pins 15 (Blue) and 4 (Red) on ESP32
- **Debouncing**: 50ms debounce delay for reliable button detection
- **Visual feedback**: Clear button prompts on 2.4" TFT display

### Software Features
- **Real-time responses**: Immediate MQTT communication to central system
- **Presence detection**: Only allows responses when faculty is physically present (BLE beacon detected)
- **Offline queuing**: Responses are queued when network is unavailable
- **Status tracking**: Database tracks consultation status with timestamps
- **Student notifications**: Real-time notifications to students about faculty responses
- **Timeout handling**: Auto-clear consultation requests after 30 seconds

## System Architecture

### Database Schema

The consultation status enum includes:
- `PENDING`: Initial status when consultation is requested
- `ACCEPTED`: Faculty has acknowledged and accepted the request
- `BUSY`: Faculty is currently busy and cannot take the request
- `COMPLETED`: Consultation has been completed
- `CANCELLED`: Request has been cancelled

New database field:
- `busy_at`: Timestamp when faculty marked the consultation as busy

### MQTT Communication

#### Topics Used
- **Requests**: `consultease/faculty/{faculty_id}/requests` (JSON format)
- **Messages**: `consultease/faculty/{faculty_id}/messages` (Plain text for ESP32)
- **Responses**: `consultease/faculty/{faculty_id}/responses` (Faculty responses)
- **Notifications**: `consultease/system/notifications` (System-wide notifications)

#### Response Message Format
```json
{
  "faculty_id": 1,
  "faculty_name": "Dr. Smith",
  "response_type": "ACKNOWLEDGE|BUSY",
  "message_id": "consultation_id",
  "original_message": "Student consultation request text",
  "timestamp": "1234567890",
  "faculty_present": true,
  "response_method": "physical_button",
  "status": "Human-readable status message"
}
```

## Hardware Setup

### ESP32 Faculty Desk Unit

#### Pin Configuration
```cpp
#define BUTTON_A_PIN 15               // Blue button (Acknowledge)
#define BUTTON_B_PIN 4                // Red button (Busy)
#define BUTTON_DEBOUNCE_DELAY 50      // Debounce delay in milliseconds
```

#### Physical Setup
1. Connect blue button to GPIO pin 15 with pull-up resistor
2. Connect red button to GPIO pin 4 with pull-up resistor
3. Ensure proper grounding and power connections
4. Test button functionality before deployment

### Display Interface

The ESP32 shows enhanced consultation request displays with:
- **Header**: "CONSULTATION REQUEST" with consultation ID
- **Student info**: Parsed student name and ID
- **Request details**: Formatted consultation message
- **Button prompts**: Clear instructions for blue (ACCEPT) and red (BUSY) buttons
- **Timeout indicator**: Shows auto-clear countdown

## Software Implementation

### Central System Components

#### 1. Database Model Updates
```python
# Updated ConsultationStatus enum
class ConsultationStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    BUSY = "busy"           # New status
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# New database field
busy_at = Column(DateTime, nullable=True)
```

#### 2. Faculty Response Controller
- Handles incoming MQTT responses from faculty desk units
- Maps response types to database status updates
- Validates faculty presence and consultation ownership
- Triggers real-time notifications to students

#### 3. Student Dashboard Integration
- Real-time status updates via callback registration
- Visual notifications for consultation status changes
- Automatic refresh of consultation history
- Color-coded status indicators

### ESP32 Firmware Features

#### 1. Enhanced Message Display
```cpp
void displayIncomingMessage(String message) {
    // Parse student information from message
    // Display formatted consultation request
    // Show clear button prompts
    // Add timeout indicator
}
```

#### 2. Button Response Handling
```cpp
void handleAcknowledgeButton() {
    // Check faculty presence via BLE
    // Validate consultation ID
    // Send ACKNOWLEDGE response via MQTT
    // Show confirmation feedback
}

void handleBusyButton() {
    // Check faculty presence via BLE
    // Validate consultation ID  
    // Send BUSY response via MQTT
    // Show confirmation feedback
}
```

#### 3. Presence Integration
- Buttons only work when faculty BLE beacon is detected
- Grace period handling for temporary disconnections
- Clear error messages when faculty not present

## User Experience

### For Faculty Members

1. **Receiving Requests**:
   - Consultation requests appear automatically on desk unit display
   - Clear student information and request details shown
   - Visual button prompts guide response actions

2. **Responding to Requests**:
   - Press **BLUE button** to accept/acknowledge request
   - Press **RED button** to mark as busy/unavailable
   - Immediate visual confirmation of response sent
   - Automatic clearing of request after response

3. **Presence Requirements**:
   - Must be physically present (BLE beacon detected) to respond
   - Clear error messages if trying to respond while away
   - Grace period handling for brief disconnections

### For Students

1. **Real-time Notifications**:
   - Immediate notifications when faculty responds
   - Different notification types for different responses:
     - ✅ **Accepted**: Green success notification
     - ⚠️ **Busy**: Orange warning notification
     - ❌ **Declined**: Red error notification

2. **Status Tracking**:
   - Consultation history automatically updates
   - Color-coded status indicators in history panel
   - Timestamps for all status changes

## Testing

### Test Script Usage

Use the provided test script to verify functionality:

```bash
# Interactive testing
python scripts/test_two_button_response.py --faculty-id 1 --student-id 1

# Single test message
python scripts/test_two_button_response.py --single-test --message "Test consultation"

# Custom broker settings
python scripts/test_two_button_response.py --broker 192.168.1.100 --port 1883
```

### Test Scenarios

1. **Basic Functionality**:
   - Send consultation request
   - Press blue button → verify ACKNOWLEDGE response
   - Press red button → verify BUSY response

2. **Presence Detection**:
   - Test responses with faculty present
   - Test responses with faculty away (should fail)
   - Test grace period handling

3. **Network Resilience**:
   - Test offline response queuing
   - Verify responses sent when network restored
   - Test MQTT reconnection handling

4. **Database Integration**:
   - Verify status updates in database
   - Check timestamp accuracy
   - Validate consultation history updates

## Troubleshooting

### Common Issues

#### 1. Buttons Not Responding
- **Check**: Faculty presence detection (BLE beacon)
- **Check**: Button wiring and GPIO pin configuration
- **Check**: MQTT connection status
- **Solution**: Verify BLE beacon is active and in range

#### 2. Responses Not Reaching Central System
- **Check**: MQTT broker connectivity
- **Check**: Topic subscription in central system
- **Check**: Network connectivity
- **Solution**: Restart MQTT services, check network configuration

#### 3. Database Status Not Updating
- **Check**: Faculty Response Controller is running
- **Check**: Database connection
- **Check**: Consultation ID matching
- **Solution**: Restart central system services

#### 4. Student Not Receiving Notifications
- **Check**: Real-time update registration
- **Check**: Student dashboard is active
- **Check**: Notification system configuration
- **Solution**: Restart student dashboard application

### Debug Information

#### ESP32 Debug Output
```
📨 Message received: CID:123 From:John Doe (SID:456): Help with assignment
🔑 Parsed Consultation ID (CID): 123
📱 Enhanced consultation request displayed. ID: 123
📤 Sending ACKNOWLEDGE response to central terminal
✅ ACKNOWLEDGE response sent successfully
```

#### Central System Logs
```
INFO - Received ACKNOWLEDGE response from faculty 1 (Dr. Smith) for message 123
INFO - Successfully updated consultation 123 to status accepted via ConsultationController
INFO - Processed real-time consultation update: ACKNOWLEDGE from Dr. Smith
```

## Configuration

### ESP32 Configuration (config.h)
```cpp
// Button pins
#define BUTTON_A_PIN 15               // Blue button (Acknowledge)
#define BUTTON_B_PIN 4                // Red button (Busy)
#define BUTTON_DEBOUNCE_DELAY 50      // Debounce delay

// Message timeout
#define MESSAGE_DISPLAY_TIMEOUT 30000 // 30 seconds

// MQTT topics
#define MQTT_TOPIC_RESPONSES "consultease/faculty/1/responses"
```

### Central System Configuration
```python
# Database migration (automatic)
migrate_database_for_busy_status()

# Faculty Response Controller (automatic startup)
faculty_response_controller = get_faculty_response_controller()
faculty_response_controller.start()
```

## Security Considerations

1. **Presence Validation**: Responses only accepted when faculty physically present
2. **Message Validation**: Consultation ID verification prevents unauthorized responses
3. **Network Security**: MQTT communication uses QoS levels for reliability
4. **Data Integrity**: Database transactions ensure consistent status updates

## Future Enhancements

1. **Additional Response Types**: Could add "LATER", "REDIRECT" options
2. **Voice Feedback**: Audio confirmation of button presses
3. **Mobile Integration**: Push notifications to faculty mobile devices
4. **Analytics**: Response time tracking and faculty availability statistics
5. **Customizable Timeouts**: Per-faculty timeout settings
6. **Multi-language Support**: Localized button prompts and messages

## API Reference

### Faculty Response Controller Methods

```python
def handle_faculty_response(topic: str, data: Any)
    """Handle faculty response from MQTT"""

def _process_faculty_response(response_data: Dict[str, Any]) -> bool
    """Process and validate faculty response"""

def get_response_statistics() -> Dict[str, Any]
    """Get faculty response statistics"""
```

### ESP32 Functions

```cpp
void handleAcknowledgeButton()
    // Handle blue button press for acknowledgment

void handleBusyButton()  
    // Handle red button press for busy status

void displayIncomingMessage(String message)
    // Display consultation request with enhanced formatting

bool publishWithQueue(const char* topic, const char* payload, bool isResponse)
    // Publish MQTT message with offline queuing support
```

This comprehensive two-button response system provides a robust, user-friendly interface for faculty-student consultation management while maintaining system reliability and security. 