// #### WIFI STUFF ####
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

void check_wifi() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.print(F("Connecting to SSID: "));
    Serial.println(ssid);

    #ifdef IP
    WiFi.config(ip, dns, gateway, subnet);
    #endif

    WiFi.begin(ssid, pass);
    byte counter = 1;
    while (WiFi.status() != WL_CONNECTED) {
      Serial.print(F("."));
      if(counter % 25 == 0)
        Serial.println("");
      if(counter >= 250){
        Serial.println("failed to connect, restarting the device");
        soft_reset();
      }
      delay(250);
      counter++;
      
    }
    printWifiStatus();
    Serial.println(F("\nConnected!"));       
  }
}
