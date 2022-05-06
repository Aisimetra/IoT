//imports
#include <ESP8266WiFi.h>
#include <DHT.h>
#include <MySQL_Connection.h>
#include <MySQL_Cursor.h>
#include "secrets.h"

//variables
float humidity = 0.0;
float temperature = 0.0;
float real_temperature = 0.0;
byte light_level = 0;
long rssi = 0;

//thresholds
float hum_min_threshold = 20.0;
float hum_max_threshold = 80.0;

float temp_min_threshold = 18.0;
float temp_max_threshold = 24.0;

byte light_min_threshold = 20;
byte light_max_threshold = 220;

long rssi_min_threshold = -60;

//bool var
bool is_alert_events_enabled = true;
bool is_sensor_grid_enabled = true;
bool temp_event = false;
bool hum_event = false;
bool real_temp_event = false;
bool light_event = false;
bool rssi_event = false;

//input pins
#define DHT_PIN D3
#define LIGHT_SENSOR_PIN A0
#define SENSOR_GRID_BUTTON D0
#define ALERT_EVENTS_BUTTON D1

//button leds
#define SENSOR_GRID_LED D5
#define ALERT_EVENTS_LED D6

/*
//output pins
#define RSSI_ALERT_LED D2
#define HUMIDITY_ALERT_LED D5
#define TEMPERATURE_ALERT_LED D6
#define REAL_TEMPERATURE_ALERT_LED D7
#define LIGHT_ALERT_LED D8
*/
//wifi setup
char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;
#ifdef IP
IPAddress ip(IP);
IPAddress subnet(SUBNET);
IPAddress dns(DNS);
IPAddress gateway(GATEWAY);
#endif
WiFiClient client;

//dht setup
#define DHT_TYPE DHT11   // sensor type DHT 11
DHT dht = DHT(DHT_PIN, DHT_TYPE);


//altro
#define BUTTON_DEBOUNCE_DELAY 20
int counter = 0;

// MySQL server cfg
char mysql_user[] = MYSQL_USER;       // MySQL user login username
char mysql_password[] = MYSQL_PASS;   // MySQL user login password
IPAddress server_addr(MYSQL_IP);      // IP of the MySQL *server* here
MySQL_Connection conn((Client *)&client);

char query[256];
char INSERT_SENSOR_DATA[] = "INSERT INTO `gmadotto1`.`sensors` (`temperature`, `humidity`,`real_temperature`, `light_value`, `rssi`) VALUES (%f,%f,%f,%d,%d)";
char INSERT_ALERT_DATA[] = "INSERT INTO `gmadotto1`.`alerts` (`temperature_alert`,`humidity_alert`, `real_temperature_alert`, `light_value_alert`, `rssi_alert`) VALUES (%d,%d,%d,%d,%d)";


void setup() {
  //setup serial
  Serial.begin(115200);
  Serial.println("### SETUP ###");
  //esp mode
  WiFi.mode(WIFI_STA);
  
  //init dht
  dht.begin();
  
  //init light sensor
  pinMode(LIGHT_SENSOR_PIN, INPUT);


  //switches
  pinMode(SENSOR_GRID_BUTTON, INPUT);
  pinMode(ALERT_EVENTS_BUTTON, INPUT);

  //led switches
  pinMode(SENSOR_GRID_LED, OUTPUT);
  pinMode(ALERT_EVENTS_LED, OUTPUT);

  digitalWrite(SENSOR_GRID_LED, is_sensor_grid_enabled);
  digitalWrite(ALERT_EVENTS_LED, is_alert_events_enabled);
  /*
  //init alert leds
  pinMode(RSSI_ALERT_LED, OUTPUT);
  pinMode(HUMIDITY_ALERT_LED, OUTPUT);
  pinMode(TEMPERATURE_ALERT_LED, OUTPUT);
  pinMode(REAL_TEMPERATURE_ALERT_LED, OUTPUT);
  pinMode(LIGHT_ALERT_LED, OUTPUT);
  
  digitalWrite(RSSI_ALERT_LED, LOW);
  digitalWrite(HUMIDITY_ALERT_LED, LOW);
  digitalWrite(TEMPERATURE_ALERT_LED, LOW);
  digitalWrite(REAL_TEMPERATURE_ALERT_LED, LOW);
  digitalWrite(LIGHT_ALERT_LED, LOW);
  */
  Serial.println("### END SETUP ###\n");
}

