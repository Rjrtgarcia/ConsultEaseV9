/**
 * Hardware Abstraction Layer for ConsultEase Faculty Desk Unit
 * Provides unified interface for different hardware configurations
 */

#ifndef HARDWARE_ABSTRACTION_H
#define HARDWARE_ABSTRACTION_H

#include <Arduino.h>

// Hardware platform detection
#ifdef ESP32
    #define PLATFORM_ESP32
    #include <esp_system.h>
    #include <esp_sleep.h>
#elif defined(ESP8266)
    #define PLATFORM_ESP8266
    #include <ESP8266WiFi.h>
#else
    #define PLATFORM_GENERIC
#endif

// Display types
enum DisplayType {
    DISPLAY_ST7789,
    DISPLAY_ILI9341,
    DISPLAY_SSD1306,
    DISPLAY_NONE
};

// BLE types
enum BLEType {
    BLE_ESP32_CLASSIC,
    BLE_ESP32_NIMBLE,
    BLE_NONE
};

// Hardware configuration structure
struct HardwareConfig {
    // Display configuration
    DisplayType displayType;
    int displayWidth;
    int displayHeight;
    int displayRotation;
    
    // Display pins
    int pinDisplayCS;
    int pinDisplayDC;
    int pinDisplayRST;
    int pinDisplayMOSI;
    int pinDisplaySCLK;
    int pinDisplayMISO;
    int pinDisplayBacklight;
    
    // BLE configuration
    BLEType bleType;
    int bleTxPower;
    
    // Power management pins
    int pinBatteryVoltage;
    int pinPowerEnable;
    int pinChargeStatus;
    
    // User interface pins
    int pinBuzzer;
    int pinLED;
    int pinButton1;
    int pinButton2;
    int pinButton3;
    
    // Communication pins
    int pinWiFiEnable;
    int pinStatusLED;
    
    // Sensors
    int pinTemperature;
    int pinHumidity;
    int pinLightSensor;
};

// Abstract display interface
class AbstractDisplay {
public:
    virtual ~AbstractDisplay() {}
    virtual bool init() = 0;
    virtual void setRotation(int rotation) = 0;
    virtual void fillScreen(uint16_t color) = 0;
    virtual void fillRect(int x, int y, int width, int height, uint16_t color) = 0;
    virtual void drawPixel(int x, int y, uint16_t color) = 0;
    virtual void drawLine(int x0, int y0, int x1, int y1, uint16_t color) = 0;
    virtual void drawRect(int x, int y, int width, int height, uint16_t color) = 0;
    virtual void drawCircle(int x, int y, int radius, uint16_t color) = 0;
    virtual void setCursor(int x, int y) = 0;
    virtual void setTextColor(uint16_t color) = 0;
    virtual void setTextSize(int size) = 0;
    virtual void print(const char* text) = 0;
    virtual void println(const char* text) = 0;
    virtual int width() = 0;
    virtual int height() = 0;
    virtual void setBacklight(bool enabled) = 0;
    virtual void setBrightness(uint8_t brightness) = 0;
    virtual void update() = 0;
};

// ST7789 display implementation
class ST7789Display : public AbstractDisplay {
private:
    void* tft;  // Adafruit_ST7789*
    HardwareConfig* config;
    
public:
    ST7789Display(HardwareConfig* hwConfig);
    virtual ~ST7789Display();
    virtual bool init() override;
    virtual void setRotation(int rotation) override;
    virtual void fillScreen(uint16_t color) override;
    virtual void fillRect(int x, int y, int width, int height, uint16_t color) override;
    virtual void drawPixel(int x, int y, uint16_t color) override;
    virtual void drawLine(int x0, int y0, int x1, int y1, uint16_t color) override;
    virtual void drawRect(int x, int y, int width, int height, uint16_t color) override;
    virtual void drawCircle(int x, int y, int radius, uint16_t color) override;
    virtual void setCursor(int x, int y) override;
    virtual void setTextColor(uint16_t color) override;
    virtual void setTextSize(int size) override;
    virtual void print(const char* text) override;
    virtual void println(const char* text) override;
    virtual int width() override;
    virtual int height() override;
    virtual void setBacklight(bool enabled) override;
    virtual void setBrightness(uint8_t brightness) override;
    virtual void update() override;
};

// Abstract BLE interface
class AbstractBLE {
public:
    virtual ~AbstractBLE() {}
    virtual bool init(const char* deviceName) = 0;
    virtual bool startAdvertising() = 0;
    virtual bool stopAdvertising() = 0;
    virtual bool isConnected() = 0;
    virtual bool sendData(const uint8_t* data, size_t length) = 0;
    virtual bool receiveData(uint8_t* data, size_t* length) = 0;
    virtual void setTxPower(int power) = 0;
    virtual void setConnectionCallback(void (*callback)(bool connected)) = 0;
    virtual void setDataCallback(void (*callback)(const uint8_t* data, size_t length)) = 0;
    virtual void update() = 0;
};

// ESP32 Classic BLE implementation
class ESP32ClassicBLE : public AbstractBLE {
private:
    HardwareConfig* config;
    void (*connectionCallback)(bool connected);
    void (*dataCallback)(const uint8_t* data, size_t length);
    bool initialized;
    bool connected;
    
public:
    ESP32ClassicBLE(HardwareConfig* hwConfig);
    virtual ~ESP32ClassicBLE();
    virtual bool init(const char* deviceName) override;
    virtual bool startAdvertising() override;
    virtual bool stopAdvertising() override;
    virtual bool isConnected() override;
    virtual bool sendData(const uint8_t* data, size_t length) override;
    virtual bool receiveData(uint8_t* data, size_t* length) override;
    virtual void setTxPower(int power) override;
    virtual void setConnectionCallback(void (*callback)(bool connected)) override;
    virtual void setDataCallback(void (*callback)(const uint8_t* data, size_t length)) override;
    virtual void update() override;
};

