#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
trade_logger.py - 日內交易損益統計模組
負責記錄開倉、平倉，並計算當日累計損益
"""

import os
from datetime import datetime
from pathlib import Path
import json


class TradeLogger:
    """日內交易損益記錄器"""
    
    def __init__(self, log_dir="logs"):
        """
        初始化交易記錄器
        
        Args:
            log_dir: 日誌檔案存放目錄
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 當日累計損益
        self.daily_pnl = 0.0
        self.daily_trades = []
        
        # 當前持倉資訊
        self.current_position = None  # {'side': 'long/short', 'price': float, 'qty': int, 'time': str}
    
    def _get_log_file(self):
        """取得當日日誌檔案路徑"""
        date_str = datetime.now().strftime("%Y%m%d")
        return self.log_dir / f"{date_str}.log"
    
    def _write_log(self, message):
        """寫入日誌"""
        log_file = self._get_log_file()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def open_long(self, price, qty=1):
        """
        記錄做多開倉
        
        Args:
            price: 開倉價格
            qty: 交易數量
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.current_position = {
            'side': 'long',
            'price': price,
            'qty': qty,
            'time': timestamp
        }
        
        message = f"📈 做多開倉 | 價格: {price} | 數量: {qty}口"
        self._write_log(message)
        print(f"\n{message}")
    
    def open_short(self, price, qty=1):
        """
        記錄做空開倉
        
        Args:
            price: 開倉價格
            qty: 交易數量
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.current_position = {
            'side': 'short',
            'price': price,
            'qty': qty,
            'time': timestamp
        }
        
        message = f"📉 做空開倉 | 價格: {price} | 數量: {qty}口"
        self._write_log(message)
        print(f"\n{message}")
    
    def close_position(self, price, qty=None):
        """
        記錄平倉並計算損益
        
        Args:
            price: 平倉價格
            qty: 平倉數量（None表示全平）
            
        Returns:
            dict: {'pnl': float, 'daily_total': float}
        """
        if not self.current_position:
            message = "⚠️ 無持倉可平"
            self._write_log(message)
            print(f"\n{message}")
            return {'pnl': 0.0, 'daily_total': self.daily_pnl}
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 計算平倉數量
        if qty is None:
            qty = self.current_position['qty']
        
        # 計算損益（期貨每點200元）
        entry_price = self.current_position['price']
        if self.current_position['side'] == 'long':
            pnl = (price - entry_price) * 200 * qty
            side_text = "做多"
        else:  # short
            pnl = (entry_price - price) * 200 * qty
            side_text = "做空"
        
        # 更新當日累計損益
        self.daily_pnl += pnl
        
        # 記錄交易
        trade_record = {
            'open_time': self.current_position['time'],
            'close_time': timestamp,
            'side': self.current_position['side'],
            'entry_price': entry_price,
            'exit_price': price,
            'qty': qty,
            'pnl': pnl
        }
        self.daily_trades.append(trade_record)
        
        # 寫入日誌
        message = (f"⏹️ {side_text}平倉 | 開倉: {entry_price} | 平倉: {price} | "
                  f"數量: {qty}口 | 損益: {pnl:+,.0f} 元 | "
                  f"當日累計: {self.daily_pnl:+,.0f} 元")
        self._write_log(message)
        print(f"\n{message}")
        
        # 如果全部平倉，清除持倉資訊
        if qty == self.current_position['qty']:
            self.current_position = None
        else:
            self.current_position['qty'] -= qty
        
        return {
            'pnl': pnl,
            'daily_total': self.daily_pnl
        }
    
    def get_daily_summary(self):
        """
        取得當日交易摘要
        
        Returns:
            dict: 當日交易統計
        """
        total_trades = len(self.daily_trades)
        winning_trades = sum(1 for t in self.daily_trades if t['pnl'] > 0)
        losing_trades = sum(1 for t in self.daily_trades if t['pnl'] < 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        summary = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'total_pnl': self.daily_pnl,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'current_position': self.current_position
        }
        
        # 寫入摘要
        message = (f"\n{'='*60}\n"
                  f"📊 當日交易摘要\n"
                  f"{'='*60}\n"
                  f"日期: {summary['date']}\n"
                  f"總損益: {summary['total_pnl']:+,.0f} 元\n"
                  f"交易次數: {summary['total_trades']} 次\n"
                  f"獲利次數: {summary['winning_trades']} 次\n"
                  f"虧損次數: {summary['losing_trades']} 次\n"
                  f"勝率: {summary['win_rate']:.1f}%\n"
                  f"{'='*60}")
        
        self._write_log(message)
        print(message)
        
        return summary
    
    def reset_daily(self):
        """重置當日統計（跨日時使用）"""
        if self.daily_pnl != 0 or self.daily_trades:
            # 寫入最終摘要
            self.get_daily_summary()
        
        self.daily_pnl = 0.0
        self.daily_trades = []
        self.current_position = None
        
        message = "🔄 日內統計已重置"
        self._write_log(message)
        print(f"\n{message}")