void loop() {
  rssi = wifi();

  check_buttons();
  
  if (WiFi.status() == WL_CONNECTED) {

    if(is_sensor_grid_enabled && counter == 2000)
      update_sensor_values();
    if(is_alert_events_enabled && counter == 2000)
      update_alert_events();

    if(counter == 2000)
    debug_print();

    check_db_connection();
    
    if(is_sensor_grid_enabled && counter == 2000)
      update_sensors_db();
    if(is_alert_events_enabled && counter == 2000)
      update_alerts_db();
  }
  
  check_counter();
  
  counter++;
  delay(1);
}
int check_db_connection(){
  // connect to MySQL
  if (!conn.connected()) {
    conn.close();
    Serial.println(F("Connecting to MySQL..."));
    if (conn.connect(server_addr, 3306, mysql_user, mysql_password)) {
      Serial.println(F("MySQL connection established."));
    } else {
      Serial.println(F("MySQL connection failed."));
      return -1;
    }
  }
  return 1;
}
void check_buttons(){
  if(is_sensor_button_pressed()){
    is_sensor_grid_enabled = !is_sensor_grid_enabled;
    digitalWrite(SENSOR_GRID_LED, is_sensor_grid_enabled);

  }
  if(is_alert_button_pressed()){
    is_alert_events_enabled = !is_alert_events_enabled;
    digitalWrite(ALERT_EVENTS_LED, is_alert_events_enabled);
  }
}

void check_counter(){
  if(counter >= 2000)
    counter = 0;
}

boolean is_sensor_button_pressed() {
  static byte lastState = digitalRead(SENSOR_GRID_BUTTON);   // the previous reading from the input pin

  for (byte count = 0; count < BUTTON_DEBOUNCE_DELAY; count++) {
    if (digitalRead(SENSOR_GRID_BUTTON) == lastState) return false;
    delay(1);
  }

  lastState = !lastState;
  return lastState == HIGH ? false : true;
}

boolean is_alert_button_pressed() {
  static byte lastState = digitalRead(ALERT_EVENTS_BUTTON);   // the previous reading from the input pin

  for (byte count = 0; count < BUTTON_DEBOUNCE_DELAY; count++) {
    if (digitalRead(ALERT_EVENTS_BUTTON) == lastState) return false;
    delay(1);
  }

  lastState = !lastState;
  return lastState == HIGH ? false : true;
}
void debug_print(){
  Serial.println(F("##### DEBUG PRINT #####"));
  Serial.println(F("=== WiFi connection status ==="));
  wifi_status();
  Serial.println(F("=============================="));
  Serial.println(F("======= Sensors status ======="));
  sensors_status();
  Serial.println(F("=============================="));
  Serial.println(F("===== Alert Events status ===="));
  alert_events_status();
  Serial.println(F("=============================="));
  Serial.println(F("##### END DEBUG PRINT #####\n"));
  
}
int connect_db(){
  Serial.println("=== DB STATUS ===");
  // connect to MySQL
  if (!conn.connected()) {
    conn.close();
    Serial.println(F("Connecting to MySQL..."));
    if (conn.connect(server_addr, 3306, mysql_user, mysql_password)) {
      Serial.println(F("MySQL connection established."));
    } else {
      Serial.println(F("MySQL connection failed."));
      return -1;
    }
  }
  Serial.println("=================\n");
  return 1;
}
void update_sensors_db(){

  // log data
  MySQL_Cursor *cur_mem = new MySQL_Cursor(&conn);
  sprintf(query, INSERT_SENSOR_DATA, temperature, humidity, real_temperature, light_level, rssi);
  Serial.println(query);
  // execute the query
  cur_mem->execute(query);
  // Note: since there are no results, we do not need to read any data
  // deleting the cursor also frees up memory used
  delete cur_mem;
  Serial.println(F("Data recorded on MySQL"));
}
void update_alerts_db(){

  // log data
  MySQL_Cursor *cur_mem = new MySQL_Cursor(&conn);
  sprintf(query, INSERT_ALERT_DATA, temp_event, hum_event, real_temp_event, light_event, rssi_event);
  Serial.println(query);
  // execute the query
  cur_mem->execute(query);
  // Note: since there are no results, we do not need to read any data
  // deleting the cursor also frees up memory used
  delete cur_mem;
  Serial.println(F("Data recorded on MySQL"));
}
void update_sensor_values(){
  humidity = dht.readHumidity();
  temperature = dht.readTemperature();
  real_temperature = dht.computeHeatIndex(temperature, humidity, false);
  light_level = analogRead(LIGHT_SENSOR_PIN);
}

