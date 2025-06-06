#!/bin/bash

# ConsultEase Enhanced Startup Script
# Comprehensive startup script with system integration checks and automated recovery

set -e  # Exit on any error

# Configuration
CONSULTEASE_DIR="/home/pi/ConsultEase"
LOG_FILE="/var/log/consultease/startup.log"
PID_FILE="/var/run/consultease.pid"
PYTHON_ENV="/home/pi/ConsultEase/venv"
CONFIG_FILE="/home/pi/ConsultEase/central_system/config.json"
BACKUP_DIR="/home/pi/ConsultEase/backups"

# System integration settings
REQUIRED_SERVICES=("postgresql" "mosquitto" "squeekboard")
CRITICAL_PORTS=(5432 1883)
MIN_DISK_SPACE_MB=1000
MIN_MEMORY_MB=512
MAX_STARTUP_TIME=120  # seconds

# Ensure log directory exists
sudo mkdir -p /var/log/consultease
sudo chown pi:pi /var/log/consultease

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Logging function with levels
log() {
    local level="${2:-INFO}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] - $1" | tee -a "$LOG_FILE"
}

log_error() { log "$1" "ERROR"; }
log_warning() { log "$1" "WARNING"; }
log_info() { log "$1" "INFO"; }
log_debug() { log "$1" "DEBUG"; }

# Error handling with recovery attempts
error_exit() {
    log_error "$1"
    cleanup_on_error
    exit 1
}

# Cleanup function for error scenarios
cleanup_on_error() {
    log_info "Performing cleanup after error..."
    
    # Kill any running ConsultEase processes
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log_info "Terminating existing ConsultEase process (PID: $pid)"
            kill -TERM "$pid" 2>/dev/null || true
            sleep 2
            kill -KILL "$pid" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi
    
    # Reset any stuck services
    reset_stuck_services
}

# Function to reset stuck services
reset_stuck_services() {
    log_info "Resetting potentially stuck services..."
    
    for service in "${REQUIRED_SERVICES[@]}"; do
        if systemctl is-failed --quiet "$service" 2>/dev/null; then
            log_warning "Service $service is in failed state, attempting reset"
            sudo systemctl reset-failed "$service" 2>/dev/null || true
        fi
    done
}

# Enhanced system resource checks
check_system_resources() {
    log_info "Checking system resources..."
    
    # Check available disk space
    local available_space=$(df / | awk 'NR==2 {print $4}')
    local available_mb=$((available_space / 1024))
    
    if [ "$available_mb" -lt "$MIN_DISK_SPACE_MB" ]; then
        log_warning "Low disk space: ${available_mb}MB available (minimum: ${MIN_DISK_SPACE_MB}MB)"
        cleanup_disk_space
        
        # Recheck after cleanup
        available_space=$(df / | awk 'NR==2 {print $4}')
        available_mb=$((available_space / 1024))
        
        if [ "$available_mb" -lt "$MIN_DISK_SPACE_MB" ]; then
            error_exit "Insufficient disk space after cleanup: ${available_mb}MB"
        fi
    fi
    
    # Check available memory
    local available_memory=$(free -m | awk 'NR==2{print $7}')
    if [ "$available_memory" -lt "$MIN_MEMORY_MB" ]; then
        log_warning "Low memory: ${available_memory}MB available (minimum: ${MIN_MEMORY_MB}MB)"
        cleanup_memory
    fi
    
    # Check CPU temperature (Raspberry Pi specific)
    if [ -f "/sys/class/thermal/thermal_zone0/temp" ]; then
        local temp=$(cat /sys/class/thermal/thermal_zone0/temp)
        local temp_celsius=$((temp / 1000))
        
        if [ "$temp_celsius" -gt 70 ]; then
            log_warning "High CPU temperature: ${temp_celsius}°C"
        else
            log_info "CPU temperature: ${temp_celsius}°C"
        fi
    fi
    
    log_info "System resources check completed"
}

