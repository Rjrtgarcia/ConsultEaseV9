# ConsultEase Keyboard Integration Guide

This document provides information about the on-screen keyboard integration in the ConsultEase system.

## Overview

ConsultEase now uses Squeekboard as the primary on-screen keyboard for touch input. Squeekboard is a modern, Wayland-compatible on-screen keyboard that provides better integration with the system and a more responsive user experience.

## Installation

To install and configure Squeekboard, run the following script:

```bash
# Navigate to the scripts directory
cd scripts

# Make the script executable
chmod +x install_squeekboard_complete.sh

# Run the installation script
./install_squeekboard_complete.sh
```

This script will:
1. Install Squeekboard if not already installed
2. Configure systemd service for Squeekboard
3. Set up environment variables
4. Create utility scripts for keyboard management
5. Configure autostart
6. Test the installation
7. Disable Onboard to avoid conflicts

## Removing Onboard

If you previously used Onboard and want to completely remove it, run:

```bash
# Navigate to the scripts directory
cd scripts

# Make the script executable
chmod +x remove_onboard.sh

# Run the removal script
./remove_onboard.sh
```

This script will:
1. Stop any running Onboard instances
2. Disable Onboard autostart
3. Remove Onboard configuration
4. Remove Onboard environment variables
5. Remove Onboard keyboard scripts
6. Update the .env file

## Manual Keyboard Control

After installation, you can use the following scripts to manually control the keyboard:

- `~/keyboard-toggle.sh` - Toggle keyboard visibility
- `~/keyboard-show.sh` - Force show keyboard
- `~/keyboard-hide.sh` - Force hide keyboard

## Automatic Keyboard Behavior

The keyboard will automatically appear when:
1. A text input field receives focus
2. A user clicks or taps on a text input field
3. A user interacts with a component that has the `keyboardOnFocus` property set to `true`

The keyboard will automatically hide when:
1. Focus moves to a non-input element
2. The user explicitly hides it using the keyboard's hide button or the hide script

## Troubleshooting

If the keyboard doesn't appear automatically:

1. Check if Squeekboard is running:
   ```bash
   pgrep -f squeekboard
   ```

2. If not running, start it manually:
   ```bash
   ~/keyboard-show.sh
   ```

3. Check if the DBus service is working:
   ```bash
   dbus-send --print-reply --type=method_call --dest=sm.puri.OSK0 /sm/puri/OSK0 sm.puri.OSK0.GetVisible
   ```

4. Verify environment variables:
   ```bash
   echo $CONSULTEASE_KEYBOARD
   echo $SQUEEKBOARD_FORCE
   ```

5. Restart the system to ensure all changes take effect:
   ```bash
   sudo reboot
   ```

## Technical Details

The keyboard integration consists of several components:

1. **Environment Configuration**: Environment variables in `.bashrc` and `~/.config/environment.d/consultease-keyboard.conf`
2. **Systemd Service**: User service for Squeekboard in `~/.config/systemd/user/squeekboard.service`
3. **Autostart Entry**: Desktop entry in `~/.config/autostart/squeekboard-autostart.desktop`
4. **Utility Scripts**: Shell scripts in the home directory for keyboard control
5. **Python Integration**: Classes in `central_system/utils/keyboard_integration.py` and `central_system/utils/keyboard_handler.py`
6. **JavaScript Integration**: Scripts in `central_system/static/js/keyboard_focus.js` and `central_system/static/js/keyboard_integration.js`

The system prioritizes Squeekboard over other keyboard options and provides multiple methods to ensure the keyboard appears when needed.
