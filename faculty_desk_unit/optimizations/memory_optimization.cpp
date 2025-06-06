/**
 * Memory optimization implementation for ConsultEase Faculty Desk Unit
 */

#include "memory_optimization.h"
#include <string.h>
#include <stdlib.h>

// Global instances
OptimizedStringHandler globalStringHandler;
char mqttTopicBuffer[64];
char timeBuffer[32];
char dateBuffer[32];

// Static member definitions
unsigned long MemoryMonitor::lastCheck = 0;
size_t MemoryMonitor::minFreeHeap = 0;
char DisplayBuffer::displayBuffer[DISPLAY_BUFFER_SIZE];
bool DisplayBuffer::bufferDirty = false;

// Optimized message processing function
void optimizedDisplayMessage(const char* message) {
    if (!message) return;

    // Use global string handler to avoid memory allocation
    globalStringHandler.reset();

    // Process message with word wrapping
    const char* ptr = message;
    int lineWidth = 35; // Approximate characters per line
    int currentLineLength = 0;

    while (*ptr) {
        char c = *ptr;

        if (c == '\n' || currentLineLength >= lineWidth) {
            globalStringHandler.append('\n');
            currentLineLength = 0;

            // Skip the newline if it was a forced wrap
            if (c != '\n') {
                globalStringHandler.append(c);
                currentLineLength = 1;
            }
        } else {
            globalStringHandler.append(c);
            currentLineLength++;
        }

        ptr++;
    }

    // Display the processed message
    Serial.println("Optimized Message Display:");
    Serial.println(globalStringHandler.getString());
}

// Optimized message processing function
void optimizedProcessMessage(const char* input, char* output, size_t outputSize) {
    if (!input || !output || outputSize == 0) return;

    globalStringHandler.reset();

    // Check if JSON format
    if (input[0] == '{') {
        // Extract message field from JSON
        const char* messageStart = strstr(input, "\"message\":\"");
        if (messageStart) {
            messageStart += 11; // Skip "message":"
            const char* messageEnd = strchr(messageStart, '"');
            if (messageEnd) {
                size_t messageLen = messageEnd - messageStart;
                if (messageLen < MAX_MESSAGE_LENGTH - 1) {
                    strncpy(output, messageStart, messageLen);
                    output[messageLen] = '\0';
                    return;
                }
            }
        }

        // Try to extract other fields
        const char* fields[] = {"student_name", "course_code", "request_message"};
        for (int i = 0; i < 3; i++) {
            char searchStr[32];
            snprintf(searchStr, sizeof(searchStr), "\"%s\":\"", fields[i]);

            const char* fieldStart = strstr(input, searchStr);
            if (fieldStart) {
                fieldStart += strlen(searchStr);
                const char* fieldEnd = strchr(fieldStart, '"');
                if (fieldEnd) {
                    size_t fieldLen = fieldEnd - fieldStart;
                    if (fieldLen > 0 && globalStringHandler.length() + fieldLen + 20 < MAX_MESSAGE_LENGTH) {
                        if (i == 0) globalStringHandler.append("Student: ");
                        else if (i == 1) globalStringHandler.append("Course: ");
                        else globalStringHandler.append("Request: ");

                        // Append field value
                        for (size_t j = 0; j < fieldLen; j++) {
                            globalStringHandler.append(fieldStart[j]);
                        }
                        globalStringHandler.append('\n');
                    }
                }
            }
        }

        SAFE_STRING_COPY(output, globalStringHandler.getString(), outputSize);
    } else {
        // Plain text message
        SAFE_STRING_COPY(output, input, outputSize);
    }
}

