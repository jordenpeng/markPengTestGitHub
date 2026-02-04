#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 Webhook 定時重啟管理器狀態
"""

import sys
import psutil
import schedule
from pathlib import Path
from datetime import datetime


def main():
    print()
    print("=" * 70)
    print("Webhook 定時重啟管理器狀態檢查")
    print("=" * 70)
    print()
    
    # 檢查管理器進程
    print("🔍 管理器進程狀態：")
    print("-" * 70)
    
    manager_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any('webhook_scheduler.py' in str(cmd) for cmd in cmdline):
                manager_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if manager_processes:
        print("✓ 管理器正在運行")
        for proc in manager_processes:
            create_time = datetime.fromtimestamp(proc.info['create_time'])
            uptime = datetime.now() - create_time
            print(f"  進程 ID: {proc.pid}")
            print(f"  啟動時間: {create_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  運行時長: {uptime}")
    else:
        print("✗ 管理器未運行")
    
    print()
    
    # 檢查 webhook 服務
    print("🔍 Webhook 服務狀態：")
    print("-" * 70)
    
    webhook_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any('tradingview_webhook.py' in str(cmd) for cmd in cmdline):
                webhook_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if webhook_processes:
        print("✓ Webhook 服務正在運行")
        for proc in webhook_processes:
            create_time = datetime.fromtimestamp(proc.info['create_time'])
            uptime = datetime.now() - create_time
            print(f"  進程 ID: {proc.pid}")
            print(f"  啟動時間: {create_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  運行時長: {uptime}")
    else:
        print("✗ Webhook 服務未運行")
    
    print()
    
    # 檢查日誌文件
    log_file = Path(__file__).parent / "webhook_restart.log"
    print("📄 日誌文件：")
    print("-" * 70)
    
    if log_file.exists():
        size_kb = log_file.stat().st_size / 1024
        print(f"  路徑: {log_file}")
        print(f"  大小: {size_kb:.2f} KB")
        print()
        print("  最近日誌內容（最後 15 行）：")
        print("  " + "-" * 66)
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-15:]:
                    print(f"  {line.rstrip()}")
        except Exception as e:
            print(f"  讀取日誌失敗: {e}")
        
        print("  " + "-" * 66)
    else:
        print("  日誌文件尚未建立")
    
    print()
    print("=" * 70)
    print("快速管理指令：")
    print("=" * 70)
    print("  啟動管理器: python start_scheduler.py")
    print("  停止管理器: python stop_scheduler.py")
    print("  立即重啟:   python webhook_scheduler.py --restart-now")
    print("  查看日誌:   python -c \"open('webhook_restart.log').read()\"")
    print()


if __name__ == '__main__':
    main()
