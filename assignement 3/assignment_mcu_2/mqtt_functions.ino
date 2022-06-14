/*
 * MQTT STUFF
 */
void mqttMessageReceived(String &topic, String &payload) {
  Serial.println("Incoming MQTT message from [" + topic + "]: " + payload);
  if(topic.equals(MQTT_TOPIC_GENERIC)){
    // deserialize the JSON object
    StaticJsonDocument<128> doc;
    deserializeJson(doc, payload);
    String id = doc["id"];
    String mac = doc["mac"];
    if(id.equalsIgnoreCase("invite")){
      if(is_invited(mac)){
        Serial.println("Scheda autorizzata a pubblicare");
        //subscribe_to_topic(MQTT_BOARD_TOPIC_LOW_PRIORITY);
        //subscribe_to_topic(MQTT_BOARD_TOPIC_HIGH_PRIORITY);
        is_already_sub_to_topic = true;
        Serial.println("Invio conferma iscrizione..");
        subscribe_to_topic(MQTT_BOARD_TOPIC_API);
        //json di iscrizione
        const int capacity = JSON_OBJECT_SIZE(256);
        StaticJsonDocument<capacity> doc2;
        doc2["id"] = "confirm";
        doc2["mac"] = mac;
        doc2["topic"] = MQTT_BOARD_TOPIC;
        //doc2["topic_l"] = MQTT_BOARD_TOPIC_LOW_PRIORITY;
        //doc2["topic_h"] = MQTT_BOARD_TOPIC_HIGH_PRIORITY;
        char buffer[512];
        size_t n = serializeJson(doc2, buffer);
        mqttClient.publish(MQTT_TOPIC_GENERIC, buffer, n);
      }else{
        Serial.println(mac);
        Serial.println("MAC Differente!");
      }  
    }
  }
//  else if(topic.equals(MQTT_BOARD_TOPIC_API)){
//    // deserialize the JSON object
//    
//    StaticJsonDocument<128> doc;
//    deserializeJson(doc, payload);
//    String id = doc["id"];
//    if(id.equalsIgnoreCase("request")){
//      Serial.println("nuova richiesta api");
//      String location = doc["location"];
//      String country = doc["country"]; 
//      loc = location;
//      ct = country;
//      is_authorized_to_get_data = true;
//    }
//  }
}
bool is_invited(String mac){
  if(mac.equalsIgnoreCase(WiFi.macAddress()))
    return true;
  return false;
}
void subscribe_to_topic(String topic){
  // connected to broker, subscribe topics
    mqttClient.subscribe(topic);
    Serial.print(F("Subscribed to ["));
    Serial.print(topic);
    Serial.println(F("]"));
}
void checkMQTTBroker() {
  if (!mqttClient.connected()) {   // not connected
    digitalWrite(CONNECTED_MQTTX, HIGH);
    Serial.print(F("Connecting to MQTT broker..."));
    while (!mqttClient.connect(MQTT_CLIENTID, MQTT_USERNAME, MQTT_PASSWORD)) {
      Serial.print(F("."));
      delay(500);
    }
    
    Serial.println(F(""));
    check_subscriptions();
  }
  digitalWrite(CONNECTED_MQTTX, LOW);
  Serial.println(F("Connected to MQTT"));
}
void check_subscriptions(){
  if (mqttClient.connected()) {
    //subscription check
    subscribe_to_topic(MQTT_TOPIC_GENERIC);
//    if(is_already_sub_to_topic){
//      subscribe_to_topic(MQTT_BOARD_TOPIC_API);
//    }   
  }
}
