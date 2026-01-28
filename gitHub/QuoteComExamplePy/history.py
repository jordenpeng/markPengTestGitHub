"""
history.py - 歷史報價資料記錄程式
持續記錄 QuoteCom 即時報價資料，並轉換為 K 線格式儲存
可供未來載入到 MACD 等技術分析策略中使用
"""

import clr
import sys
from time import sleep, time
from datetime import datetime, timedelta
from collections import deque
import json
import os
import csv

# 引用必要的 DLL
clr.AddReference("Package")
clr.AddReference("PushClient")
clr.AddReference("QuoteCom")

from Intelligence import QuoteCom, MARKET_FLAG, COM_STATUS

# 導入配置檔
import config


class HistoryDataRecorder:
    """歷史資料記錄器 - 記錄即時報價並轉換為 K 線"""
    
    def __init__(self, timeframes=[3, 5], data_dir="historical_data"):
        """
        初始化歷史資料記錄器
        
        Args:
            timeframes: K 線週期列表（分鐘），預設 [3, 5] 分鐘
            data_dir: 資料儲存目錄
        """
        print("=" * 70)
        print("QuoteCom 歷史資料記錄程式")
        print("=" * 70)
        
        # 從 config 讀取配置
        self.host = config.SERVER_HOST
        self.port = config.SERVER_PORT
        self.sid = config.SESSION_ID
        self.token = config.API_TOKEN
        self.account = config.ACCOUNT
        self.password = config.PASSWORD
        self.stock_code = config.STOCK_CODE
        self.query_interval = config.QUOTE_QUERY_INTERVAL
        
        # K 線設定
        self.timeframes = timeframes if isinstance(timeframes, list) else [timeframes]
        self.data_dir = data_dir
        
        # 建立資料目錄
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            print(f">>> 建立資料目錄: {data_dir}")
        
        # 初始化 QuoteCom
        self.quoteCom = QuoteCom("", self.port, self.sid, self.token)
        print(f"QuoteCom API 版本: {self.quoteCom.version}")
        print(f"商品代碼: {self.stock_code}")
        print(f"K 線週期: {', '.join([str(tf) + '分' for tf in self.timeframes])}")
        print(f"資料儲存目錄: {self.data_dir}")
        
        # K 線資料 - 為每個時間週期維護獨立的 K 線
        self.current_candles = {tf: None for tf in self.timeframes}
        self.candles = {tf: deque(maxlen=10000) for tf in self.timeframes}  # 保留最近 10000 根 K 線
        
        # Tick 資料記錄（選用）
        self.tick_data = deque(maxlen=50000)  # 保留最近 50000 筆 tick
        self.record_tick = True  # 是否記錄原始 tick 資料
        
        # 統計資訊
        self.tick_count = 0
        self.candle_counts = {tf: 0 for tf in self.timeframes}
        self.start_time = None
        
        # 檔案名稱 - 為每個時間週期維護獨立的檔案
        self.candle_filenames = {tf: self._get_candle_filename(tf) for tf in self.timeframes}
        self.tick_filename = self._get_tick_filename()
        
        # 初始化檔案
        self._init_data_files()
        
        print("=" * 70 + "\n")
        
        # 註冊事件處理器
        self.quoteCom.OnRcvMessage += self.on_receive_message
        self.quoteCom.OnGetStatus += self.on_get_status
        self.quoteCom.OnRecoverStatus += self.on_recover_status
        
        self.is_logged_in = False
        self.is_downloaded = False
        self.keep_running = True
        self.last_query_time = 0
        self.last_save_time = time()
    
    def _get_candle_filename(self, timeframe):
        """取得 K 線資料檔案名稱"""
        today = datetime.now().strftime('%Y%m%d')
        return os.path.join(self.data_dir, f"{self.stock_code}_candle_{timeframe}m_{today}.csv")
    
    def _get_tick_filename(self):
        """取得 Tick 資料檔案名稱"""
        today = datetime.now().strftime('%Y%m%d')
        return os.path.join(self.data_dir, f"{self.stock_code}_tick_{today}.csv")
    
    def _init_data_files(self):
        """初始化資料檔案（寫入標題列）"""
        # K 線資料檔案 - 為每個時間週期建立檔案
        for tf, filename in self.candle_filenames.items():
            if not os.path.exists(filename):
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['時間', '開盤價', '最高價', '最低價', '收盤價', '成交量'])
                print(f">>> 建立 {tf}分K 線資料檔案: {filename}")
            else:
                print(f">>> {tf}分K 線資料檔案已存在: {filename}")
        
        # Tick 資料檔案
        if self.record_tick and not os.path.exists(self.tick_filename):
            with open(self.tick_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['時間', '價格', '數量', '累計量'])
            print(f">>> 建立 Tick 資料檔案: {self.tick_filename}")
    
    def on_receive_message(self, sender, pkg):
        """接收報價訊息事件"""
        try:
            if pkg.DT == 1503:  # 登入成功
                self.handle_login_response(pkg)
            elif pkg.DT == 20026:  # 查詢商品最後價格
                self.handle_last_price(pkg)
            elif pkg.DT == 5005:  # 盤別資訊
                pass  # 忽略盤別資訊
        except Exception as e:
            print(f"處理訊息時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_login_response(self, pkg):
        """處理登入回應"""
        print("\n登入回應:")
        print(f"結果: {self.quoteCom.GetSubQuoteMsg(pkg.Code)}")
        
        if pkg.Code == 0:
            self.is_logged_in = True
            self.start_time = datetime.now()
            print(">>> 登入成功！\n")
        else:
            print(">>> 登入失敗！\n")
    
    def handle_last_price(self, pkg):
        """處理最後價格查詢並記錄資料"""
        timestamp = datetime.now()
        
        # 安全地轉換成交價格
        try:
            match_price = float(pkg.MatchPrice.ToString()) if hasattr(pkg.MatchPrice, 'ToString') else float(pkg.MatchPrice)
        except:
            match_price = float(pkg.MatchPrice)
        
        total_qty = pkg.MatchTotalQty
        
        # 記錄 tick 資料
        if self.record_tick:
            tick = {
                'time': timestamp,
                'price': match_price,
                'quantity': 1,  # 單筆數量（QuoteCom 不提供此欄位，設為 1）
                'total_qty': total_qty
            }
            self.tick_data.append(tick)
            self.tick_count += 1
        
        # 更新所有時間週期的 K 線
        for tf in self.timeframes:
            self._update_candle(match_price, timestamp, total_qty, tf)
        
        # 顯示即時資訊
        candle_info = ' | '.join([f"{tf}分K:{self.candle_counts[tf]}" for tf in self.timeframes])
        print(f"[{timestamp.strftime('%H:%M:%S')}] "
              f"{self.stock_code} | 價格: {match_price:.2f} | 總量: {total_qty:,} | "
              f"Tick數: {self.tick_count} | {candle_info}")
    
    def _update_candle(self, price, timestamp, volume=0, timeframe=5):
        """更新指定時間週期的 K 線資料"""
        # 計算當前 K 線的時間區間
        candle_time = self._get_candle_time(timestamp, timeframe)
        
        # 如果是新的 K 線
        if self.current_candles[timeframe] is None or self.current_candles[timeframe]['time'] != candle_time:
            # 保存上一根 K 線
            if self.current_candles[timeframe] is not None:
                self.candles[timeframe].append(self.current_candles[timeframe])
                self._save_candle(self.current_candles[timeframe], timeframe)
                self.candle_counts[timeframe] += 1
                print(f"\n>>> {timeframe}分K 線收盤: {self.current_candles[timeframe]['time'].strftime('%Y-%m-%d %H:%M')} | "
                      f"開: {self.current_candles[timeframe]['open']:.2f} | "
                      f"高: {self.current_candles[timeframe]['high']:.2f} | "
                      f"低: {self.current_candles[timeframe]['low']:.2f} | "
                      f"收: {self.current_candles[timeframe]['close']:.2f} | "
                      f"量: {self.current_candles[timeframe]['volume']:,}\n")
            
            # 創建新 K 線
            self.current_candles[timeframe] = {
                'time': candle_time,
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'volume': volume
            }
        else:
            # 更新當前 K 線
            self.current_candles[timeframe]['high'] = max(self.current_candles[timeframe]['high'], price)
            self.current_candles[timeframe]['low'] = min(self.current_candles[timeframe]['low'], price)
            self.current_candles[timeframe]['close'] = price
            # 更新成交量（使用累計量的差異）
            if volume > self.current_candles[timeframe]['volume']:
                self.current_candles[timeframe]['volume'] = volume
    
    def _get_candle_time(self, timestamp, timeframe):
        """取得指定時間週期 K 線的時間標記（對齊到時間區間）"""
        minutes = (timestamp.hour * 60 + timestamp.minute) // timeframe * timeframe
        hour = minutes // 60
        minute = minutes % 60
        return timestamp.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    def _save_candle(self, candle, timeframe):
        """儲存指定時間週期的 K 線資料到檔案"""
        try:
            with open(self.candle_filenames[timeframe], 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    candle['time'].strftime('%Y-%m-%d %H:%M:%S'),
                    candle['open'],
                    candle['high'],
                    candle['low'],
                    candle['close'],
                    candle['volume']
                ])
        except Exception as e:
            print(f">>> 儲存 {timeframe}分K 線資料時發生錯誤: {e}")
    
    def _save_tick_batch(self):
        """批次儲存 tick 資料"""
        if not self.record_tick or len(self.tick_data) == 0:
            return
        
        try:
            with open(self.tick_filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for tick in self.tick_data:
                    writer.writerow([
                        tick['time'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                        tick['price'],
                        tick['quantity'],
                        tick['total_qty']
                    ])
            
            print(f"\n>>> 已儲存 {len(self.tick_data)} 筆 tick 資料")
            self.tick_data.clear()
        except Exception as e:
            print(f">>> 儲存 tick 資料時發生錯誤: {e}")
    
    def on_get_status(self, sender, status, msg):
        """接收狀態事件"""
        try:
            smsg = bytes(msg).decode('UTF-8', 'ignore')
            if smsg:  # 只顯示有內容的訊息
                print(f"[狀態] {status.ToString()}: {smsg}")
        except:
            pass
    
    def on_recover_status(self, sender, topic, status, count):
        """資料回補事件"""
        print(f"[回補] 主題: {topic} | 狀態: {status.ToString()} | 數量: {count}")
    
    def login(self):
        """登入報價系統"""
        print("\n>>> 嘗試登入...")
        self.quoteCom.Connect2Quote(self.host, self.port, self.account, 
                                     self.password, ' ', '')
        sleep(3)
        return self.is_logged_in
    
    def download_product_list(self):
        """下載商品基本資料"""
        print("\n>>> 下載商品基本資料...")
        res = self.quoteCom.RetriveQuoteList()
        if res == 0:
            print(">>> 下載請求已送出，等待回應...")
            sleep(3)
            self.quoteCom.LoadTaifexProductXMLT1()
            sleep(2)
            self.is_downloaded = True
            print(">>> 商品資料下載完成！")
        else:
            print(f">>> 下載失敗: {self.quoteCom.GetSubQuoteMsg(res)}")
        return self.is_downloaded
    
    def subscribe_quote(self, symbol_id):
        """訂閱商品報價"""
        print(f"\n>>> 訂閱商品: {symbol_id}")
        res = self.quoteCom.SubQuote(symbol_id)
        if res == 0:
            print(f">>> 訂閱成功！")
            sleep(1)
            return True
        else:
            print(f">>> 訂閱失敗: {self.quoteCom.GetSubQuoteMsg(res)}")
            return False
    
    def unsubscribe_quote(self, symbol_id):
        """取消訂閱商品報價"""
        print(f"\n>>> 取消訂閱商品: {symbol_id}")
        self.quoteCom.UnsubQuotes(symbol_id)
        sleep(1)
    
    def query_last_price(self, symbol_id):
        """查詢商品最後價格"""
        res = self.quoteCom.RetriveLastPrice(symbol_id)
        if res == 0:
            sleep(0.5)
        else:
            print(f">>> 查詢失敗: {self.quoteCom.GetSubQuoteMsg(res)}")
    
    def start_recording(self, symbol_id):
        """開始記錄歷史資料"""
        print(f"\n{'=' * 70}")
        print(f"開始記錄歷史資料")
        print(f"{'=' * 70}")
        print(f"商品代碼: {symbol_id}")
        print(f"K 線週期: {', '.join([str(tf) + '分' for tf in self.timeframes])}")
        print(f"查詢間隔: {self.query_interval} 秒")
        for tf in self.timeframes:
            print(f"{tf}分K 線檔案: {self.candle_filenames[tf]}")
        if self.record_tick:
            print(f"Tick 檔案: {self.tick_filename}")
        print(f"{'=' * 70}")
        print(">>> 按 Ctrl+C 停止記錄並匯出資料")
        print(f"{'=' * 70}\n")
        
        try:
            while self.keep_running:
                current_time = time()
                
                # 檢查是否到達查詢間隔
                if current_time - self.last_query_time >= self.query_interval:
                    # 查詢最後價格
                    self.query_last_price(symbol_id)
                    self.last_query_time = current_time
                
                # 每 60 秒批次儲存 tick 資料
                if self.record_tick and current_time - self.last_save_time >= 60:
                    self._save_tick_batch()
                    self.last_save_time = current_time
                
                # 每 5 分鐘顯示統計資訊
                if self.start_time and (datetime.now() - self.start_time).seconds % 300 < self.query_interval:
                    self._print_statistics()
                
                # 短暫休息避免 CPU 過度使用
                sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n\n>>> 使用者中斷記錄")
            self.keep_running = False
    
    def _print_statistics(self):
        """顯示統計資訊"""
        if not self.start_time:
            return
        
        duration = datetime.now() - self.start_time
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        print(f"\n{'=' * 70}")
        print(f"統計資訊")
        print(f"{'=' * 70}")
        print(f"記錄時間: {hours} 小時 {minutes} 分鐘")
        print(f"Tick 數量: {self.tick_count:,}")
        for tf in self.timeframes:
            print(f"{tf}分K 線數量: {self.candle_counts[tf]}")
            print(f"{tf}分K 線檔案: {self.candle_filenames[tf]}")
        if self.record_tick:
            print(f"Tick 檔案: {self.tick_filename}")
        print(f"{'=' * 70}\n")
    
    def export_summary(self):
        """匯出摘要資訊"""
        print(f"\n{'=' * 70}")
        print("匯出資料摘要")
        print(f"{'=' * 70}")
        
        summary = {
            'stock_code': self.stock_code,
            'timeframes': self.timeframes,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else None,
            'end_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tick_count': self.tick_count,
            'candle_counts': self.candle_counts,
            'candle_files': self.candle_filenames,
            'tick_file': self.tick_filename if self.record_tick else None
        }
        
        # 儲存摘要檔案
        summary_filename = os.path.join(
            self.data_dir, 
            f"{self.stock_code}_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        try:
            with open(summary_filename, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=4, ensure_ascii=False)
            
            print(f"商品代碼: {summary['stock_code']}")
            print(f"K 線週期: {', '.join([str(tf) + '分' for tf in summary['timeframes']])}")
            print(f"記錄期間: {summary['start_time']} ~ {summary['end_time']}")
            print(f"Tick 數量: {summary['tick_count']:,}")
            for tf in self.timeframes:
                print(f"{tf}分K 線數量: {summary['candle_counts'][tf]}")
            print(f"\n>>> 摘要檔案: {summary_filename}")
            for tf in self.timeframes:
                print(f">>> {tf}分K 線檔案: {summary['candle_files'][tf]}")
            if summary['tick_file']:
                print(f">>> Tick 檔案: {summary['tick_file']}")
            print(f"{'=' * 70}\n")
            
        except Exception as e:
            print(f">>> 匯出摘要時發生錯誤: {e}")
    
    def logout(self):
        """登出系統"""
        print("\n>>> 登出系統...")
        self.quoteCom.Logout()
        sleep(1)
    
    def dispose(self):
        """釋放資源"""
        print(">>> 釋放資源...")
        self.keep_running = False
        
        # 儲存剩餘的 tick 資料
        if self.record_tick and len(self.tick_data) > 0:
            self._save_tick_batch()
        
        self.quoteCom.Dispose()


def main():
    """主程式"""
    print("\n啟動歷史資料記錄程式...\n")
    
    # 建立記錄器（可自訂 K 線週期和儲存目錄）
    recorder = HistoryDataRecorder(
        timeframes=[3, 5],  # 同時記錄 3 分 K 和 5 分 K
        data_dir="historical_data"
    )
    
    try:
        # 1. 登入
        if not recorder.login():
            print("登入失敗，程式結束")
            return
        
        # 2. 下載商品資料
        if not recorder.download_product_list():
            print("下載商品資料失敗，程式結束")
            return
        
        # 3. 訂閱商品報價
        symbol = recorder.stock_code
        if recorder.subscribe_quote(symbol):
            # 4. 開始記錄歷史資料
            recorder.start_recording(symbol)
            
            # 5. 取消訂閱
            recorder.unsubscribe_quote(symbol)
        
    except Exception as e:
        print(f"\n發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 匯出摘要
        recorder.export_summary()
        
        # 清理資源
        recorder.logout()
        recorder.dispose()
        print("\n程式結束")


if __name__ == '__main__':
    main()
