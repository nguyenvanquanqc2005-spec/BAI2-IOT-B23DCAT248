import streamlit as st
import pandas as pd
from influxdb_client import InfluxDBClient

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "Avq8SudGC0jNz9gNfte-61jA6CVcZRgrHPjp9-seDO_mlPM2RunGyQrcXYW0KRMX-dyg8PZE20oYidjflyWUFg=="
INFLUX_ORG = "PTIT"
INFLUX_BUCKET = "iot_lab2"

client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

query_api = client.query_api()

query = '''
from(bucket: "iot_lab2")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "sensor_raw")
  |> pivot(
      rowKey: ["_time"],
      columnKey: ["_field"],
      valueColumn: "_value"
  )
'''

df = query_api.query_data_frame(query)

st.title("IoT Sensor Monitoring - B23DCAT248")

if df.empty:
    st.warning("Chua co du lieu")
    st.stop()

latest = df.iloc[-1]

col1, col2, col3 = st.columns(3)

col1.metric(
    "Temperature",
    f"{latest['temperature']:.2f} °C"
)

col2.metric(
    "Humidity",
    f"{latest['humidity']:.2f} %"
)

col3.metric(
    "Distance",
    f"{latest['distance_cm']:.2f} cm"
)

st.subheader("Temperature")
st.line_chart(
    df.set_index("_time")["temperature"]
)

st.subheader("Humidity")
st.line_chart(
    df.set_index("_time")["humidity"]
)

st.subheader("Distance")
st.line_chart(
    df.set_index("_time")["distance_cm"]
)

st.subheader("Raw Data")

st.dataframe(
    df[
        [
            "_time",
            "temperature",
            "humidity",
            "distance_cm",
            "sequence"
        ]
    ].sort_values("_time", ascending=False)
)

client.close()