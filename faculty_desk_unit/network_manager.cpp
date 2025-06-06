#include "network_manager.h"
#include "config.h"

// Static instance for callbacks
NetworkManager* NetworkManager::_instance = nullptr;

// ================================
// CONSTRUCTOR & DESTRUCTOR
// ================================

NetworkManager::NetworkManager() {
    _instance = this;
    _wifi_state = WIFI_IDLE;
    _mqtt_state = MQTT_IDLE;
    _last_error = ERROR_NONE;
    _mqtt_client = nullptr;
    _wifi_last_attempt = 0;
    _mqtt_last_attempt = 0;
    _last_health_check = 0;
    _connection_start_time = 0;
    _wifi_retry_count = 0;
    _mqtt_retry_count = 0;
    _wifi_connect_time = 0;
    _mqtt_connect_time = 0;
    _message_queue_size = 0;
    _wifi_callback = nullptr;
    _mqtt_callback = nullptr;
    _message_callback = nullptr;
    _diagnostics_callback = nullptr;
    _watchdog_enabled = false;
    _last_watchdog_feed = 0;
    _watchdog_timeout_ms = 30000; // 30 seconds default
    
    // Initialize stats
    memset(&_stats, 0, sizeof(_stats));
}

NetworkManager::~NetworkManager() {
    end();
    _instance = nullptr;
}

// ================================
// INITIALIZATION
// ================================

bool NetworkManager::begin(const NetworkConfig& config) {
    DEBUG_PRINTLN("🔧 NetworkManager: Initializing robust connectivity system...");
    
    // Store configuration
    _config = config;
    
    // Initialize WiFi with advanced settings
    WiFi.mode(WIFI_STA);
    WiFi.setAutoConnect(false);
    WiFi.setAutoReconnect(false); // We handle reconnection manually
    
    // Configure power management
    if (_config.wifi_power_save_enabled) {
        esp_wifi_set_ps(WIFI_PS_MIN_MODEM); // Minimal power save for better reliability
    } else {
        esp_wifi_set_ps(WIFI_PS_NONE); // No power save for maximum performance
    }
    
    // Initialize MQTT client
    if (_mqtt_client) {
        delete _mqtt_client;
    }
    _mqtt_client = new PubSubClient(_wifi_client);
    
    if (!_mqtt_client) {
        DEBUG_PRINTLN("❌ NetworkManager: Failed to allocate MQTT client");
        setError(ERROR_MEMORY_ALLOCATION);
        return false;
    }
    
    // Configure MQTT
    _mqtt_client->setBufferSize(_config.mqtt_buffer_size);
    _mqtt_client->setServer(_config.mqtt_server, _config.mqtt_port);
    _mqtt_client->setCallback(mqttCallback);
    _mqtt_client->setKeepAlive(_config.mqtt_keepalive);
    
    // Enable watchdog if configured
    if (_config.enable_watchdog) {
        enableWatchdog(30); // 30 seconds default
    }
    
    // Reset statistics
    resetStats();
    
    DEBUG_PRINTLN("✅ NetworkManager: Initialization complete");
    DEBUG_PRINTF("   WiFi SSID: %s\n", _config.wifi_ssid);
    DEBUG_PRINTF("   MQTT Server: %s:%d\n", _config.mqtt_server, _config.mqtt_port);
    DEBUG_PRINTF("   Buffer Size: %d bytes\n", _config.mqtt_buffer_size);
    DEBUG_PRINTF("   Watchdog: %s\n", _config.enable_watchdog ? "ENABLED" : "DISABLED");
    
    return true;
}

void NetworkManager::end() {
    DEBUG_PRINTLN("🔧 NetworkManager: Shutting down...");
    
    disconnect();
    
    if (_mqtt_client) {
        delete _mqtt_client;
        _mqtt_client = nullptr;
    }
    
    WiFi.mode(WIFI_OFF);
    
    if (_watchdog_enabled) {
        esp_task_wdt_delete(NULL);
        _watchdog_enabled = false;
    }
    
    DEBUG_PRINTLN("✅ NetworkManager: Shutdown complete");
}

// ================================
// CALLBACK REGISTRATION
// ================================

