#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHTesp.h>

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

const char* MQTT_SERVER = "broker.hivemq.com";
const int MQTT_PORT = 1883;
const char* MQTT_TOPIC = "iot/B23DCAT248/sensor";

const int DHT_PIN = 15;
const int TRIG_PIN = 5;
const int ECHO_PIN = 18;
const int LED_PIN = 2;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
DHTesp dht;

unsigned long lastSend = 0;
unsigned long sequence = 1;

void connectWiFi() {
  Serial.print("Connecting WiFi");

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD, 6);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void connectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connecting MQTT... ");

    String clientId = "ESP32-B23DCAT248-" + String(random(1000, 9999));

    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("OK");
    } else {
      Serial.print("FAILED, state=");
      Serial.println(mqttClient.state());
      delay(2000);
    }
  }
}

float readDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);

  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);

  if (duration == 0) {
    return -1;
  }

  return duration * 0.0343 / 2.0;
}

void setup() {
  Serial.begin(115200);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);

  dht.setup(DHT_PIN, DHTesp::DHT22);

  connectWiFi();

  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);

  Serial.println("System started");
}

void loop() {
  if (!mqttClient.connected()) {
    connectMQTT();
  }

  mqttClient.loop();

  if (millis() - lastSend >= 5000) {
    lastSend = millis();

    TempAndHumidity data = dht.getTempAndHumidity();

    float temperature = data.temperature;
    float humidity = data.humidity;
    float distance = readDistance();

    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("DHT22 ERROR");
      return;
    }

    String payload = "{";

    payload += "\"device_id\":\"B23DCAT248\",";
    payload += "\"temperature\":" + String(temperature, 2) + ",";
    payload += "\"humidity\":" + String(humidity, 2) + ",";
    payload += "\"distance_cm\":" + String(distance, 2) + ",";
    payload += "\"sequence\":" + String(sequence++);
    payload += "\"timestamp_ms\":" + String(millis()) + ",";
    payload += "}";

    bool sent = mqttClient.publish(
      MQTT_TOPIC,
      payload.c_str()
    );

    if (sent) {
      digitalWrite(LED_PIN, HIGH);

      Serial.println("MQTT SEND OK");
      Serial.println(payload);

      delay(100);

      digitalWrite(LED_PIN, LOW);
    } else {
      Serial.println("MQTT SEND FAILED");
    }
  }
}