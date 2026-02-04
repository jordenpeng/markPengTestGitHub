#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingView Webhook 定時重啟管理器
使用 Python schedule 庫實現每日定時重啟功能
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

# 配置
WEBHOOK_SCRIPT = "tradingview_webhook.py"
RESTART_TIME = "22:05"  # 每日重啟時間
LOG_FILE = "webhook_restart.log"
WEBHOOK_HOST = "0.0.0.0"
WEBHOOK_PORT = 5000

# 獲取當前腳本目錄
SCRIPT_DIR = Path(__file__).parent.absolute()
WEBHOOK_PATH = SCRIPT_DIR / WEBHOOK_SCRIPT
LOG_PATH = SCRIPT_DIR / LOG_FILE


class WebhookManager:
    """Webhook 服務管理器"""
    
    def __init__(self):
        # 延遲導入，避免在安裝依賴前失敗
        global psutil, schedule
        import psutil
        import schedule
        
        self.webhook_process = None
        self.log_file = open(LOG_PATH, 'a', encoding='utf-8')
        
    def log(self, message, level="INFO"):
        """記錄日誌"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        try:
            if self.log_file and not self.log_file.closed:
                self.log_file.write(log_message + "\n")
                self.log_file.flush()
        except:
            pass  # 忽略日誌寫入錯誤
    
    def find_webhook_processes(self):
        """查找所有 tradingview_webhook.py 進程"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any(WEBHOOK_SCRIPT in str(cmd) for cmd in cmdline):
                    processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes
    
    def stop_webhook_processes(self):
        """停止所有 webhook 進程"""
        self.log("=" * 70)
        self.log("開始停止 TradingView Webhook 服務")
        
        processes = self.find_webhook_processes()
        
        if not processes:
            self.log("沒有找到正在運行的 webhook 進程")
            return True
        
        # 嘗試優雅關閉
        for proc in processes:
            try:
                self.log(f"正在停止進程 PID: {proc.pid}")
                proc.terminate()  # 發送 SIGTERM
            except Exception as e:
                self.log(f"停止進程 {proc.pid} 時發生錯誤: {e}", "ERROR")
        
        # 等待進程結束
        time.sleep(3)
        
        # 強制關閉仍在運行的進程
        remaining = self.find_webhook_processes()
        for proc in remaining:
            try:
                self.log(f"強制終止進程 PID: {proc.pid}", "WARNING")
                proc.kill()  # 發送 SIGKILL
            except Exception as e:
                self.log(f"強制終止進程 {proc.pid} 時發生錯誤: {e}", "ERROR")
        
        time.sleep(1)
        
        # 確認所有進程已停止
        final_check = self.find_webhook_processes()
        if final_check:
            self.log(f"警告：仍有 {len(final_check)} 個進程在運行", "WARNING")
            return False
        else:
            self.log("✓ 所有 webhook 進程已成功停止")
            return True
    
    def start_webhook_service(self):
        """啟動 webhook 服務"""
        self.log("正在啟動 TradingView Webhook 服務")
        
        # 檢查腳本是否存在
        if not WEBHOOK_PATH.exists():
            self.log(f"錯誤：找不到 {WEBHOOK_SCRIPT}", "ERROR")
            return False
        
        try:
            # 創建日誌文件路徑
            webhook_log = SCRIPT_DIR / "webhook_service.log"
            
            # 啟動新進程
            cmd = [
                sys.executable,
                str(WEBHOOK_PATH),
                "--host", WEBHOOK_HOST,
                "--port", str(WEBHOOK_PORT)
            ]
            
            # 打開日誌文件
            log_file = open(webhook_log, 'a', encoding='utf-8')
            log_file.write(f"\n{'='*70}\n")
            log_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 啟動 Webhook 服務\n")
            log_file.write(f"{'='*70}\n")
            log_file.flush()
            
            # Windows 上使用特殊標誌在背景運行
            if sys.platform == 'win32':
                # 使用 DETACHED_PROCESS 標誌使進程獨立運行
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                DETACHED_PROCESS = 0x00000008
                
                self.webhook_process = subprocess.Popen(
                    cmd,
                    cwd=str(SCRIPT_DIR),
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
                )
            else:
                # Linux/Mac
                self.webhook_process = subprocess.Popen(
                    cmd,
                    cwd=str(SCRIPT_DIR),
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
            
            self.log(f"✓ 服務進程已啟動 (PID: {self.webhook_process.pid})")
            self.log(f"  監聽地址: http://{WEBHOOK_HOST}:{WEBHOOK_PORT}")
            self.log(f"  日誌文件: {webhook_log}")
            
            # 等待並檢查進程
            time.sleep(5)
            
            # 使用 psutil 檢查進程是否存在
            import psutil
            if psutil.pid_exists(self.webhook_process.pid):
                try:
                    proc = psutil.Process(self.webhook_process.pid)
                    if proc.is_running():
                        self.log("✓ 服務確認正在運行")
                        
                        # 健康檢查（可選）
                        time.sleep(2)
                        if self.health_check():
                            self.log("✓ 健康檢查通過")
                        else:
                            self.log("⚠️  健康檢查失敗（服務可能仍在初始化）", "WARNING")
                        
                        return True
                except:
                    pass
            
            # 進程已退出，讀取日誌查看錯誤
            try:
                log_file.close()
                with open(webhook_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) > 0:
                        self.log("服務啟動失敗，最後幾行日誌:", "ERROR")
                        for line in lines[-10:]:  # 顯示最後10行
                            self.log(f"  {line.rstrip()}", "ERROR")
            except:
                pass
            
            self.log("✗ 服務進程已退出", "ERROR")
            return False
                
        except Exception as e:
            self.log(f"啟動服務時發生錯誤: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            return False
    
    def health_check(self):
        """健康檢查"""
        try:
            import urllib.request
            url = f"http://localhost:{WEBHOOK_PORT}/health"
            response = urllib.request.urlopen(url, timeout=5)
            return response.status == 200
        except Exception:
            return False
    
    def restart_webhook(self):
        """重啟 webhook 服務"""
        self.log("=" * 70)
        self.log("執行定時重啟任務")
        
        # 步驟 1: 停止服務
        if not self.stop_webhook_processes():
            self.log("警告：停止服務時遇到問題", "WARNING")
        
        # 步驟 2: 啟動服務
        if self.start_webhook_service():
            self.log("✓ 重啟完成")
        else:
            self.log("✗ 重啟失敗", "ERROR")
        
        self.log("=" * 70)
    
    def run_scheduler(self, start_service_now=True):
        """運行定時調度器"""
        import schedule  # 確保 schedule 已導入
        
        self.log("=" * 70)
        self.log("TradingView Webhook 定時重啟管理器已啟動")
        self.log(f"每日重啟時間: {RESTART_TIME}")
        self.log(f"當前時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("=" * 70)
        
        # 啟動時先確保服務正在運行
        if start_service_now:
            self.log("\n>>> 檢查 Webhook 服務狀態...")
            processes = self.find_webhook_processes()
            if not processes:
                self.log(">>> Webhook 服務未運行，正在啟動...")
                if self.start_webhook_service():
                    self.log("✓ Webhook 服務已啟動")
                else:
                    self.log("✗ Webhook 服務啟動失敗", "ERROR")
            else:
                self.log(f"✓ Webhook 服務已在運行 (PID: {[p.pid for p in processes]})")
            self.log("")
        
        # 註冊定時任務
        schedule.every().day.at(RESTART_TIME).do(self.restart_webhook)
        
        # 顯示下次執行時間
        next_run = schedule.next_run()
        if next_run:
            self.log(f"下次執行時間: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 持續運行調度器
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分鐘檢查一次
        except KeyboardInterrupt:
            self.log("收到停止信號，正在關閉...")
            self.cleanup()
    
    def cleanup(self):
        """清理資源"""
        self.log("清理資源...")
        if self.log_file and not self.log_file.closed:
            self.log_file.close()
        self.log("管理器已關閉")


def install_dependencies():
    """安裝必要的依賴套件"""
    print("檢查並安裝必要的 Python 套件...")
    
    required_packages = ['schedule', 'psutil']
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} 已安裝")
        except ImportError:
            print(f"正在安裝 {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ {package} 安裝完成")


def main():
    """主函數"""
    import argparse
    
    # 先聲明全域變數
    global RESTART_TIME, WEBHOOK_HOST, WEBHOOK_PORT
    
    parser = argparse.ArgumentParser(description='TradingView Webhook 定時重啟管理器')
    parser.add_argument('--time', default=RESTART_TIME, 
                        help=f'每日重啟時間 (格式: HH:MM，預設: {RESTART_TIME})')
    parser.add_argument('--install-deps', action='store_true',
                        help='安裝必要的依賴套件')
    parser.add_argument('--restart-now', action='store_true',
                        help='立即執行一次重啟（不啟動定時器）')
    parser.add_argument('--start-now', action='store_true', default=True,
                        help='啟動時自動啟動 webhook 服務（預設啟用）')
    parser.add_argument('--no-start', action='store_true',
                        help='啟動時不自動啟動 webhook 服務')
    parser.add_argument('--host', default=WEBHOOK_HOST,
                        help=f'Webhook 監聽地址 (預設: {WEBHOOK_HOST})')
    parser.add_argument('--port', type=int, default=WEBHOOK_PORT,
                        help=f'Webhook 監聽埠號 (預設: {WEBHOOK_PORT})')
    
    args = parser.parse_args()
    
    # 安裝依賴
    if args.install_deps:
        install_dependencies()
        return
    
    # 更新全域配置
    RESTART_TIME = args.time
    WEBHOOK_HOST = args.host
    WEBHOOK_PORT = args.port
    
    # 創建管理器實例
    manager = WebhookManager()
    
    # 立即重啟模式
    if args.restart_now:
        manager.restart_webhook()
        manager.cleanup()
        return
    
    # 決定是否在啟動時啟動服務
    start_service_now = not args.no_start
    
    # 啟動定時調度器
    try:
        manager.run_scheduler(start_service_now=start_service_now)
    except Exception as e:
        manager.log(f"管理器運行時發生錯誤: {e}", "ERROR")
        import traceback
        manager.log(traceback.format_exc(), "ERROR")
        manager.cleanup()
        sys.exit(1)


if __name__ == '__main__':
    main()
