#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_trade_logger.py - 測試交易日誌系統
"""

from trade_logger import TradeLogger
import time


def test_trade_logger():
    """測試交易日誌系統"""
    print("=" * 70)
    print("交易日誌系統測試")
    print("=" * 70)
    
    # 初始化日誌記錄器
    logger = TradeLogger(log_dir="logs")
    
    # 模擬交易場景1: 做多獲利
    print("\n\n場景1: 做多獲利")
    print("-" * 70)
    logger.open_long(price=23000, qty=1)
    time.sleep(1)
    logger.close_position(price=23050, qty=1)
    
    # 模擬交易場景2: 做空獲利
    print("\n\n場景2: 做空獲利")
    print("-" * 70)
    logger.open_short(price=23050, qty=1)
    time.sleep(1)
    logger.close_position(price=23000, qty=1)
    
    # 模擬交易場景3: 做多虧損
    print("\n\n場景3: 做多虧損")
    print("-" * 70)
    logger.open_long(price=23000, qty=1)
    time.sleep(1)
    logger.close_position(price=22950, qty=1)
    
    # 模擬交易場景4: 做空虧損
    print("\n\n場景4: 做空虧損")
    print("-" * 70)
    logger.open_short(price=22950, qty=1)
    time.sleep(1)
    logger.close_position(price=23000, qty=1)
    
    # 顯示當日摘要
    print("\n\n" + "=" * 70)
    summary = logger.get_daily_summary()
    print("=" * 70)
    
    return summary


if __name__ == '__main__':
    test_trade_logger()
