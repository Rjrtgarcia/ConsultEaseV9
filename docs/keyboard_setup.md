# ConsultEase Keyboard Setup Guide

This guide explains how to set up and configure the on-screen keyboard for the ConsultEase system.

## Overview

ConsultEase supports two on-screen keyboard options:

1. **Squeekboard** - A mobile-friendly keyboard optimized for Wayland environments
2. **Onboard** - A traditional on-screen keyboard with more customization options

The system includes a unified setup script that can automatically detect and configure the appropriate keyboard based on your environment.

## Automatic Setup

The easiest way to set up the keyboard is to use the unified setup script:

```bash
sudo chmod +x scripts/keyboard_setup.sh
sudo ./scripts/keyboard_setup.sh
```

This script will:

1. Detect your desktop environment
2. Install the appropriate keyboard (squeekboard for mobile environments, onboard for traditional desktops)
3. Configure environment variables
4. Create keyboard toggle scripts
5. Update the ConsultEase configuration

After running the script, you'll need to log out and log back in for all settings to take effect.

## Manual Configuration

If you prefer to manually configure the keyboard, follow these steps:

### For Squeekboard

1. Install squeekboard:
   ```bash
   sudo apt update
   sudo apt install -y squeekboard
   ```

2. Set up environment variables:
   ```bash
   mkdir -p ~/.config/environment.d/
   cat > ~/.config/environment.d/consultease-keyboard.conf << EOF
   # ConsultEase keyboard environment variables
   GDK_BACKEND=wayland,x11
   QT_QPA_PLATFORM=wayland;xcb
   SQUEEKBOARD_FORCE=1
   CONSULTEASE_KEYBOARD=squeekboard
   MOZ_ENABLE_WAYLAND=1
   QT_IM_MODULE=wayland
   CLUTTER_IM_MODULE=wayland
   # Disable onboard
   ONBOARD_DISABLE=1
   EOF
   ```

3. Add to .bashrc for immediate effect:
   ```bash
   cat >> ~/.bashrc << EOF

   # ConsultEase keyboard environment variables
   export GDK_BACKEND=wayland,x11
   export QT_QPA_PLATFORM="wayland;xcb"
   export SQUEEKBOARD_FORCE=1
   export CONSULTEASE_KEYBOARD=squeekboard
   export MOZ_ENABLE_WAYLAND=1
   export QT_IM_MODULE=wayland
   export CLUTTER_IM_MODULE=wayland
   # Disable onboard
   export ONBOARD_DISABLE=1
   EOF
   ```

### For Onboard

1. Install onboard:
   ```bash
   sudo apt update
   sudo apt install -y onboard
   ```

2. Set up environment variables:
   ```bash
   mkdir -p ~/.config/environment.d/
   cat > ~/.config/environment.d/consultease-keyboard.conf << EOF
   # ConsultEase keyboard environment variables
   GDK_BACKEND=wayland,x11
   QT_QPA_PLATFORM=wayland;xcb
   ONBOARD_ENABLE_TOUCH=1
   ONBOARD_XEMBED=1
   CONSULTEASE_KEYBOARD=onboard
   # Disable squeekboard
   SQUEEKBOARD_DISABLE=1
   EOF
   ```

3. Add to .bashrc for immediate effect:
   ```bash
   cat >> ~/.bashrc << EOF

   # ConsultEase keyboard environment variables
   export GDK_BACKEND=wayland,x11
   export QT_QPA_PLATFORM=wayland;xcb
   export ONBOARD_ENABLE_TOUCH=1
   export ONBOARD_XEMBED=1
   export CONSULTEASE_KEYBOARD=onboard
   # Disable squeekboard
   export SQUEEKBOARD_DISABLE=1
   EOF
   ```

4. Configure onboard settings:
   ```bash
   mkdir -p ~/.config/onboard
   cat > ~/.config/onboard/onboard.conf << EOF
   [main]
   layout=Phone
   theme=Nightshade
   key-size=small
   enable-background-transparency=true
   show-status-icon=true
   start-minimized=false
   show-tooltips=false
   auto-show=true
   auto-show-delay=500
   auto-hide=true
   auto-hide-delay=1000
   xembed-onboard=true
   enable-touch-input=true
   touch-feedback-enabled=true
   touch-feedback-size=small
   EOF
   ```

## Keyboard Toggle Scripts

The setup script creates three useful scripts in your home directory:

1. **~/keyboard-toggle.sh** - Toggle keyboard visibility
2. **~/keyboard-show.sh** - Force show the keyboard
3. **~/keyboard-hide.sh** - Force hide the keyboard

You can run these scripts from the terminal or bind them to keyboard shortcuts.

## Troubleshooting

### Keyboard Not Appearing

If the keyboard doesn't appear automatically when clicking on text fields:

1. Make sure you've logged out and logged back in after setup
2. Try running `~/keyboard-show.sh` to manually show the keyboard
3. Check if the keyboard service is running:
   - For squeekboard: `systemctl --user status squeekboard.service`
   - For onboard: `pgrep -f onboard`
4. Verify environment variables are set correctly: `env | grep KEYBOARD`

### Keyboard Not Hiding

If the keyboard doesn't hide when expected:

1. Try running `~/keyboard-hide.sh` to manually hide the keyboard
2. Check if multiple instances are running:
   - For squeekboard: `pgrep -f squeekboard`
   - For onboard: `pgrep -f onboard`
3. Kill any running instances and restart:
   - For squeekboard: `pkill -f squeekboard && SQUEEKBOARD_FORCE=1 squeekboard &`
   - For onboard: `pkill -f onboard && onboard --size=small --layout=Phone --enable-background-transparency &`

### Switching Between Keyboards

If you want to switch from one keyboard to another:

1. Run the unified setup script with the desired keyboard:
   ```bash
   sudo ./scripts/keyboard_setup.sh
   ```
   
2. The script will detect your current configuration and ask if you want to change it.

## Integration with ConsultEase

ConsultEase automatically detects and uses the configured keyboard. The system:

1. Detects which keyboard is installed
2. Shows the keyboard when text fields receive focus
3. Hides the keyboard when focus is lost
4. Provides keyboard toggle functionality via F5 key

No additional configuration is needed within the application itself.

## Advanced Configuration

For advanced users who need more customization:

### Squeekboard

Squeekboard configuration files are located in:
- `~/.config/squeekboard/`

### Onboard

Onboard offers more customization options:
- `~/.config/onboard/onboard.conf` - Main configuration
- Layouts can be customized via the onboard settings UI
- Themes can be selected via the onboard settings UI

You can launch the onboard settings UI with:
```bash
onboard-settings
```

## Conclusion

With the keyboard properly configured, ConsultEase will provide a seamless touch experience with automatic keyboard functionality. If you encounter any issues, please refer to the troubleshooting section or contact support.