void NetworkManager::setWiFiEventCallback(WiFiEventCallback callback) {
    _wifi_callback = callback;
}

void NetworkManager::setMQTTEventCallback(MQTTEventCallback callback) {
    _mqtt_callback = callback;
}

void NetworkManager::setMessageCallback(MessageCallback callback) {
    _message_callback = callback;
}

void NetworkManager::setDiagnosticsCallback(DiagnosticsCallback callback) {
    _diagnostics_callback = callback;
}

// ================================
// CONNECTION MANAGEMENT
// ================================

bool NetworkManager::connectWiFi() {
    if (_wifi_state == WIFI_CONNECTED) {
        return true;
    }
    
    if (_wifi_state == WIFI_CONNECTING || _wifi_state == WIFI_RECONNECTING) {
        return false; // Already attempting connection
    }
    
    DEBUG_PRINTF("📡 NetworkManager: Connecting to WiFi '%s'...\n", _config.wifi_ssid);
    setWiFiState(WIFI_CONNECTING);
    
    return startWiFiConnection();
}

bool NetworkManager::connectMQTT() {
    if (_mqtt_state == MQTT_CONNECTED) {
        return true;
    }
    
    if (!isWiFiConnected()) {
        DEBUG_PRINTLN("⚠️ NetworkManager: Cannot connect MQTT - WiFi not connected");
        return false;
    }
    
    if (_mqtt_state == MQTT_CONNECTING || _mqtt_state == MQTT_RECONNECTING) {
        return false; // Already attempting connection
    }
    
    DEBUG_PRINTF("📡 NetworkManager: Connecting to MQTT %s:%d...\n", 
                _config.mqtt_server, _config.mqtt_port);
    setMQTTState(MQTT_CONNECTING);
    
    return startMQTTConnection();
}

void NetworkManager::disconnect() {
    DEBUG_PRINTLN("📡 NetworkManager: Disconnecting...");
    
    if (_mqtt_client && _mqtt_client->connected()) {
        _mqtt_client->disconnect();
    }
    
    if (WiFi.isConnected()) {
        WiFi.disconnect(true);
    }
    
    setWiFiState(WIFI_IDLE);
    setMQTTState(MQTT_IDLE);
}

void NetworkManager::reset() {
    DEBUG_PRINTLN("🔄 NetworkManager: Performing system reset...");
    
    disconnect();
    
    // Clear retry counters
    _wifi_retry_count = 0;
    _mqtt_retry_count = 0;
    _wifi_last_attempt = 0;
    _mqtt_last_attempt = 0;
    
    // Clear message queue
    _message_queue_size = 0;
    
    // Reset error state
    _last_error = ERROR_NONE;
    
    // Reset statistics
    resetStats();
    
    DEBUG_PRINTLN("✅ NetworkManager: Reset complete");
}

// ================================
// CONNECTION QUALITY
// ================================

int NetworkManager::getWiFiRSSI() const {
    if (isWiFiConnected()) {
        return WiFi.RSSI();
    }
    return -100; // Poor signal indicator when not connected
}

int NetworkManager::getConnectionQuality() const {
    if (!isFullyConnected()) {
        return 0;
    }
    
    int rssi = getWiFiRSSI();
    
    // Convert RSSI to quality percentage
    if (rssi >= -50) return 100;  // Excellent
    if (rssi >= -60) return 80;   // Good
    if (rssi >= -70) return 60;   // Fair
    if (rssi >= -80) return 40;   // Poor
    if (rssi >= -90) return 20;   // Very poor
    return 10;                    // Almost unusable
}

// ================================
// MQTT OPERATIONS
// ================================

bool NetworkManager::publish(const char* topic, const char* payload, bool retained, int qos) {
    if (!isMQTTConnected()) {
        DEBUG_PRINTF("⚠️ NetworkManager: MQTT not connected, queueing message: %s\n", topic);
        return queueMessage(topic, payload, retained, qos);
    }
    
    DEBUG_PRINTF("📤 NetworkManager: Publishing to %s (%d bytes)\n", topic, strlen(payload));
    
    bool result = false;
    if (qos == 0) {
        result = _mqtt_client->publish(topic, payload, retained);
    } else {
        // QoS 1 not directly supported by PubSubClient, queue for retry
        result = _mqtt_client->publish(topic, payload, retained);
    }
    
    if (result) {
        _stats.messages_sent++;
        DEBUG_PRINTF("✅ NetworkManager: Message published successfully\n");
    } else {
        _stats.messages_failed++;
        DEBUG_PRINTF("❌ NetworkManager: Failed to publish, queueing for retry\n");
        queueMessage(topic, payload, retained, qos);
    }
    
    return result;
}

