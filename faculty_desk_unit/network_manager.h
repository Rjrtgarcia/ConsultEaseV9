#ifndef NETWORK_MANAGER_H
#define NETWORK_MANAGER_H

#include <WiFi.h>
#include <PubSubClient.h>
#include <esp_wifi.h>
#include <esp_system.h>
#include <esp_task_wdt.h>

// ================================
// NETWORK MANAGER - ROBUST CONNECTIVITY
// ================================
// This class provides enterprise-grade WiFi and MQTT connectivity
// with comprehensive error handling and automatic recovery

class NetworkManager {
public:
    // Connection states
    enum WiFiState {
        WIFI_IDLE,
        WIFI_CONNECTING,
        WIFI_CONNECTED,
        WIFI_RECONNECTING,
        WIFI_FAILED,
        WIFI_DISABLED
    };

    enum MQTTState {
        MQTT_IDLE,
        MQTT_CONNECTING,
        MQTT_CONNECTED,
        MQTT_RECONNECTING,
        MQTT_FAILED,
        MQTT_DISABLED
    };

    // Error types
    enum ConnectionError {
        ERROR_NONE,
        ERROR_WIFI_AUTH_FAIL,
        ERROR_WIFI_NO_SSID_AVAIL,
        ERROR_WIFI_CONNECT_FAIL,
        ERROR_MQTT_CONNECTION_REFUSED,
        ERROR_MQTT_PROTOCOL_VERSION,
        ERROR_MQTT_CLIENT_ID_REJECTED,
        ERROR_MQTT_SERVER_UNAVAILABLE,
        ERROR_MQTT_BAD_CREDENTIALS,
        ERROR_MQTT_NOT_AUTHORIZED,
        ERROR_NETWORK_TIMEOUT,
        ERROR_MEMORY_ALLOCATION,
        ERROR_SYSTEM_OVERLOAD
    };

    // Configuration structure
    struct NetworkConfig {
        // WiFi settings
        const char* wifi_ssid;
        const char* wifi_password;
        int wifi_timeout_ms;
        int wifi_retry_interval_ms;
        int wifi_max_retries;
        bool wifi_power_save_enabled;
        
        // MQTT settings
        const char* mqtt_server;
        int mqtt_port;
        const char* mqtt_username;
        const char* mqtt_password;
        const char* mqtt_client_id;
        int mqtt_keepalive;
        int mqtt_timeout_ms;
        int mqtt_retry_interval_ms;
        int mqtt_max_retries;
        int mqtt_buffer_size;
        
        // Advanced settings
        bool enable_diagnostics;
        bool enable_watchdog;
        int health_check_interval_ms;
        int connection_quality_threshold;
    };

    // Statistics structure
    struct ConnectionStats {
        unsigned long wifi_uptime_ms;
        unsigned long mqtt_uptime_ms;
        uint32_t wifi_reconnect_count;
        uint32_t mqtt_reconnect_count;
        uint32_t wifi_failures;
        uint32_t mqtt_failures;
        int8_t last_wifi_rssi;
        unsigned long last_connection_time;
        unsigned long total_uptime_ms;
        uint32_t messages_sent;
        uint32_t messages_failed;
        uint32_t messages_queued;
    };

    // Callback function types
    typedef void (*WiFiEventCallback)(WiFiState state, ConnectionError error);
    typedef void (*MQTTEventCallback)(MQTTState state, ConnectionError error);
    typedef void (*MessageCallback)(char* topic, byte* payload, unsigned int length);
    typedef void (*DiagnosticsCallback)(const ConnectionStats& stats);

    // Constructor & Destructor
    NetworkManager();
    ~NetworkManager();

    // Initialization
    bool begin(const NetworkConfig& config);
    void end();

    // Callback registration
    void setWiFiEventCallback(WiFiEventCallback callback);
    void setMQTTEventCallback(MQTTEventCallback callback);
    void setMessageCallback(MessageCallback callback);
    void setDiagnosticsCallback(DiagnosticsCallback callback);

    // Connection management
    bool connectWiFi();
    bool connectMQTT();
    void disconnect();
    void reset();

