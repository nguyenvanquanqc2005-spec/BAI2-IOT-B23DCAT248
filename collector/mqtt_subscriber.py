import json
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import time

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "iot/B23DCAT248/sensor"
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "Avq8SudGC0jNz9gNfte-61jA6CVcZRgrHPjp9-seDO_mlPM2RunGyQrcXYW0KRMX-dyg8PZE20oYidjflyWUFg=="
INFLUX_ORG = "PTIT"
INFLUX_BUCKET = "iot_lab2"
last_sequence = None
def validate_data(data):
    required_fields = [
        "device_id",
        "temperature",
        "humidity",
        "distance_cm",
        "sequence"
    ]

    for field in required_fields:
        if field not in data:
            return False

    if not -40 <= data["temperature"] <= 80:
        return False

    if not 0 <= data["humidity"] <= 100:
        return False

    if data["distance_cm"] < 0:
        return False

    return True


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT connected")

        client.subscribe(MQTT_TOPIC)

        print("Subscribed:", MQTT_TOPIC)
        print("Waiting for data...\n")
    else:
        print("MQTT connection failed:", rc)


def on_message(client, userdata, msg):
    start_time = time.perf_counter()
    try:
        payload = msg.payload.decode("utf-8")

        data = json.loads(payload)

        print("Received:")
        print(data)

        if validate_data(data):
            print("Validation: PASS")

            print("Device:", data["device_id"])
            print("Temperature:", data["temperature"], "C")
            print("Humidity:", data["humidity"], "%")
            print("Distance:", data["distance_cm"], "cm")
            print("Sequence:", data["sequence"])
            global last_sequence

            current_sequence = int(data["sequence"])

            if last_sequence is not None:
                if current_sequence == last_sequence:
                    print("Warning: DUPLICATE PACKET")

                elif current_sequence > last_sequence + 1:
                    lost = current_sequence - last_sequence - 1
                    print("Warning: LOST", lost, "PACKET(S)")

            last_sequence = current_sequence
            point = (
                Point("sensor_raw")
                .tag("device_id", data["device_id"])
                .field("temperature", float(data["temperature"]))
                .field("humidity", float(data["humidity"]))
                .field("distance_cm", float(data["distance_cm"]))
                .field("sequence", int(data["sequence"]))
            )

            write_api.write(
                bucket=INFLUX_BUCKET,
                org=INFLUX_ORG,
                record=point
            )
            latency_ms = (time.perf_counter() - start_time) * 1000

            print("InfluxDB: WRITE SUCCESS")
            print("Processing latency:", round(latency_ms, 2), "ms")
        else:
            print("Validation: FAILED")

        print("-" * 40)

    except json.JSONDecodeError:
        print("Invalid JSON")

    except Exception as e:
        print("Error:", e)
influx_client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

write_api = influx_client.write_api(
    write_options=SYNCHRONOUS
)

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

print("Connecting to MQTT Broker...")

client.connect(
    MQTT_BROKER,
    MQTT_PORT,
    60
)

client.loop_forever()