bool NetworkManager::subscribe(const char* topic, int qos) {
    if (!isMQTTConnected()) {
        DEBUG_PRINTF("⚠️ NetworkManager: Cannot subscribe - MQTT not connected\n");
        return false;
    }
    
    DEBUG_PRINTF("📥 NetworkManager: Subscribing to %s\n", topic);
    return _mqtt_client->subscribe(topic, qos);
}

bool NetworkManager::unsubscribe(const char* topic) {
    if (!isMQTTConnected()) {
        return false;
    }
    
    DEBUG_PRINTF("📥 NetworkManager: Unsubscribing from %s\n", topic);
    return _mqtt_client->unsubscribe(topic);
}

// ================================
// MESSAGE QUEUE MANAGEMENT
// ================================

bool NetworkManager::queueMessage(const char* topic, const char* payload, bool retained, int qos) {
    if (_message_queue_size >= MAX_QUEUE_SIZE) {
        DEBUG_PRINTLN("⚠️ NetworkManager: Message queue full, dropping oldest message");
        
        // Shift queue to make room
        for (int i = 0; i < MAX_QUEUE_SIZE - 1; i++) {
            _message_queue[i] = _message_queue[i + 1];
        }
        _message_queue_size = MAX_QUEUE_SIZE - 1;
    }
    
    // Add new message to queue
    QueuedMessage& msg = _message_queue[_message_queue_size];
    strncpy(msg.topic, topic, sizeof(msg.topic) - 1);
    strncpy(msg.payload, payload, sizeof(msg.payload) - 1);
    msg.topic[sizeof(msg.topic) - 1] = '\0';
    msg.payload[sizeof(msg.payload) - 1] = '\0';
    msg.retained = retained;
    msg.qos = qos;
    msg.timestamp = millis();
    msg.retry_count = 0;
    
    _message_queue_size++;
    _stats.messages_queued++;
    
    DEBUG_PRINTF("📥 NetworkManager: Message queued (%d in queue): %s\n", _message_queue_size, topic);
    return true;
}

void NetworkManager::processMessageQueue() {
    if (_message_queue_size == 0 || !isMQTTConnected()) {
        return;
    }
    
    // Process one message at a time to avoid blocking
    QueuedMessage& msg = _message_queue[0];
    
    DEBUG_PRINTF("📤 NetworkManager: Processing queued message: %s\n", msg.topic);
    
    bool success = _mqtt_client->publish(msg.topic, msg.payload, msg.retained);
    
    if (success) {
        DEBUG_PRINTF("✅ NetworkManager: Queued message sent successfully\n");
        _stats.messages_sent++;
        
        // Remove processed message by shifting queue
        for (int i = 0; i < _message_queue_size - 1; i++) {
            _message_queue[i] = _message_queue[i + 1];
        }
        _message_queue_size--;
    } else {
        msg.retry_count++;
        _stats.messages_failed++;
        
        if (msg.retry_count >= 3) {
            DEBUG_PRINTF("❌ NetworkManager: Message failed after 3 retries, dropping: %s\n", msg.topic);
            
            // Remove failed message
            for (int i = 0; i < _message_queue_size - 1; i++) {
                _message_queue[i] = _message_queue[i + 1];
            }
            _message_queue_size--;
        } else {
            DEBUG_PRINTF("⏳ NetworkManager: Message retry %d/3: %s\n", msg.retry_count, msg.topic);
        }
    }
}

// ================================
// MAIN UPDATE FUNCTION
// ================================

