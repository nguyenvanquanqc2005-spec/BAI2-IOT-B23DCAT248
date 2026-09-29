# BAI2-IOT-B23DCAT248

## 1. Giới thiệu

Bài thực hành số 2 môn **IoT và Ứng dụng (INT14149)**.

Pipeline hệ thống:

**ESP32/Wokwi → MQTT Broker → Python Collector → InfluxDB → Preprocessing → Streamlit Dashboard**

Thiết bị sử dụng:
- ESP32 DevKit V1
- DHT22
- HC-SR04
- LED

Dữ liệu thu thập:
- `temperature`
- `humidity`
- `distance_cm`
- `sequence`

## 2. Cấu trúc project

```text
BAI1-IOT-ESP32/
│
├── src/
│   └── main.cpp
├── collector/
│   └── mqtt_subscriber.py
├── preprocessing/
│   └── preprocessing.py
├── dashboard/
│   └── app.py
├── diagram.json
├── wokwi.toml
├── platformio.ini
├── requirements.txt
├── .gitignore
└── README.md
```

## 3. MQTT

Broker:

```text
broker.hivemq.com
```

Topic:

```text
iot/B23DCAT248/sensor
```

Dữ liệu JSON mẫu:

```json
{
  "device_id": "B23DCAT248",
  "temperature": 24.0,
  "humidity": 40.0,
  "distance_cm": 120.5,
  "sequence": 1
}
```

## 4. Cài thư viện Python

```powershell
py -m pip install paho-mqtt influxdb-client pandas numpy scikit-learn streamlit plotly
```

Hoặc:

```powershell
py -m pip install -r requirements.txt
```

`requirements.txt`:

```text
paho-mqtt
influxdb-client
pandas
numpy
scikit-learn
streamlit
plotly
```

## 5. Cấu hình InfluxDB

```text
URL: http://localhost:8086
Organization: PTIT
Bucket: iot_lab2
```

Measurement:
- `sensor_raw`
- `sensor_processed`
- `sensor_resampled`

Không commit API Token thật lên GitHub.

Trong source code nên để:

```python
INFLUX_TOKEN = "TOKEN_CUA_BAN"
```

## 6. Cách chạy

### Bước 1: Chạy InfluxDB

```powershell
.\influxd.exe
```

Truy cập:

```text
http://localhost:8086
```

### Bước 2: Chạy ESP32 trên Wokwi

Trong VS Code:

```text
PlatformIO: Build
Wokwi: Start Simulator
```

ESP32 gửi dữ liệu MQTT khoảng 5 giây/lần.

### Bước 3: Chạy MQTT Collector

```powershell
py collector/mqtt_subscriber.py
```

Kết quả mong đợi:

```text
Validation: PASS
InfluxDB: WRITE SUCCESS
Processing latency: ... ms
```

### Bước 4: Chạy preprocessing

```powershell
py preprocessing/preprocessing.py
```

Các bước tiền xử lý:
- Missing value
- Outlier bằng IQR
- Rolling mean
- Delta
- Min-Max normalization
- Resampling 1 phút

### Bước 5: Chạy Streamlit Dashboard

```powershell
py -m streamlit run dashboard/app.py
```

Truy cập:

```text
http://localhost:8501
```

## 7. InfluxDB Script Editor

Xem 20 bản ghi mới nhất:

```flux
from(bucket: "iot_lab2")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "sensor_raw")
  |> filter(fn: (r) => r.device_id == "B23DCAT248")
  |> pivot(
      rowKey: ["_time"],
      columnKey: ["_field"],
      valueColumn: "_value"
  )
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: 20)
```

## 8. Đánh giá độ trễ

| Lần đo | Processing latency (ms) |
|---:|---:|
| 1 | 2.79 |
| 2 | 2.87 |
| 3 | 2.54 |
| 4 | 2.46 |
| 5 | 2.79 |
| 6 | 2.35 |
| **Trung bình** | **2.63** |

Độ trễ đo từ lúc Python nhận MQTT message đến khi ghi hoàn tất vào InfluxDB.

## 9. Bảo mật

Không đưa lên GitHub:
- InfluxDB API Token
- Mật khẩu
- Thông tin xác thực riêng

Nên dùng file `.env` hoặc biến môi trường khi triển khai thực tế.

## 10. Sinh viên thực hiện

```text
MSSV: B23DCAT248
Họ và tên: Nguyễn Văn Quân
```
