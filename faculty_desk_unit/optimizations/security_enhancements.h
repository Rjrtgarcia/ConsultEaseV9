/**
 * Security enhancements for ConsultEase Faculty Desk Unit
 * Implements encryption, authentication, and secure communication
 */

#ifndef SECURITY_ENHANCEMENTS_H
#define SECURITY_ENHANCEMENTS_H

#include <Arduino.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <mbedtls/aes.h>
#include <mbedtls/sha256.h>
#include <esp_random.h>

// Security configuration
#define MAX_KEY_LENGTH 32
#define MAX_IV_LENGTH 16
#define MAX_HASH_LENGTH 32
#define MAX_TOKEN_LENGTH 64
#define NONCE_LENGTH 16
#define SIGNATURE_LENGTH 32

// Security levels
enum SecurityLevel {
    SECURITY_NONE,
    SECURITY_BASIC,
    SECURITY_ENHANCED,
    SECURITY_MAXIMUM
};

// Encryption utilities
class EncryptionManager {
private:
    static uint8_t deviceKey[MAX_KEY_LENGTH];
    static uint8_t sessionKey[MAX_KEY_LENGTH];
    static bool keyInitialized;
    static mbedtls_aes_context aesContext;
    
    static void generateRandomBytes(uint8_t* buffer, size_t length);
    static bool deriveKey(const char* password, const uint8_t* salt, uint8_t* key);
    
public:
    static void init();
    static bool setDeviceKey(const char* password);
    static bool generateSessionKey();
    
    // AES encryption/decryption
    static bool encryptData(const uint8_t* plaintext, size_t plaintextLen,
                           uint8_t* ciphertext, size_t* ciphertextLen,
                           const uint8_t* key = nullptr);
    static bool decryptData(const uint8_t* ciphertext, size_t ciphertextLen,
                           uint8_t* plaintext, size_t* plaintextLen,
                           const uint8_t* key = nullptr);
    
    // String encryption helpers
    static bool encryptString(const char* plaintext, char* ciphertext, size_t ciphertextSize);
    static bool decryptString(const char* ciphertext, char* plaintext, size_t plaintextSize);
    
    // Key management
    static void rotateSessionKey();
    static bool exportPublicKey(char* publicKey, size_t keySize);
    static void clearKeys();
};

// Message authentication
class MessageAuthenticator {
private:
    static uint8_t hmacKey[MAX_KEY_LENGTH];
    static bool keySet;
    
public:
    static void init();
    static bool setKey(const uint8_t* key, size_t keyLength);
    static bool generateHMAC(const uint8_t* data, size_t dataLength, 
                            uint8_t* hmac, size_t hmacSize);
    static bool verifyHMAC(const uint8_t* data, size_t dataLength,
                          const uint8_t* expectedHmac, size_t hmacLength);
    static bool signMessage(const char* message, char* signature, size_t signatureSize);
    static bool verifyMessage(const char* message, const char* signature);
};

// Secure MQTT client
class SecureMQTTClient {
private:
    WiFiClientSecure wifiClient;
    PubSubClient mqttClient;
    char clientCertificate[2048];
    char clientPrivateKey[2048];
    char caCertificate[2048];
    bool tlsEnabled;
    SecurityLevel securityLevel;
    
    bool loadCertificates();
    bool validateServerCertificate();
    bool performMutualAuthentication();
    
public:
    SecureMQTTClient();
    
    // Configuration
    void setSecurityLevel(SecurityLevel level);
    bool setCertificates(const char* cert, const char* key, const char* ca);
    void enableTLS(bool enable);
    
    // Connection management
    bool connect(const char* server, int port, const char* clientId,
                const char* username = nullptr, const char* password = nullptr);
    void disconnect();
    bool isConnected();
    
    // Secure messaging
    bool publishSecure(const char* topic, const char* payload, bool encrypt = true);
    bool subscribeSecure(const char* topic);
    void setSecureCallback(void (*callback)(char*, uint8_t*, unsigned int));
    
    // Maintenance
    void loop();
    bool reconnect();
};

// Device authentication
class DeviceAuthenticator {
private:
    static char deviceId[64];
    static char authToken[MAX_TOKEN_LENGTH];
    static unsigned long tokenExpiry;
    static bool authenticated;
    