void NetworkManager::update() {
    unsigned long now = millis();
    
    // Feed watchdog
    if (_watchdog_enabled) {
        feedWatchdog();
    }
    
    // Update WiFi connection
    updateWiFi();
    
    // Update MQTT connection
    updateMQTT();
    
    // Process MQTT messages
    if (_mqtt_client && isMQTTConnected()) {
        _mqtt_client->loop();
    }
    
    // Process message queue
    processMessageQueue();
    
    // Health check
    if (now - _last_health_check > _config.health_check_interval_ms) {
        updateHealthCheck();
        _last_health_check = now;
    }
    
    // Update statistics
    updateStats();
    
    // Diagnostics callback
    if (_diagnostics_callback && _config.enable_diagnostics) {
        static unsigned long last_diagnostics = 0;
        if (now - last_diagnostics > 30000) { // Every 30 seconds
            _diagnostics_callback(_stats);
            last_diagnostics = now;
        }
    }
}

// ================================
// INTERNAL METHODS
// ================================

void NetworkManager::updateWiFi() {
    unsigned long now = millis();
    
    switch (_wifi_state) {
        case WIFI_CONNECTING:
            if (WiFi.status() == WL_CONNECTED) {
                _wifi_connect_time = now;
                _stats.last_connection_time = now;
                _wifi_retry_count = 0;
                setWiFiState(WIFI_CONNECTED);
                DEBUG_PRINTF("✅ NetworkManager: WiFi connected! IP: %s\n", WiFi.localIP().toString().c_str());
            } else if (now - _wifi_last_attempt > _config.wifi_timeout_ms) {
                _stats.wifi_failures++;
                setWiFiState(WIFI_RECONNECTING, mapWiFiError(WiFi.status()));
                DEBUG_PRINTF("❌ NetworkManager: WiFi connection timeout\n");
            }
            break;
            
        case WIFI_CONNECTED:
            if (WiFi.status() != WL_CONNECTED) {
                _stats.wifi_failures++;
                setWiFiState(WIFI_RECONNECTING);
                DEBUG_PRINTLN("⚠️ NetworkManager: WiFi connection lost");
            }
            break;
            
        case WIFI_RECONNECTING:
            if (isTimeToRetry(_wifi_last_attempt, calculateBackoffDelay(_config.wifi_retry_interval_ms, _wifi_retry_count))) {
                if (_wifi_retry_count < _config.wifi_max_retries) {
                    _wifi_retry_count++;
                    _stats.wifi_reconnect_count++;
                    DEBUG_PRINTF("🔄 NetworkManager: WiFi reconnect attempt %d/%d\n", _wifi_retry_count, _config.wifi_max_retries);
                    startWiFiConnection();
                } else {
                    setWiFiState(WIFI_FAILED, ERROR_WIFI_CONNECT_FAIL);
                    DEBUG_PRINTLN("❌ NetworkManager: WiFi reconnection failed - max retries reached");
                }
            }
            break;
            
        case WIFI_FAILED:
            // Reset retry count after a longer delay
            if (now - _wifi_last_attempt > 300000) { // 5 minutes
                _wifi_retry_count = 0;
                setWiFiState(WIFI_RECONNECTING);
                DEBUG_PRINTLN("🔄 NetworkManager: Resetting WiFi after extended failure");
            }
            break;
            
        default:
            break;
    }
}

