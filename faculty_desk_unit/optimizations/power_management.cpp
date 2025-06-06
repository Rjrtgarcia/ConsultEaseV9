/**
 * Power management implementation for ConsultEase Faculty Desk Unit
 */

#include "power_management.h"
#include <esp_pm.h>
#include <esp_wifi.h>
#include <esp_bt.h>
#include <driver/adc.h>

// Static member definitions
PowerState PowerManager::currentState = POWER_ACTIVE;
unsigned long PowerManager::lastActivity = 0;
unsigned long PowerManager::lastDisplayActivity = 0;
bool PowerManager::displayEnabled = true;
uint8_t PowerManager::displayBrightness = 255;
bool PowerManager::wifiPowerSaveEnabled = false;

// Power management initialization
void PowerManager::init() {
    lastActivity = millis();
    lastDisplayActivity = millis();
    currentState = POWER_ACTIVE;
    displayEnabled = true;
    displayBrightness = 255;
    
    // Configure power management
    esp_pm_config_esp32_t pm_config = {
        .max_freq_mhz = NORMAL_CPU_FREQ,
        .min_freq_mhz = LOW_POWER_CPU_FREQ,
        .light_sleep_enable = true
    };
    esp_pm_configure(&pm_config);
    
    // Configure wakeup sources
    configureWakeupSources();
    
    Serial.println("Power Manager initialized");
    Serial.printf("CPU Frequency: %d MHz\n", getCpuFrequencyMhz());
}

void PowerManager::recordActivity() {
    lastActivity = millis();
    
    // Wake up from power save modes if needed
    if (currentState != POWER_ACTIVE) {
        forceState(POWER_ACTIVE);
    }
}

void PowerManager::recordDisplayActivity() {
    lastDisplayActivity = millis();
    recordActivity(); // Display activity is also general activity
}

void PowerManager::update() {
    unsigned long currentTime = millis();
    
    switch (currentState) {
        case POWER_ACTIVE:
            // Check if we should enter display off mode
            if (currentTime - lastDisplayActivity > DISPLAY_TIMEOUT_MS) {
                enterDisplayOffMode();
            }
            break;
            
        case POWER_DISPLAY_OFF:
            // Check if we should enter idle mode
            if (currentTime - lastActivity > IDLE_TIMEOUT_MS) {
                enterIdleMode();
            }
            // Check if display should be turned back on
            else if (currentTime - lastDisplayActivity < 1000) {
                setDisplayEnabled(true);
                currentState = POWER_ACTIVE;
            }
            break;
            
        case POWER_IDLE:
            // Check if we should enter deep sleep
            if (currentTime - lastActivity > IDLE_TIMEOUT_MS * 2) {
                enterDeepSleep();
            }
            // Check if we should wake up
            else if (currentTime - lastActivity < 5000) {
                forceState(POWER_ACTIVE);
            }
            break;
            
        case POWER_DEEP_SLEEP:
            // This state should not be reached in normal operation
            // as the device would be sleeping
            break;
    }
}

void PowerManager::enterDisplayOffMode() {
    Serial.println("Entering display off mode");
    setDisplayEnabled(false);
    currentState = POWER_DISPLAY_OFF;
    
    // Reduce CPU frequency
    adjustCPUFrequency(LOW_POWER_CPU_FREQ);
    
    // Enable WiFi power save
    enableWiFiPowerSave();
}

void PowerManager::enterIdleMode() {
    Serial.println("Entering idle mode");
    currentState = POWER_IDLE;
    
    // Further reduce CPU frequency
    adjustCPUFrequency(LOW_POWER_CPU_FREQ);
    
    // Enable aggressive WiFi power save
    configureWiFiPowerSave(true);
    
    // Reduce BLE power
    configureBLEPowerSave(true);
}

