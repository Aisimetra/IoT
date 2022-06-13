//bool retrieve_location() {
//  Serial.println(F("\n=== Location ==="));
//  char location[loc.length()+1];
//  char country[ct.length()+1];
//  loc.toCharArray(location, sizeof(loc));
//  ct.toCharArray(country, sizeof(ct));
//  // call API for current weather
//  if (client.connect(weather_server, 80)) {
//    char request[100];
//    sprintf(request, location_query, location, country, WEATHER_API_KEY);
//    client.println(request);
//    client.println(F("Host: api.openweathermap.org"));
//    client.println(F("User-Agent: ArduinoWiFi/1.1"));
//    client.println(F("Connection: close"));
//    client.println();
//  } else {
//    Serial.println(F("Connection to api.openweathermap.org failed!\n"));
//    return false;
//  }
//
//  while (client.connected() && !client.available()) delay(1);   // wait for data
//  String result;
//  while (client.connected() || client.available()) {   // read data
//    char c = client.read();
//    result = result + c;
//  }
//  
//  client.stop();   // end communication
//  //result.replace('⸮', '\0');
//  Serial.println(result);  // print JSON
//
//  char jsonArray[result.length() + 1];
//  result.toCharArray(jsonArray, sizeof(jsonArray));
//  jsonArray[result.length() + 1] = '\0';
//  StaticJsonDocument<1024> doc;
//  DeserializationError error = deserializeJson(doc, jsonArray);
//
//  if (error) {
//    Serial.print(F("deserializeJson() failed: "));
//    Serial.println(error.c_str());
//    return false;
//  }
//
//  lat = (float)doc[0]["lat"];
//  lon = (float)doc[0]["lon"];
//  Serial.print(F("Location: "));
//  Serial.println(doc[0]["name"].as<String>());
//  Serial.print(F("Country: "));
//  Serial.println(doc[0]["country"].as<String>());
//  Serial.print(F("lon: "));
//  Serial.println((float)doc[0]["lat"]);
//  Serial.print(F("lat: "));
//  Serial.println((float)doc[0]["lon"]);
//  Serial.println(F("==============================\n"));
//  return true;
//}


bool get_weather(bool flag){
  Serial.println(F("\n=== Forecast ==="));
  char location[loc.length()+1];
  char country[ct.length()+1];
  loc.toCharArray(location, sizeof(loc));
  ct.toCharArray(country, sizeof(ct));
  if(flag){
    // call API for current weather
    if (client.connect(weather_server, 80)) {
      char request[200];
      //sprintf(request, weather_query, lat, lon, WEATHER_API_KEY);
      sprintf(request, weather_query, location, country, WEATHER_API_KEY);
      client.println(request);
      client.println(F("Host: api.openweathermap.org"));
      client.println(F("User-Agent: ArduinoWiFi/1.1"));
      client.println(F("Connection: close"));
      client.println();
    } else {
      Serial.println(F("Connection to api.openweathermap.org failed!\n"));
      client.stop();   // end communication
      return false;
    }
  
    while (client.connected() && !client.available()) delay(1);   // wait for data
    String result;
    while (client.connected() || client.available()) {   // read data
      char c = client.read();
      result = result + c;
    }
    
    client.stop();   // end communication
    //result.replace('⸮', '\0');
    Serial.println(result);  // print JSON
  
    char jsonArray[result.length() + 1];
    result.toCharArray(jsonArray, sizeof(jsonArray));
    jsonArray[result.length() + 1] = '\0';
    StaticJsonDocument<1024> doc;
    DeserializationError error = deserializeJson(doc, jsonArray);
  
    if (error) {
      Serial.print(F("deserializeJson() failed: "));
      Serial.println(error.c_str());
      return false;
    }
    Serial.print(F("Location: "));
  Serial.println(doc["name"].as<String>());
  Serial.print(F("Country: "));
  Serial.println(doc["sys"]["country"].as<String>());
  Serial.print(F("Temperature (°C): "));
  Serial.println((float)doc["main"]["temp"]);
  Serial.print(F("Humidity (%): "));
  Serial.println((float)doc["main"]["humidity"]);
  Serial.print(F("Weather: "));
  Serial.println(doc["weather"][0]["main"].as<String>());
  Serial.print(F("Weather description: "));
  Serial.println(doc["weather"][0]["description"].as<String>());
  Serial.print(F("Pressure (hPa): "));
  Serial.println((float)doc["main"]["pressure"]);
  Serial.print(F("Sunrise (UNIX timestamp): "));
  Serial.println((float)doc["sys"]["sunrise"]);
  Serial.print(F("Sunset (UNIX timestamp): "));
  Serial.println((float)doc["sys"]["sunset"]);
  Serial.print(F("Temperature min. (°C): "));
  Serial.println((float)doc["main"]["temp_min"]);
  Serial.print(F("Temperature max. (°C): "));
  Serial.println((float)doc["main"]["temp_max"]);
  Serial.print(F("Wind speed (m/s): "));
  Serial.println((float)doc["wind"]["speed"]);
  Serial.print(F("Wind angle: "));
  Serial.println((float)doc["visibility"]);
  Serial.print(F("Visibility (m): "));
  Serial.println((float)doc["wind"]["deg"]);

  Serial.println(F("==============================\n"));

  if(mqttClient.connected() && WiFi.status() == WL_CONNECTED && is_already_sub_to_topic){
    Serial.print(F("UPLOAD TO MQTT (api) on ["));
    Serial.print(MQTT_BOARD_TOPIC_API);
    Serial.println(F("]"));
    //const int capacity = JSON_OBJECT_SIZE(1024);
    StaticJsonDocument<2048> query;
    query["id"] = "result";  
    query["location"] = doc["name"].as<String>();
    query["country"] = doc["sys"]["country"].as<String>();
    query["temp"] = (float)doc["main"]["temp"];
    query["humidity"] = (float)doc["main"]["humidity"];
    query["temp_min"] = (float)doc["main"]["temp_min"];
    query["temp_max"] = (float)doc["main"]["temp_max"];
    query["weather"] = doc["weather"][0]["main"].as<String>();
    char buffer[2048];
    size_t api = serializeJson(query, buffer);
    mqttClient.publish(MQTT_BOARD_TOPIC_API, buffer, api);
  }else{
    Serial.println(F("Failed to upload [api result] (not connected to MQTT or lost WIFI connection)"));
    return false;
  }
    return true;
  }
  client.stop();   // end communication
  return false;
}

