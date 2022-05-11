//imports
//esp8266 wifi
//#include <ESP8266WiFi.h>
//mkr wifi
#include <SPI.h>
#include <WiFi101.h>

#include <MySQL_Connection.h>
#include <MySQL_Cursor.h>
#include "secrets.h"

//mkr lcd
#include "rgb_lcd.h"
rgb_lcd lcd;

//sensor_values
float temperature = 0.0;
float humidity = 0.0;
float real_temperature = 0.0;
byte light_level = 0;
long rssi = 0;
long id = 0;
long prev_id = -1;
String timestamp = "";

//alerts
bool temp_event = false;
bool hum_event = false;
bool real_temp_event = false;
bool light_event = false;
bool rssi_event = false;

//leds
#define TEMPERATURE_ALERT_LED 0
#define HUMIDITY_ALERT_LED 1
#define LIGHT_ALERT_LED 2
#define RSSI_ALERT_LED 3

//wifi setup (ESP8266)
char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;
#ifdef IP
IPAddress ip(IP);
IPAddress subnet(SUBNET);
IPAddress dns(DNS);
IPAddress gateway(GATEWAY);
#endif
WiFiClient client;

// MySQL server cfg
char mysql_user[] = MYSQL_USER;       // MySQL user login username
char mysql_password[] = MYSQL_PASS;   // MySQL user login password
IPAddress server_addr(MYSQL_IP);      // IP of the MySQL *server* here
MySQL_Connection conn((Client *)&client);
MySQL_Cursor cur = MySQL_Cursor(&conn);

// QUERY
char query[256];
const char SELECT_SENSOR_DATA[] = "SELECT * FROM `gmadotto1`.`sensors` ORDER BY id DESC LIMIT 1";
char SELECT_ALERT_DATA[] = "SELECT * FROM `gmadotto1`.`alerts` ORDER BY id DESC LIMIT 1";

//altro
int counter = 0;
int timer = 5000;
byte grad[8] = {
  B00111,
  B00101,
  B00111,
  B00000,
  B00000,
  B00000,
  B00000,
  B00000,
};


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  //lcd setup
  lcd.begin(16, 2);   // 16 cols, 2 rows
  lcd.createChar(6,  grad);
  lcd.setRGB(255, 255, 255);
  lcd.home();
  lcd.clear();
  lcd.print("setup");
  
  //setup dei led di alert
  pinMode(RSSI_ALERT_LED, OUTPUT);
  pinMode(HUMIDITY_ALERT_LED, OUTPUT);
  pinMode(TEMPERATURE_ALERT_LED, OUTPUT);
  pinMode(LIGHT_ALERT_LED, OUTPUT);
  
  
  digitalWrite(RSSI_ALERT_LED, HIGH);
  digitalWrite(HUMIDITY_ALERT_LED, HIGH);
  digitalWrite(TEMPERATURE_ALERT_LED, HIGH);
  digitalWrite(LIGHT_ALERT_LED, HIGH);
  lcd.clear();
  lcd.print("setup completed");
}