void NetworkManager::updateMQTT() {
    unsigned long now = millis();
    
    if (!isWiFiConnected()) {
        if (_mqtt_state != MQTT_IDLE) {
            setMQTTState(MQTT_IDLE);
        }
        return;
    }
    
    switch (_mqtt_state) {
        case MQTT_CONNECTING:
            if (_mqtt_client->connected()) {
                _mqtt_connect_time = now;
                _mqtt_retry_count = 0;
                setMQTTState(MQTT_CONNECTED);
                DEBUG_PRINTLN("✅ NetworkManager: MQTT connected!");
            } else if (now - _mqtt_last_attempt > _config.mqtt_timeout_ms) {
                _stats.mqtt_failures++;
                setMQTTState(MQTT_RECONNECTING, mapMQTTError(_mqtt_client->state()));
                DEBUG_PRINTF("❌ NetworkManager: MQTT connection timeout (state: %d)\n", _mqtt_client->state());
            }
            break;
            
        case MQTT_CONNECTED:
            if (!_mqtt_client->connected()) {
                _stats.mqtt_failures++;
                setMQTTState(MQTT_RECONNECTING);
                DEBUG_PRINTLN("⚠️ NetworkManager: MQTT connection lost");
            }
            break;
            
        case MQTT_RECONNECTING:
            if (isTimeToRetry(_mqtt_last_attempt, calculateBackoffDelay(_config.mqtt_retry_interval_ms, _mqtt_retry_count))) {
                if (_mqtt_retry_count < _config.mqtt_max_retries) {
                    _mqtt_retry_count++;
                    _stats.mqtt_reconnect_count++;
                    DEBUG_PRINTF("🔄 NetworkManager: MQTT reconnect attempt %d/%d\n", _mqtt_retry_count, _config.mqtt_max_retries);
                    startMQTTConnection();
                } else {
                    setMQTTState(MQTT_FAILED, ERROR_MQTT_SERVER_UNAVAILABLE);
                    DEBUG_PRINTLN("❌ NetworkManager: MQTT reconnection failed - max retries reached");
                }
            }
            break;
            
        case MQTT_FAILED:
            // Reset retry count after a longer delay
            if (now - _mqtt_last_attempt > 300000) { // 5 minutes
                _mqtt_retry_count = 0;
                setMQTTState(MQTT_RECONNECTING);
                DEBUG_PRINTLN("🔄 NetworkManager: Resetting MQTT after extended failure");
            }
            break;
            
        default:
            if (_mqtt_state == MQTT_IDLE && isWiFiConnected()) {
                connectMQTT();
            }
            break;
    }
}

bool NetworkManager::startWiFiConnection() {
    _wifi_last_attempt = millis();
    
    // Disconnect first if connected
    if (WiFi.isConnected()) {
        WiFi.disconnect();
        delay(100);
    }
    
    // Start connection
    WiFi.begin(_config.wifi_ssid, _config.wifi_password);
    setWiFiState(WIFI_CONNECTING);
    
    DEBUG_PRINTF("📡 NetworkManager: WiFi connection started (RSSI target: >%d dBm)\n", 
                _config.connection_quality_threshold);
    
    return true;
}

bool NetworkManager::startMQTTConnection() {
    _mqtt_last_attempt = millis();
    
    // Attempt connection with or without credentials
    bool connected = false;
    if (strlen(_config.mqtt_username) > 0) {
        connected = _mqtt_client->connect(_config.mqtt_client_id, _config.mqtt_username, _config.mqtt_password);
    } else {
        connected = _mqtt_client->connect(_config.mqtt_client_id);
    }
    
    if (connected) {
        setMQTTState(MQTT_CONNECTED);
        return true;
    } else {
        setMQTTState(MQTT_RECONNECTING, mapMQTTError(_mqtt_client->state()));
        return false;
    }
}

void NetworkManager::setWiFiState(WiFiState state, ConnectionError error) {
    if (_wifi_state != state) {
        WiFiState old_state = _wifi_state;
        _wifi_state = state;
        
        if (error != ERROR_NONE) {
            setError(error);
        }
        
        DEBUG_PRINTF("📡 NetworkManager: WiFi state: %s -> %s\n", 
                    getWiFiStateString(old_state).c_str(), 
                    getWiFiStateString(state).c_str());
        
        if (_wifi_callback) {
            _wifi_callback(state, error);
        }
    }
}

void NetworkManager::setMQTTState(MQTTState state, ConnectionError error) {
    if (_mqtt_state != state) {
        MQTTState old_state = _mqtt_state;
        _mqtt_state = state;
        
        if (error != ERROR_NONE) {
            setError(error);
        }
        
        DEBUG_PRINTF("📡 NetworkManager: MQTT state: %s -> %s\n", 
                    getMQTTStateString(old_state).c_str(), 
                    getMQTTStateString(state).c_str());
        
        if (_mqtt_callback) {
            _mqtt_callback(state, error);
        }
    }
}

// ================================
// UTILITY FUNCTIONS
// ================================

int NetworkManager::calculateBackoffDelay(int base_delay, int retry_count, int max_delay) {
    // Exponential backoff with jitter
    int delay = base_delay * (1 << min(retry_count, 6)); // Cap at 2^6 = 64x
    delay = min(delay, max_delay);
    
    // Add jitter (±10%)
    int jitter = (delay * 10) / 100;
    delay += random(-jitter, jitter + 1);
    
    return max(delay, base_delay);
}