# Function to cleanup disk space
cleanup_disk_space() {
    log_info "Attempting to free disk space..."
    
    # Clean package cache
    sudo apt-get clean 2>/dev/null || true
    
    # Clean old logs
    sudo journalctl --vacuum-time=7d 2>/dev/null || true
    
    # Clean temporary files
    sudo rm -rf /tmp/* 2>/dev/null || true
    
    # Clean old ConsultEase logs
    find /var/log/consultease -name "*.log" -mtime +7 -delete 2>/dev/null || true
    
    log_info "Disk cleanup completed"
}

# Function to cleanup memory
cleanup_memory() {
    log_info "Attempting to free memory..."
    
    # Drop caches
    sudo sync
    echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null 2>&1 || true
    
    log_info "Memory cleanup completed"
}

# Enhanced dependency checks
check_dependencies() {
    log_info "Checking system dependencies..."
    
    # Check if Python 3 is installed
    if ! command -v python3 &> /dev/null; then
        error_exit "Python 3 is not installed"
    fi
    
    local python_version=$(python3 --version | cut -d' ' -f2)
    log_info "Python version: $python_version"
    
    # Check if pip is installed
    if ! command -v pip3 &> /dev/null; then
        error_exit "pip3 is not installed"
    fi
    
    # Check if virtual environment exists and is valid
    if [ ! -d "$PYTHON_ENV" ]; then
        log_info "Virtual environment not found, creating..."
        python3 -m venv "$PYTHON_ENV" || error_exit "Failed to create virtual environment"
    else
        # Verify virtual environment integrity
        if [ ! -f "$PYTHON_ENV/bin/python" ]; then
            log_warning "Virtual environment corrupted, recreating..."
            rm -rf "$PYTHON_ENV"
            python3 -m venv "$PYTHON_ENV" || error_exit "Failed to recreate virtual environment"
        fi
    fi
    
    # Check if ConsultEase directory exists
    if [ ! -d "$CONSULTEASE_DIR" ]; then
        error_exit "ConsultEase directory not found: $CONSULTEASE_DIR"
    fi
    
    # Check critical files
    local critical_files=(
        "$CONSULTEASE_DIR/central_system/main.py"
        "$CONSULTEASE_DIR/requirements.txt"
    )
    
    for file in "${critical_files[@]}"; do
        if [ ! -f "$file" ]; then
            error_exit "Critical file missing: $file"
        fi
    done
    
    log_info "Dependencies check completed successfully"
}

# Enhanced service checks with recovery
check_services() {
    log_info "Checking required services..."
    
    for service in "${REQUIRED_SERVICES[@]}"; do
        check_and_start_service "$service"
    done
    
    # Check critical ports
    check_critical_ports
    
    log_info "Service check completed"
}

# Function to check and start individual service
check_and_start_service() {
    local service="$1"
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if systemctl is-active --quiet "$service"; then
            log_info "$service service is running"
            return 0
        else
            log_warning "$service service is not running (attempt $attempt/$max_attempts)"
            
            # Try to start the service
            if sudo systemctl start "$service" 2>/dev/null; then
                sleep 2
                if systemctl is-active --quiet "$service"; then
                    log_info "$service service started successfully"
                    return 0
                fi
            fi
            
            # If service failed to start, try reset
            if [ $attempt -eq 2 ]; then
                log_info "Attempting to reset $service service"
                sudo systemctl reset-failed "$service" 2>/dev/null || true
                sudo systemctl restart "$service" 2>/dev/null || true
                sleep 3
            fi
            
            ((attempt++))
        fi
    done
    
    log_error "Failed to start $service service after $max_attempts attempts"
    return 1
}

# Function to check critical ports
check_critical_ports() {
    log_info "Checking critical ports..."
    
    for port in "${CRITICAL_PORTS[@]}"; do
        if netstat -tuln | grep -q ":$port "; then
            log_info "Port $port is listening"
        else
            log_warning "Port $port is not listening"
        fi
    done
}

# Function to install/update Python dependencies
install_dependencies() {
    log_info "Installing/updating Python dependencies..."
    
    # Activate virtual environment
    source "$PYTHON_ENV/bin/activate" || error_exit "Failed to activate virtual environment"
    
    # Upgrade pip
    pip install --upgrade pip 2>/dev/null || log_warning "Failed to upgrade pip"
    
    # Install requirements
    if [ -f "$CONSULTEASE_DIR/requirements.txt" ]; then
        pip install -r "$CONSULTEASE_DIR/requirements.txt" || error_exit "Failed to install Python dependencies"
        log_info "Python dependencies installed successfully"
    else
        log_warning "requirements.txt not found, skipping dependency installation"
    fi
}

# Function to validate configuration
validate_configuration() {
    log_info "Validating system configuration..."
    
    # Check if config file exists
    if [ ! -f "$CONFIG_FILE" ]; then
        log_warning "Configuration file not found: $CONFIG_FILE"
        log_info "Using default configuration"
    else
        # Validate JSON syntax
        if python3 -m json.tool "$CONFIG_FILE" > /dev/null 2>&1; then
            log_info "Configuration file is valid JSON"
        else
            log_error "Configuration file has invalid JSON syntax"
            
            # Backup corrupted config
            local backup_file="$BACKUP_DIR/config_corrupted_$(date +%Y%m%d_%H%M%S).json"
            cp "$CONFIG_FILE" "$backup_file" 2>/dev/null || true
            log_info "Corrupted config backed up to: $backup_file"
            
            # Remove corrupted config to use defaults
            rm -f "$CONFIG_FILE"
            log_info "Using default configuration due to corrupted config file"
        fi
    fi
}

# Function to perform system integration tests
run_integration_tests() {
    log_info "Running system integration tests..."
    
    # Test database connectivity
    if command -v psql &> /dev/null; then
        if sudo -u postgres psql -c "SELECT 1;" > /dev/null 2>&1; then
            log_info "Database connectivity test: PASSED"
        else
            log_warning "Database connectivity test: FAILED"
        fi
    fi
    
    # Test MQTT connectivity
    if command -v mosquitto_pub &> /dev/null; then
        if timeout 5 mosquitto_pub -h localhost -t "test/connectivity" -m "test" > /dev/null 2>&1; then
            log_info "MQTT connectivity test: PASSED"
        else
            log_warning "MQTT connectivity test: FAILED"
        fi
    fi
    
    log_info "Integration tests completed"
}

# Function to start the application with monitoring
start_application() {
    log_info "Starting ConsultEase application..."
    
    # Change to application directory
    cd "$CONSULTEASE_DIR" || error_exit "Failed to change to ConsultEase directory"
    
    # Activate virtual environment
    source "$PYTHON_ENV/bin/activate" || error_exit "Failed to activate virtual environment"
    
    # Set environment variables
    export CONSULTEASE_KEYBOARD="squeekboard"
    export CONSULTEASE_FULLSCREEN="true"
    export PYTHONUNBUFFERED=1
    export DISPLAY=:0
    export XAUTHORITY="/home/pi/.Xauthority"
    
    # Start application in background
    nohup python3 central_system/main.py > "$LOG_FILE.app" 2>&1 &
    local app_pid=$!
    
    # Save PID
    echo $app_pid > "$PID_FILE"
    log_info "Application started with PID: $app_pid"
    
    # Monitor startup for a few seconds
    local startup_timeout=$MAX_STARTUP_TIME
    local check_interval=2
    local elapsed=0
    
    while [ $elapsed -lt $startup_timeout ]; do
        if ! ps -p $app_pid > /dev/null 2>&1; then
            log_error "Application process died during startup"
            return 1
        fi
        
        # Check if application is responding (basic check)
        if [ $elapsed -gt 10 ]; then
            # Application has been running for more than 10 seconds, likely successful
            log_info "Application appears to be running successfully"
            return 0
        fi
        
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    log_warning "Application startup monitoring timed out, but process is still running"
    return 0
}

# Main execution
main() {
    log_info "Starting ConsultEase Enhanced Startup Script"
    
    # Pre-flight checks
    check_system_resources
    check_dependencies
    check_services
    validate_configuration
    
    # Install/update dependencies
    install_dependencies
    
    # Run integration tests
    run_integration_tests
    
    # Start the application
    if start_application; then
        log_info "ConsultEase startup completed successfully"
        log_info "Application logs: $LOG_FILE.app"
        log_info "PID file: $PID_FILE"
    else
        error_exit "Failed to start ConsultEase application"
    fi
}

# Trap signals for cleanup
trap cleanup_on_error EXIT

# Run main function
main "$@"

# Remove trap on successful completion
trap - EXIT

log_info "Enhanced startup script completed successfully"
exit 0
