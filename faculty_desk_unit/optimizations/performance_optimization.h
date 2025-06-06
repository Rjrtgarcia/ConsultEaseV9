/**
 * Performance optimization utilities for ConsultEase Faculty Desk Unit
 * Optimizes display rendering, network operations, and system responsiveness
 */

#ifndef PERFORMANCE_OPTIMIZATION_H
#define PERFORMANCE_OPTIMIZATION_H

#include <Arduino.h>
#include <Adafruit_ST7789.h>

// Performance monitoring constants
#define PERF_SAMPLE_SIZE 10
#define PERF_UPDATE_INTERVAL 5000
#define MAX_FRAME_TIME 33  // ~30 FPS target

// Performance metrics structure
struct PerformanceMetrics {
    unsigned long frameTime;
    unsigned long displayUpdateTime;
    unsigned long networkLatency;
    unsigned long memoryUsage;
    float cpuUsage;
    int frameRate;
    unsigned long lastUpdate;
};

// Display optimization class
class DisplayOptimizer {
private:
    static uint16_t* frameBuffer;
    static bool frameBufferEnabled;
    static bool dirtyRegions[8][6];  // 8x6 grid for dirty region tracking
    static int regionWidth;
    static int regionHeight;
    static unsigned long lastFrameTime;
    static int currentFrameRate;
    static bool vsyncEnabled;
    
    static void initFrameBuffer();
    static void markRegionDirty(int x, int y, int width, int height);
    static void updateDirtyRegions();
    static void optimizeSPISettings();
    
public:
    static void init(Adafruit_ST7789* tft);
    static void enableFrameBuffer(bool enabled);
    static void enableVSync(bool enabled);
    static void beginFrame();
    static void endFrame();
    static void markDirty(int x, int y, int width, int height);
    static void optimizedFillRect(int x, int y, int width, int height, uint16_t color);
    static void optimizedDrawText(int x, int y, const char* text, uint16_t color, uint8_t size);
    static void optimizedDrawLine(int x0, int y0, int x1, int y1, uint16_t color);
    static void flushFrameBuffer();
    static int getCurrentFrameRate();
    static unsigned long getLastFrameTime();
    static void printDisplayStats();
};

// Network optimization class
class NetworkOptimizer {
private:
    static unsigned long lastPingTime;
    static unsigned long averageLatency;
    static int connectionQuality;
    static bool adaptiveQoS;
    static int messageQueue[16];
    static int queueHead;
    static int queueTail;
    static unsigned long lastOptimization;
    
    static void measureLatency();
    static void adjustQoS();
    static void optimizeWiFiSettings();
    static void queueMessage(int messageId);
    static int dequeueMessage();
    
public:
    static void init();
    static void enableAdaptiveQoS(bool enabled);
    static void optimizeConnection();
    static void recordNetworkActivity();
    static unsigned long getAverageLatency();
    static int getConnectionQuality();
    static void flushMessageQueue();
    static void printNetworkStats();
};

// CPU optimization class
class CPUOptimizer {
private:
    static unsigned long taskTimes[8];
    static int taskCount;
    static unsigned long totalCPUTime;
    static unsigned long idleTime;
    static bool dynamicFrequency;
    static uint32_t currentFrequency;
    static unsigned long lastFrequencyChange;
    
    static void measureTaskTime(int taskId, unsigned long startTime);
    static void adjustCPUFrequency();
    static void optimizeTaskScheduling();
    
public:
    static void init();
    static void enableDynamicFrequency(bool enabled);
    static void beginTask(int taskId);
    static void endTask(int taskId);
    static float getCPUUsage();
    static uint32_t getCurrentFrequency();
    static void forceCPUFrequency(uint32_t frequency);
    static void printCPUStats();
};

// Memory optimization class
class MemoryOptimizer {
private:
    static size_t peakMemoryUsage;
    static size_t currentMemoryUsage;
    static unsigned long lastGarbageCollection;
    static bool autoGarbageCollection;
    static int fragmentationLevel;
    
    static void measureFragmentation();
    static void performGarbageCollection();
    static void optimizeHeap();
    
public:
    static void init();
    static void enableAutoGarbageCollection(bool enabled);
    static void recordAllocation(size_t size);
    static void recordDeallocation(size_t size);
    static size_t getCurrentUsage();
    static size_t getPeakUsage();
    static int getFragmentationLevel();
    static void forceGarbageCollection();
    static void printMemoryStats();
};

