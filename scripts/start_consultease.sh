#!/bin/bash
# ConsultEase Startup Script
# This script starts the ConsultEase system with proper error handling and logging

# Set script to exit on error
set -e

# Configuration
CONSULTEASE_DIR="$HOME/ConsultEase"
LOG_DIR="$CONSULTEASE_DIR/logs"
MAIN_SCRIPT="central_system/main.py"
KEYBOARD_TYPE="squeekboard"  # or "onboard"
FULLSCREEN="true"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Log file with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/startup_$TIMESTAMP.log"

# Function to log messages
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a "$LOG_FILE"
}

# Function to check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log "ERROR: Python 3 is not installed"
        exit 1
    fi
    
    # Check PostgreSQL
    if ! command -v psql &> /dev/null; then
        log "WARNING: PostgreSQL client not found, database operations may fail"
    fi
    
    # Check MQTT
    if ! command -v mosquitto_pub &> /dev/null; then
        log "WARNING: Mosquitto clients not found, MQTT operations may fail"
    fi
    
    # Check keyboard
    if [ "$KEYBOARD_TYPE" = "squeekboard" ]; then
        if ! command -v squeekboard &> /dev/null; then
            log "WARNING: Squeekboard not found, falling back to onboard"
            KEYBOARD_TYPE="onboard"
        fi
    fi
    
    if [ "$KEYBOARD_TYPE" = "onboard" ]; then
        if ! command -v onboard &> /dev/null; then
            log "WARNING: Onboard not found, on-screen keyboard may not work"
        fi
    fi
    
    log "Dependency check completed"
}

# Function to check services
check_services() {
    log "Checking required services..."
    
    # Check PostgreSQL service
    if systemctl is-active --quiet postgresql; then
        log "PostgreSQL service is running"
    else
        log "WARNING: PostgreSQL service is not running, attempting to start"
        sudo systemctl start postgresql || log "ERROR: Failed to start PostgreSQL"
    fi
    
    # Check MQTT broker service
    if systemctl is-active --quiet mosquitto; then
        log "Mosquitto service is running"
    else
        log "WARNING: Mosquitto service is not running, attempting to start"
        sudo systemctl start mosquitto || log "ERROR: Failed to start Mosquitto"
    fi
    
    log "Service check completed"
}

# Function to start the application
start_application() {
    log "Starting ConsultEase application..."
    
    # Change to the ConsultEase directory
    cd "$CONSULTEASE_DIR"
    
    # Set environment variables
    export CONSULTEASE_KEYBOARD="$KEYBOARD_TYPE"
    export PYTHONUNBUFFERED=1
    
    # Start the application
    if [ "$FULLSCREEN" = "true" ]; then
        log "Starting in fullscreen mode"
        python3 "$MAIN_SCRIPT" --fullscreen >> "$LOG_FILE" 2>&1 &
    else
        log "Starting in windowed mode"
        python3 "$MAIN_SCRIPT" >> "$LOG_FILE" 2>&1 &
    fi
    
    APP_PID=$!
    log "Application started with PID: $APP_PID"
    
    # Save PID to file for later reference
    echo $APP_PID > "$CONSULTEASE_DIR/.consultease.pid"
    
    # Wait for a moment to check if the application crashed immediately
    sleep 2
    if ! ps -p $APP_PID > /dev/null; then
        log "ERROR: Application failed to start, check the log file: $LOG_FILE"
        exit 1
    fi
    
    log "Application started successfully"
}

# Main execution
log "Starting ConsultEase system"

# Check dependencies and services
check_dependencies
check_services

# Start the application
start_application

log "Startup completed successfully"
exit 0