void PowerManager::enterDeepSleep() {
    Serial.println("Preparing for deep sleep");
    prepareSleep();
    
    currentState = POWER_DEEP_SLEEP;
    
    // Configure wake up sources
    esp_sleep_enable_timer_wakeup(DEEP_SLEEP_DURATION_US);
    
    Serial.println("Entering deep sleep...");
    Serial.flush();
    
    esp_deep_sleep_start();
}

void PowerManager::adjustCPUFrequency(uint32_t freq) {
    if (getCpuFrequencyMhz() != freq) {
        setCpuFrequencyMhz(freq);
        Serial.printf("CPU frequency adjusted to %d MHz\n", freq);
    }
}

void PowerManager::configureWiFiPowerSave(bool enable) {
    if (enable && !wifiPowerSaveEnabled) {
        esp_wifi_set_ps(WIFI_PS_MAX_MODEM);
        wifiPowerSaveEnabled = true;
        Serial.println("WiFi power save enabled");
    } else if (!enable && wifiPowerSaveEnabled) {
        esp_wifi_set_ps(WIFI_PS_NONE);
        wifiPowerSaveEnabled = false;
        Serial.println("WiFi power save disabled");
    }
}

void PowerManager::configureBLEPowerSave(bool enable) {
    if (enable) {
        // Reduce BLE advertising interval and power
        Serial.println("BLE power save enabled");
    } else {
        // Restore normal BLE settings
        Serial.println("BLE power save disabled");
    }
}

PowerState PowerManager::getCurrentState() {
    return currentState;
}

void PowerManager::forceState(PowerState state) {
    if (state == currentState) return;
    
    Serial.printf("Forcing power state change: %d -> %d\n", currentState, state);
    
    switch (state) {
        case POWER_ACTIVE:
            setDisplayEnabled(true);
            adjustCPUFrequency(NORMAL_CPU_FREQ);
            configureWiFiPowerSave(false);
            configureBLEPowerSave(false);
            break;
            
        case POWER_DISPLAY_OFF:
            setDisplayEnabled(false);
            adjustCPUFrequency(LOW_POWER_CPU_FREQ);
            configureWiFiPowerSave(true);
            break;
            
        case POWER_IDLE:
            setDisplayEnabled(false);
            adjustCPUFrequency(LOW_POWER_CPU_FREQ);
            configureWiFiPowerSave(true);
            configureBLEPowerSave(true);
            break;
            
        case POWER_DEEP_SLEEP:
            enterDeepSleep();
            return; // Function won't return
    }
    
    currentState = state;
}

void PowerManager::setDisplayEnabled(bool enabled) {
    if (displayEnabled != enabled) {
        displayEnabled = enabled;
        
        if (enabled) {
            Serial.println("Display enabled");
            // Turn on display backlight
            // This would be hardware-specific implementation
        } else {
            Serial.println("Display disabled");
            // Turn off display backlight
            // This would be hardware-specific implementation
        }
    }
}

bool PowerManager::isDisplayEnabled() {
    return displayEnabled;
}

void PowerManager::setDisplayBrightness(uint8_t brightness) {
    displayBrightness = brightness;
    // Hardware-specific brightness control would go here
    Serial.printf("Display brightness set to %d\n", brightness);
}

uint8_t PowerManager::getDisplayBrightness() {
    return displayBrightness;
}

void PowerManager::fadeDisplayBrightness(uint8_t targetBrightness, uint16_t duration) {
    uint8_t startBrightness = displayBrightness;
    uint16_t steps = duration / 10; // 10ms per step
    
    if (steps == 0) steps = 1;
    
    int16_t brightnessStep = (int16_t)(targetBrightness - startBrightness) / steps;
    
    for (uint16_t i = 0; i < steps; i++) {
        uint8_t currentBrightness = startBrightness + (brightnessStep * i);
        setDisplayBrightness(currentBrightness);
        delay(10);
    }
    
    setDisplayBrightness(targetBrightness);
}

void PowerManager::enableWiFiPowerSave() {
    configureWiFiPowerSave(true);
}

