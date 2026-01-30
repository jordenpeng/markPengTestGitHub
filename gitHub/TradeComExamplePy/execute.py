#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
execute.py - 交易發送執行模組
負責檢查倉位、發送交易指令到 money.py
"""

import sys
import os
from pathlib import Path
from time import sleep
from datetime import datetime

# 導入 money 模組
from money import FuturesTrader
from trade_logger import TradeLogger
import money_config as config


class TradeExecutor:
    """交易發送執行器 - 檢查倉位並發送交易指令"""
    
    def __init__(self):
        """初始化交易發送執行器"""
        print("=" * 70)
        print("交易發送執行器啟動中...")
        print("=" * 70)
        
        # 初始化交易日誌記錄器
        self.logger = TradeLogger(log_dir="logs")
        
        # 建立交易者實例，並傳入logger
        self.trader = FuturesTrader(logger=self.logger)
        
        # 登入交易系統
        print("\n>>> 正在登入交易系統...")
        self.trader.login()
        
        if not self.trader.is_logged_in:
            raise Exception("登入失敗，無法啟動交易發送執行器")
        
        print(">>> 交易發送執行器已就緒！")
        print("=" * 70 + "\n")
        
        # 倉位資訊快取
        self.position_cache = {
            'has_position': False,
            'position_side': None,  # 'B' 或 'S'
            'position_qty': 0,
            'last_check_time': None
        }
    
    def check_position(self):
        """
        檢查當前倉位
        
        Returns:
            dict: {
                'has_position': bool,  # 是否有倉位
                'position_side': str,  # 'B' 買方(多單) 或 'S' 賣方(空單)
                'position_qty': int,   # 倉位數量
            }
        """
        print("\n>>> 檢查倉位中...")
        
        # 查詢部位彙總並取得結果
        position_data = self.trader.query_position()
        
        # 初始化結果
        result = {
            'has_position': False,
            'position_side': None,
            'position_qty': 0
        }
        
        # 解析倉位資訊
        if position_data['has_position'] and len(position_data['positions']) > 0:
            # 取第一個倉位（通常只有一個商品）
            first_position = position_data['positions'][0]
            result['has_position'] = True
            result['position_side'] = first_position['side']  # 'B' 或 'S'
            result['position_qty'] = first_position['qty']
        
        # 更新快取
        self.position_cache = result
        self.position_cache['last_check_time'] = datetime.now()
        
        print(f">>> 倉位檢查結果: {'有倉位' if result['has_position'] else '無倉位'}")
        if result['has_position']:
            side_text = '多單' if result['position_side'] == 'B' else '空單'
            print(f">>> 倉位類型: {side_text}, 數量: {result['position_qty']}口")
        
        return result
    
    def close_all_positions(self, price=None):
        """
        平掉所有倉位
        
        Args:
            price: 平倉價格（可選，不使用）
        
        Returns:
            bool: 是否執行成功
        """
        print("\n>>> 準備平掉所有倉位...")
        
        # 檢查倉位
        position = self.check_position()
        
        if not position['has_position']:
            print(">>> 目前無倉位，無需平倉")
            return True
        
        # 取得倉位詳細資訊
        position_data = self.trader.position_data
        if not position_data['positions']:
            print(">>> 無法取得倉位詳細資訊")
            return False
        
        # 平掉所有倉位（使用 place_order 並設置 position_effect='C'）
        all_success = True
        for pos in position_data['positions']:
            base_symbol = pos['symbol']  # 例如: TMF
            side = pos['side']  # 'B' 或 'S'
            qty = pos['qty']
            
            # 轉換成完整的期貨代碼（例如: TMF → TMFF3）
            full_symbol = self.trader.trader.futSymbol(base_symbol, config.DEFAULT_MONTH)
            
            # 根據倉位方向執行平倉
            # 多單(B) → 賣出(S)平倉
            # 空單(S) → 買進(B)平倉
            close_side = 'S' if side == 'B' else 'B'
            
            print(f">>> 執行平倉 {base_symbol} ({full_symbol}) {'多單' if side == 'B' else '空單'} {qty} 口")
            result = self.trader.place_order(
                symbol=full_symbol,  # ✅ 使用完整代碼
                side=close_side,
                price_type='MR',
                qty=qty,
                position_effect='C'  # ✅ 關鍵：設置為平倉
            )
            
            if not result:
                all_success = False
                print(f">>> ✗ 平倉 {base_symbol} 失敗")
            else:
                print(f">>> ✓ 平倉 {base_symbol} 指令已發送")
        
        return all_success
    
    def execute_golden_cross_signal(self, price=None):
        """
        執行黃金交叉訊號
        1. 先檢查倉位
        2. 若有倉位則先平倉
        3. 執行市價買入1口
        
        Args:
            price: 當前價格（用於記錄）
            
        Returns:
            dict: {
                'success': bool,
                'actions': list,  # 執行的動作列表
                'price': float    # 成交價格
            }
        """
        print("\n" + "=" * 70)
        print("⚡ 接收到黃金交叉訊號！")
        print("=" * 70)
        
        actions = []
        
        # 步驟1: 檢查倉位
        position = self.check_position()
        
        # 步驟2: 若有倉位，先平倉
        if position['has_position']:
            print(f">>> 發現倉位，先執行平倉...")
            close_result = self.close_all_positions()
            if close_result:
                actions.append({
                    'action': '平倉',
                    'side': 'S' if position['position_side'] == 'B' else 'B',
                    'qty': position['position_qty'],
                    'price': price
                })
                sleep(1)  # 等待平倉完成
        
        # 步驟3: 執行範圍市價買入1口
        print(f">>> 執行範圍市價買入 1 口")
        buy_result = self.trader.place_order(
            side='B',
            price_type='MR',
            qty=1
        )
        
        if buy_result:
            actions.append({
                'action': '買入',
                'side': 'B',
                'qty': 1,
                'price': price
            })
            print("✓ 黃金交叉訊號執行成功")
            success = True
        else:
            print("✗ 黃金交叉訊號執行失敗")
            success = False
        
        print("=" * 70)
        
        return {
            'success': success,
            'actions': actions,
            'price': price
        }
    
    def execute_death_cross_signal(self, price=None):
        """
        執行死亡交叉訊號
        1. 先檢查倉位
        2. 若有倉位則先平倉
        3. 執行市價賣出1口
        
        Args:
            price: 當前價格（用於記錄）
            
        Returns:
            dict: {
                'success': bool,
                'actions': list,  # 執行的動作列表
                'price': float    # 成交價格
            }
        """
        print("\n" + "=" * 70)
        print("⚡ 接收到死亡交叉訊號！")
        print("=" * 70)
        
        actions = []
        
        # 步驟1: 檢查倉位
        position = self.check_position()
        
        # 步驟2: 若有倉位，先平倉
        if position['has_position']:
            print(f">>> 發現倉位，先執行平倉...")
            close_result = self.close_all_positions()
            if close_result:
                actions.append({
                    'action': '平倉',
                    'side': 'S' if position['position_side'] == 'B' else 'B',
                    'qty': position['position_qty'],
                    'price': price
                })
                sleep(1)  # 等待平倉完成
        
        # 步驟3: 執行範圍市價賣出1口
        print(f">>> 執行範圍市價賣出 1 口")
        sell_result = self.trader.place_order(
            side='S',
            price_type='MR',
            qty=1
        )
        
        if sell_result:
            actions.append({
                'action': '賣出',
                'side': 'S',
                'qty': 1,
                'price': price
            })
            print("✓ 死亡交叉訊號執行成功")
            success = True
        else:
            print("✗ 死亡交叉訊號執行失敗")
            success = False
        
        print("=" * 70)
        
        return {
            'success': success,
            'actions': actions,
            'price': price
        }
    
    def dispose(self):
        """清理資源"""
        print("\n>>> 正在清理交易發送執行器資源...")
        if self.trader and self.trader.is_logged_in:
            self.trader.logout()
        print(">>> 交易發送執行器已關閉")


# 全域執行器實例
_executor_instance = None


def init_executor():
    """初始化全域執行器實例"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = TradeExecutor()
    return _executor_instance


