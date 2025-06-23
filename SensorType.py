from dataclasses import dataclass


@dataclass
class Orientation:
    """姿勢角データを表現するクラス

    Attributes:
        roll (float): ロール角 (度)
        pitch (float): ピッチ角 (度)
        yaw (float): ヨー角 (度)
    """

    roll: float
    pitch: float
    yaw: float


@dataclass
class Vector3D:
    """3次元ベクトルデータを表現するクラス

    Attributes:
        x (float): X軸の値
        y (float): Y軸の値
        z (float): Z軸の値
    """

    x: float
    y: float
    z: float


@dataclass
class MotionData:
    """モーションセンサーのデータを表現するクラス

    Attributes:
        orientation (Orientation): 姿勢角データ
        acceleration (Vector3D): 加速度データ
        gyroscope (Vector3D): ジャイロスコープデータ
        magnetic (Vector3D): 磁気センサーデータ
    """

    orientation: Orientation
    acceleration: Vector3D
    gyroscope: Vector3D
    magnetic: Vector3D


@dataclass
class EnvironmentData:
    """環境センサーのデータを表現するクラス

    Attributes:
        temperature (float): 温度 (℃)
        humidity (float): 湿度 (%)
        pressure (float): 気圧 (hPa)
        light (float): 照度 (lux)
        uv (int): UV値
        voc (float): VOC値
    """

    temperature: float
    humidity: float
    pressure: float
    light: float
    uv: int
    voc: float


@dataclass
class SensorData:
    """全センサーデータを表現するクラス

    Attributes:
        environment (EnvironmentData): 環境センサーデータ
        motion (MotionData): モーションセンサーデータ
    """

    environment: EnvironmentData
    motion: MotionData