// Optimized JSON field extraction
bool optimizedJSONExtract(const char* json, const char* key, char* value, size_t valueSize) {
    if (!json || !key || !value || valueSize == 0) return false;

    // Create search pattern
    char searchPattern[64];
    snprintf(searchPattern, sizeof(searchPattern), "\"%s\":\"", key);

    const char* start = strstr(json, searchPattern);
    if (!start) return false;

    start += strlen(searchPattern);
    const char* end = strchr(start, '"');
    if (!end) return false;

    size_t length = end - start;
    if (length >= valueSize) length = valueSize - 1;

    strncpy(value, start, length);
    value[length] = '\0';

    return true;
}

// Memory monitoring functions
void MemoryMonitor::init() {
    lastCheck = millis();
    minFreeHeap = ESP.getFreeHeap();
    Serial.printf("Memory Monitor initialized - Free: %d bytes\n", minFreeHeap);
}

void MemoryMonitor::checkMemory() {
    size_t currentFree = ESP.getFreeHeap();
    size_t currentTime = millis();

    // Update minimum free heap tracking
    if (currentFree < minFreeHeap) {
        minFreeHeap = currentFree;
    }

    // Proactive memory leak detection
    detectMemoryLeaks(currentFree, currentTime);

    // Proactive memory management based on usage patterns
    performProactiveCleanup(currentFree, currentTime);

    // Log memory status every 30 seconds
    if (currentTime - lastCheck > 30000) {
        logMemoryStatus(currentFree, currentTime);
        lastCheck = currentTime;
    }

    // Emergency memory management
    handleCriticalMemory(currentFree);
}

void MemoryMonitor::detectMemoryLeaks(size_t currentFree, unsigned long currentTime) {
    // Track memory usage over time for leak detection
    static size_t memoryHistory[MEMORY_HISTORY_SIZE] = {0};
    static int historyIndex = 0;
    static unsigned long lastLeakCheck = 0;

    // Update memory history every 5 seconds
    if (currentTime - lastLeakCheck > 5000) {
        memoryHistory[historyIndex] = currentFree;
        historyIndex = (historyIndex + 1) % MEMORY_HISTORY_SIZE;
        lastLeakCheck = currentTime;

        // Analyze trend if we have enough data
        if (historyIndex == 0) { // We've filled the circular buffer
            analyzeMemoryTrend(memoryHistory);
        }
    }
}

void MemoryMonitor::analyzeMemoryTrend(size_t* history) {
    // Calculate average memory usage and trend
    size_t sum = 0;
    size_t min_val = history[0];
    size_t max_val = history[0];

    for (int i = 0; i < MEMORY_HISTORY_SIZE; i++) {
        sum += history[i];
        if (history[i] < min_val) min_val = history[i];
        if (history[i] > max_val) max_val = history[i];
    }

    size_t average = sum / MEMORY_HISTORY_SIZE;
    size_t variance = max_val - min_val;

    // Detect potential memory leak (consistent downward trend)
    bool possibleLeak = true;
    for (int i = 1; i < MEMORY_HISTORY_SIZE; i++) {
        if (history[i] > history[i-1] + 500) { // Allow for 500 byte fluctuation
            possibleLeak = false;
            break;
        }
    }

    if (possibleLeak && variance > 2000) {
        Serial.printf("WARNING: Possible memory leak detected! Variance: %d bytes\n", variance);
        Serial.printf("Memory trend: %d -> %d bytes over %d samples\n",
                     history[0], history[MEMORY_HISTORY_SIZE-1], MEMORY_HISTORY_SIZE);

        // Force aggressive cleanup
        performAggressiveCleanup();
    }

    Serial.printf("Memory analysis - Avg: %d, Min: %d, Max: %d, Variance: %d\n",
                 average, min_val, max_val, variance);
}

