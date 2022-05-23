//imports
#include <WiFi101.h>
#include <MQTT.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include "secrets.h"


#define BUTTON_DEBOUNCE_DELAY 20


//support leds
#define CONNECTED_WIFI LED_BUILTIN  
#define CONNECTED_MQTTX D9   
#define IS_POWERED D8


//alarms led
#define FIRE_LED D7
#define PROXIMITY_LED D6
#define IS_PROXIMITY_BUTTON_ENABLED_LED D5


//variables
bool fire_level = false;
bool proximity = false;
bool is_proximity_enabled = false;


//input pins
#define PROXIMITY_SENSOR_PIN D4
#define BUTTON_PROXIMITY_ENABLER_PIN D3
#define FIRE_SENSOR_PIN A0


//wifi setup
char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;
#ifdef IP
IPAddress ip(IP);
IPAddress subnet(SUBNET);
IPAddress dns(DNS);
IPAddress gateway(GATEWAY);
#endif


// MQTT data
#define MQTT_BUFFER_SIZE 256               // the maximum size for packets being published and received
MQTTClient mqttClient(MQTT_BUFFER_SIZE);   // handles the MQTT communication protocol
WiFiClient networkClient;
#define MQTT_TOPIC_GENERIC "gmadotto1/general"
#define MQTT_BOARD_TOPIC_LOW_PRIORITY "gmadotto1/storage/low_priority"
#define MQTT_BOARD_TOPIC_HIGH_PRIORITY "gmadotto1/storage/high_priority"
bool is_subscribed_to_general = false;
bool is_already_sub_to_topic = false;


//timers
int high_priority_sensors_timer = 0;
int high_priority_sensors_timer_flag = 5000;

int connections_timer = 0;
int connections_timer_flag = 10000;


/*
 * SETUP
 */
void setup() {

  pinMode(IS_POWERED, OUTPUT);
  pinMode(CONNECTED_WIFI, OUTPUT);
  pinMode(CONNECTED_MQTTX, OUTPUT);
  pinMode(FIRE_LED, OUTPUT);
  pinMode(PROXIMITY_LED, OUTPUT);
  pinMode(IS_PROXIMITY_BUTTON_ENABLED_LED, OUTPUT);

  
  digitalWrite(IS_POWERED, HIGH);
  //led builtin HIGH -> led down 
  digitalWrite(CONNECTED_WIFI, HIGH);
  digitalWrite(CONNECTED_MQTTX, HIGH);
  digitalWrite(FIRE_LED, LOW);
  digitalWrite(PROXIMITY_LED, LOW);
  digitalWrite(IS_PROXIMITY_BUTTON_ENABLED_LED, LOW);
  
  
  Serial.begin(115200);
  delay(1000);
  Serial.println(F("\n=== Begin Setup ==="));
  
  //wifi
  Serial.println(F("Connecting to wifi.."));
  WiFi.mode(WIFI_STA);
  check_wifi();
  
  // setup MQTT
  Serial.println("");
  Serial.println(F("Setting up MQTT.."));
  mqttClient.begin(MQTT_BROKERIP, 1883, networkClient);   // setup communication with MQTT broker
  mqttClient.onMessage(mqttMessageReceived);
  checkMQTTBroker();
  
  
  //setup sensors
  Serial.println(F("Setting up sensors.."));
  //proximity
  Serial.println(F("Proximity sensor"));
  pinMode(PROXIMITY_SENSOR_PIN, INPUT);
  pinMode(BUTTON_PROXIMITY_ENABLER_PIN, INPUT);
  Serial.println(F("=== Setup completed ===\n"));
}
/*
 * LOOP
 */
void loop() {
  check_buttons();
  if(connections_timer >= connections_timer_flag){
    Serial.println(F("\nChecking if connections are ok.."));
    check_wifi();   
    checkMQTTBroker();
    connections_timer = 0;
  }
  
  mqttClient.loop();
  if(high_priority_sensors_timer >= high_priority_sensors_timer_flag && WiFi.status() == WL_CONNECTED){
    update_high_priority_sensors();
    high_priority_sensors_status();
    publish_high_priority_sensor_values();
    high_priority_sensors_timer = 0;
  }
  
  high_priority_sensors_timer++;
  connections_timer++;
  delay(1);
}

//ESP Reset
void soft_reset() { 
  NVIC_SystemReset();
}
String bool2str(bool value){
  if(value)
    return "TRUE";
  return "FALSE";
}