void PowerManager::disableWiFiPowerSave() {
    configureWiFiPowerSave(false);
}

bool PowerManager::isWiFiPowerSaveEnabled() {
    return wifiPowerSaveEnabled;
}

float PowerManager::getBatteryVoltage() {
    // This would read from an ADC pin connected to battery voltage divider
    // For now, return a simulated value
    return 3.7f; // Simulated battery voltage
}

uint8_t PowerManager::getBatteryPercentage() {
    float voltage = getBatteryVoltage();
    
    // Convert voltage to percentage (3.0V = 0%, 4.2V = 100%)
    if (voltage <= 3.0f) return 0;
    if (voltage >= 4.2f) return 100;
    
    return (uint8_t)((voltage - 3.0f) / 1.2f * 100.0f);
}

bool PowerManager::isBatteryLow() {
    return getBatteryPercentage() < 20;
}

void PowerManager::prepareSleep() {
    Serial.println("Preparing for sleep mode");
    
    // Save any important state
    // Flush serial output
    Serial.flush();
    
    // Disable unnecessary peripherals
    // This would be hardware-specific
}

void PowerManager::wakeFromSleep() {
    Serial.println("Waking from sleep");
    
    // Restore normal operation
    forceState(POWER_ACTIVE);
    
    // Re-initialize any peripherals that were disabled
    recordActivity();
}

void PowerManager::configureWakeupSources() {
    // Configure timer wakeup (always enabled)
    esp_sleep_enable_timer_wakeup(DEEP_SLEEP_DURATION_US);
    
    // Configure external wakeup sources if available
    // This would be hardware-specific based on available pins
    
    Serial.println("Wakeup sources configured");
}

unsigned long PowerManager::getUptimeMs() {
    return millis();
}

void PowerManager::emergencyPowerSave() {
    Serial.println("EMERGENCY: Entering emergency power save mode");
    
    // Immediately disable display
    setDisplayEnabled(false);
    
    // Set minimum CPU frequency
    adjustCPUFrequency(LOW_POWER_CPU_FREQ);
    
    // Enable all power saving features
    enableWiFiPowerSave();
    configureBLEPowerSave(true);
    
    // Force idle state
    currentState = POWER_IDLE;
}

void PowerManager::criticalBatteryShutdown() {
    Serial.println("CRITICAL: Battery critically low - shutting down");
    
    // Save any critical data
    // Prepare for shutdown
    prepareSleep();
    
    // Enter deep sleep indefinitely
    esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_ALL);
    esp_deep_sleep_start();
}

// Power-aware delay function
void powerAwareDelay(unsigned long ms) {
    unsigned long startTime = millis();
    
    while (millis() - startTime < ms) {
        // Allow power management to run
        PowerManager::update();
        
        // Use light sleep for longer delays
        if (ms > 100) {
            delay(10);
        } else {
            delayMicroseconds(1000);
        }
    }
}

// Power statistics and monitoring
void printPowerStatistics() {
    Serial.println("=== Power Statistics ===");
    Serial.printf("Current State: %d\n", PowerManager::getCurrentState());
    Serial.printf("Display Enabled: %s\n", PowerManager::isDisplayEnabled() ? "Yes" : "No");
    Serial.printf("Display Brightness: %d\n", PowerManager::getDisplayBrightness());
    Serial.printf("WiFi Power Save: %s\n", PowerManager::isWiFiPowerSaveEnabled() ? "Yes" : "No");
    Serial.printf("CPU Frequency: %d MHz\n", getCpuFrequencyMhz());
    Serial.printf("Battery Voltage: %.2f V\n", PowerManager::getBatteryVoltage());
    Serial.printf("Battery Percentage: %d%%\n", PowerManager::getBatteryPercentage());
    Serial.printf("Battery Low: %s\n", PowerManager::isBatteryLow() ? "Yes" : "No");
    Serial.printf("Uptime: %lu ms\n", PowerManager::getUptimeMs());
    Serial.println("=======================");
}
