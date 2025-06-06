#!/bin/bash
#
# MQTT Broker Permission Fix Script for ConsultEase
# Fixes the asymmetric permissions issue where ESP32 can subscribe but cannot publish
#
# This script:
# 1. Checks current Mosquitto configuration
# 2. Creates proper user accounts and permissions  
# 3. Sets up ACL for faculty desk units
# 4. Tests the configuration
# 5. Restarts services
#
# Usage: sudo bash scripts/fix_mqtt_permissions.sh
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MQTT_USER="faculty_desk"
MQTT_PASSWORD="desk_password"
CENTRAL_USER="central_system" 
CENTRAL_PASSWORD="central_secure_password"
CONFIG_DIR="/etc/mosquitto"
CONF_FILE="$CONFIG_DIR/mosquitto.conf"
ACL_FILE="$CONFIG_DIR/acl.conf"
PASSWD_FILE="$CONFIG_DIR/passwd"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_status "🚀 Starting MQTT Broker Permission Fix..."
echo "================================================================"

# Step 1: Check if Mosquitto is installed
print_status "📦 Checking Mosquitto installation..."
if ! command -v mosquitto &> /dev/null; then
    print_warning "Mosquitto not found. Installing..."
    apt-get update
    apt-get install -y mosquitto mosquitto-clients
    print_success "Mosquitto installed successfully"
else
    print_success "Mosquitto is already installed"
fi

# Step 2: Stop Mosquitto service
print_status "🛑 Stopping Mosquitto service..."
systemctl stop mosquitto
print_success "Mosquitto service stopped"

# Step 3: Backup existing configuration
print_status "💾 Backing up existing configuration..."
timestamp=$(date +%Y%m%d_%H%M%S)
if [ -f "$CONF_FILE" ]; then
    cp "$CONF_FILE" "$CONF_FILE.backup_$timestamp"
    print_success "Configuration backed up to $CONF_FILE.backup_$timestamp"
fi
if [ -f "$ACL_FILE" ]; then
    cp "$ACL_FILE" "$ACL_FILE.backup_$timestamp"
    print_success "ACL file backed up to $ACL_FILE.backup_$timestamp"
fi

# Step 4: Create mosquitto configuration
print_status "📝 Creating Mosquitto configuration..."
cat > "$CONF_FILE" << EOF
# ConsultEase MQTT Broker Configuration
# Generated on $(date)

# Basic settings
pid_file /var/run/mosquitto.pid
persistence true
persistence_location /var/lib/mosquitto/
log_dest file /var/log/mosquitto/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information

# Network settings  
port 1883
max_connections -1
allow_anonymous false

# Authentication
password_file $PASSWD_FILE

# Access Control List
acl_file $ACL_FILE

# Connection settings
connection_messages true
log_timestamp true
EOF

print_success "Mosquitto configuration created"

# Step 5: Create ACL file with proper permissions
print_status "🔐 Creating Access Control List..."
cat > "$ACL_FILE" << EOF
# ConsultEase MQTT Access Control List
# Generated on $(date)

# Central System - Full access to all topics
user $CENTRAL_USER
topic readwrite consultease/#
topic readwrite faculty/#
topic readwrite student/#
topic readwrite system/#
topic readwrite test/#

# Faculty Desk Units - Specific permissions for faculty operations
user $MQTT_USER
# Read permissions (subscribe)
topic read consultease/faculty/+/messages
topic read consultease/faculty/+/commands
topic read consultease/system/+
topic read test/+

# Write permissions (publish) - THIS IS THE KEY FIX
topic write consultease/faculty/+/responses
topic write consultease/faculty/+/status
topic write consultease/faculty/+/heartbeat
topic write faculty/+/responses
topic write faculty/+/status
topic write test/+

# Legacy topic support
topic read faculty/+/messages
topic write faculty/+/responses
topic write faculty/+/status

# Pattern examples for reference:
# consultease/faculty/1/messages    <- ESP32 subscribes (READ)
# consultease/faculty/1/responses   <- ESP32 publishes (WRITE) 
# consultease/faculty/1/status      <- ESP32 publishes (WRITE)
# consultease/faculty/1/heartbeat   <- ESP32 publishes (WRITE)
EOF

print_success "ACL file created with proper permissions"

# Step 6: Create user accounts
print_status "👤 Creating MQTT user accounts..."

# Remove existing password file to start fresh
if [ -f "$PASSWD_FILE" ]; then
    rm "$PASSWD_FILE"
fi

# Create central system user
echo "Creating central system user..."
mosquitto_passwd -c "$PASSWD_FILE" "$CENTRAL_USER" << EOF
$CENTRAL_PASSWORD
$CENTRAL_PASSWORD
EOF

# Create faculty desk user
echo "Creating faculty desk user..."
mosquitto_passwd "$PASSWD_FILE" "$MQTT_USER" << EOF
$MQTT_PASSWORD
$MQTT_PASSWORD
EOF