void MemoryMonitor::performProactiveCleanup(size_t currentFree, unsigned long currentTime) {
    static unsigned long lastProactiveCleanup = 0;

    // Perform proactive cleanup every 2 minutes or when memory drops below threshold
    bool timeForCleanup = (currentTime - lastProactiveCleanup > 120000);
    bool memoryPressure = (currentFree < 15000); // 15KB threshold

    if (timeForCleanup || memoryPressure) {
        Serial.println("Performing proactive memory cleanup...");

        // Clean up display buffers
        cleanupDisplayBuffers();

        // Clean up string buffers
        cleanupStringBuffers();

        // Force WiFi cleanup if needed
        if (memoryPressure) {
            cleanupNetworkBuffers();
        }

        lastProactiveCleanup = currentTime;

        size_t freedMemory = ESP.getFreeHeap() - currentFree;
        Serial.printf("Proactive cleanup freed %d bytes\n", freedMemory);
    }
}

void MemoryMonitor::performAggressiveCleanup() {
    Serial.println("Performing aggressive memory cleanup due to leak detection...");

    // More aggressive cleanup measures
    cleanupDisplayBuffers();
    cleanupStringBuffers();
    cleanupNetworkBuffers();

    // Force garbage collection multiple times
    for (int i = 0; i < 3; i++) {
        forceGarbageCollection();
        delay(10);
    }

    // Reset WiFi if memory is still critically low
    if (ESP.getFreeHeap() < 8000) {
        Serial.println("CRITICAL: Resetting WiFi to free memory...");
        WiFi.disconnect();
        delay(100);
        // WiFi will be reconnected by the main loop
    }
}

void MemoryMonitor::cleanupDisplayBuffers() {
    // Clear any cached display data
    extern DisplayBuffer displayBuffer;
    displayBuffer.clear();

    Serial.println("Display buffers cleaned");
}

void MemoryMonitor::cleanupStringBuffers() {
    // Reset string handlers
    extern OptimizedStringHandler stringHandler;
    stringHandler.clear();

    Serial.println("String buffers cleaned");
}

void MemoryMonitor::cleanupNetworkBuffers() {
    // Force cleanup of network buffers
    WiFi.printDiag(Serial);

    // Disconnect and reconnect MQTT to clear buffers
    extern PubSubClient mqttClient;
    if (mqttClient.connected()) {
        mqttClient.disconnect();
        delay(100);
        // MQTT will be reconnected by the main loop
    }

    Serial.println("Network buffers cleaned");
}

void MemoryMonitor::logMemoryStatus(size_t currentFree, unsigned long currentTime) {
    Serial.printf("Memory Status - Free: %d bytes, Min: %d bytes\n",
                 currentFree, minFreeHeap);

    // Log additional memory statistics
    Serial.printf("Largest block: %d bytes, Total heap: %d bytes\n",
                 ESP.getMaxAllocHeap(), ESP.getHeapSize());

    // Calculate memory usage percentage
    size_t totalHeap = ESP.getHeapSize();
    int usagePercent = ((totalHeap - currentFree) * 100) / totalHeap;
    Serial.printf("Memory usage: %d%%\n", usagePercent);

    // Warning if memory usage is high
    if (usagePercent > 80) {
        Serial.println("WARNING: High memory usage detected!");
    }
}

void MemoryMonitor::handleCriticalMemory(size_t currentFree) {
    // Warning if memory is low
    if (currentFree < 10000) {
        Serial.println("WARNING: Low memory detected!");
        performProactiveCleanup(currentFree, millis());
    }

    // Critical memory warning
    if (currentFree < 5000) {
        Serial.println("CRITICAL: Very low memory! Emergency cleanup...");
        performAggressiveCleanup();

        // If still critical, restart the system
        if (ESP.getFreeHeap() < 3000) {
            Serial.println("EMERGENCY: Restarting system due to critical memory shortage...");
            delay(1000);
            ESP.restart();
        }
    }
}

size_t MemoryMonitor::getFreeHeap() {
    return ESP.getFreeHeap();
}

size_t MemoryMonitor::getMinFreeHeap() {
    return minFreeHeap;
}

