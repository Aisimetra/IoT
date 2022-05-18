//imports
#include <ESP8266WiFi.h>
#include <MQTT.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include "secrets.h"

//variables
float humidity = 0.0;
float temperature = 0.0;
float real_temperature = 0.0;
byte light_level = 0;
long rssi = 0;

//input pins
#define DHT_PIN D3
#define LIGHT_SENSOR_PIN A0

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
#define MQTT_BOARD_TOPIC "gmadotto1/production"
bool is_subscribed_to_general = false;
bool is_already_sub_to_topic = false;

//timers
int global_timer = 0;
int max_global_timer = 40000;
int sensors_timer = 10000;
int connections_timer = 20000;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println(F("\n=== Begin Setup ==="));
  
  //wifi
  Serial.println("Connecting to wifi..");
  WiFi.mode(WIFI_STA);
  check_wifi();
  printWifiStatus();
  
  // setup MQTT
  Serial.println("");
  Serial.println("Setting up MQTT..");
  mqttClient.begin(MQTT_BROKERIP, 1883, networkClient);   // setup communication with MQTT broker
  mqttClient.onMessage(mqttMessageReceived);
  checkMQTTBroker();
  
  //setup sensors
  Serial.println("Setting up sensors..");
  //dth
  dht.begin();
  Serial.println("DTH11");
  //light sensor
  Serial.println("light sensor");
  pinMode(LIGHT_SENSOR_PIN, INPUT);
  
  Serial.println(F("=== Setup completed ==="));
}
void loop() {
  check_wifi();   
  checkMQTTBroker();
  mqttClient.loop();
  delay(1);
}

//ESP Reset
void soft_reset() { 
  ESP.reset();
}

