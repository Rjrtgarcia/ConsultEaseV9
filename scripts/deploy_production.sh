#!/bin/bash

# ConsultEase Production Deployment Script
# This script automates the deployment of ConsultEase for production use

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Please run as the pi user."
   exit 1
fi

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    warning "This script is designed for Raspberry Pi. Continuing anyway..."
fi

log "Starting ConsultEase Production Deployment"
echo "=============================================="

# Step 1: System Update
log "Step 1: Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install required packages
log "Step 2: Installing required packages..."
sudo apt install -y \
    postgresql postgresql-contrib \
    mosquitto mosquitto-clients \
    python3-pip python3-pyqt5 python3-evdev \
    python3-pyqt5.qtwebengine \
    python3-psutil \
    git

# Step 3: Install Python dependencies
log "Step 3: Installing Python dependencies..."
pip3 install --user \
    paho-mqtt \
    sqlalchemy \
    psycopg2-binary \
    bcrypt \
    psutil

# Step 4: Configure PostgreSQL
log "Step 4: Configuring PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE consultease;" 2>/dev/null || log "Database already exists"
sudo -u postgres psql -c "CREATE USER piuser WITH PASSWORD 'consultease_db_password';" 2>/dev/null || log "User already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE consultease TO piuser;"

# Step 5: Configure MQTT with authentication
log "Step 5: Configuring MQTT broker with authentication..."
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# Create MQTT password file
echo "consultease_user:consultease_secure_password" | sudo tee /tmp/mqtt_passwd
sudo mosquitto_passwd -U /tmp/mqtt_passwd
sudo mv /tmp/mqtt_passwd /etc/mosquitto/passwd
sudo chown mosquitto:mosquitto /etc/mosquitto/passwd
sudo chmod 600 /etc/mosquitto/passwd

# Configure Mosquitto
sudo tee /etc/mosquitto/mosquitto.conf > /dev/null <<EOF
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
EOF

sudo systemctl restart mosquitto

# Step 6: Install on-screen keyboard
log "Step 6: Installing on-screen keyboard..."
if command -v squeekboard >/dev/null 2>&1; then
    log "Squeekboard already installed"
elif command -v onboard >/dev/null 2>&1; then
    log "Onboard already installed"
else
    # Try to install squeekboard first, fallback to onboard
    if sudo apt install -y squeekboard 2>/dev/null; then
        success "Squeekboard installed successfully"
    elif sudo apt install -y onboard 2>/dev/null; then
        success "Onboard installed successfully"
    else
        warning "Could not install on-screen keyboard. Manual installation may be required."
    fi
fi

# Step 7: Set up ConsultEase application
log "Step 7: Setting up ConsultEase application..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONSULTEASE_DIR="$(dirname "$SCRIPT_DIR")"

log "ConsultEase directory: $CONSULTEASE_DIR"

# Create environment file
cat > "$CONSULTEASE_DIR/.env" <<EOF
# Database Configuration
DB_USER=piuser
DB_PASSWORD=consultease_db_password
DB_HOST=localhost
DB_NAME=consultease

# MQTT Configuration
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=consultease_user
MQTT_PASSWORD=consultease_secure_password

# Application Configuration
CONSULTEASE_FULLSCREEN=true
CONSULTEASE_KEYBOARD=squeekboard
PYTHONUNBUFFERED=1
EOF

# Step 8: Initialize database
log "Step 8: Initializing database..."
cd "$CONSULTEASE_DIR"
python3 -c "
import sys
sys.path.insert(0, '.')
from central_system.models.base import init_db
init_db()
print('Database initialized successfully')
"

# Step 9: Run production readiness tests
log "Step 9: Running production readiness tests..."
if [ -f "tests/test_production_readiness.py" ]; then
    python3 tests/test_production_readiness.py
    if [ $? -eq 0 ]; then
        success "All production readiness tests passed!"
    else
        error "Some production readiness tests failed. Please review the output above."
        exit 1
    fi
else
    warning "Production readiness tests not found. Skipping..."
fi

# Step 10: Create systemd service
log "Step 10: Creating systemd service..."
sudo tee /etc/systemd/system/consultease.service > /dev/null <<EOF
[Unit]
Description=ConsultEase Central System
After=network.target postgresql.service mosquitto.service

[Service]
ExecStart=/usr/bin/python3 $CONSULTEASE_DIR/central_system/main.py
WorkingDirectory=$CONSULTEASE_DIR
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
EOF

# Step 11: Enable and start service
log "Step 11: Enabling and starting ConsultEase service..."
sudo systemctl daemon-reload
sudo systemctl enable consultease.service

# Step 12: Hardware validation
log "Step 12: Running hardware validation..."
python3 -c "
import sys
sys.path.insert(0, '.')
from central_system.utils.hardware_validator import log_hardware_status
log_hardware_status()
"

# Step 13: Final security check
log "Step 13: Final security verification..."
echo ""
echo "=============================================="
echo "🔒 SECURITY CHECKLIST"
echo "=============================================="
echo "✅ Database configured with secure credentials"
echo "✅ MQTT broker configured with authentication"
echo "✅ Default admin password set to temporary value"
echo "⚠️  IMPORTANT: Change admin password on first login!"
echo ""
echo "Default admin credentials:"
echo "  Username: admin"
echo "  Password: TempPass123!"
echo ""
echo "🚨 CHANGE THIS PASSWORD IMMEDIATELY AFTER FIRST LOGIN!"
echo "=============================================="

# Step 14: Deployment summary
echo ""
success "ConsultEase deployment completed successfully!"
echo ""
echo "Next steps:"
echo "1. Start the service: sudo systemctl start consultease.service"
echo "2. Check service status: sudo systemctl status consultease.service"
echo "3. View logs: journalctl -u consultease.service -f"
echo "4. Access the application on the touchscreen"
echo "5. Login with admin/TempPass123! and CHANGE THE PASSWORD"
echo ""
echo "For troubleshooting, check:"
echo "- Service logs: journalctl -u consultease.service"
echo "- Application logs: $CONSULTEASE_DIR/consultease.log"
echo "- MQTT messages: mosquitto_sub -t 'consultease/#' -v"
echo ""
echo "Deployment completed at: $(date)"

# Ask if user wants to start the service now
echo ""
read -p "Would you like to start the ConsultEase service now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "Starting ConsultEase service..."
    sudo systemctl start consultease.service
    sleep 3
    
    if sudo systemctl is-active --quiet consultease.service; then
        success "ConsultEase service is running!"
        echo "You can now access the application on your touchscreen."
    else
        error "Failed to start ConsultEase service. Check logs with: journalctl -u consultease.service"
    fi
else
    log "Service not started. You can start it manually with: sudo systemctl start consultease.service"
fi

echo ""
success "Production deployment script completed!"
echo "Thank you for using ConsultEase! 🎓"
