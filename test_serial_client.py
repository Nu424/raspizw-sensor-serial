#!/usr/bin/env python3
"""
センサーシリアルサーバーのテスト用クライアント
"""

import serial
import json
import time
import sys
from typing import Optional


class SerialTestClient:
    """シリアルテストクライアント"""
    
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
    
    def connect(self) -> bool:
        """シリアル接続を開始"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=2.0
            )
            print(f"シリアルポート {self.port} に接続しました")
            return True
        except serial.SerialException as e:
            print(f"接続エラー: {e}")
            return False
    
    def disconnect(self):
        """シリアル接続を終了"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("シリアル接続を終了しました")
    
    def send_command(self, command: str) -> Optional[str]:
        """コマンドを送信して応答を受信"""
        if not self.serial_conn or not self.serial_conn.is_open:
            print("シリアル接続が開いていません")
            return None
        
        try:
            # コマンド送信
            cmd_bytes = f"{command}\r\n".encode('utf-8')
            self.serial_conn.write(cmd_bytes)
            self.serial_conn.flush()
            print(f"送信: {command}")
            
            # 応答受信
            response = self.serial_conn.readline()
            if response:
                decoded = response.decode('utf-8', errors='replace').strip()
                print(f"受信: {decoded}")
                return decoded
            else:
                print("応答がありません")
                return None
                
        except Exception as e:
            print(f"通信エラー: {e}")
            return None
    
    def test_all_commands(self):
        """すべてのコマンドをテスト"""
        commands = ["ping", "status", "get_sensor_data", "invalid_command"]
        
        for cmd in commands:
            print(f"\n--- {cmd} をテスト ---")
            response = self.send_command(cmd)
            
            if response:
                try:
                    # JSONとしてパース可能かチェック
                    parsed = json.loads(response)
                    print(f"JSON解析成功: {type(parsed)}")
                    if cmd == "get_sensor_data" and "environment" in parsed:
                        print("センサーデータの構造を確認:")
                        print(f"  温度: {parsed['environment'].get('temperature')}℃")
                        print(f"  湿度: {parsed['environment'].get('humidity')}%")
                        print(f"  気圧: {parsed['environment'].get('pressure')}hPa")
                except json.JSONDecodeError:
                    print("JSON解析失敗 - プレーンテキスト応答")
            
            time.sleep(1)  # 間隔を空ける
    
    def interactive_mode(self):
        """対話モード"""
        print("\n対話モードを開始します。'exit'で終了。")
        while True:
            try:
                command = input("\nコマンドを入力: ").strip()
                if command.lower() == 'exit':
                    break
                elif command:
                    self.send_command(command)
                    
            except KeyboardInterrupt:
                print("\n対話モードを終了します")
                break


def main():
    """メイン関数"""
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = "/dev/ttyUSB0"
    
    client = SerialTestClient(port)
    
    try:
        if not client.connect():
            print("接続に失敗しました")
            sys.exit(1)
        
        print("\n1. 全コマンドテスト")
        print("2. 対話モード")
        choice = input("\n選択してください (1/2): ").strip()
        
        if choice == "1":
            client.test_all_commands()
        elif choice == "2":
            client.interactive_mode()
        else:
            print("無効な選択です")
    
    except KeyboardInterrupt:
        print("\nテストを中断しました")
    
    finally:
        client.disconnect()


if __name__ == "__main__":
    main() 