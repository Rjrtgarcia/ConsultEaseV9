/**
 * Enhanced messaging system for ConsultEase Faculty Desk Unit
 * Supports new consultation format and improved message handling
 */

#ifndef ENHANCED_MESSAGING_H
#define ENHANCED_MESSAGING_H

#include <Arduino.h>
#include <ArduinoJson.h>

// Message type definitions
enum MessageType {
    MSG_CONSULTATION_REQUEST,
    MSG_SYSTEM_NOTIFICATION,
    MSG_STATUS_UPDATE,
    MSG_EMERGENCY,
    MSG_MAINTENANCE,
    MSG_UNKNOWN
};

// Priority levels
enum MessagePriority {
    PRIORITY_LOW = 1,
    PRIORITY_NORMAL = 2,
    PRIORITY_HIGH = 3,
    PRIORITY_URGENT = 4,
    PRIORITY_EMERGENCY = 5
};

// Message status
enum MessageStatus {
    STATUS_UNREAD,
    STATUS_READ,
    STATUS_ACKNOWLEDGED,
    STATUS_EXPIRED
};

// Enhanced consultation request structure
struct ConsultationRequest {
    char studentId[16];
    char studentName[64];
    char studentDepartment[32];
    char courseCode[16];
    char courseName[64];
    char requestMessage[256];
    char timestamp[32];
    MessagePriority priority;
    unsigned long expiryTime;
    bool requiresResponse;
    char sessionId[32];
};

// System notification structure
struct SystemNotification {
    char notificationId[32];
    char title[64];
    char message[128];
    char timestamp[32];
    MessagePriority priority;
    unsigned long expiryTime;
    bool persistent;
};

// Enhanced message container
struct EnhancedMessage {
    MessageType type;
    MessagePriority priority;
    MessageStatus status;
    unsigned long receivedTime;
    unsigned long expiryTime;
    char messageId[32];
    char senderId[32];
    
    union {
        ConsultationRequest consultation;
        SystemNotification notification;
        char rawMessage[512];
    } data;
};

// Message parser class
class MessageParser {
private:
    static DynamicJsonDocument jsonDoc;
    static bool parseConsultationRequest(const char* json, ConsultationRequest& request);
    static bool parseSystemNotification(const char* json, SystemNotification& notification);
    static MessageType detectMessageType(const char* json);
    static MessagePriority parsePriority(const char* priorityStr);
    
public:
    static void init();
    static bool parseMessage(const char* rawMessage, EnhancedMessage& message);
    static bool parseJSON(const char* json, EnhancedMessage& message);
    static bool parsePlainText(const char* text, EnhancedMessage& message);
    static bool validateMessage(const EnhancedMessage& message);
    static void printMessage(const EnhancedMessage& message);
};

// Message queue management
class MessageQueue {
private:
    static const int MAX_MESSAGES = 10;
    static EnhancedMessage messages[MAX_MESSAGES];
    static int messageCount;
    static int currentIndex;
    static unsigned long lastCleanup;
    
    static void removeExpiredMessages();
    static int findOldestMessage();
    static void shiftMessages(int startIndex);
    
public:
    static void init();
    static bool addMessage(const EnhancedMessage& message);
    static bool getMessage(int index, EnhancedMessage& message);
    static bool getCurrentMessage(EnhancedMessage& message);
    static bool getNextMessage(EnhancedMessage& message);
    static bool getPreviousMessage(EnhancedMessage& message);
    static int getMessageCount();
    static int getUnreadCount();
    static void markAsRead(int index);
    static void markAsAcknowledged(int index);
    static void removeMessage(int index);
    static void clearAll();
    static void cleanup();
    static void printQueue();
};

// Enhanced display manager
class EnhancedDisplayManager {
private:
    static EnhancedMessage currentMessage;
    static bool messageDisplayed;
    static unsigned long displayStartTime;
    static int currentPage;
    static int totalPages;
    