def get_executor():
    """取得全域執行器實例"""
    global _executor_instance
    if _executor_instance is None:
        raise Exception("交易發送執行器未初始化，請先呼叫 init_executor()")
    return _executor_instance


def on_golden_cross_signal(price=None):
    """
    黃金交叉訊號處理函數
    供 MACD.py 調用
    """
    executor = get_executor()
    return executor.execute_golden_cross_signal(price)


def on_death_cross_signal(price=None):
    """
    死亡交叉訊號處理函數
    供 MACD.py 調用
    """
    executor = get_executor()
    return executor.execute_death_cross_signal(price)


def close_all_positions():
    """
    平掉所有倉位
    供外部調用
    """
    executor = get_executor()
    return executor.close_all_positions()


def cleanup_executor():
    """清理全域執行器"""
    global _executor_instance
    if _executor_instance is not None:
        _executor_instance.dispose()
        _executor_instance = None


if __name__ == '__main__':
    print("\n交易發送執行器測試程式")
    print("=" * 70)
    
    try:
        # 初始化執行器
        executor = TradeExecutor()
        
        print("\n測試選單:")
        print("1. 檢查倉位")
        print("2. 測試黃金交叉訊號")
        print("3. 測試死亡交叉訊號")
        print("4. 平掉所有倉位")
        print("0. 結束測試")
        
        while True:
            choice = input("\n請選擇測試項目 (0-4): ").strip()
            
            if choice == '1':
                executor.check_position()
            elif choice == '2':
                executor.execute_golden_cross_signal(price=23000.0)
            elif choice == '3':
                executor.execute_death_cross_signal(price=23000.0)
            elif choice == '4':
                executor.close_all_positions()
            elif choice == '0':
                break
            else:
                print("✗ 無效的選項")
        
    except Exception as e:
        print(f"\n✗ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理資源
        if 'executor' in locals():
            executor.dispose()
        print("\n測試結束")
