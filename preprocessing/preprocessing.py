import pandas as pd
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from sklearn.preprocessing import MinMaxScaler

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

if df.empty:
    print("Khong co du lieu")
    client.close()
    exit()

print("So dong ban dau:", len(df))

df = df[
    [
        "_time",
        "device_id",
        "temperature",
        "humidity",
        "distance_cm",
        "sequence"
    ]
].copy()

# =========================
# 1. Missing value
# =========================

df["temperature"] = df["temperature"].interpolate()
df["humidity"] = df["humidity"].interpolate()
df["distance_cm"] = df["distance_cm"].interpolate()

# =========================
# 2. Outlier - IQR
# =========================

def remove_outlier_iqr(dataframe, column):
    q1 = dataframe[column].quantile(0.25)
    q3 = dataframe[column].quantile(0.75)

    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    dataframe[column] = dataframe[column].clip(
        lower=lower,
        upper=upper
    )

    return dataframe


df = remove_outlier_iqr(df, "temperature")
df = remove_outlier_iqr(df, "humidity")
df = remove_outlier_iqr(df, "distance_cm")

# =========================
# 3. Rolling Mean
# =========================

df["temp_rolling_mean"] = (
    df["temperature"]
    .rolling(window=3, min_periods=1)
    .mean()
)

df["humidity_rolling_mean"] = (
    df["humidity"]
    .rolling(window=3, min_periods=1)
    .mean()
)

# =========================
# 4. Delta
# =========================

df["temp_delta"] = (
    df["temperature"]
    .diff()
    .fillna(0)
)

# =========================
# 5. Normalization
# =========================

scaler = MinMaxScaler()

df[
    [
        "temperature_norm",
        "humidity_norm",
        "distance_norm"
    ]
] = scaler.fit_transform(
    df[
        [
            "temperature",
            "humidity",
            "distance_cm"
        ]
    ]
)

# =========================
# 6. Resampling 1 phút
# =========================

df["_time"] = pd.to_datetime(df["_time"])

resampled = (
    df.set_index("_time")
    .resample("1min")
    .mean(numeric_only=True)
)

print("\nDu lieu sau resampling:")
print(resampled.head())

print("\nDu lieu sau preprocessing:")
print(df.head())

# =========================
# 7. Ghi sensor_processed
# =========================

write_api = client.write_api(
    write_options=SYNCHRONOUS
)

for _, row in df.iterrows():

    point = (
        Point("sensor_processed")
        .tag("device_id", str(row["device_id"]))
        .field("temperature", float(row["temperature"]))
        .field("humidity", float(row["humidity"]))
        .field("distance_cm", float(row["distance_cm"]))
        .field("temp_rolling_mean", float(row["temp_rolling_mean"]))
        .field("humidity_rolling_mean", float(row["humidity_rolling_mean"]))
        .field("temp_delta", float(row["temp_delta"]))
        .field("temperature_norm", float(row["temperature_norm"]))
        .field("humidity_norm", float(row["humidity_norm"]))
        .field("distance_norm", float(row["distance_norm"]))
        .time(row["_time"])
    )

    write_api.write(
        bucket=INFLUX_BUCKET,
        org=INFLUX_ORG,
        record=point
    )

print("\nPREPROCESSING COMPLETED")
print("Da ghi vao measurement: sensor_processed")

client.close()