    static void displayConsultationRequest(const ConsultationRequest& request);
    static void displaySystemNotification(const SystemNotification& notification);
    static void displayMessageHeader(const EnhancedMessage& message);
    static void displayMessageFooter(const EnhancedMessage& message);
    static void displayPriorityIndicator(MessagePriority priority);
    static void displayStatusIndicator(MessageStatus status);
    static void calculatePages(const char* text);
    static void displayPage(const char* text, int page);
    
public:
    static void init();
    static void displayMessage(const EnhancedMessage& message);
    static void displayMessageQueue();
    static void nextPage();
    static void previousPage();
    static void nextMessage();
    static void previousMessage();
    static void refreshDisplay();
    static void clearDisplay();
    static bool isMessageDisplayed();
    static void setAutoAdvance(bool enabled, unsigned long interval);
};

// Message notification system
class NotificationManager {
private:
    static bool audioEnabled;
    static bool visualEnabled;
    static int buzzerPin;
    static unsigned long lastNotification;
    static MessagePriority lastPriority;
    
    static void playNotificationSound(MessagePriority priority);
    static void showVisualNotification(MessagePriority priority);
    static void flashDisplay(int count, unsigned long interval);
    
public:
    static void init(int buzzerPin = -1);
    static void enableAudio(bool enabled);
    static void enableVisual(bool enabled);
    static void notifyNewMessage(const EnhancedMessage& message);
    static void notifyUrgentMessage(const EnhancedMessage& message);
    static void notifyEmergencyMessage(const EnhancedMessage& message);
    static void setVolume(int volume);
    static void testNotifications();
};

// Message response system
class ResponseManager {
private:
    static char responseBuffer[256];
    static bool responseRequired;
    static char currentSessionId[32];
    
public:
    static void init();
    static bool isResponseRequired();
    static void setResponseRequired(bool required, const char* sessionId = nullptr);
    static bool sendAcknowledgment(const char* messageId);
    static bool sendResponse(const char* messageId, const char* response);
    static void clearResponse();
    static const char* getCurrentSessionId();
};

// Message statistics and monitoring
class MessageStatistics {
private:
    static unsigned long totalMessages;
    static unsigned long consultationRequests;
    static unsigned long systemNotifications;
    static unsigned long emergencyMessages;
    static unsigned long averageResponseTime;
    static unsigned long lastResetTime;
    
public:
    static void init();
    static void recordMessage(MessageType type);
    static void recordResponseTime(unsigned long responseTime);
    static void printStatistics();
    static void resetStatistics();
    static unsigned long getTotalMessages();
    static unsigned long getMessagesPerHour();
    static float getAverageResponseTime();
};

// Message formatting utilities
namespace MessageFormatter {
    // Text formatting
    void formatConsultationForDisplay(const ConsultationRequest& request, char* output, size_t outputSize);
    void formatNotificationForDisplay(const SystemNotification& notification, char* output, size_t outputSize);
    void formatTimestamp(const char* timestamp, char* formatted, size_t formattedSize);
    void formatPriority(MessagePriority priority, char* formatted, size_t formattedSize);
    
    // Text wrapping and pagination
    int calculateTextPages(const char* text, int lineWidth, int linesPerPage);
    void getTextPage(const char* text, int page, int lineWidth, int linesPerPage, char* output, size_t outputSize);
    void wrapText(const char* input, char* output, size_t outputSize, int lineWidth);
    
    // Color and styling
    uint16_t getPriorityColor(MessagePriority priority);
    uint16_t getStatusColor(MessageStatus status);
    uint16_t getTypeColor(MessageType type);
}

// Configuration and settings
struct MessagingConfig {
    bool enableNotifications;
    bool enableAudio;
    bool enableVisual;
    int maxMessages;
    unsigned long messageTimeout;
    unsigned long displayTimeout;
    bool autoAdvance;
    unsigned long autoAdvanceInterval;
    MessagePriority minNotificationPriority;
};

extern MessagingConfig messagingConfig;

// Function prototypes
void initEnhancedMessaging();
void processIncomingMessage(const char* topic, const char* payload);
void updateMessagingSystem();
void handleMessageTimeout();
void handleUserInteraction();

// Macros for enhanced messaging
#define MSG_RECORD_STAT(type) MessageStatistics::recordMessage(type)
#define MSG_NOTIFY(message) NotificationManager::notifyNewMessage(message)
#define MSG_DISPLAY(message) EnhancedDisplayManager::displayMessage(message)
#define MSG_QUEUE_ADD(message) MessageQueue::addMessage(message)

#endif // ENHANCED_MESSAGING_H
