/**
 * Memory optimization utilities for ConsultEase Faculty Desk Unit
 * Optimized for ESP32 platform with limited RAM
 */

#ifndef MEMORY_OPTIMIZATION_H
#define MEMORY_OPTIMIZATION_H

#include <Arduino.h>

// Memory management constants
#define MAX_MESSAGE_LENGTH 512
#define MAX_LINE_LENGTH 64
#define DISPLAY_BUFFER_SIZE 1024
#define MEMORY_HISTORY_SIZE 20  // Number of memory samples to track for leak detection

// Optimized string handling class
class OptimizedStringHandler {
private:
    char buffer[MAX_MESSAGE_LENGTH];
    size_t bufferPos;

public:
    OptimizedStringHandler() : bufferPos(0) {
        memset(buffer, 0, MAX_MESSAGE_LENGTH);
    }

    void reset() {
        bufferPos = 0;
        memset(buffer, 0, MAX_MESSAGE_LENGTH);
    }

    bool append(const char* str) {
        size_t len = strlen(str);
        if (bufferPos + len >= MAX_MESSAGE_LENGTH - 1) {
            return false; // Buffer overflow protection
        }
        strcpy(buffer + bufferPos, str);
        bufferPos += len;
        return true;
    }

    bool append(char c) {
        if (bufferPos >= MAX_MESSAGE_LENGTH - 1) {
            return false;
        }
        buffer[bufferPos++] = c;
        buffer[bufferPos] = '\0';
        return true;
    }

    const char* getString() const {
        return buffer;
    }

    size_t length() const {
        return bufferPos;
    }

    void clear() {
        reset();
    }
};

// Memory monitoring utilities
class MemoryMonitor {
private:
    static unsigned long lastCheck;
    static size_t minFreeHeap;

public:
    static void init() {
        lastCheck = millis();
        minFreeHeap = ESP.getFreeHeap();
    }

    static void checkMemory() {
        size_t currentFree = ESP.getFreeHeap();
        if (currentFree < minFreeHeap) {
            minFreeHeap = currentFree;
        }

        // Log memory status every 30 seconds
        if (millis() - lastCheck > 30000) {
            Serial.printf("Memory Status - Free: %d bytes, Min: %d bytes\n",
                         currentFree, minFreeHeap);
            lastCheck = millis();

            // Warning if memory is low
            if (currentFree < 10000) {
                Serial.println("WARNING: Low memory detected!");
            }
        }
    }

    static size_t getFreeHeap() {
        return ESP.getFreeHeap();
    }

    static size_t getMinFreeHeap() {
        return minFreeHeap;
    }

    static void forceGarbageCollection() {
        // Force garbage collection by allocating and freeing memory
        void* ptr = malloc(1024);
        if (ptr) {
            free(ptr);
        }
    }

    // Enhanced memory management methods
    static void detectMemoryLeaks(size_t currentFree, unsigned long currentTime);
    static void analyzeMemoryTrend(size_t* history);
    static void performProactiveCleanup(size_t currentFree, unsigned long currentTime);
    static void performAggressiveCleanup();
    static void cleanupDisplayBuffers();
    static void cleanupStringBuffers();
    static void cleanupNetworkBuffers();
    static void logMemoryStatus(size_t currentFree, unsigned long currentTime);
    static void handleCriticalMemory(size_t currentFree);
};

// Optimized display buffer management
class DisplayBuffer {
private:
    static char displayBuffer[DISPLAY_BUFFER_SIZE];
    static bool bufferDirty;

public:
    static void init() {
        memset(displayBuffer, 0, DISPLAY_BUFFER_SIZE);
        bufferDirty = false;
    }

    static char* getBuffer() {
        return displayBuffer;
    }

    static void markDirty() {
        bufferDirty = true;
    }

    static bool isDirty() {
        return bufferDirty;
    }

    static void markClean() {
        bufferDirty = false;
    }

    static void clear() {
        memset(displayBuffer, 0, DISPLAY_BUFFER_SIZE);
        bufferDirty = true;
    }
};

// Static memory allocation for frequently used objects
extern OptimizedStringHandler globalStringHandler;
extern char mqttTopicBuffer[64];
extern char timeBuffer[32];
extern char dateBuffer[32];

// Initialize static members
unsigned long MemoryMonitor::lastCheck = 0;
size_t MemoryMonitor::minFreeHeap = 0;
char DisplayBuffer::displayBuffer[DISPLAY_BUFFER_SIZE];
bool DisplayBuffer::bufferDirty = false;

// Memory optimization macros
#define SAFE_STRING_COPY(dest, src, size) \
    do { \
        strncpy(dest, src, size - 1); \
        dest[size - 1] = '\0'; \
    } while(0)

#define CHECK_MEMORY() MemoryMonitor::checkMemory()

#define FORCE_GC() MemoryMonitor::forceGarbageCollection()

// Function prototypes for optimized operations
void optimizedDisplayMessage(const char* message);
void optimizedProcessMessage(const char* input, char* output, size_t outputSize);
bool optimizedJSONExtract(const char* json, const char* key, char* value, size_t valueSize);

#endif // MEMORY_OPTIMIZATION_H