bool NetworkManager::isTimeToRetry(unsigned long last_attempt, int interval) const {
    return (millis() - last_attempt) >= interval;
}

NetworkManager::ConnectionError NetworkManager::mapWiFiError(wl_status_t status) {
    switch (status) {
        case WL_NO_SSID_AVAIL:
            return ERROR_WIFI_NO_SSID_AVAIL;
        case WL_CONNECT_FAILED:
            return ERROR_WIFI_AUTH_FAIL;
        case WL_CONNECTION_LOST:
        case WL_DISCONNECTED:
            return ERROR_WIFI_CONNECT_FAIL;
        default:
            return ERROR_NETWORK_TIMEOUT;
    }
}

NetworkManager::ConnectionError NetworkManager::mapMQTTError(int mqtt_state) {
    switch (mqtt_state) {
        case -4: return ERROR_NETWORK_TIMEOUT;
        case -3: return ERROR_MQTT_SERVER_UNAVAILABLE;
        case -2: return ERROR_MQTT_CONNECTION_REFUSED;
        case 1: return ERROR_MQTT_PROTOCOL_VERSION;
        case 2: return ERROR_MQTT_CLIENT_ID_REJECTED;
        case 3: return ERROR_MQTT_SERVER_UNAVAILABLE;
        case 4: return ERROR_MQTT_BAD_CREDENTIALS;
        case 5: return ERROR_MQTT_NOT_AUTHORIZED;
        default: return ERROR_MQTT_CONNECTION_REFUSED;
    }
}

void NetworkManager::setError(ConnectionError error) {
    if (error != ERROR_NONE) {
        _last_error = error;
        DEBUG_PRINTF("❌ NetworkManager: Error set: %s\n", getErrorString(error).c_str());
    }
}

// ================================
// MQTT CALLBACK
// ================================

void NetworkManager::mqttCallback(char* topic, byte* payload, unsigned int length) {
    if (_instance && _instance->_message_callback) {
        _instance->_message_callback(topic, payload, length);
    }
}

// ================================
// STATISTICS AND DIAGNOSTICS
// ================================

void NetworkManager::updateStats() {
    unsigned long now = millis();
    
    _stats.total_uptime_ms = now;
    _stats.last_wifi_rssi = getWiFiRSSI();
    
    if (isWiFiConnected()) {
        _stats.wifi_uptime_ms += (now - _wifi_connect_time);
    }
    
    if (isMQTTConnected()) {
        _stats.mqtt_uptime_ms += (now - _mqtt_connect_time);
    }
}

void NetworkManager::resetStats() {
    memset(&_stats, 0, sizeof(_stats));
    _stats.last_wifi_rssi = -100;
}

void NetworkManager::printDiagnostics() const {
    DEBUG_PRINTLN("📊 NetworkManager Diagnostics:");
    DEBUG_PRINTF("   WiFi State: %s\n", getWiFiStateString(_wifi_state).c_str());
    DEBUG_PRINTF("   MQTT State: %s\n", getMQTTStateString(_mqtt_state).c_str());
    DEBUG_PRINTF("   WiFi RSSI: %d dBm\n", _stats.last_wifi_rssi);
    DEBUG_PRINTF("   Connection Quality: %d%%\n", getConnectionQuality());
    DEBUG_PRINTF("   WiFi Uptime: %lu ms\n", _stats.wifi_uptime_ms);
    DEBUG_PRINTF("   MQTT Uptime: %lu ms\n", _stats.mqtt_uptime_ms);
    DEBUG_PRINTF("   WiFi Reconnects: %u\n", _stats.wifi_reconnect_count);
    DEBUG_PRINTF("   MQTT Reconnects: %u\n", _stats.mqtt_reconnect_count);
    DEBUG_PRINTF("   Messages Sent: %u\n", _stats.messages_sent);
    DEBUG_PRINTF("   Messages Failed: %u\n", _stats.messages_failed);
    DEBUG_PRINTF("   Messages Queued: %d\n", _message_queue_size);
    DEBUG_PRINTF("   Last Error: %s\n", getErrorString(_last_error).c_str());
    DEBUG_PRINTF("   Free Heap: %u bytes\n", ESP.getFreeHeap());
}

