/**
 * Security enhancements implementation for ConsultEase Faculty Desk Unit
 */

#include "security_enhancements.h"
#include <Preferences.h>
#include <esp_random.h>
#include <mbedtls/md.h>

// Static member definitions
uint8_t EncryptionManager::deviceKey[MAX_KEY_LENGTH];
uint8_t EncryptionManager::sessionKey[MAX_KEY_LENGTH];
bool EncryptionManager::keyInitialized = false;
mbedtls_aes_context EncryptionManager::aesContext;

uint8_t MessageAuthenticator::hmacKey[MAX_KEY_LENGTH];
bool MessageAuthenticator::keySet = false;

char DeviceAuthenticator::deviceId[64];
char DeviceAuthenticator::authToken[MAX_TOKEN_LENGTH];
unsigned long DeviceAuthenticator::tokenExpiry = 0;
bool DeviceAuthenticator::authenticated = false;

const char* SecureConfig::CONFIG_NAMESPACE = "secure_config";
bool SecureConfig::initialized = false;

unsigned long SecurityMonitor::lastSecurityCheck = 0;
int SecurityMonitor::failedAuthAttempts = 0;
int SecurityMonitor::suspiciousActivities = 0;
bool SecurityMonitor::securityBreach = false;

// Encryption Manager Implementation
void EncryptionManager::init() {
    mbedtls_aes_init(&aesContext);
    keyInitialized = false;
    
    // Generate device-specific key if not exists
    Preferences prefs;
    prefs.begin("security", false);
    
    if (!prefs.isKey("device_key")) {
        // Generate new device key
        generateRandomBytes(deviceKey, MAX_KEY_LENGTH);
        prefs.putBytes("device_key", deviceKey, MAX_KEY_LENGTH);
        Serial.println("Generated new device key");
    } else {
        // Load existing device key
        prefs.getBytes("device_key", deviceKey, MAX_KEY_LENGTH);
        Serial.println("Loaded existing device key");
    }
    
    prefs.end();
    keyInitialized = true;
    
    // Generate session key
    generateSessionKey();
}

void EncryptionManager::generateRandomBytes(uint8_t* buffer, size_t length) {
    for (size_t i = 0; i < length; i++) {
        buffer[i] = esp_random() & 0xFF;
    }
}

bool EncryptionManager::setDeviceKey(const char* password) {
    if (!password) return false;
    
    // Derive key from password using simple hash (in production, use PBKDF2)
    mbedtls_md_context_t ctx;
    mbedtls_md_init(&ctx);
    
    const mbedtls_md_info_t* info = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
    if (mbedtls_md_setup(&ctx, info, 0) != 0) {
        mbedtls_md_free(&ctx);
        return false;
    }
    
    mbedtls_md_starts(&ctx);
    mbedtls_md_update(&ctx, (const unsigned char*)password, strlen(password));
    mbedtls_md_finish(&ctx, deviceKey);
    mbedtls_md_free(&ctx);
    
    keyInitialized = true;
    return true;
}

bool EncryptionManager::generateSessionKey() {
    generateRandomBytes(sessionKey, MAX_KEY_LENGTH);
    Serial.println("Generated new session key");
    return true;
}

bool EncryptionManager::encryptData(const uint8_t* plaintext, size_t plaintextLen,
                                   uint8_t* ciphertext, size_t* ciphertextLen,
                                   const uint8_t* key) {
    if (!keyInitialized || !plaintext || !ciphertext || !ciphertextLen) {
        return false;
    }
    
    const uint8_t* useKey = key ? key : sessionKey;
    
    // Simple XOR encryption for demonstration (use AES in production)
    for (size_t i = 0; i < plaintextLen; i++) {
        ciphertext[i] = plaintext[i] ^ useKey[i % MAX_KEY_LENGTH];
    }
    
    *ciphertextLen = plaintextLen;
    return true;
}

bool EncryptionManager::decryptData(const uint8_t* ciphertext, size_t ciphertextLen,
                                   uint8_t* plaintext, size_t* plaintextLen,
                                   const uint8_t* key) {
    // XOR decryption is the same as encryption
    return encryptData(ciphertext, ciphertextLen, plaintext, plaintextLen, key);
}

