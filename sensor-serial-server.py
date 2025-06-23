#!/usr/bin/env python3
"""
Raspberry Pi Zero W Sensor Serial Server
シリアル通信でセンサーデータを提供するサーバー

改善点:
- 包括的なエラーハンドリング
- 適切なリソース管理
- 設定ファイル対応
- ログ機能
- 入力検証
- Graceful shutdown
- パフォーマンス最適化
"""

import serial
import json
import time
import logging
import signal
import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler
from dataclasses import asdict

from Sensor import SensorHub


class SerialServerConfig:
    """設定管理クラス"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込む"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logging.warning(f"設定ファイル {self.config_path} が見つかりません。デフォルト設定を使用します。")
                return self._get_default_config()
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"設定ファイル読み込みエラー: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を返す"""
        return {
            "serial": {
                "port": "/dev/ttyUSB0",
                "baudrate": 9600,
                "timeout": 1.0,
                "write_timeout": 1.0
            },
            "system": {
                "loop_interval": 0.1,
                "max_command_length": 256,
                "shutdown_timeout": 5.0
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "sensor_server.log",
                "max_bytes": 1048576,
                "backup_count": 3
            }
        }
    
    def get(self, section: str, key: str, default=None):
        """設定値を取得"""
        return self.config.get(section, {}).get(key, default)


