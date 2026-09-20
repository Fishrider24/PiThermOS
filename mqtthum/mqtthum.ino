/*
  PiThermOS ESP32 Thermostat Controller

  Based on:
  "ESP32 MQTT – Publish and Subscribe with Arduino IDE"
  by Rui Santos / Random Nerd Tutorials

  Original source:
  https://randomnerdtutorials.com/esp32-mqtt-publish-subscribe-arduino-ide/

  Modified for PiThermOS by Evan Potts.
*/


#include <WiFi.h>
#define MQTT_KEEPALIVE 60
#include <PubSubClient.h>

// Replace the next variables with your SSID/Password combination
const char* ssid = "YourSSID";                    //SET WIFI SSID
const char* password = "YourWifiPass";            //SET WIFI PASSWORD

// Add your MQTT Broker IP address, example:
const char* mqtt_server = "Yourthermip";      //SET THERMOSTAT IP ADDRESS OR OTHER MQTT SERVER
const char* mqtt_username = "yourmqttuser";             //SET MQTT USERNAMER
const char* mqtt_password = "yourmqttpass";             //SET MQTT PASSWORD

WiFiClient espClient;
PubSubClient client(espClient);
long lastMsg = 0;
char msg[50];
int value = 0;

// LED Pin
bool humtimeout = false;
unsigned long humdelayStart = 0;
bool heattimeout = false;
unsigned long heatdelayStart = 0;
bool cooltimeout = false;
unsigned long cooldelayStart = 0;
bool fantimeout = false;
unsigned long fandelayStart = 0;
const int ledPin = 2;
const int humPin = 23;
const int heatPin =22;
const int coolPin = 19;
const int fanPin = 18;

void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  pinMode(ledPin, OUTPUT);
  pinMode(humPin, OUTPUT);
  pinMode(heatPin, OUTPUT);
  pinMode(coolPin, OUTPUT);
  pinMode(fanPin, OUTPUT);
}

void setup_wifi() {
  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* message, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
  String messageTemp;
  
  for (int i = 0; i < length; i++) {
    Serial.print((char)message[i]);
    messageTemp += (char)message[i];
  }
  Serial.println();

  // Feel free to add more if statements to control more GPIOs with MQTT

  // If a message is received on the topic esp32/output, you check if the message is either "on" or "off". 
  // Changes the output state according to the message
  if (String(topic) == "Hum") {
//    Serial.print("Changing output to ");
    if(messageTemp == "humon"){
      Serial.println("humon");
      digitalWrite(humPin, HIGH);
      }
    else if(messageTemp == "humoff"){
      Serial.println("humoff");
      digitalWrite(humPin, LOW);
    }
  }
  if (String(topic) == "Alive") {
    if(messageTemp == "HumKeepAlive"){
      Serial.println("HumKeepAlive");
      humdelayStart = millis();
      humtimeout = false;
      humtimeout = true;
    }
    else if(messageTemp == "HeatKeepAlive"){
      Serial.println("HeatKeepAlive");
      heatdelayStart = millis();
      heattimeout = false;
      heattimeout = true;
    }
    else if(messageTemp == "CoolKeepAlive"){
      Serial.println("CoolKeepAlive");
      cooldelayStart = millis();
      cooltimeout = false;
      cooltimeout = true;
    }
    else if(messageTemp == "FanKeepAlive"){
      Serial.println("FanKeepAlive");
      fandelayStart = millis();
      fantimeout = false;
      fantimeout = true;
    }
  }
  if (String(topic) == "Heat") {
//    Serial.print("Changing output to ");
    if(messageTemp == "heaton"){
      Serial.println("heaton");
      digitalWrite(heatPin, HIGH);
      }
    else if(messageTemp == "heatoff"){
      Serial.println("heatoff");
      digitalWrite(heatPin, LOW);
    }
  }
  if (String(topic) == "Cool") {
    Serial.print("Changing output to ");
    if(messageTemp == "coolon"){
     Serial.println("coolon");
      digitalWrite(coolPin, HIGH);
      }
    else if(messageTemp == "cooloff"){
      Serial.println("cooloff");
      digitalWrite(coolPin, LOW);
    }
  }
  if (String(topic) == "Fan") {
    Serial.print("Changing output to ");
    if(messageTemp == "fanon"){
      Serial.println("fanon");
      digitalWrite(fanPin, HIGH);
      }
    else if(messageTemp == "fanoff"){
      Serial.println("fanoff");
      digitalWrite(fanPin, LOW);
    }
  }
}
void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect("ESP32Client", mqtt_username, mqtt_password)) {
      digitalWrite(ledPin, HIGH);
      Serial.println("connected");
      // Subscribe
      client.subscribe("Hum");
      client.subscribe("Alive");
      client.subscribe("Heat");
      client.subscribe("Cool");
      Serial.print("Subscribed");
    } 
    else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println("Connection failed shutting off");
      digitalWrite(ledPin, LOW);
      digitalWrite(humPin, LOW);
      digitalWrite(heatPin, LOW);
      digitalWrite(coolPin, LOW);
      digitalWrite(fanPin, LOW);
      Serial.println(" try again in 30 seconds");
      // Wait 30 seconds before retrying
      delay(30000);
    }
  }
}
void loop() {
//  delay(5000);
  if (!client.connected()) {
//    Serial.println("Connection failed shutting off");
//    digitalWrite(ledPin, LOW);
//    digitalWrite(humPin, LOW);
//    digitalWrite(heatPin, LOW);
//    digitalWrite(coolPin, LOW);
//    digitalWrite(fanPin, LOW);
    reconnect();
  }
  client.loop();

  long now = millis();
  if (now - lastMsg > 5000) {
    lastMsg = now;
  }
  if ((humtimeout == true) && (millis() - humdelayStart) >= 30000) {
    Serial.println("No HumKeepAlive, Turning off");
    digitalWrite(humPin, LOW);
    humtimeout = false;
  }
  if ((heattimeout == true) && (millis() - heatdelayStart) >= 30000) {
    Serial.println("No HeatKeepAlive, Turning off");
    digitalWrite(heatPin, LOW);
    heattimeout = false;
  }
  if ((cooltimeout == true) && (millis() - cooldelayStart) >= 30000) {
    Serial.println("No CoolKeepAlive, Turning off");
    digitalWrite(coolPin, LOW);
    cooltimeout = false;
  }
  if ((fantimeout == true) && (millis() - fandelayStart) >= 30000) {
    Serial.println("No FanKeepAlive, Turning off");
    digitalWrite(fanPin, LOW);
    fantimeout = false;
  }
}  
