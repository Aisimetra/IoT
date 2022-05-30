/*
 * SENSORS STUFF
 */
void publish_sensor_values(){
  if(mqttClient.connected() && WiFi.status() == WL_CONNECTED && is_already_sub_to_topic){
    Serial.print(F("UPLOAD TO MQTT (LOW priority) on ["));
    Serial.print(MQTT_BOARD_TOPIC);
    Serial.println(F("]"));
    const int capacity = JSON_OBJECT_SIZE(256);
    StaticJsonDocument<capacity> doc;
    doc["id"] = "production";  
    doc["priority"] = "low";  
    doc["temperature"] = temperature;
    doc["real_temperature"] = real_temperature;
    doc["humidity"] = humidity;
    char buffer[256];
    size_t sensors = serializeJson(doc, buffer);
    mqttClient.publish(MQTT_BOARD_TOPIC, buffer, sensors);
  }
  else
    Serial.println(F("Failed to upload (not connected to MQTT or lost WIFI connection)"));
}
void publish_high_priority_sensor_values(){
  if(mqttClient.connected() && WiFi.status() == WL_CONNECTED && is_already_sub_to_topic){
    Serial.print(F("UPLOAD TO MQTT (HIGH priority) on ["));
    Serial.print(MQTT_BOARD_TOPIC);
    Serial.println(F("]"));
    const int capacity = JSON_OBJECT_SIZE(256);
    StaticJsonDocument<capacity> doc;
    doc["id"] = "production";  
    doc["priority"] = "high";  
    doc["fire"] = fire_level;
    doc["proximity"]=false;
    //doc["proximity"] = proximity;
    char buffer[256];
    size_t sensors = serializeJson(doc, buffer);
    mqttClient.publish(MQTT_BOARD_TOPIC, buffer, sensors);
  }
  else
    Serial.println(F("Failed to upload (not connected to MQTT or lost WIFI connection)"));
}
void update_high_priority_sensors(){
  //proximity = digitalRead(PROXIMITY_SENSOR_PIN);
  int fire = analogRead(FIRE_SENSOR_PIN);
  
  if(fire < 250){
    digitalWrite(FIRE_LED, HIGH);
    fire_level = true;
  }
  else{
    digitalWrite(FIRE_LED, LOW);
    fire_level = false;
  }
      
/*
  if(proximity){
    digitalWrite(PROXIMITY_LED, HIGH);
    proximity = true;
  }  
  else{
    digitalWrite(PROXIMITY_LED, LOW);
    proximity = false;
  }
      */
}
void update_sensor_values(){
  humidity = dht.readHumidity();
  temperature = dht.readTemperature();
  real_temperature = dht.computeHeatIndex(temperature, humidity, false);
  
  rssi = WiFi.RSSI();
}

void sensors_status(){
  Serial.println(F(""));
  Serial.println(F("LOW PRIORITY SENSOR READINGS"));
  // humidity
  Serial.print(F("humidity: "));
  Serial.println(humidity);

  // temperature
  Serial.print(F("temp: "));
  Serial.println(temperature);

  // real temperature
  Serial.print(F("real temp: "));
  Serial.println(real_temperature);

   // rssi
  Serial.print(F("rssi: "));
  Serial.println(rssi);

}
void high_priority_sensors_status(){
  Serial.println(F(""));
  Serial.println(F("HIGH PRIORITY SENSOR READINGS"));
  
  // fire level
  Serial.print(F("fire: "));
  Serial.println(bool2str(fire_level));

   // proximity
  Serial.print(F("proximity: "));
  Serial.println(bool2str(proximity));
}