void MemoryMonitor::forceGarbageCollection() {
    // Force garbage collection by allocating and freeing memory
    void* ptr = malloc(1024);
    if (ptr) {
        free(ptr);
    }

    // Also try to trigger ESP32 garbage collection
    size_t beforeGC = ESP.getFreeHeap();
    delay(10);
    size_t afterGC = ESP.getFreeHeap();

    Serial.printf("Garbage collection: %d -> %d bytes (freed %d)\n",
                 beforeGC, afterGC, afterGC - beforeGC);
}

// Display buffer functions
void DisplayBuffer::init() {
    memset(displayBuffer, 0, DISPLAY_BUFFER_SIZE);
    bufferDirty = false;
    Serial.println("Display buffer initialized");
}

char* DisplayBuffer::getBuffer() {
    return displayBuffer;
}

void DisplayBuffer::markDirty() {
    bufferDirty = true;
}

bool DisplayBuffer::isDirty() {
    return bufferDirty;
}

void DisplayBuffer::markClean() {
    bufferDirty = false;
}

void DisplayBuffer::clear() {
    memset(displayBuffer, 0, DISPLAY_BUFFER_SIZE);
    bufferDirty = true;
}

// Optimized string handler implementation
void OptimizedStringHandler::reset() {
    bufferPos = 0;
    memset(buffer, 0, MAX_MESSAGE_LENGTH);
}

bool OptimizedStringHandler::append(const char* str) {
    size_t len = strlen(str);
    if (bufferPos + len >= MAX_MESSAGE_LENGTH - 1) {
        return false; // Buffer overflow protection
    }
    strcpy(buffer + bufferPos, str);
    bufferPos += len;
    return true;
}

bool OptimizedStringHandler::append(char c) {
    if (bufferPos >= MAX_MESSAGE_LENGTH - 1) {
        return false;
    }
    buffer[bufferPos++] = c;
    buffer[bufferPos] = '\0';
    return true;
}

const char* OptimizedStringHandler::getString() const {
    return buffer;
}

size_t OptimizedStringHandler::length() const {
    return bufferPos;
}

void OptimizedStringHandler::clear() {
    reset();
}

// Memory optimization utility functions
void* optimizedMalloc(size_t size) {
    // Check available memory before allocation
    if (ESP.getFreeHeap() < size + 1000) { // Keep 1KB safety margin
        Serial.printf("WARNING: Low memory for allocation of %d bytes\n", size);
        MemoryMonitor::forceGarbageCollection();

        if (ESP.getFreeHeap() < size + 500) {
            Serial.println("ERROR: Insufficient memory for allocation");
            return nullptr;
        }
    }

    void* ptr = malloc(size);
    if (ptr) {
        MemoryMonitor::checkMemory();
    }
    return ptr;
}

void optimizedFree(void* ptr) {
    if (ptr) {
        free(ptr);
        MemoryMonitor::checkMemory();
    }
}

// String optimization utilities
void optimizedStringCopy(char* dest, const char* src, size_t maxLen) {
    if (!dest || !src || maxLen == 0) return;

    size_t i = 0;
    while (i < maxLen - 1 && src[i] != '\0') {
        dest[i] = src[i];
        i++;
    }
    dest[i] = '\0';
}

int optimizedStringCompare(const char* str1, const char* str2) {
    if (!str1 || !str2) return -1;

    while (*str1 && *str2 && *str1 == *str2) {
        str1++;
        str2++;
    }

    return *str1 - *str2;
}

// Memory statistics
void printMemoryStatistics() {
    Serial.println("=== Memory Statistics ===");
    Serial.printf("Free Heap: %d bytes\n", ESP.getFreeHeap());
    Serial.printf("Min Free Heap: %d bytes\n", MemoryMonitor::getMinFreeHeap());
    Serial.printf("Largest Free Block: %d bytes\n", ESP.getMaxAllocHeap());
    Serial.printf("Total Heap: %d bytes\n", ESP.getHeapSize());
    Serial.printf("Free PSRAM: %d bytes\n", ESP.getFreePsram());
    Serial.println("========================");
}