// Abstract power management interface
class AbstractPowerManager {
public:
    virtual ~AbstractPowerManager() {}
    virtual bool init() = 0;
    virtual float getBatteryVoltage() = 0;
    virtual uint8_t getBatteryPercentage() = 0;
    virtual bool isCharging() = 0;
    virtual bool isUSBPowered() = 0;
    virtual void enablePowerSave(bool enabled) = 0;
    virtual void setCPUFrequency(uint32_t frequency) = 0;
    virtual void enterDeepSleep(uint64_t sleepTimeUs) = 0;
    virtual void enableWakeupSource(int pin, int mode) = 0;
    virtual void update() = 0;
};

// ESP32 power manager implementation
class ESP32PowerManager : public AbstractPowerManager {
private:
    HardwareConfig* config;
    float lastBatteryVoltage;
    unsigned long lastBatteryCheck;
    
public:
    ESP32PowerManager(HardwareConfig* hwConfig);
    virtual ~ESP32PowerManager();
    virtual bool init() override;
    virtual float getBatteryVoltage() override;
    virtual uint8_t getBatteryPercentage() override;
    virtual bool isCharging() override;
    virtual bool isUSBPowered() override;
    virtual void enablePowerSave(bool enabled) override;
    virtual void setCPUFrequency(uint32_t frequency) override;
    virtual void enterDeepSleep(uint64_t sleepTimeUs) override;
    virtual void enableWakeupSource(int pin, int mode) override;
    virtual void update() override;
};

// Hardware abstraction layer manager
class HardwareManager {
private:
    static HardwareConfig config;
    static AbstractDisplay* display;
    static AbstractBLE* ble;
    static AbstractPowerManager* powerManager;
    static bool initialized;
    
    static bool detectHardware();
    static bool loadConfiguration();
    static bool createDisplayInstance();
    static bool createBLEInstance();
    static bool createPowerManagerInstance();
    
public:
    static bool init();
    static bool init(const HardwareConfig& hwConfig);
    static void shutdown();
    
    // Hardware access
    static AbstractDisplay* getDisplay();
    static AbstractBLE* getBLE();
    static AbstractPowerManager* getPowerManager();
    static HardwareConfig* getConfig();
    
    // Hardware detection
    static DisplayType detectDisplayType();
    static BLEType detectBLEType();
    static bool hasFeature(const char* feature);
    
    // Configuration management
    static bool saveConfiguration();
    static bool loadConfiguration(const char* filename);
    static void printConfiguration();
    
    // Hardware testing
    static bool testDisplay();
    static bool testBLE();
    static bool testPowerManager();
    static bool runHardwareTest();
};

// Hardware feature detection
namespace HardwareFeatures {
    bool hasDisplay();
    bool hasBLE();
    bool hasBattery();
    bool hasCharging();
    bool hasButtons();
    bool hasBuzzer();
    bool hasLED();
    bool hasSensors();
    bool hasWiFi();
    bool hasSDCard();
    bool hasRTC();
    
    // Platform-specific features
    bool supportsDeepSleep();
    bool supportsOTA();
    bool supportsTouchscreen();
    bool supportsCamera();
    bool supportsAudio();
}

// Hardware utilities
namespace HardwareUtils {
    // Pin management
    void configurePinMode(int pin, int mode);
    void setPinValue(int pin, int value);
    int getPinValue(int pin);
    void enablePullup(int pin, bool enabled);
    void enablePulldown(int pin, bool enabled);
    
    // Analog operations
    int readAnalog(int pin);
    void writeAnalog(int pin, int value);
    float analogToVoltage(int analogValue, float referenceVoltage = 3.3);
    
    // I2C operations
    bool initI2C(int sdaPin, int sclPin, uint32_t frequency = 100000);
    bool i2cWrite(uint8_t address, const uint8_t* data, size_t length);
    bool i2cRead(uint8_t address, uint8_t* data, size_t length);
    bool i2cScan(uint8_t* addresses, size_t* count);
    
    // SPI operations
    bool initSPI(int mosiPin, int misoPin, int sclkPin, uint32_t frequency = 1000000);
    void spiTransfer(const uint8_t* txData, uint8_t* rxData, size_t length);
    
    // System information
    const char* getPlatformName();
    const char* getChipModel();
    uint32_t getChipRevision();
    uint32_t getFlashSize();
    uint32_t getPSRAMSize();
    const char* getMACAddress();
}

// Default hardware configurations
extern const HardwareConfig ESP32_ST7789_CONFIG;
extern const HardwareConfig ESP32_ILI9341_CONFIG;
extern const HardwareConfig ESP8266_SSD1306_CONFIG;

// Macros for hardware abstraction
#define HAL_DISPLAY() HardwareManager::getDisplay()
#define HAL_BLE() HardwareManager::getBLE()
#define HAL_POWER() HardwareManager::getPowerManager()
#define HAL_CONFIG() HardwareManager::getConfig()

#define HAL_HAS_FEATURE(feature) HardwareFeatures::has##feature()
#define HAL_SUPPORTS(feature) HardwareFeatures::supports##feature()

#endif // HARDWARE_ABSTRACTION_H