void loop() {
  if(check_timer()){
	//check wifi
    connect_wifi("esp");
    if(WiFi.status() == WL_CONNECTED){
      debug_print();
	  //connessione al db
      connect_db();
	  //recupero i sensori dal db
      get_db_sensor_values();
      get_db_alert_values();
    }+ì
    lcd_print();
    update_leds();
  }
  delay(1);
  counter++;
}
void update_leds(){
  //temp event
  if(temp_event){
    digitalWrite(TEMPERATURE_ALERT_LED, HIGH);
  }
  else{
    digitalWrite(TEMPERATURE_ALERT_LED, LOW);
  }
  //hum event
  if(hum_event){
    digitalWrite(HUMIDITY_ALERT_LED, HIGH);
  }
  else{
    digitalWrite(HUMIDITY_ALERT_LED, LOW);
  }
  //light event
  if(light_event){
    digitalWrite(LIGHT_ALERT_LED, HIGH);
  }
  else{
    digitalWrite(LIGHT_ALERT_LED, LOW);
  }
  //rssi event
  if(rssi_event){
    digitalWrite(RSSI_ALERT_LED, HIGH);
  }
  else{
    digitalWrite(RSSI_ALERT_LED, LOW);
  }
}
void lcd_print(){
  lcd.home();               // move cursor to 0,0
  lcd.clear();    
  lcd.print("T:");
  lcd.print(temperature);
  lcd.write(6);
  lcd.print("C H:");
  lcd.print(humidity);
  lcd.print("%");
  lcd.setCursor(0, 1);
  lcd.print("L:");
  lcd.print(light_level);
  lcd.print(" R:");
  lcd.print(rssi);  

  delay(5000);

  lcd.home();               // move cursor to 0,0
  lcd.clear();    
  lcd.print("T:");
  lcd.print(bool2str(temp_event));
  lcd.print(" H:");
  lcd.print(bool2str(hum_event));

  lcd.setCursor(0, 1);
  lcd.print("L:");
  lcd.print(bool2str(light_event));
  lcd.print(" R:");
  lcd.print(bool2str(rssi_event));
}
bool check_timer(){
  if(counter >= timer){
    counter = 0;
    return true;
  }
  return false;
}
void connect_wifi(String device){
  // connection stage ----------------------------------------------
  if(device.equalsIgnoreCase("esp")){
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
    }
  }
  if(device.equalsIgnoreCase("mkr")){
    bool first_status_print = false;
    bool static led_status = HIGH;
    long rssi =  WiFi.RSSI();

    while (WiFi.status() != WL_CONNECTED) {
      lcd.clear();
      lcd.print("connessione al wifi");
      Serial.print("Attempting to connect to network: ");
      Serial.println(ssid);

      // for static ip by default network is configured using DHCP
      #ifdef IP
        WiFi.config(ip, dns, gateway, subnet);
      #endif

      WiFi.begin(ssid, pass); // start connection
      // wait 1 seconds for connection:
      delay(1000);
      first_status_print = true;
    }
    if(WiFi.status() == WL_CONNECTED and first_status_print == true){
        lcd.clear();
        lcd.print("connesso!");
        Serial.println("Connection Successful");
      }
    // end connection stage ----------------------------------------------
  }
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
}
void debug_print(){
  Serial.println(F("\n\n##### NEW ITERATION #####"));
  Serial.println(F("=== WiFi connection status ==="));
  wifi_status();
  Serial.println(F("=============================="));
  Serial.println(F("======= Sensors status ======="));
  sensors_status();
  Serial.println(F("=============================="));
  Serial.println(F("===== Alert Events status ===="));
  alert_events_status();
  Serial.println(F("=============================="));
  
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
  }else{
    Serial.println(F("Connected to db"));
  }
  Serial.println("=================\n");
  return 1;
}

void get_db_sensor_values(){
  MySQL_Cursor *cur_mem = new MySQL_Cursor(&conn);
  sprintf(query, SELECT_SENSOR_DATA, 9000000);
  cur_mem->execute(SELECT_SENSOR_DATA);
  column_names *cols = cur_mem->get_columns();
  for (int f = 0; f < cols->num_fields; f++) {
    Serial.print(cols->fields[f]->name);
    if (f < cols->num_fields-1) {
      Serial.print(',');
    }
  }
  Serial.println();
  // Read the rows and print them
  row_values *row = NULL;
  do {
    row = cur_mem->get_next_row();
    if (row != NULL) {
      for (int f = 0; f < cols->num_fields; f++) {
        Serial.print(row->values[f]);
        if (f < cols->num_fields-1) {
          Serial.print(',');
        }
      }
      Serial.println();
      //aggiorno i valori
      id = atol(row->values[0]);
      timestamp = atol(row->values[1]);
      temperature = atol(row->values[2]);
      humidity = atol(row->values[3]);
      //real_temperature = atol(row->values[4]);
      light_level = atol(row->values[5]);
      rssi = atol(row->values[6]);
    }
  } while (row != NULL);
  // Deleting the cursor also frees up memory used
  delete cur_mem;
}
void get_db_alert_values(){
  MySQL_Cursor *cur_mem = new MySQL_Cursor(&conn);
  sprintf(query, SELECT_ALERT_DATA, 9000000);
  cur_mem->execute(SELECT_ALERT_DATA);
  column_names *cols = cur_mem->get_columns();
  for (int f = 0; f < cols->num_fields; f++) {
    Serial.print(cols->fields[f]->name);
    if (f < cols->num_fields-1) {
      Serial.print(',');
    }
  }
  Serial.println();
  // Read the rows and print them
  row_values *row = NULL;
  do {
    row = cur_mem->get_next_row();
    if (row != NULL) {
      for (int f = 0; f < cols->num_fields; f++) {
        Serial.print(row->values[f]);
        if (f < cols->num_fields-1) {
          Serial.print(',');
        }
      }
      Serial.println();
      temp_event = atol(row->values[2]);
      hum_event = atol(row->values[3]);
      real_temp_event = atol(row->values[4]);
      light_event = atol(row->values[5]);
      rssi_event = atol(row->values[6]);
    }
  } while (row != NULL);
  // Deleting the cursor also frees up memory used
  delete cur_mem;
}

void sensors_status(){  
  //id
  Serial.print(F("id: "));
  Serial.println(id);
    //timestamp
  Serial.print(F("timestamp: "));
  Serial.println(timestamp);
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
