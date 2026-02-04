#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
啟動 Webhook 定時重啟管理器的便捷腳本
"""

import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.absolute()
SCHEDULER_SCRIPT = SCRIPT_DIR / "webhook_scheduler.py"


def main():
    print("=" * 70)
    print("TradingView Webhook 定時重啟管理器")
    print("=" * 70)
    print()
    
    # 檢查腳本是否存在
    if not SCHEDULER_SCRIPT.exists():
        print(f"✗ 錯誤：找不到 {SCHEDULER_SCRIPT}")
        sys.exit(1)
    
    print("正在啟動定時重啟管理器...")
    print("按 Ctrl+C 可以停止管理器")
    print()
    
    try:
        # 在背景啟動管理器
        if sys.platform == 'win32':
            # Windows: 使用 pythonw 在背景運行（無控制台視窗）
            pythonw = sys.executable.replace('python.exe', 'pythonw.exe')
            if Path(pythonw).exists():
                subprocess.Popen(
                    [pythonw, str(SCHEDULER_SCRIPT)],
                    cwd=str(SCRIPT_DIR),
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                print("✓ 管理器已在背景啟動（無視窗）")
            else:
                # 如果沒有 pythonw，使用普通 python
                subprocess.Popen(
                    [sys.executable, str(SCHEDULER_SCRIPT)],
                    cwd=str(SCRIPT_DIR)
                )
                print("✓ 管理器已啟動")
        else:
            # Linux/Mac: 使用 nohup 在背景運行
            subprocess.Popen(
                ['nohup', sys.executable, str(SCHEDULER_SCRIPT), '&'],
                cwd=str(SCRIPT_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("✓ 管理器已在背景啟動")
        
        print()
        print("查看日誌: webhook_restart.log")
        print("停止管理器: python stop_scheduler.py")
        print()
        
    except Exception as e:
        print(f"✗ 啟動失敗: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