print_success "User accounts created successfully"

# Step 7: Set proper file permissions
print_status "🔒 Setting file permissions..."
chown mosquitto:mosquitto "$PASSWD_FILE"
chown mosquitto:mosquitto "$ACL_FILE"
chown mosquitto:mosquitto "$CONF_FILE"
chmod 640 "$PASSWD_FILE"
chmod 644 "$ACL_FILE"
chmod 644 "$CONF_FILE"
print_success "File permissions set correctly"

# Step 8: Start Mosquitto service
print_status "🔄 Starting Mosquitto service..."
systemctl start mosquitto
systemctl enable mosquitto
sleep 2

# Check if service is running
if systemctl is-active --quiet mosquitto; then
    print_success "Mosquitto service started successfully"
else
    print_error "Failed to start Mosquitto service"
    print_status "Checking logs..."
    journalctl -u mosquitto --no-pager -n 10
    exit 1
fi

# Step 9: Test the configuration
print_status "🧪 Testing MQTT broker configuration..."

# Test 1: Test central system login
print_status "Testing central system authentication..."
timeout 5 mosquitto_sub -h localhost -u "$CENTRAL_USER" -P "$CENTRAL_PASSWORD" -t "test/central" -C 1 &
SUB_PID=$!
sleep 1
mosquitto_pub -h localhost -u "$CENTRAL_USER" -P "$CENTRAL_PASSWORD" -t "test/central" -m "central_test_$(date +%s)"
wait $SUB_PID 2>/dev/null && print_success "Central system authentication working" || print_warning "Central system test failed"

# Test 2: Test faculty desk login  
print_status "Testing faculty desk authentication..."
timeout 5 mosquitto_sub -h localhost -u "$MQTT_USER" -P "$MQTT_PASSWORD" -t "test/faculty" -C 1 &
SUB_PID=$!
sleep 1
mosquitto_pub -h localhost -u "$MQTT_USER" -P "$MQTT_PASSWORD" -t "test/faculty" -m "faculty_test_$(date +%s)"
wait $SUB_PID 2>/dev/null && print_success "Faculty desk authentication working" || print_warning "Faculty desk test failed"

# Test 3: Test specific ConsultEase topics
print_status "Testing ConsultEase topic permissions..."

# Test faculty response topic (the key issue)
print_status "Testing faculty response publishing..."
RESPONSE_TEST="{\"test\":\"permission_fix\",\"faculty_id\":1,\"status\":\"available\",\"timestamp\":$(date +%s)}"
mosquitto_pub -h localhost -u "$MQTT_USER" -P "$MQTT_PASSWORD" -t "consultease/faculty/1/responses" -m "$RESPONSE_TEST"
if [ $? -eq 0 ]; then
    print_success "✅ Faculty can now publish responses! Permission issue FIXED!"
else
    print_error "❌ Faculty still cannot publish responses"
fi

# Test faculty status topic
print_status "Testing faculty status publishing..."
STATUS_TEST="{\"faculty_id\":1,\"status\":\"available\",\"timestamp\":$(date +%s)}"
mosquitto_pub -h localhost -u "$MQTT_USER" -P "$MQTT_PASSWORD" -t "consultease/faculty/1/status" -m "$STATUS_TEST"
if [ $? -eq 0 ]; then
    print_success "✅ Faculty can publish status updates"
else
    print_warning "⚠️ Faculty cannot publish status updates"
fi

# Step 10: Display connection information
echo ""
print_status "📋 MQTT Broker Configuration Summary"
echo "================================================================"
echo "🏠 Broker Address: localhost (127.0.0.1)"
echo "🔌 Port: 1883"
echo "👤 Central System User: $CENTRAL_USER"
echo "👤 Faculty Desk User: $MQTT_USER"
echo ""
echo "📝 ESP32 Configuration (config.h):"
echo "   #define MQTT_SERVER \"$(hostname -I | awk '{print $1}')\""
echo "   #define MQTT_PORT 1883"
echo "   #define MQTT_USERNAME \"$MQTT_USER\""
echo "   #define MQTT_PASSWORD \"$MQTT_PASSWORD\""
echo ""
echo "🔐 Key Permissions Fixed:"
echo "   ✅ consultease/faculty/+/responses (WRITE)"
echo "   ✅ consultease/faculty/+/status (WRITE)" 
echo "   ✅ consultease/faculty/+/heartbeat (WRITE)"
echo ""

# Step 11: Show next steps
print_status "🎯 Next Steps:"
echo "1. Update ESP32 firmware with new MQTT credentials"
echo "2. Restart ESP32 device"
echo "3. Test faculty button responses"
echo "4. Monitor logs: journalctl -u mosquitto -f"
echo ""

print_success "🎉 MQTT Broker Permission Fix Completed!"
print_status "🔍 Run this to test ESP32 communication:"
echo "   python3 scripts/test_esp32_communication.py"

exit 0 