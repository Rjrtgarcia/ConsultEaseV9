/**
 * Power management system for ConsultEase Faculty Desk Unit
 * Optimized for battery operation and energy efficiency
 */

#ifndef POWER_MANAGEMENT_H
#define POWER_MANAGEMENT_H

#include <Arduino.h>
#include <WiFi.h>
#include <esp_wifi.h>
#include <esp_bt.h>
#include <esp_sleep.h>

// Power management constants
#define DISPLAY_TIMEOUT_MS 300000        // 5 minutes
#define IDLE_TIMEOUT_MS 600000           // 10 minutes
#define DEEP_SLEEP_DURATION_US 30000000  // 30 seconds
#define LOW_POWER_CPU_FREQ 80            // MHz
#define NORMAL_CPU_FREQ 240              // MHz

// Power states
enum PowerState {
    POWER_ACTIVE,
    POWER_DISPLAY_OFF,
    POWER_IDLE,
    POWER_DEEP_SLEEP
};

// Power management class
class PowerManager {
private:
    static PowerState currentState;
    static unsigned long lastActivity;
    static unsigned long lastDisplayActivity;
    static bool displayEnabled;
    static uint8_t displayBrightness;
    static bool wifiPowerSaveEnabled;
    
    // Private methods
    static void enterDisplayOffMode();
    static void enterIdleMode();
    static void enterDeepSleep();
    static void adjustCPUFrequency(uint32_t freq);
    static void configureWiFiPowerSave(bool enable);
    static void configureBLEPowerSave(bool enable);
    
public:
    // Initialization
    static void init();
    
    // Activity tracking
    static void recordActivity();
    static void recordDisplayActivity();
    
    // Power state management
    static void update();
    static PowerState getCurrentState();
    static void forceState(PowerState state);
    
    // Display management
    static void setDisplayEnabled(bool enabled);
    static bool isDisplayEnabled();
    static void setDisplayBrightness(uint8_t brightness);
    static uint8_t getDisplayBrightness();
    static void fadeDisplayBrightness(uint8_t targetBrightness, uint16_t duration);
    
    // WiFi power management
    static void enableWiFiPowerSave();
    static void disableWiFiPowerSave();
    static bool isWiFiPowerSaveEnabled();
    
    // BLE power management
    static void setBLEPower(esp_power_level_t powerLevel);
    static void enableBLEPowerSave();
    static void disableBLEPowerSave();
    
    // Sleep management
    static void prepareSleep();
    static void wakeFromSleep();
    static void configureWakeupSources();
    
    // Battery monitoring (if available)
    static float getBatteryVoltage();
    static uint8_t getBatteryPercentage();
    static bool isBatteryLow();
    
    // Power statistics
    static unsigned long getUptimeMs();
    static unsigned long getActiveTimeMs();
    static unsigned long getSleepTimeMs();
    
    // Emergency power management
    static void emergencyPowerSave();
    static void criticalBatteryShutdown();
};

// Power-aware delay function
void powerAwareDelay(unsigned long ms);

// Power-aware task scheduling
class PowerAwareScheduler {
private:
    struct Task {
        unsigned long interval;
        unsigned long lastRun;
        void (*callback)();
        bool powerSensitive;
    };
    
    static const int MAX_TASKS = 10;
    static Task tasks[MAX_TASKS];
    static int taskCount;
    
public:
    static void init();
    static bool addTask(void (*callback)(), unsigned long interval, bool powerSensitive = true);
    static void update();
    static void pausePowerSensitiveTasks();
    static void resumePowerSensitiveTasks();
};

// Display power management
class DisplayPowerManager {
private:
    static bool backlightEnabled;
    static uint8_t currentBrightness;
    static unsigned long lastUpdate;
    
public:
    static void init();
    static void setBacklight(bool enabled);
    static void setBrightness(uint8_t brightness);
    static void fadeToBlack(uint16_t duration);
    static void fadeFromBlack(uint16_t duration);
    static void enableAutoTimeout();
    static void disableAutoTimeout();
    static void update();
};

// WiFi power optimization
class WiFiPowerOptimizer {
private:
    static wifi_ps_type_t currentPowerSaveMode;
    static bool adaptivePowerSave;
    static unsigned long lastTrafficTime;
    
public:
    static void init();
    static void enableAdaptivePowerSave();
    static void disableAdaptivePowerSave();
    static void setStaticPowerSaveMode(wifi_ps_type_t mode);
    static void recordNetworkActivity();
    static void update();
    static int8_t getSignalStrength();
    static void optimizeForSignalStrength();
};

// BLE power optimization
class BLEPowerOptimizer {
private:
    static esp_power_level_t currentPowerLevel;
    static bool adaptivePower;
    static unsigned long lastConnectionTime;
    static int connectionAttempts;
    
public:
    static void init();
    static void enableAdaptivePower();
    static void disableAdaptivePower();
    static void setPowerLevel(esp_power_level_t level);
    static void recordConnectionAttempt();
    static void recordSuccessfulConnection();
    static void update();
    static void optimizeForConnectionQuality();
};

// Power monitoring and logging
class PowerMonitor {
private:
    static unsigned long totalActiveTime;
    static unsigned long totalSleepTime;
    static unsigned long bootTime;
    static float averageCurrent;
    
public:
    static void init();
    static void logPowerEvent(const char* event);
    static void updatePowerStats();
    static void printPowerReport();
    static float getAveragePowerConsumption();
    static unsigned long getEstimatedBatteryLife();
};

// Macros for power-aware operations
#define POWER_RECORD_ACTIVITY() PowerManager::recordActivity()
#define POWER_RECORD_DISPLAY_ACTIVITY() PowerManager::recordDisplayActivity()
#define POWER_AWARE_DELAY(ms) powerAwareDelay(ms)
#define POWER_CHECK_BATTERY() PowerManager::isBatteryLow()

// Configuration macros
#define ENABLE_DISPLAY_TIMEOUT
#define ENABLE_CPU_SCALING
#define ENABLE_WIFI_POWER_SAVE
#define ENABLE_BLE_POWER_SAVE
#define ENABLE_DEEP_SLEEP

#endif // POWER_MANAGEMENT_H
