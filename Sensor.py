"""
# Sensor.py
Environment Sensor HATからセンサーデータを取得するためのクラス。
ref: https://www.waveshare.com/wiki/Environment_Sensor_HAT

## 使い方
```python
# ---センサーを初期化する
sensor_hub = SensorHub()

# ---センサーデータを取得する
data = sensor_hub.read_all()

# ---データは、以下のような形式で取得できる
{
    "environment": {
        "temperature": 25.0,
        "humidity": 50.0,
        "pressure": 1013.25,
        "light": 100.0,
        "uv": 100,
        "voc": 100.0
    },
    "motion": {
        "orientation": {
            "roll": 0.0,
            "pitch": 0.0,
            "yaw": 0.0
        },
        "acceleration": {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0
        },
        "gyroscope": {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0
        },
        "magnetic": {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0
        }
    }
}


"""

from typing import Union
import time
from modules import ICM20948  # Gyroscope/Acceleration/Magnetometer
from modules import MPU925x  # Gyroscope/Acceleration/Magnetometer
from modules import BME280  # Atmospheric Pressure/Temperature and humidity
from modules import LTR390  # UV
from modules import TSL2591  # LIGHT
from modules import SGP40  # VOC
import smbus
from SensorType import EnvironmentData, MotionData, Orientation, Vector3D, SensorData


class SensorHub:
    """複数のセンサーを統合して扱うためのラッパークラス"""

    def __init__(self) -> None:
        """センサーハブの初期化を行う

        各センサーのインスタンスを作成し、初期設定を行います。
        9軸センサーは自動的にICM20948かMPU925xを検出します。
        """
        self.bus = smbus.SMBus(1)

        # BME280の初期化
        self.bme280 = BME280.BME280()
        self.bme280.get_calib_param()

        # その他のセンサーの初期化
        self.light = TSL2591.TSL2591()
        self.uv = LTR390.LTR390()
        self.sgp = SGP40.SGP40()

        # 9軸センサーの検出と初期化
        self.mpu = self._initialize_motion_sensor()

    def _initialize_motion_sensor(
        self,
    ) -> Union[ICM20948.ICM20948, MPU925x.MPU925x]:
        """9軸センサーを検出して初期化する

        Returns:
            Union[ICM20948.ICM20948, MPU925x.MPU925x]: 検出されたモーションセンサーのインスタンス

        Raises:
            RuntimeError: モーションセンサーが検出できない場合
        """
        device_id1 = self.bus.read_byte_data(int(0x68), int(0x00))  # ICM_ADD_WIA
        device_id2 = self.bus.read_byte_data(int(0x68), int(0x75))  # MPU_ADD_WIA
        if device_id1 == 0xEA:  # ICM_VAL_WIA
            return ICM20948.ICM20948()
        elif device_id2 == 0x71:  # MPU_VAL_WIA
            return MPU925x.MPU925x()
        raise RuntimeError("No compatible motion sensor detected")

    def read_environment(self) -> EnvironmentData:
        """環境センサーの値を読み取る

        Returns:
            EnvironmentData: 環境センサーの測定値
        """
        bme_data = self.bme280.readData()

        return EnvironmentData(
            temperature=round(bme_data[1], 2),
            humidity=round(bme_data[2], 2),
            pressure=round(bme_data[0], 2),
            light=round(self.light.Lux(), 2),
            uv=self.uv.UVS(),
            voc=round(self.sgp.raw(), 2),
        )

    def read_motion(self) -> MotionData:
        """モーションセンサーの値を読み取る

        Returns:
            MotionData: モーションセンサーの測定値
        """
        data = self.mpu.getdata()

        return MotionData(
            orientation=Orientation(data[0], data[1], data[2]),
            acceleration=Vector3D(data[3], data[4], data[5]),
            gyroscope=Vector3D(data[6], data[7], data[8]),
            magnetic=Vector3D(data[9], data[10], data[11]),
        )

    def read_all(self) -> SensorData:
        """全センサーの値を読み取る

        Returns:
            SensorData: 全センサーの測定値
        """
        return SensorData(
            environment=self.read_environment(), motion=self.read_motion()
        )


if __name__ == "__main__":
    sensor_hub = SensorHub()
    while True:
        data = sensor_hub.read_all()

        print("==================================================")
        print(f"pressure : {data.environment.pressure:.2f} hPa")
        print(f"temp : {data.environment.temperature:.2f} ℃")
        print(f"hum : {data.environment.humidity:.2f} ％")
        print(f"lux : {data.environment.light:.2f}")
        print(f"uv : {data.environment.uv}")
        print(f"gas : {data.environment.voc:.2f}")
        print(
            f"Roll = {data.motion.orientation.roll:.2f}, "
            f"Pitch = {data.motion.orientation.pitch:.2f}, "
            f"Yaw = {data.motion.orientation.yaw:.2f}"
        )
        print(
            f"Acceleration: X = {data.motion.acceleration.x}, "
            f"Y = {data.motion.acceleration.y}, "
            f"Z = {data.motion.acceleration.z}"
        )
        print(
            f"Gyroscope:     X = {data.motion.gyroscope.x}, "
            f"Y = {data.motion.gyroscope.y}, "
            f"Z = {data.motion.gyroscope.z}"
        )
        print(
            f"Magnetic:      X = {data.motion.magnetic.x}, "
            f"Y = {data.motion.magnetic.y}, "
            f"Z = {data.motion.magnetic.z}"
        )

        time.sleep(1)