class SensorSerialServer:
    """センサーシリアルサーバーメインクラス"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = SerialServerConfig(config_path)
        self.logger = self._setup_logging()
        self.sensor_hub: Optional[SensorHub] = None
        self.serial_port: Optional[serial.Serial] = None
        self.running = False
        self.shutdown_event = threading.Event()
        
        # シグナルハンドラーの設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("センサーシリアルサーバーを初期化しました")
    
    def _setup_logging(self) -> logging.Logger:
        """ログ設定を初期化"""
        logger = logging.getLogger("SensorSerialServer")
        logger.setLevel(getattr(logging, self.config.get("logging", "level", "INFO")))
        
        # ファイルハンドラー（ローテーション対応）
        log_file = self.config.get("logging", "file", "sensor_server.log")
        max_bytes = self.config.get("logging", "max_bytes", 1048576)
        backup_count = self.config.get("logging", "backup_count", 3)
        
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
        )
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        
        # フォーマッター
        formatter = logging.Formatter(
            self.config.get("logging", "format", 
                           "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _signal_handler(self, signum, frame):
        """シグナルハンドラー（Graceful shutdown）"""
        self.logger.info(f"シグナル {signum} を受信しました。サーバーを停止します...")
        self.shutdown()
    
    @contextmanager
    def _serial_connection(self):
        """シリアル接続のコンテキストマネージャー"""
        try:
            self.serial_port = serial.Serial(
                port=self.config.get("serial", "port", "/dev/ttyUSB0"),
                baudrate=self.config.get("serial", "baudrate", 9600),
                timeout=self.config.get("serial", "timeout", 1.0),
                write_timeout=self.config.get("serial", "write_timeout", 1.0)
            )
            self.logger.info(f"シリアルポート {self.serial_port.port} を開きました")
            yield self.serial_port
        except serial.SerialException as e:
            self.logger.error(f"シリアルポートエラー: {e}")
            raise
        finally:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                self.logger.info("シリアルポートを閉じました")
    
    def _initialize_sensors(self) -> bool:
        """センサーを初期化"""
        try:
            self.sensor_hub = SensorHub()
            self.logger.info("センサーハブの初期化が完了しました")
            return True
        except Exception as e:
            self.logger.error(f"センサー初期化エラー: {e}")
            return False
    
    def _validate_command(self, command: str) -> bool:
        """コマンドの検証"""
        max_length = self.config.get("system", "max_command_length", 256)
        
        if len(command) > max_length:
            self.logger.warning(f"コマンド長が上限を超過: {len(command)} > {max_length}")
            return False
        
        # 許可されたコマンドのリスト
        valid_commands = ["get_sensor_data", "ping", "status"]
        
        if command not in valid_commands:
            self.logger.warning(f"無効なコマンド: {command}")
            return False
        
        return True
    
    def _process_command(self, command: str) -> bytes:
        """コマンドを処理して応答を生成"""
        try:
            if command == "get_sensor_data":
                if not self.sensor_hub:
                    return b'{"error": "sensor not initialized"}\r\n'
                
                data = self.sensor_hub.read_all()
                # dataclassを辞書に変換してJSONシリアライズ
                data_dict = asdict(data)
                response = json.dumps(data_dict, ensure_ascii=False)
                self.logger.debug(f"センサーデータを送信: {len(response)} bytes")
                return f"{response}\r\n".encode('utf-8')
            
            elif command == "ping":
                return b'{"status": "pong"}\r\n'
            
            elif command == "status":
                status = {
                    "sensor_initialized": self.sensor_hub is not None,
                    "running": self.running,
                    "port": self.config.get("serial", "port")
                }
                response = json.dumps(status)
                return f"{response}\r\n".encode('utf-8')
            
            else:
                return b'{"error": "invalid command"}\r\n'
                
        except Exception as e:
            self.logger.error(f"コマンド処理エラー: {e}")
            error_response = json.dumps({"error": f"processing error: {str(e)}"})
            return f"{error_response}\r\n".encode('utf-8')
    
    def _read_serial_data(self, serial_port: serial.Serial) -> Optional[str]:
        """シリアルデータを読み取り"""
        try:
            if serial_port.in_waiting > 0:
                line = serial_port.readline()
                if line:
                    decoded = line.decode('utf-8', errors='replace')
                    return decoded
        except (serial.SerialException, UnicodeDecodeError) as e:
            self.logger.error(f"シリアル読み取りエラー: {e}")
        return None
    
    def _write_serial_data(self, serial_port: serial.Serial, data: bytes) -> bool:
        """シリアルデータを書き込み"""
        try:
            serial_port.write(data)
            serial_port.flush()
            return True
        except serial.SerialException as e:
            self.logger.error(f"シリアル書き込みエラー: {e}")
            return False
    
    def run(self):
        """メインサーバーループ"""
        self.logger.info("センサーシリアルサーバーを開始します")
        
        # センサー初期化
        if not self._initialize_sensors():
            self.logger.error("センサー初期化に失敗しました。終了します。")
            return False
        
        try:
            with self._serial_connection() as serial_port:
                self.running = True
                self.logger.info("サーバーが正常に開始されました")
                
                temp_data = ""
                loop_interval = self.config.get("system", "loop_interval", 0.1)
                
                while self.running and not self.shutdown_event.is_set():
                    # シリアルデータ読み取り
                    data = self._read_serial_data(serial_port)
                    if data:
                        temp_data += data
                    
                    # コマンド完了チェック(最後に改行がある場合、コマンドを処理する)
                    if '\n' in temp_data or '\r' in temp_data:
                        if not temp_data.endswith('\n'):
                            continue
                        command = temp_data.rstrip('\n').rstrip('\r')
                        if command:
                            self.logger.info(f"コマンド受信: {command}")
                            
                            if self._validate_command(command):
                                response = self._process_command(command)
                                if self._write_serial_data(serial_port, response):
                                    self.logger.debug(f"応答送信完了: {len(response)} bytes")
                            else:
                                error_response = b'{"error": "invalid command"}\r\n'
                                self._write_serial_data(serial_port, error_response)
                        temp_data = ""
                    
                    # CPU使用率を抑制
                    time.sleep(loop_interval)
                
                self.logger.info("サーバーループを終了しました")
                return True
                
        except Exception as e:
            self.logger.error(f"サーバー実行エラー: {e}")
            return False
        finally:
            self.running = False
    
    def shutdown(self):
        """サーバーを停止"""
        self.logger.info("サーバーの停止を開始します...")
        self.running = False
        self.shutdown_event.set()
        
        # タイムアウト付きで停止を待機
        timeout = self.config.get("system", "shutdown_timeout", 5.0)
        if self.shutdown_event.wait(timeout):
            self.logger.info("サーバーが正常に停止しました")
        else:
            self.logger.warning("サーバー停止がタイムアウトしました")


def main():
    """メイン関数"""
    try:
        # 設定ファイルパスの指定（コマンドライン引数対応）
        config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
        
        server = SensorSerialServer(config_path)
        success = server.run()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt: サーバーを停止します...")
        sys.exit(0)
    except Exception as e:
        print(f"予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
