# Raspberry Pi Zero W センサーシリアルサーバー

Raspberry Pi Zero W上でEnvironment Sensor HATからセンサーデータを取得し、シリアル通信でクライアントに提供する高性能なサーバーアプリケーションです。

## 📋 目次

- [📖 概要](#-概要)
- [🎯 主な機能・改善点](#-主な機能改善点)
- [🚀 利用者向けガイド](#-利用者向けガイド)
  - [前提条件](#前提条件)
  - [インストールと初期設定](#インストールと初期設定)
  - [設定](#設定)
  - [実行](#実行)
  - [API仕様](#api仕様)
  - [トラブルシューティング](#トラブルシューティング)
- [⚙️ システム管理者向けガイド](#️-システム管理者向けガイド)
  - [サービス化](#サービス化)
  - [パフォーマンス監視](#パフォーマンス監視)
  - [ログ管理](#ログ管理)
- [🔧 開発者向けガイド](#-開発者向けガイド)
  - [アーキテクチャ概要](#アーキテクチャ概要)
  - [コードベース構造](#コードベース構造)
  - [開発環境セットアップ](#開発環境セットアップ)
  - [コードスタイル・規約](#コードスタイル規約)
  - [機能拡張ガイド](#機能拡張ガイド)
  - [テスト・デバッグ](#テストデバッグ)

---

## 📖 概要

本プロジェクトは、Raspberry Pi Zero W上でWaveshare Environment Sensor HATの6種類のセンサー（環境センサー＋9軸モーションセンサー）から取得したデータを、安定したシリアル通信で外部クライアントに提供するサーバーアプリケーションです。

### 対応センサー
- **環境センサー**: BME280（温度・湿度・気圧）、TSL2591（照度）、LTR390（UV）、SGP40（VOC）
- **モーションセンサー**: ICM20948/MPU925x（加速度・ジャイロ・磁気）

### 主な特徴
- ⚡ **高性能**: 最適化されたループ処理で低CPU使用率を実現
- 🛡️ **堅牢性**: 包括的なエラーハンドリングと適切なリソース管理
- 📊 **豊富なデータ**: JSON形式で構造化されたセンサーデータを提供
- 🔧 **柔軟な設定**: 外部設定ファイルによる詳細なカスタマイズ

---

## 🎯 主な特徴

### 🛡️ 安定性・信頼性
- **エラーから自動復旧**: 通信エラーやセンサー異常が発生しても安全に動作継続
- **安全な終了処理**: Ctrl+Cでの停止時も、データを失うことなく正常終了
- **標準的なデータ形式**: JSONで読み取りやすいデータを提供

### ⚙️ 使いやすさ
- **設定ファイルで簡単カスタマイズ**: 通信速度やログレベルなどを自由に調整
- **低CPU使用率**: 長時間動作してもPi Zero Wに負荷をかけません
- **動作確認コマンド**: `ping`や`status`で接続状態をすぐに確認

### 🔧 開発・運用サポート
- **詳細なログ出力**: 問題発生時の原因調査が容易
- **自動ログ管理**: ファイルサイズが大きくなっても自動で整理
- **テストツール付属**: 動作確認用のスクリプトで簡単に動作テスト
- **サービス化対応**: システム起動時の自動実行をサポート

---

## 🚀 利用者向けガイド

### 前提条件

#### ハードウェア要件
- Raspberry Pi Zero W（または他のRaspberry Piモデル）
- Waveshare Environment Sensor HAT
- USB-OTGによるシリアル通信設定、またはUSB-Serial変換器

#### ソフトウェア要件
- Raspberry Pi OS（推奨: Lite版）
- Python 3.7以上
- I2Cインターフェース有効化

### インストールと初期設定

#### 1. USB-OTGシリアル通信の設定

詳細は以下の記事を参照してください：
- https://suzu-ha.com/entry/2024/06/01/232052

⚠️ **重要**: `serial-getty@ttyGS0.service`の有効化は行わないでください。これを有効にすると、コンソール出力がシリアルポートに混在し、サーバーが正常に動作しません。

#### 2. 必要なシステムパッケージのインストール

```bash
# I2C関連パッケージ
sudo apt-get update
sudo apt-get install python3-smbus i2c-tools python3-pil

# GPIO制御ライブラリ
pip install RPi.GPIO
```

#### 3. I2Cインターフェースの有効化

```bash
sudo raspi-config
# 「3 Interfacing Options」→「I5 I2C」を選択し、有効化
```

#### 4. プロジェクトのセットアップ

```bash
# リポジトリのクローンまたはダウンロード
git clone <repository-url>
cd raspizw-sensor-serial

# Python仮想環境の作成
python3 -m venv venv
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt
```

#### 5. シリアルポートの確認と設定

```bash
# 利用可能なシリアルポートの確認
python -m serial.tools.list_ports

# USB-OTGの場合は通常 /dev/ttyS0 → /dev/ttyGS0 に設定
# 設定ファイルの編集
nano config.json
```

### 設定

`config.json`ファイルで詳細な設定が可能です：

```json
{
    "serial": {
        "port": "/dev/ttyGS0",         # シリアルポート（USB-OTG使用時）
        "baudrate": 9600,              # ボーレート
        "timeout": 1.0,                # 読み取りタイムアウト（秒）
        "write_timeout": 1.0           # 書き込みタイムアウト（秒）
    },
    "system": {
        "loop_interval": 0.1,          # メインループ間隔（秒）- 性能調整
        "max_command_length": 256,     # コマンド最大長（セキュリティ）
        "shutdown_timeout": 5.0        # 終了処理タイムアウト（秒）
    },
    "logging": {
        "level": "INFO",               # ログレベル: DEBUG/INFO/WARNING/ERROR
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "sensor_server.log",   # ログファイル名
        "max_bytes": 1048576,          # ログファイル最大サイズ（1MB）
        "backup_count": 3              # ローテーション保持数
    }
}
```

#### 設定パラメータ詳細

| カテゴリ | パラメータ | 説明 | デフォルト値 | 推奨値 |
|----------|------------|------|-------------|--------|
| serial | port | シリアルデバイスパス | /dev/ttyUSB0 | /dev/ttyGS0（USB-OTG） |
| serial | baudrate | 通信速度 | 9600 | 9600〜115200 |
| system | loop_interval | ポーリング間隔 | 0.1秒 | 0.05〜0.5秒 |
| system | max_command_length | セキュリティ制限 | 256文字 | 256〜512文字 |
| logging | level | ログレベル | INFO | INFO（本番）/DEBUG（開発） |

### 実行

#### 基本実行

```bash
# デフォルト設定で実行
python sensor-serial-server.py

# カスタム設定ファイルで実行
python sensor-serial-server.py custom_config.json
```

#### 動作確認

```bash
# テストクライアントでの確認
python test_serial_client.py

# カスタムポートでのテスト
python test_serial_client.py /dev/ttyUSB1
```

### API仕様

#### サポートコマンド

| コマンド | 説明 | 戻り値 | 用途 |
|----------|------|--------|------|
| `get_sensor_data` | 全センサーデータを取得 | SensorDataオブジェクト | メインデータ取得 |
| `ping` | サーバー疎通確認 | `{"status": "pong"}` | 接続テスト |
| `status` | サーバー状態確認 | サーバー情報オブジェクト | ヘルスチェック |

#### リクエスト形式

- すべてのコマンドは`\r\n`で終端して送信
- 文字エンコーディング: UTF-8
- 最大コマンド長: 256文字（設定可能）

例:
```
get_sensor_data\r\n
```

#### レスポンス形式

すべてのレスポンスは`\r\n`で終端されるJSON形式です。

##### `get_sensor_data`のレスポンス例:

```json
{
    "environment": {
        "temperature": 25.0,        // 温度（℃）
        "humidity": 50.0,           // 湿度（%）
        "pressure": 1013.25,        // 気圧（hPa）
        "light": 100.0,             // 照度（lux）
        "uv": 100,                  // UV値
        "voc": 100.0                // VOC値
    },
    "motion": {
        "orientation": {
            "roll": 0.0,            // ロール角（度）
            "pitch": 0.0,           // ピッチ角（度）
            "yaw": 0.0              // ヨー角（度）
        },
        "acceleration": {
            "x": 0.0,               // X軸加速度
            "y": 0.0,               // Y軸加速度
            "z": 0.0                // Z軸加速度
        },
        "gyroscope": {
            "x": 0.0,               // X軸角速度
            "y": 0.0,               // Y軸角速度
            "z": 0.0                // Z軸角速度
        },
        "magnetic": {
            "x": 0.0,               // X軸磁場
            "y": 0.0,               // Y軸磁場
            "z": 0.0                // Z軸磁場
        }
    }
}
```

##### `status`のレスポンス例:

```json
{
    "sensor_initialized": true,     // センサー初期化状態
    "running": true,                // サーバー稼働状態
    "port": "/dev/ttyGS0"          // 使用中のシリアルポート
}
```

#### エラー処理

不正なコマンドや処理エラーの場合:

```json
{
    "error": "invalid command"      // エラーメッセージ
}
```

---

## ⚙️ システム管理者向けガイド

### サービス化

systemdを利用して、サーバーをバックグラウンドサービスとして自動起動できます。

#### 1. サービスファイルの編集

プロジェクトに含まれる `sensor-serial-server.service` ファイルを編集します。
`WorkingDirectory` と `ExecStart` に書かれているプレースホルダー `/path/to/your/project` を、`raspizw-sensor-serial` プロジェクトをクローンした実際の絶対パスに置き換えてください。

**例:** `/home/pi/raspizw-sensor-serial` など

```ini
[Unit]
Description=Sensor Serial Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/your/project
ExecStart=/path/to/your/project/venv/bin/python3 /path/to/your/project/sensor-serial-server.py
Restart=on-failure
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### 2. サービスのインストールと起動

```bash
# 編集したサービスファイルをシステムディレクトリにコピー
sudo cp sensor-serial-server.service /etc/systemd/system/

# systemdに新しいサービスを認識させる
sudo systemctl daemon-reload

# サービスを有効化（OS起動時に自動実行）
sudo systemctl enable sensor-serial-server.service

# サービスを開始
sudo systemctl start sensor-serial-server.service
```

#### 3. サービスの状態確認

```bash
# サービスの状態を確認
sudo systemctl status sensor-serial-server.service

# ログのリアルタイム表示
sudo journalctl -u sensor-serial-server.service -f
```

### パフォーマンス監視

#### ログ管理

#### ログローテーション設定

自動ローテーションは設定済みですが、手動管理も可能：

```bash
# ログファイルサイズ確認
ls -lh sensor_server.log*

# 古いログの圧縮
gzip sensor_server.log.1

# ログの削除（注意：重要なデータを確認後）
rm sensor_server.log.2.gz
```

#### 集中ログ管理

rsyslogやjournaldとの連携:

```bash
# systemdジャーナルでの確認
sudo journalctl -u sensor-serial-server --since "1 hour ago"

# ログレベル別フィルタ
sudo journalctl -u sensor-serial-server -p err
```

---

## 🔧 開発者向けガイド

### アーキテクチャ概要

#### システム構成

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Serial Client │◄──►│ Serial Server   │◄──►│ Sensor HAT      │
│                 │    │                 │    │                 │
│ - Test Client   │    │ - Main Loop     │    │ - BME280        │
│ - External App  │    │ - Command Proc  │    │ - TSL2591       │
│                 │    │ - Config Mgmt   │    │ - LTR390        │
└─────────────────┘    │ - Logging       │    │ - SGP40         │
                       │ - Error Handling│    │ - ICM20948/MPU  │
                       └─────────────────┘    └─────────────────┘
```

#### コンポーネント関係図

```
SensorSerialServer (メイン)
├── SerialServerConfig (設定管理)
├── SensorHub (センサー統合)
│   ├── BME280 (環境)
│   ├── TSL2591 (照度)  
│   ├── LTR390 (UV)
│   ├── SGP40 (VOC)
│   └── ICM20948/MPU925x (モーション)
└── ログ・エラーハンドリング
```

### コードベース構造

#### ファイル構成

```
raspizw-sensor-serial/
├── sensor-serial-server.py    # メインサーバーアプリケーション
├── Sensor.py                  # センサー統合クラス
├── config.json                # 設定ファイル
├── requirements.txt           # Python依存関係
├── sensor-serial-server.service # systemdサービス設定
├── modules/                   # センサーモジュール
│   ├── BME280.py             # 温度・湿度・気圧センサー
│   ├── TSL2591.py            # 照度センサー
│   ├── LTR390.py             # UVセンサー
│   ├── SGP40.py              # VOCセンサー
│   ├── ICM20948.py           # 9軸センサー（新型）
│   └── MPU925x.py            # 9軸センサー（旧型）
└── README.md                  # このドキュメント
```

#### 主要クラス設計

##### `SensorSerialServer`クラス

```python
class SensorSerialServer:
    """メインサーバークラス
    
    責務:
    - シリアル通信管理
    - コマンド処理
    - センサーデータ取得
    - エラーハンドリング
    - ログ管理
    """
    
    def __init__(self, config_path: str = "config.json")
    def run(self) -> bool
    def shutdown(self) -> None
    def _process_command(self, command: str) -> bytes
    def _validate_command(self, command: str) -> bool
```

##### `SensorHub`クラス

```python
class SensorHub:
    """センサー統合管理クラス
    
    責務:
    - 各センサーの初期化
    - データ取得の統一インターフェース
    - センサー固有エラーのハンドリング
    """
    
    def __init__(self) -> None
    def read_all(self) -> SensorData
    def read_environment(self) -> EnvironmentData  
    def read_motion(self) -> MotionData
```

##### データクラス階層

```python
@dataclass
class SensorData:
    environment: EnvironmentData
    motion: MotionData

@dataclass  
class EnvironmentData:
    temperature: float  # 温度（℃）
    humidity: float     # 湿度（%）
    pressure: float     # 気圧（hPa）
    light: float        # 照度（lux）
    uv: int            # UV値
    voc: float         # VOC値

@dataclass
class MotionData:
    orientation: Orientation    # 姿勢角
    acceleration: Vector3D     # 加速度
    gyroscope: Vector3D        # ジャイロ
    magnetic: Vector3D         # 磁場
```

### 開発環境セットアップ

```bash
# プロジェクトクローン
git clone <repository-url>
cd raspizw-sensor-serial

# 開発用仮想環境
python3 -m venv dev-venv
source dev-venv/bin/activate

# 依存関係
pip install -r requirements.txt
```

### 機能拡張ガイド

#### 新しいコマンドの追加

1. **`_validate_command()`の更新:**

```python
def _validate_command(self, command: str) -> bool:
    # 許可されたコマンドのリスト
    valid_commands = [
        "get_sensor_data", 
        "ping", 
        "status",
        "new_command"  # 新しいコマンドを追加
    ]
    
    if command not in valid_commands:
        self.logger.warning(f"無効なコマンド: {command}")
        return False
    
    return True
```

2. **`_process_command()`の更新:**

```python
def _process_command(self, command: str) -> bytes:
    try:
        if command == "new_command":
            # 新しい処理ロジック
            result = self._handle_new_command()
            response = json.dumps(result)
            return f"{response}\r\n".encode('utf-8')
        
        # 既存のコマンド処理...
        
    except Exception as e:
        self.logger.error(f"コマンド処理エラー: {e}")
        error_response = json.dumps({"error": f"processing error: {str(e)}"})
        return f"{error_response}\r\n".encode('utf-8')
```

3. **処理メソッドの実装:**

```python
def _handle_new_command(self) -> Dict[str, Any]:
    """新しいコマンドの処理ロジック
    
    Returns:
        コマンドの実行結果
    """
    return {"result": "success", "data": "command executed"}
```


## 🔗 関連リンク

- [Waveshare Environment Sensor HAT](https://www.waveshare.com/wiki/Environment_Sensor_HAT)
- [Raspberry Pi USB-OTG設定ガイド](https://suzu-ha.com/entry/2024/06/01/232052)
- [Python Serial通信ドキュメント](https://pyserial.readthedocs.io/)
