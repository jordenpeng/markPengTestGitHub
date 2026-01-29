#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查詢帳號資訊工具
用於查詢正確的分公司代碼
"""

import clr
from System import UInt16
from time import sleep

# 匯入設定檔
import money_config as config

# 匯入交易API
from TradeComFutPySample import TradecomPyFut


def callback(data):
    """處理回調資料"""
    dt = data.get('DT', '')
    
    if dt == 'P001503':
        print("\n" + "="*60)
        print("登入成功！帳號資訊如下：")
        print("="*60)
        print(f"帳號 ID: {data.get('ID')}")
        print(f"姓名: {data.get('Name')}")
        print(f"登入代碼: {data.get('Code')}")
        
        # 顯示所有子帳號資訊
        count = data.get('Count', 0)
        print(f"\n共有 {count} 個子帳號：")
        print("-"*60)
        
        has_trader = False
        for i in range(1, count + 1):
            broker = data.get(f'BROKER{i}', '')
            account = data.get(f'ACC{i}', '')
            acc_flag = data.get(f'ACCFL{i}', '')
            ib = data.get(f'IB{i}', '')
            
            print(f"\n子帳號 {i}:")
            print(f"  分公司代碼 (BROKER_ID): {broker}")
            print(f"  帳號 (ACCOUNT): {account}")
            print(f"  帳號類型: {acc_flag}")
            print(f"  IB: {ib}")
            
            # 檢查是否有子帳號 (Trader)
            # 通常 IB 欄位如果有值，表示這是子帳號
            if ib and ib.strip():
                print(f"  ⭐ 子帳號代碼 (TRADER): {ib}")
                has_trader = True
            
            if i == 1:
                print(f"\n  ⭐ 建議使用此分公司代碼：{broker}")
                if ib and ib.strip():
                    print(f"  ⭐ 建議使用此子帳號代碼：{ib}")
        
        print("\n" + "="*60)
        print("配置建議：")
        print("="*60)
        print("\n請將以下資訊填入 money_config.py：")
        print(f"  BROKER_ID = \"{data.get('BROKER1', 'F004000')}\"")
        if has_trader and data.get('IB1'):
            print(f"  TRADER = \"{data.get('IB1', '')}\"  # 子帳號")
        else:
            print(f"  TRADER = ''  # 一般帳號無需填寫")
        print("="*60)


def main():
    """主程式"""
    print("\n" + "="*60)
    print("帳號資訊查詢工具")
    print("="*60)
    print(f"正在查詢帳號：{config.ACCOUNT}")
    print("請稍候...\n")
    
    try:
        # 初始化API
        trader = TradecomPyFut(
            config.HOST,
            UInt16(config.PORT),
            config.SID,
            timeout=5000,
            callback=callback
        )
        trader.debug = False
        
        # 設定自動參數
        trader.tradecom.AutoSubReport = True
        trader.tradecom.AutoRecoverReport = False
        trader.tradecom.AutoRetriveProductInfo = False
        
        # 登入
        trader.tradecom.LoginDirect(
            config.HOST, 
            config.PORT, 
            config.ACCOUNT, 
            config.PASSWORD, 
            ' '
        )
        
        # 等待登入完成
        sleep(3)
        
        print("\n查詢完成！")
        print("請按 Enter 結束程式...")
        input()
        
        # 清理
        trader.logout()
        trader.dispose()
        
    except Exception as e:
        print(f"\n發生錯誤：{e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