bool EncryptionManager::encryptString(const char* plaintext, char* ciphertext, size_t ciphertextSize) {
    if (!plaintext || !ciphertext) return false;
    
    size_t plaintextLen = strlen(plaintext);
    uint8_t* tempCipher = (uint8_t*)malloc(plaintextLen);
    if (!tempCipher) return false;
    
    size_t cipherLen;
    bool result = encryptData((const uint8_t*)plaintext, plaintextLen, tempCipher, &cipherLen);
    
    if (result && cipherLen * 2 + 1 < ciphertextSize) {
        // Convert to hex string
        for (size_t i = 0; i < cipherLen; i++) {
            sprintf(ciphertext + i * 2, "%02x", tempCipher[i]);
        }
        ciphertext[cipherLen * 2] = '\0';
    } else {
        result = false;
    }
    
    free(tempCipher);
    return result;
}

bool EncryptionManager::decryptString(const char* ciphertext, char* plaintext, size_t plaintextSize) {
    if (!ciphertext || !plaintext) return false;
    
    size_t cipherLen = strlen(ciphertext) / 2;
    uint8_t* tempCipher = (uint8_t*)malloc(cipherLen);
    if (!tempCipher) return false;
    
    // Convert from hex string
    for (size_t i = 0; i < cipherLen; i++) {
        sscanf(ciphertext + i * 2, "%2hhx", &tempCipher[i]);
    }
    
    size_t plainLen;
    bool result = decryptData(tempCipher, cipherLen, (uint8_t*)plaintext, &plainLen);
    
    if (result && plainLen < plaintextSize) {
        plaintext[plainLen] = '\0';
    } else {
        result = false;
    }
    
    free(tempCipher);
    return result;
}

void EncryptionManager::rotateSessionKey() {
    generateSessionKey();
    Serial.println("Session key rotated");
}

void EncryptionManager::clearKeys() {
    memset(deviceKey, 0, MAX_KEY_LENGTH);
    memset(sessionKey, 0, MAX_KEY_LENGTH);
    keyInitialized = false;
    Serial.println("Encryption keys cleared");
}

// Message Authenticator Implementation
void MessageAuthenticator::init() {
    keySet = false;
    memset(hmacKey, 0, MAX_KEY_LENGTH);
}

bool MessageAuthenticator::setKey(const uint8_t* key, size_t keyLength) {
    if (!key || keyLength == 0) return false;
    
    size_t copyLen = keyLength < MAX_KEY_LENGTH ? keyLength : MAX_KEY_LENGTH;
    memcpy(hmacKey, key, copyLen);
    keySet = true;
    
    Serial.println("HMAC key set");
    return true;
}

bool MessageAuthenticator::generateHMAC(const uint8_t* data, size_t dataLength, 
                                       uint8_t* hmac, size_t hmacSize) {
    if (!keySet || !data || !hmac || hmacSize < MAX_HASH_LENGTH) {
        return false;
    }
    
    // Simple hash-based MAC (use proper HMAC in production)
    mbedtls_md_context_t ctx;
    mbedtls_md_init(&ctx);
    
    const mbedtls_md_info_t* info = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
    if (mbedtls_md_setup(&ctx, info, 1) != 0) {
        mbedtls_md_free(&ctx);
        return false;
    }
    
    mbedtls_md_hmac_starts(&ctx, hmacKey, MAX_KEY_LENGTH);
    mbedtls_md_hmac_update(&ctx, data, dataLength);
    mbedtls_md_hmac_finish(&ctx, hmac);
    mbedtls_md_free(&ctx);
    
    return true;
}

bool MessageAuthenticator::verifyHMAC(const uint8_t* data, size_t dataLength,
                                     const uint8_t* expectedHmac, size_t hmacLength) {
    if (hmacLength != MAX_HASH_LENGTH) return false;
    
    uint8_t calculatedHmac[MAX_HASH_LENGTH];
    if (!generateHMAC(data, dataLength, calculatedHmac, MAX_HASH_LENGTH)) {
        return false;
    }
    
    // Constant-time comparison
    int result = 0;
    for (size_t i = 0; i < MAX_HASH_LENGTH; i++) {
        result |= calculatedHmac[i] ^ expectedHmac[i];
    }
    
    return result == 0;
}

