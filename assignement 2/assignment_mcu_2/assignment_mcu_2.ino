//imports
#include <ESP8266WiFi.h>
#include <MQTT.h>
#include <ArduinoJson.h>
#include "secrets.h"

// WiFi cfg
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
#define MQTT_TOPIC_GENERIC "testtopic/general"
  char buffer[256];
   size_t n;

String topic_to_work = "";

byte state = 0;

void setup() {
  // put your setup code here, to run once:
  // setup MQTT
  mqttClient.begin(MQTT_BROKERIP, 1883, networkClient);   // setup communication with MQTT broker
  mqttClient.onMessage(mqttMessageReceived);
  Serial.begin(115200);
  Serial.println(F("\n\nSetup completed.\n\n"));
}

void loop() {
  connectToWiFi();
  mqttClient.loop();
  

      
  if(!mqttClient.connected()){
    connectToMQTTBroker(MQTT_TOPIC_GENERIC);  
    state = 0;
    Serial.println(state);


    
  // scrive la richiesta 
  const int capacity = JSON_OBJECT_SIZE(2);
  StaticJsonDocument<capacity> doc;
  doc["id"] = "sub_request";
  doc["type"] = "alarm";

   n = serializeJson(doc, buffer);
  Serial.print(F("JSON message: "));
  Serial.println(buffer);
  mqttClient.publish(MQTT_TOPIC_GENERIC, buffer, n);
    
  }
  else{
    if(state==0){
      Serial.println(state);
      subscribe_to_topic(MQTT_TOPIC_GENERIC);
      bool success = false;
      Serial.println("provo a inviare messaggio");
        Serial.print("sent text [");
        Serial.print(buffer);
        Serial.print("] to [");
        Serial.print(MQTT_TOPIC_GENERIC);
        Serial.println("]");
        state++;
    }
    if(state == 1){
      Serial.println(state);
      Serial.println("waiting for response");
      mqttClient.onMessage(mqttMessageReceived);
    }
    if(state==2){
      Serial.println(state);
      Serial.print("iscrizione al nuovo topic [");
      Serial.print(topic_to_work);
      Serial.println("]");
      mqttClient.subscribe(topic_to_work);
      Serial.print(F("\nSubscribed to ["));
      Serial.print(topic_to_work);
      Serial.println(F("]"));
      mqttClient.publish(topic_to_work, "CIAO BRO");
      state++;
    }
  }
  delay(5000);
}
  
  
void mqttMessageReceived(String &topic, String &payload) {
    Serial.println("Incoming MQTT message from [" + topic + "]: " + payload);

//    if (topic == MQTT_TOPIC_GENERIC) {
    // deserialize the JSON object
    StaticJsonDocument<128> doc;
    deserializeJson(doc, payload);
    const char *desiredRequest = doc["id"];
    const char *desiredTypeRequest = doc["type"];
    
    if (strcmp(desiredRequest, "invite") == 0 ) {   // ho ricevuto l'invito e nell'altro avrò il nuovo indirizzo
      topic_to_work = desiredTypeRequest;
      state++;
    } else {
      Serial.println(F("MQTT Topic not recognized, message skipped"));
   // }
  }
  
  
  
}
void connectToMQTTBroker(String topic) {
  if (!mqttClient.connected()) {   // not connected
    Serial.print(F("\nConnecting to MQTT broker..."));
    while (!mqttClient.connect(MQTT_CLIENTID, MQTT_USERNAME, MQTT_PASSWORD)) {
      Serial.print(F("."));
      delay(1000);
    }
    Serial.println(F("\nConnected!"));
  }
}
void subscribe_to_topic(String topic){
  // connected to broker, subscribe topics
    mqttClient.subscribe(topic);
    Serial.print(F("\nSubscribed to ["));
    Serial.print(topic);
    Serial.println(F("]"));
}
void printWifiStatus() {

  // print the SSID of the network you're attached to
  Serial.print(F("SSID: "));
  Serial.println(WiFi.SSID());

  // print your board's IP address
  IPAddress ip = WiFi.localIP();
  Serial.print(F("IP Address: "));
  Serial.println(ip);

  // print the received signal strength
  long rssi = WiFi.RSSI();
  Serial.print(F("Signal strength (RSSI):"));
  Serial.print(rssi);
  Serial.println(F(" dBm"));
  Serial.println(WiFi.macAddress());
}

void connectToWiFi() {
  if (WiFi.status() != WL_CONNECTED) {   // not connected
    Serial.print(F("Attempting to connect to SSID: "));
    Serial.println(SECRET_SSID);

    while (WiFi.status() != WL_CONNECTED) {
#ifdef IP
      WiFi.config(ip, dns, gateway, subnet);
#endif
      WiFi.mode(WIFI_STA);
      WiFi.begin(SECRET_SSID, SECRET_PASS);   // Connect to WPA/WPA2 network. Change this line if using open or WEP network
      Serial.print(F("."));
      delay(5000);
    }
    Serial.println(F("\nConnected"));
    printWifiStatus();
  }
}