void update_alert_events(){
  //temp event
  if(isnan(temperature) || temperature < temp_min_threshold || temperature > temp_max_threshold){
    temp_event = true;
    //digitalWrite(TEMPERATURE_ALERT_LED, HIGH);
  }
  else{
    temp_event = false;
    //digitalWrite(TEMPERATURE_ALERT_LED, LOW);
  }
  //hum event
  if(isnan(humidity) || humidity < hum_min_threshold || humidity > hum_max_threshold){
    hum_event = true;
    //digitalWrite(HUMIDITY_ALERT_LED, HIGH);
  }
  else{
    hum_event = false;
    //digitalWrite(HUMIDITY_ALERT_LED, LOW);
  }
  //real temp event
  if(isnan(real_temperature) || real_temperature < temp_min_threshold || real_temperature > temp_max_threshold){
    real_temp_event = true;
    //digitalWrite(REAL_TEMPERATURE_ALERT_LED, HIGH);
  }
  else{
    real_temp_event = false;
    //digitalWrite(REAL_TEMPERATURE_ALERT_LED, LOW);
  }
  //light event
  if(isnan(light_level) || light_level < light_min_threshold || light_level > light_max_threshold){
    light_event = true;
    //digitalWrite(LIGHT_ALERT_LED, HIGH);
  }
  else{
    light_event = false;
    //digitalWrite(LIGHT_ALERT_LED, LOW);
  }
  //rssi event
  if(isnan(rssi) || rssi < rssi_min_threshold){
    rssi_event = true;
    //digitalWrite(RSSI_ALERT_LED, HIGH);
  }
  else{
    rssi_event = false;
    //digitalWrite(RSSI_ALERT_LED, LOW);
  }
}

void sensors_status(){
  // sensor grid
  Serial.print(F("sensor grid enabled: "));
  Serial.println(bool2str(is_sensor_grid_enabled));
  
  // alerting
  Serial.print(F("alerting events enabled: "));
  Serial.println(bool2str(is_alert_events_enabled));
  
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
void alert_events_status(){
  Serial.print(F("temperature alert: "));
  Serial.println(bool2str(temp_event));
  Serial.print(F("humidity alert: "));
  Serial.println(bool2str(hum_event));
  Serial.print(F("real temperature alert: "));
  Serial.println(bool2str(real_temp_event));
  Serial.print(F("light alert: "));
  Serial.println(bool2str(light_event));
  Serial.print(F("rssi alert: "));
  Serial.println(bool2str(rssi_event));
}


String bool2str(bool value){
  if(value)
    return "TRUE";
  return "FALSE";
}

long wifi() {
  long rssi_strength;
  // connect to WiFi (if not already connected)
  if (WiFi.status() != WL_CONNECTED) {
    Serial.print(F("Connecting to SSID: "));
    Serial.println(ssid);

    #ifdef IP
    WiFi.config(ip, dns, gateway, subnet);
    #endif

    WiFi.begin(ssid, pass);
    while (WiFi.status() != WL_CONNECTED) {
      Serial.print(F("."));
      delay(250);
    }
    Serial.println(F("\nConnected!"));
    rssi_strength = WiFi.RSSI();
    
  } else {
    rssi_strength = WiFi.RSSI();
  }

  return rssi_strength;
}

void wifi_status() {
  // SSID
  Serial.print(F("SSID: "));
  Serial.println(WiFi.SSID());

  // signal strength
  Serial.print(F("Signal strength (RSSI): "));
  Serial.print(WiFi.RSSI());
  Serial.println(F(" dBm"));

  // current IP
  Serial.print(F("IP Address: "));
  Serial.println(WiFi.localIP());

  // subnet mask
  Serial.print(F("Subnet mask: "));
  Serial.println(WiFi.subnetMask());

  // gateway
  Serial.print(F("Gateway IP: "));
  Serial.println(WiFi.gatewayIP());

  // DNS
  Serial.print(F("DNS IP: "));
  Serial.println(WiFi.dnsIP());
}