bool MessageAuthenticator::signMessage(const char* message, char* signature, size_t signatureSize) {
    if (!message || !signature || signatureSize < SIGNATURE_LENGTH * 2 + 1) {
        return false;
    }
    
    uint8_t hmac[MAX_HASH_LENGTH];
    if (!generateHMAC((const uint8_t*)message, strlen(message), hmac, MAX_HASH_LENGTH)) {
        return false;
    }
    
    // Convert to hex string
    for (int i = 0; i < SIGNATURE_LENGTH; i++) {
        sprintf(signature + i * 2, "%02x", hmac[i]);
    }
    signature[SIGNATURE_LENGTH * 2] = '\0';
    
    return true;
}

bool MessageAuthenticator::verifyMessage(const char* message, const char* signature) {
    if (!message || !signature) return false;
    
    // Convert signature from hex
    uint8_t expectedHmac[SIGNATURE_LENGTH];
    for (int i = 0; i < SIGNATURE_LENGTH; i++) {
        sscanf(signature + i * 2, "%2hhx", &expectedHmac[i]);
    }
    
    return verifyHMAC((const uint8_t*)message, strlen(message), expectedHmac, SIGNATURE_LENGTH);
}

// Device Authenticator Implementation
void DeviceAuthenticator::init() {
    authenticated = false;
    tokenExpiry = 0;
    
    // Generate device ID if not exists
    Preferences prefs;
    prefs.begin("auth", false);
    
    if (!prefs.isKey("device_id")) {
        generateDeviceId();
        prefs.putString("device_id", deviceId);
    } else {
        String storedId = prefs.getString("device_id", "");
        strncpy(deviceId, storedId.c_str(), sizeof(deviceId) - 1);
        deviceId[sizeof(deviceId) - 1] = '\0';
    }
    
    prefs.end();
    
    Serial.printf("Device ID: %s\n", deviceId);
}

bool DeviceAuthenticator::generateDeviceId() {
    // Generate device ID based on MAC address and random data
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    
    uint32_t random = esp_random();
    
    snprintf(deviceId, sizeof(deviceId), "FDU_%02X%02X%02X%02X%02X%02X_%08X",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5], random);
    
    return true;
}

bool DeviceAuthenticator::authenticate(const char* username, const char* password) {
    if (!username || !password) return false;
    
    // Simple authentication (implement proper authentication in production)
    if (strcmp(username, "faculty") == 0 && strcmp(password, "secure123") == 0) {
        // Generate auth token
        uint32_t random1 = esp_random();
        uint32_t random2 = esp_random();
        snprintf(authToken, sizeof(authToken), "%08X%08X", random1, random2);
        
        tokenExpiry = millis() + 3600000; // 1 hour
        authenticated = true;
        
        Serial.println("Authentication successful");
        return true;
    }
    
    SecurityMonitor::recordFailedAuth();
    Serial.println("Authentication failed");
    return false;
}

bool DeviceAuthenticator::refreshToken() {
    if (!authenticated) return false;
    
    // Generate new token
    uint32_t random1 = esp_random();
    uint32_t random2 = esp_random();
    snprintf(authToken, sizeof(authToken), "%08X%08X", random1, random2);
    
    tokenExpiry = millis() + 3600000; // 1 hour
    
    Serial.println("Auth token refreshed");
    return true;
}

bool DeviceAuthenticator::isAuthenticated() {
    if (!authenticated) return false;
    
    if (millis() > tokenExpiry) {
        authenticated = false;
        Serial.println("Auth token expired");
        return false;
    }
    
    return true;
}

const char* DeviceAuthenticator::getDeviceId() {
    return deviceId;
}

const char* DeviceAuthenticator::getAuthToken() {
    return isAuthenticated() ? authToken : nullptr;
}

void DeviceAuthenticator::logout() {
    authenticated = false;
    tokenExpiry = 0;
    memset(authToken, 0, sizeof(authToken));
    Serial.println("Logged out");
}

unsigned long DeviceAuthenticator::getTokenTimeRemaining() {
    if (!authenticated || millis() > tokenExpiry) return 0;
    return tokenExpiry - millis();
}

// Security Monitor Implementation
void SecurityMonitor::init() {
    lastSecurityCheck = millis();
    failedAuthAttempts = 0;
    suspiciousActivities = 0;
    securityBreach = false;
    
    Serial.println("Security Monitor initialized");
}

