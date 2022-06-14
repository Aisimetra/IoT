//imports
#include <ESP8266WiFi.h>
#include <MQTT.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include "secrets.h"


//support leds
#define CONNECTED_WIFI LED_BUILTIN  
#define CONNECTED_MQTTX LED_BUILTIN_AUX   
#define IS_POWERED D1


//alarms led
#define FIRE_LED D8
//#define PROXIMITY_LED D6


//variables
float humidity = 0.0;
float temperature = 0.0;
float real_temperature = 0.0;
bool fire_level = false;
long rssi = 0;
bool proximity = false;

bool previous_fire_state = false;



//input pins
//#define PROXIMITY_SENSOR_PIN D5
#define DHT_PIN D3
#define FIRE_SENSOR_PIN A0


//declare DHT
#define DHT_TYPE DHT11   // sensor type DHT 11
DHT dht = DHT(DHT_PIN, DHT_TYPE);


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
#define MQTT_BOARD_TOPIC "gmadotto1/data"
#define MQTT_BOARD_TOPIC_API "gmadotto1/api"


// weather api (refer to https://openweathermap.org/current)
String loc="";
String ct="";
float lat = 0.0;
float lon = 0.0;
bool is_authorized_to_get_data = false;
WiFiClient client;
const char weather_server[] = "api.openweathermap.org";
//const char weather_query[] = "GET /data/2.5/forecast?lat=%f&lon=%f&cnt=5&appid=%s";
const char weather_query[] = "GET /data/2.5/weather?q=%s,%s&units=metric&APPID=%s";
const char location_query[] = "GET /geo/1.0/direct?q=%s,%s&limit=1&appid=%s";
//"GET /data/2.5/weather?q=%s,%s&units=metric&APPID=%s";


bool is_subscribed_to_general = false;
bool is_already_sub_to_topic = false;


//timers
int low_priority_sensors_timer = 0;
int low_priority_sensors_timer_flag = 20000;

int high_priority_sensors_timer = 0;
int high_priority_sensors_timer_flag = 1000;

int connections_timer = 0;
int connections_timer_flag = 10000;

bool wifi_status = false;


/*
 * SETUP
 */
void setup() {

  pinMode(IS_POWERED, OUTPUT);
  pinMode(CONNECTED_WIFI, OUTPUT);
  pinMode(CONNECTED_MQTTX, OUTPUT);
  pinMode(FIRE_LED, OUTPUT);

  
  digitalWrite(IS_POWERED, HIGH);
  //led builtin HIGH -> led down 
  digitalWrite(CONNECTED_WIFI, HIGH);
  digitalWrite(CONNECTED_MQTTX, HIGH);
  digitalWrite(FIRE_LED, LOW);

  Serial.begin(115200);
  delay(1000);
  Serial.println(F("\n=== Begin Setup ==="));
  
  //wifi
  //Serial.println(F("Connecting to wifi.."));
  //WiFi.mode(WIFI_STA);
  //check_wifi();
  
  // setup MQTT
  Serial.println("");
  Serial.println(F("Setting up MQTT.."));
  mqttClient.begin(MQTT_BROKERIP, 1883, networkClient);   // setup communication with MQTT broker
  mqttClient.onMessage(mqttMessageReceived);
  //checkMQTTBroker();
  
  
  //setup sensors
  Serial.println(F("Setting up sensors.."));
  //dth
  dht.begin();
  Serial.println(F("DTH11"));
  
  WiFi.mode(WIFI_OFF);
  WiFi.forceSleepBegin();
  Serial.println("WiFi is down");
  wifi_status = false;
  Serial.println(F("=== Setup completed ===\n"));
  
}
/*
 * LOOP
 */
void loop() {
//  if(connections_timer >= connections_timer_flag){
//    WiFi.forceSleepWake();
//    delay(2);
//    Serial.println(F("\nWifi is on"));
//    wifi_status = true;
//    Serial.println(F("Checking if connections are ok.."));
//    check_wifi();   
//    checkMQTTBroker();
//  }
//  mqttClient.loop();
  
  if(low_priority_sensors_timer >= low_priority_sensors_timer_flag){
    update_sensor_values();
    sensors_status();
    wake_mcu();
    delay(500);
    mqttClient.loop();
    publish_sensor_values();
    delay(500);
    low_priority_sensors_timer = 0;
    send_mcu_to_sleep();
  }
  
  if(high_priority_sensors_timer >= high_priority_sensors_timer_flag){
    update_high_priority_sensors();
    previous_fire_state = fire_level;
      high_priority_sensors_status();
      wake_mcu();
      delay(500);
      mqttClient.loop();
      publish_high_priority_sensor_values();
      delay(500);
      send_mcu_to_sleep();
    if(fire_level != previous_fire_state){
      
    }
    previous_fire_state = fire_level;
    high_priority_sensors_timer = 0;
    
  }
//  if(is_authorized_to_get_data && wifi_status){
//    //retrieve_location()
//    delay(100);
//    get_weather(true);
//    is_authorized_to_get_data = false;
//  }
  high_priority_sensors_timer++;
  low_priority_sensors_timer++;
  connections_timer++;
  delay(1);
}

//ESP Reset
void soft_reset() { 
  ESP.reset();
}
String bool2str(bool value){
  if(value)
    return "TRUE";
  return "FALSE";
}

void wake_mcu(){
  WiFi.forceSleepWake();
    delay(2);
    Serial.println(F("\nWifi is on"));
    wifi_status = true;
    Serial.println(F("Checking if connections are ok.."));
    check_wifi();   
    checkMQTTBroker();
}
void send_mcu_to_sleep(){
  WiFi.mode(WIFI_OFF);
  WiFi.forceSleepBegin();
  Serial.println("WiFi is down");
  wifi_status = false;
}

