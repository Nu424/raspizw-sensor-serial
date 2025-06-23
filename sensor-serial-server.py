import serial
import json
import time
from Sensor import SensorHub

sensor_hub = SensorHub()
serial_port = serial.Serial("/dev/ttyUSB0", 9600)

temp_data = ""

while True:
    # ---シリアル通信を待機する
    if serial_port.in_waiting > 0:
        temp_data += serial_port.readline().decode("utf-8").strip()
    if temp_data.endswith("\r\n"):
        # temp_dataの末尾の\r\nを削除
        command = temp_data.rstrip("\r\n")
        temp_data = ""
        if command == "get_sensor_data":
            # ---センサーの値を読み取り、シリアル通信で送信する
            data = sensor_hub.read_all()
            data_str = json.dumps(data)
            serial_port.write(data_str.encode())
        else:
            serial_port.write(b"invalid command")
    time.sleep(1)