// ================================
// WATCHDOG FUNCTIONS
// ================================

void NetworkManager::enableWatchdog(int timeout_seconds) {
    _watchdog_timeout_ms = timeout_seconds * 1000;
    _watchdog_enabled = true;
    _last_watchdog_feed = millis();
    
    // Initialize ESP32 watchdog
    esp_task_wdt_init(timeout_seconds, true);
    esp_task_wdt_add(NULL);
    
    DEBUG_PRINTF("🐕 NetworkManager: Watchdog enabled (%d seconds)\n", timeout_seconds);
}

void NetworkManager::feedWatchdog() {
    if (_watchdog_enabled) {
        esp_task_wdt_reset();
        _last_watchdog_feed = millis();
    }
}

bool NetworkManager::isSystemHealthy() const {
    if (!_watchdog_enabled) {
        return true;
    }
    
    unsigned long since_last_feed = millis() - _last_watchdog_feed;
    return since_last_feed < (_watchdog_timeout_ms / 2); // Healthy if fed within half timeout
}

// ================================
// UTILITY FUNCTIONS
// ================================

String getWiFiStateString(NetworkManager::WiFiState state) {
    switch (state) {
        case NetworkManager::WIFI_IDLE: return "IDLE";
        case NetworkManager::WIFI_CONNECTING: return "CONNECTING";
        case NetworkManager::WIFI_CONNECTED: return "CONNECTED";
        case NetworkManager::WIFI_RECONNECTING: return "RECONNECTING";
        case NetworkManager::WIFI_FAILED: return "FAILED";
        case NetworkManager::WIFI_DISABLED: return "DISABLED";
        default: return "UNKNOWN";
    }
}

String getMQTTStateString(NetworkManager::MQTTState state) {
    switch (state) {
        case NetworkManager::MQTT_IDLE: return "IDLE";
        case NetworkManager::MQTT_CONNECTING: return "CONNECTING";
        case NetworkManager::MQTT_CONNECTED: return "CONNECTED";
        case NetworkManager::MQTT_RECONNECTING: return "RECONNECTING";
        case NetworkManager::MQTT_FAILED: return "FAILED";
        case NetworkManager::MQTT_DISABLED: return "DISABLED";
        default: return "UNKNOWN";
    }
}

String getErrorString(NetworkManager::ConnectionError error) {
    switch (error) {
        case NetworkManager::ERROR_NONE: return "NONE";
        case NetworkManager::ERROR_WIFI_AUTH_FAIL: return "WIFI_AUTH_FAIL";
        case NetworkManager::ERROR_WIFI_NO_SSID_AVAIL: return "WIFI_NO_SSID_AVAIL";
        case NetworkManager::ERROR_WIFI_CONNECT_FAIL: return "WIFI_CONNECT_FAIL";
        case NetworkManager::ERROR_MQTT_CONNECTION_REFUSED: return "MQTT_CONNECTION_REFUSED";
        case NetworkManager::ERROR_MQTT_PROTOCOL_VERSION: return "MQTT_PROTOCOL_VERSION";
        case NetworkManager::ERROR_MQTT_CLIENT_ID_REJECTED: return "MQTT_CLIENT_ID_REJECTED";
        case NetworkManager::ERROR_MQTT_SERVER_UNAVAILABLE: return "MQTT_SERVER_UNAVAILABLE";
        case NetworkManager::ERROR_MQTT_BAD_CREDENTIALS: return "MQTT_BAD_CREDENTIALS";
        case NetworkManager::ERROR_MQTT_NOT_AUTHORIZED: return "MQTT_NOT_AUTHORIZED";
        case NetworkManager::ERROR_NETWORK_TIMEOUT: return "NETWORK_TIMEOUT";
        case NetworkManager::ERROR_MEMORY_ALLOCATION: return "MEMORY_ALLOCATION";
        case NetworkManager::ERROR_SYSTEM_OVERLOAD: return "SYSTEM_OVERLOAD";
        default: return "UNKNOWN";
    }
} 