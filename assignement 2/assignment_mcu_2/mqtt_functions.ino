// #### MQTT STUFF ####
void mqttMessageReceived(String &topic, String &payload) {
  Serial.println("Incoming MQTT message from [" + topic + "]: " + payload);
  if(topic.equals(MQTT_TOPIC_GENERIC)){
    // deserialize the JSON object
    StaticJsonDocument<128> doc;
    deserializeJson(doc, payload);
    String id = doc["id"];
    String mac = doc["mac"];
    if(id.equals("invite") && is_invited(mac)){
      Serial.println("Scheda invitata a connettersi");
      subscribe_to_topic(MQTT_BOARD_TOPIC);
      Serial.println("Invio conferma iscrizione..");
      const int capacity = JSON_OBJECT_SIZE(256);
      StaticJsonDocument<capacity> doc2;
      doc2["id"] = "confirm";
      doc2["mac"] = mac;
      char buffer[512];
      size_t n = serializeJson(doc2, buffer);
      mqttClient.publish(MQTT_TOPIC_GENERIC, buffer, n);
    }
  }  
}
bool is_invited(String mac){
  if(mac.equals(WiFi.macAddress()))
    return true;
  return false;
}
void reset_subscriptions(){
  Serial.println(F(">> Resetting subs"));
  is_subscribed_to_general = false;
}
void subscribe_to_topic(String topic){
  // connected to broker, subscribe topics
    mqttClient.subscribe(topic);
    Serial.print(F("\nSubscribed to ["));
    Serial.print(topic);
    Serial.println(F("]"));
}
void checkMQTTBroker() {
  if (!mqttClient.connected()) {   // not connected
    
    Serial.print(F("Connecting to MQTT broker..."));
    while (!mqttClient.connect(MQTT_CLIENTID, MQTT_USERNAME, MQTT_PASSWORD)) {
      Serial.print(F("."));
      delay(1000);
    }
    Serial.println(F("\nConnected!"));
    Serial.println(F(""));
    check_subscriptions();
  }
  
}
void check_subscriptions(){
  if (mqttClient.connected()) {
    //subscription check
    if(!is_subscribed_to_general){        
      subscribe_to_topic(MQTT_TOPIC_GENERIC);
      is_subscribed_to_general = true;
    }
    if(is_already_sub_to_topic){
       subscribe_to_topic(MQTT_BOARD_TOPIC);
    }
  }
}
