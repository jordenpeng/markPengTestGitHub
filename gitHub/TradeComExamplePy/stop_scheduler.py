#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
停止 Webhook 定時重啟管理器
"""

import sys
import psutil


def main():
    print("=" * 70)
    print("停止 Webhook 定時重啟管理器")
    print("=" * 70)
    print()
    
    # 查找管理器進程
    found = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any('webhook_scheduler.py' in str(cmd) for cmd in cmdline):
                print(f"找到管理器進程 PID: {proc.pid}")
                proc.terminate()
                print(f"✓ 已發送停止信號給進程 {proc.pid}")
                found = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if not found:
        print("沒有找到正在運行的管理器進程")
    else:
        print()
        print("管理器已停止")
    
    print()


if __name__ == '__main__':
    main()