// Task scheduler optimization
class TaskScheduler {
private:
    struct Task {
        void (*function)();
        unsigned long interval;
        unsigned long lastRun;
        unsigned long executionTime;
        int priority;
        bool enabled;
    };
    
    static const int MAX_TASKS = 16;
    static Task tasks[MAX_TASKS];
    static int taskCount;
    static unsigned long totalExecutionTime;
    static bool priorityScheduling;
    
    static void sortTasksByPriority();
    static void balanceTaskLoad();
    
public:
    static void init();
    static bool addTask(void (*function)(), unsigned long interval, int priority = 5);
    static void removeTask(void (*function)());
    static void enableTask(void (*function)(), bool enabled);
    static void enablePriorityScheduling(bool enabled);
    static void update();
    static void printTaskStats();
};

// Performance profiler
class PerformanceProfiler {
private:
    static PerformanceMetrics metrics[PERF_SAMPLE_SIZE];
    static int currentSample;
    static unsigned long profilingStartTime;
    static bool profilingEnabled;
    
    static void updateMetrics();
    static void calculateAverages();
    
public:
    static void init();
    static void enableProfiling(bool enabled);
    static void beginProfile(const char* name);
    static void endProfile(const char* name);
    static void recordFrameTime(unsigned long frameTime);
    static void recordNetworkLatency(unsigned long latency);
    static void update();
    static void printReport();
    static PerformanceMetrics getAverageMetrics();
};

// Cache optimization
class CacheOptimizer {
private:
    struct CacheEntry {
        char key[32];
        void* data;
        size_t size;
        unsigned long lastAccess;
        int accessCount;
    };
    
    static const int CACHE_SIZE = 8;
    static CacheEntry cache[CACHE_SIZE];
    static int cacheHits;
    static int cacheMisses;
    static unsigned long lastCleanup;
    
    static int findLRUEntry();
    static void evictEntry(int index);
    static void updateAccessStats(int index);
    
public:
    static void init();
    static bool put(const char* key, void* data, size_t size);
    static void* get(const char* key);
    static void remove(const char* key);
    static void clear();
    static float getHitRatio();
    static void printCacheStats();
};

// Interrupt optimization
class InterruptOptimizer {
private:
    static unsigned long interruptCount;
    static unsigned long totalInterruptTime;
    static bool interruptProfiling;
    
public:
    static void init();
    static void enableProfiling(bool enabled);
    static void recordInterrupt(unsigned long duration);
    static float getInterruptLoad();
    static void printInterruptStats();
};

// Performance monitoring utilities
namespace PerformanceUtils {
    // Timing utilities
    unsigned long micros_safe();
    void delay_optimized(unsigned long ms);
    void yield_optimized();
    
    // Memory utilities
    void* malloc_tracked(size_t size);
    void free_tracked(void* ptr);
    void* realloc_tracked(void* ptr, size_t size);
    
    // String utilities
    void strcpy_optimized(char* dest, const char* src, size_t maxLen);
    int strcmp_optimized(const char* str1, const char* str2);
    char* strstr_optimized(const char* haystack, const char* needle);
    
    // Math utilities
    int fast_sqrt(int x);
    int fast_abs(int x);
    int fast_min(int a, int b);
    int fast_max(int a, int b);
}

// Performance configuration
struct PerformanceConfig {
    bool enableFrameBuffer;
    bool enableVSync;
    bool enableAdaptiveQoS;
    bool enableDynamicFrequency;
    bool enableAutoGarbageCollection;
    bool enablePriorityScheduling;
    bool enableProfiling;
    int targetFrameRate;
    uint32_t maxCPUFrequency;
    uint32_t minCPUFrequency;
    size_t maxMemoryUsage;
};

extern PerformanceConfig performanceConfig;

// Performance macros
#define PERF_BEGIN_PROFILE(name) PerformanceProfiler::beginProfile(name)
#define PERF_END_PROFILE(name) PerformanceProfiler::endProfile(name)
#define PERF_BEGIN_FRAME() DisplayOptimizer::beginFrame()
#define PERF_END_FRAME() DisplayOptimizer::endFrame()
#define PERF_MARK_DIRTY(x, y, w, h) DisplayOptimizer::markDirty(x, y, w, h)
#define PERF_YIELD() PerformanceUtils::yield_optimized()

// Function prototypes
void initPerformanceOptimization();
void updatePerformanceOptimization();
void printPerformanceReport();
void optimizeForBatteryLife();
void optimizeForPerformance();

#endif // PERFORMANCE_OPTIMIZATION_H