    // State queries
    WiFiState getWiFiState() const { return _wifi_state; }
    MQTTState getMQTTState() const { return _mqtt_state; }
    bool isWiFiConnected() const { return _wifi_state == WIFI_CONNECTED; }
    bool isMQTTConnected() const { return _mqtt_state == MQTT_CONNECTED; }
    bool isFullyConnected() const { return isWiFiConnected() && isMQTTConnected(); }

    // Connection quality
    int getWiFiRSSI() const;
    int getConnectionQuality() const;
    ConnectionError getLastError() const { return _last_error; }

    // MQTT operations
    bool publish(const char* topic, const char* payload, bool retained = false, int qos = 0);
    bool subscribe(const char* topic, int qos = 0);
    bool unsubscribe(const char* topic);

    // Message queue management
    bool queueMessage(const char* topic, const char* payload, bool retained = false, int qos = 0);
    void processMessageQueue();
    int getQueueSize() const { return _message_queue_size; }

    // Diagnostics and statistics
    ConnectionStats getStats() const { return _stats; }
    void resetStats();
    void printDiagnostics() const;

    // Main update function - call frequently
    void update();

    // System health
    void enableWatchdog(int timeout_seconds);
    void feedWatchdog();
    bool isSystemHealthy() const;

private:
    // Configuration
    NetworkConfig _config;
    
    // State management
    WiFiState _wifi_state;
    MQTTState _mqtt_state;
    ConnectionError _last_error;
    
    // Network objects
    WiFiClient _wifi_client;
    PubSubClient* _mqtt_client;
    
    // Timing and retry logic
    unsigned long _wifi_last_attempt;
    unsigned long _mqtt_last_attempt;
    unsigned long _last_health_check;
    unsigned long _connection_start_time;
    int _wifi_retry_count;
    int _mqtt_retry_count;
    
    // Exponential backoff
    int calculateBackoffDelay(int base_delay, int retry_count, int max_delay = 60000);
    
    // Statistics
    ConnectionStats _stats;
    unsigned long _wifi_connect_time;
    unsigned long _mqtt_connect_time;
    
    // Message queue
    struct QueuedMessage {
        char topic[128];
        char payload[512];
        bool retained;
        int qos;
        unsigned long timestamp;
        int retry_count;
    };
    static const int MAX_QUEUE_SIZE = 10;
    QueuedMessage _message_queue[MAX_QUEUE_SIZE];
    int _message_queue_size;
    
    // Callbacks
    WiFiEventCallback _wifi_callback;
    MQTTEventCallback _mqtt_callback;
    MessageCallback _message_callback;
    DiagnosticsCallback _diagnostics_callback;
    
    // Watchdog
    bool _watchdog_enabled;
    unsigned long _last_watchdog_feed;
    int _watchdog_timeout_ms;
    
    // Internal methods
    void updateWiFi();
    void updateMQTT();
    void updateHealthCheck();
    void updateStats();
    
    // WiFi management
    bool startWiFiConnection();
    void handleWiFiEvent();
    void setWiFiState(WiFiState state, ConnectionError error = ERROR_NONE);
    
    // MQTT management
    bool startMQTTConnection();
    void handleMQTTEvent();
    void setMQTTState(MQTTState state, ConnectionError error = ERROR_NONE);
    static void mqttCallback(char* topic, byte* payload, unsigned int length);
    
    // Error handling
    void setError(ConnectionError error);
    ConnectionError mapWiFiError(wl_status_t status);
    ConnectionError mapMQTTError(int mqtt_state);
    
    // Utilities
    void logDebug(const char* message) const;
    void logError(const char* message) const;
    bool isTimeToRetry(unsigned long last_attempt, int interval) const;
    
    // Static instance for callbacks
    static NetworkManager* _instance;
};

// Global utility functions
String getWiFiStateString(NetworkManager::WiFiState state);
String getMQTTStateString(NetworkManager::MQTTState state);
String getErrorString(NetworkManager::ConnectionError error);

#endif // NETWORK_MANAGER_H 