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
#define MQTT_BOARD_TOPIC "gmadotto1/production"
bool is_subscribed_to_general = false;
bool is_already_sub_to_topic = false;

//timers
int sensors_timer = 0;
int sensors_timer_flag = 10000;
int connections_timer = 0;
int connections_timer_flag = 20000;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println(F("\n=== Begin Setup ==="));
  
  //wifi
  Serial.println("Connecting to wifi..");
  WiFi.mode(WIFI_STA);
  check_wifi();
  
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
  
  Serial.println(F("=== Setup completed ===\n"));
}
void loop() {
  mqttClient.loop();
  if(connections_timer >= connections_timer_flag){
    Serial.println(F("\nChecking if connections are ok.."));
    check_wifi();   
    checkMQTTBroker();
    connections_timer = 0;
  }
  if(sensors_timer >= sensors_timer_flag){
    update_sensor_values();
    sensors_status();
    publish_sensor_values();
    sensors_timer = 0;
  }
  sensors_timer++;
  connections_timer++;
  delay(1);
}
void publish_sensor_values(){
  if(is_already_sub_to_topic){
    Serial.print(F("pubblico dati dei sensori su ["));
    Serial.print(MQTT_BOARD_TOPIC);
    Serial.println(F("]"));
    const int capacity = JSON_OBJECT_SIZE(256);
    StaticJsonDocument<capacity> doc;
    doc["id"] = "sensor_values_production";  
    doc["temperature"] = temperature;
    doc["real_temperature"] = real_temperature;
    doc["humidity"] = humidity;
    doc["light"] = light_level;
    doc["rssi"] = rssi;
    char buffer[256];
    size_t sensors = serializeJson(doc, buffer);
    mqttClient.publish(MQTT_BOARD_TOPIC, buffer, sensors);
    //doc2["temperature"] = temperature;
    //doc2["real_temperature"] = real_temperature;
    //doc2["light"] = light_level;
    //doc2["rssi"] = rssi;
    //char buffer[128];
    //size_t n = serializeJson(sensors, buffer);
    //mqttClient.publish(topic, buffer, n);
  }
}
void update_sensor_values(){
  humidity = dht.readHumidity();
  temperature = dht.readTemperature();
  real_temperature = dht.computeHeatIndex(temperature, humidity, false);
  light_level = analogRead(LIGHT_SENSOR_PIN);
}

void sensors_status(){
  Serial.println(F(""));
  Serial.println(F("SENSOR READINGS"));
  // humidity
  Serial.print(F("humidity: "));
  Serial.println(humidity);

  // temperature
  Serial.print(F("temp: "));
  Serial.println(temperature);

  // real temperature
  Serial.print(F("real temp: "));
  Serial.println(real_temperature);

  // light level
  Serial.print(F("light: "));
  Serial.println(light_level);
}

//ESP Reset
void soft_reset() { 
  ESP.reset();
}

