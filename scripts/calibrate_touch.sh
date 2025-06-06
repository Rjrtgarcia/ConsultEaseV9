#!/bin/bash

# Touch calibration script for ConsultEase system
# This script will install the necessary utilities and guide the user through
# touchscreen calibration on a Raspberry Pi

# Set script to exit on error
set -e

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}ConsultEase Touch Calibration Utility${NC}"
echo "This script will help you calibrate your touchscreen."
echo "-------------------------------------------------------"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}Please run this script with sudo privileges.${NC}"
  echo "Usage: sudo ./calibrate_touch.sh"
  exit 1
fi

# Check if we're running on a Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
  echo -e "${YELLOW}Warning: This script is designed for Raspberry Pi.${NC}"
  echo "It may not work correctly on other systems."
  read -p "Continue anyway? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Install required packages
echo -e "${GREEN}Installing required packages...${NC}"
apt update
apt install -y xinput xinput-calibrator x11-xserver-utils xserver-xorg-input-evdev

# Create necessary configuration directory
mkdir -p /etc/X11/xorg.conf.d/

# Check if calibration file already exists
if [ -f /etc/X11/xorg.conf.d/99-calibration.conf ]; then
  echo -e "${YELLOW}Existing calibration found.${NC}"
  echo "Current calibration parameters:"
  cat /etc/X11/xorg.conf.d/99-calibration.conf
  echo
  read -p "Overwrite existing calibration? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Keeping existing calibration. Exiting.${NC}"
    exit 0
  fi
fi

# Create a basic calibration configuration if it doesn't exist
if [ ! -f /etc/X11/xorg.conf.d/99-calibration.conf ]; then
  echo -e "${GREEN}Creating initial calibration file...${NC}"
  cat > /etc/X11/xorg.conf.d/99-calibration.conf << 'EOF'
Section "InputClass"
    Identifier      "Touchscreen"
    MatchIsTouchscreen "on"
    Driver          "evdev"
    Option          "SwapAxes"      "0"
    Option          "InvertX"       "0"
    Option          "InvertY"       "0"
EndSection
EOF
fi

# Create a script to run the calibration tool
cat > /tmp/run_calibration.sh << 'EOF'
#!/bin/bash
export DISPLAY=:0
xinput_calibrator --output-type xorg.conf.d --output-filename /etc/X11/xorg.conf.d/99-calibration.conf
EOF
chmod +x /tmp/run_calibration.sh

echo -e "${GREEN}Calibration utility is ready.${NC}"
echo "Please follow these steps to calibrate your touchscreen:"
echo
echo -e "1. ${YELLOW}Make sure X is running and you're in the graphical environment${NC}"
echo -e "2. ${YELLOW}Run this command in the terminal:${NC}"
echo -e "   ${BLUE}sudo /tmp/run_calibration.sh${NC}"
echo -e "3. ${YELLOW}Follow the on-screen instructions to tap the calibration points${NC}"
echo -e "4. ${YELLOW}After calibration completes, restart your system:${NC}"
echo -e "   ${BLUE}sudo reboot${NC}"
echo
echo -e "${RED}IMPORTANT:${NC}"
echo "If you run into issues with the touch calibration, you can manually edit"
echo "the configuration file at: /etc/X11/xorg.conf.d/99-calibration.conf"
echo "Common adjustments include setting SwapAxes, InvertX, or InvertY to 1"
echo "if your touchscreen axes are inverted or swapped."
echo

echo -e "${GREEN}Do you want to run the calibration now? (y/n)${NC}"
read -p "" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo "Running calibration tool..."
  if pgrep -x "Xorg" > /dev/null || pgrep -x "X" > /dev/null; then
    /tmp/run_calibration.sh
    echo -e "${GREEN}Calibration completed. Please reboot your system.${NC}"
  else
    echo -e "${YELLOW}X server is not running. Please start X and run:${NC}"
    echo -e "${BLUE}sudo /tmp/run_calibration.sh${NC}"
  fi
else
  echo -e "${GREEN}You can run the calibration later using:${NC}"
  echo -e "${BLUE}sudo /tmp/run_calibration.sh${NC}"
fi

echo
echo -e "${GREEN}Touch calibration setup completed.${NC}" 