    static bool generateDeviceId();
    static bool requestAuthToken();
    static bool validateAuthToken();
    
public:
    static void init();
    static bool authenticate(const char* username, const char* password);
    static bool refreshToken();
    static bool isAuthenticated();
    static const char* getDeviceId();
    static const char* getAuthToken();
    static void logout();
    static unsigned long getTokenTimeRemaining();
};

// Secure configuration storage
class SecureConfig {
private:
    static const char* CONFIG_NAMESPACE;
    static bool initialized;
    
    static bool encryptValue(const char* value, char* encrypted, size_t encryptedSize);
    static bool decryptValue(const char* encrypted, char* value, size_t valueSize);
    
public:
    static void init();
    static bool setString(const char* key, const char* value, bool encrypt = true);
    static bool getString(const char* key, char* value, size_t valueSize, bool decrypt = true);
    static bool setBlob(const char* key, const uint8_t* data, size_t dataSize, bool encrypt = true);
    static bool getBlob(const char* key, uint8_t* data, size_t* dataSize, bool decrypt = true);
    static bool remove(const char* key);
    static void clear();
    static bool exists(const char* key);
};

// Security monitoring
class SecurityMonitor {
private:
    static unsigned long lastSecurityCheck;
    static int failedAuthAttempts;
    static int suspiciousActivities;
    static bool securityBreach;
    
public:
    static void init();
    static void recordFailedAuth();
    static void recordSuspiciousActivity(const char* description);
    static void checkSecurityStatus();
    static bool isSecurityBreached();
    static void resetSecurityCounters();
    static void enableSecurityMode();
    static void disableSecurityMode();
    static void logSecurityEvent(const char* event);
};

// Firmware integrity verification
class FirmwareVerifier {
private:
    static uint8_t firmwareHash[MAX_HASH_LENGTH];
    static bool hashCalculated;
    
public:
    static void init();
    static bool calculateFirmwareHash();
    static bool verifyFirmwareIntegrity();
    static bool verifyUpdate(const uint8_t* updateData, size_t updateSize);
    static void storeFirmwareHash();
    static bool loadFirmwareHash();
};

// Anti-tampering measures
class AntiTamper {
private:
    static bool tamperDetected;
    static unsigned long lastTamperCheck;
    
public:
    static void init();
    static void checkTamperStatus();
    static bool isTampered();
    static void enableTamperProtection();
    static void disableTamperProtection();
    static void handleTamperDetection();
};

// Security utility functions
namespace SecurityUtils {
    // Random number generation
    uint32_t generateSecureRandom();
    void generateSecureRandomBytes(uint8_t* buffer, size_t length);
    
    // Hash functions
    bool sha256Hash(const uint8_t* data, size_t dataLength, uint8_t* hash);
    bool sha256HashString(const char* data, char* hashHex, size_t hashHexSize);
    
    // Time-based security
    bool isTimeValid();
    unsigned long getSecureTimestamp();
    bool validateTimestamp(unsigned long timestamp, unsigned long tolerance);
    
    // Input validation
    bool validateMQTTTopic(const char* topic);
    bool validateMQTTPayload(const char* payload, size_t maxLength);
    bool sanitizeInput(const char* input, char* output, size_t outputSize);
    
    // Memory protection
    void secureMemset(void* ptr, int value, size_t length);
    void secureMemcpy(void* dest, const void* src, size_t length);
}

// Security configuration macros
#define ENABLE_ENCRYPTION
#define ENABLE_MESSAGE_AUTHENTICATION
#define ENABLE_TLS
#define ENABLE_DEVICE_AUTHENTICATION
#define ENABLE_FIRMWARE_VERIFICATION
#define ENABLE_ANTI_TAMPER

// Security check macros
#define SECURITY_CHECK_AUTH() DeviceAuthenticator::isAuthenticated()
#define SECURITY_CHECK_TAMPER() (!AntiTamper::isTampered())
#define SECURITY_CHECK_INTEGRITY() FirmwareVerifier::verifyFirmwareIntegrity()

#endif // SECURITY_ENHANCEMENTS_H
