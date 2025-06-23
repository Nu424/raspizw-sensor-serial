"""
# PiSensorClient.py
sensor-serial-server.pyが動作するRaspberry Pi Zero Wを、
外部センサーとして楽に使用するためのクラス。

## 使い方
```python
from PiSensorClient import PiSensorClient

# ---シリアル接続を開始
pi_sensor = PiSensorClient(port="COM20")
pi_sensor.connect()

# ---センサーデータの取得
sensor_data = pi_sensor.get_sensor_data()
print(sensor_data)
status = pi_sensor.get_status()
print(status)
ping = pi_sensor.ping()
print(ping)

# ---シリアル接続を終了
pi_sensor.disconnect()
```

"""

from dataclasses import dataclass
import json
from typing import Optional
import serial
from SensorType import EnvironmentData, MotionData, Orientation, Vector3D, SensorData


# ----------
# ---各種データクラスの定義
# ----------
@dataclass
class PiSensorError:
    """エラーを表現するクラス"""

    error: str


@dataclass
class PiSensorPing:
    """pingの応答を表現するクラス"""

    status: str


@dataclass
class PiSensorStatus:
    """センサーの状態を表現するクラス"""

    sensor_initialized: bool
    running: bool
    port: str


# ----------
# ----------
# ----------
class PiSensorClient:
    """sensor-serial-server.pyが動作するRaspberry Pi Zero Wを、
    外部センサーとして楽に使用するためのクラス。
    """

    def __init__(self, port: str, baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None

    # ----------
    # ---シリアル通信関連のメソッド
    # ----------

    def connect(self) -> bool:
        """シリアル接続を開始"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port, baudrate=self.baudrate, timeout=2.0
            )
            return True
        except serial.SerialException as e:
            print(f"接続エラー: {e}")
            return False

    def disconnect(self):
        """シリアル接続を終了"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

    def send_command(self, command: str) -> Optional[dict]:
        """コマンドを送信し、応答を取得"""
        if not self.serial_conn or not self.serial_conn.is_open:
            raise ValueError("シリアル接続が開かれていません")
        try:
            # コマンド送信
            cmd_bytes = f"{command}\r\n".encode("utf-8")
            self.serial_conn.write(cmd_bytes)
            self.serial_conn.flush()
            # 応答受信
            response = self.serial_conn.readline()
            if response:
                decoded = response.decode("utf-8", errors="replace").strip()
                response_json = json.loads(decoded)
                return response_json
            else:
                raise ValueError("応答がありません")
        except Exception as e:
            raise ValueError(f"コマンド送信エラー: {e}")

    # ----------
    # ---ユーザー向けメソッド
    # ----------

    def get_sensor_data(self) -> Optional[SensorData]:
        """センサーデータを取得"""
        try:
            command = "get_sensor_data"
            response = self.send_command(command)
            if not self.is_error(response):
                environment = EnvironmentData(**response["environment"])
                motion_dict = response["motion"]
                orientation = Orientation(**motion_dict["orientation"])
                acceleration = Vector3D(**motion_dict["acceleration"])
                gyroscope = Vector3D(**motion_dict["gyroscope"])
                magnetic = Vector3D(**motion_dict["magnetic"])
                motion = MotionData(
                    orientation=orientation,
                    acceleration=acceleration,
                    gyroscope=gyroscope,
                    magnetic=magnetic,
                )
                return SensorData(environment=environment, motion=motion)
            else:
                raise ValueError(f"センサーデータがありません: {response.get('error')}")
        except Exception as e:
            raise ValueError(f"センサーデータ取得エラー: {e}")

    def get_status(self) -> Optional[str]:
        """センサーの状態を取得"""
        try:
            command = "status"
            response = self.send_command(command)
            if not self.is_error(response):
                return PiSensorStatus(**response)
            else:
                raise ValueError(f"センサーの状態がありません: {response.get('error')}")
        except Exception as e:
            raise ValueError(f"センサーの状態取得エラー: {e}")

    def ping(self) -> Optional[str]:
        """センサーへのpingを送信"""
        try:
            command = "ping"
            response = self.send_command(command)
            if not self.is_error(response):
                return PiSensorPing(**response)
            else:
                raise ValueError(f"pingエラー: {response.get('error')}")
        except Exception as e:
            raise ValueError(f"pingエラー: {e}")

    # ----------
    # ---内部メソッド
    # ----------
    def is_error(self, response: Optional[dict]) -> bool:
        """responseがエラーかどうかを確認する

        Args:
            response: センサーからの応答

        Returns:
            bool: エラーかどうか。エラーの場合はTrue、それ以外はFalse。
        """
        if response:
            return response.get("error") is not None
        return True