void SecurityMonitor::recordFailedAuth() {
    failedAuthAttempts++;
    logSecurityEvent("Failed authentication attempt");
    
    if (failedAuthAttempts >= 5) {
        securityBreach = true;
        logSecurityEvent("SECURITY BREACH: Multiple failed auth attempts");
    }
}

void SecurityMonitor::recordSuspiciousActivity(const char* description) {
    suspiciousActivities++;
    
    char logMessage[128];
    snprintf(logMessage, sizeof(logMessage), "Suspicious activity: %s", description);
    logSecurityEvent(logMessage);
    
    if (suspiciousActivities >= 3) {
        securityBreach = true;
        logSecurityEvent("SECURITY BREACH: Multiple suspicious activities");
    }
}

void SecurityMonitor::checkSecurityStatus() {
    unsigned long currentTime = millis();
    
    // Reset counters every hour
    if (currentTime - lastSecurityCheck > 3600000) {
        resetSecurityCounters();
        lastSecurityCheck = currentTime;
    }
    
    // Check for security breaches
    if (securityBreach) {
        Serial.println("SECURITY ALERT: Breach detected!");
        // Implement security response (e.g., disable features, alert admin)
    }
}

bool SecurityMonitor::isSecurityBreached() {
    return securityBreach;
}

void SecurityMonitor::resetSecurityCounters() {
    failedAuthAttempts = 0;
    suspiciousActivities = 0;
    securityBreach = false;
    Serial.println("Security counters reset");
}

void SecurityMonitor::logSecurityEvent(const char* event) {
    Serial.printf("[SECURITY] %lu: %s\n", millis(), event);
    
    // In production, also log to secure storage or send to server
}

// Security utility functions
namespace SecurityUtils {
    uint32_t generateSecureRandom() {
        return esp_random();
    }
    
    void generateSecureRandomBytes(uint8_t* buffer, size_t length) {
        for (size_t i = 0; i < length; i++) {
            buffer[i] = esp_random() & 0xFF;
        }
    }
    
    bool sha256Hash(const uint8_t* data, size_t dataLength, uint8_t* hash) {
        mbedtls_md_context_t ctx;
        mbedtls_md_init(&ctx);
        
        const mbedtls_md_info_t* info = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
        if (mbedtls_md_setup(&ctx, info, 0) != 0) {
            mbedtls_md_free(&ctx);
            return false;
        }
        
        mbedtls_md_starts(&ctx);
        mbedtls_md_update(&ctx, data, dataLength);
        mbedtls_md_finish(&ctx, hash);
        mbedtls_md_free(&ctx);
        
        return true;
    }
    
    bool validateMQTTTopic(const char* topic) {
        if (!topic) return false;
        
        // Check for valid topic format
        if (strstr(topic, "consultease/") != topic) return false;
        
        // Check for injection attempts
        if (strstr(topic, "../") || strstr(topic, "..\\")) return false;
        
        return true;
    }
    
    bool validateMQTTPayload(const char* payload, size_t maxLength) {
        if (!payload) return false;
        
        size_t length = strlen(payload);
        if (length > maxLength) return false;
        
        // Check for suspicious patterns
        if (strstr(payload, "<script>") || strstr(payload, "javascript:")) return false;
        
        return true;
    }
    
    void secureMemset(void* ptr, int value, size_t length) {
        volatile uint8_t* p = (volatile uint8_t*)ptr;
        for (size_t i = 0; i < length; i++) {
            p[i] = value;
        }
    }
}

// Print security status
void printSecurityStatus() {
    Serial.println("=== Security Status ===");
    Serial.printf("Authenticated: %s\n", DeviceAuthenticator::isAuthenticated() ? "Yes" : "No");
    Serial.printf("Device ID: %s\n", DeviceAuthenticator::getDeviceId());
    Serial.printf("Token Time Remaining: %lu ms\n", DeviceAuthenticator::getTokenTimeRemaining());
    Serial.printf("Security Breach: %s\n", SecurityMonitor::isSecurityBreached() ? "Yes" : "No");
    Serial.printf("Failed Auth Attempts: %d\n", SecurityMonitor::failedAuthAttempts);
    Serial.printf("Suspicious Activities: %d\n", SecurityMonitor::suspiciousActivities);
    Serial.println("======================");
}
