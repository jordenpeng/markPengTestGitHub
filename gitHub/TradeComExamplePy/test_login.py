#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試登入功能
用於除錯登入問題
"""

import clr
from System import UInt16
from TradeComFutPySample import TradecomPyFut
from time import sleep
import money_config as config

print("=" * 70)
print("期貨 API 登入測試")
print("=" * 70)

print("\n>>> 當前設定:")
print(f"  HOST: {config.HOST}")
print(f"  PORT: {config.PORT}")
print(f"  登入帳號: {config.LOGIN_ACCOUNT}")
print(f"  密碼: {'*' * len(config.PASSWORD)} (已隱藏)")
print(f"  交易帳號: {config.ACCOUNT}")
print(f"  分公司代碼: {config.BROKER_ID}")
print(f"  子帳號: {config.TRADER if config.TRADER else '(無)'}")

# 登入狀態
is_logged_in = False

def on_callback(data):
    """處理 API 回調"""
    global is_logged_in
    dt = data.get('DT', '')
    
    print("\n" + "=" * 70)
    print(f"[回調] 收到訊息類型: {dt}")
    print("=" * 70)
    print(f"[回調] 完整資料:")
    for key, value in data.items():
        print(f"  {key}: {value}")
    print("=" * 70)
    
    if dt == 'P001503':
        code = data.get('Code', -1)
        if code == 0:
            print(f"\n✓✓✓ 登入成功！ ✓✓✓")
            print(f"  帳號: {data.get('ID')}")
            print(f"  姓名: {data.get('Name')}")
            is_logged_in = True
        else:
            print(f"\n✗✗✗ 登入失敗！ ✗✗✗")
            print(f"  錯誤代碼: {code}")
            print(f"  錯誤訊息: {data.get('MSG')}")
            print(f"  完整訊息: {data.get('Msg', 'N/A')}")
            is_logged_in = False
    elif dt == 'CONNECT_STATUS':
        status = data.get('Status', '')
        print(f"[連線狀態] {status}")
    else:
        print(f"[其他訊息] 類型={dt}")
        print(f"[其他訊息] 內容={data}")

try:
    print("\n>>> 正在建立連線...")
    trader = TradecomPyFut(
        config.HOST,
        UInt16(config.PORT),
        config.SID,
        timeout=10000,  # 增加 timeout
        callback=on_callback
    )
    trader.debug = True
    
    print(">>> 連線建立成功！")
    
    print("\n>>> 正在嘗試登入...")
    print(f"    使用帳號: {config.LOGIN_ACCOUNT}")
    print(f"    密碼長度: {len(config.PASSWORD)} 字元")
    
    # 執行登入
    print(">>> 呼叫 doLogin()...")
    result = trader.doLogin(config.LOGIN_ACCOUNT, config.PASSWORD)
    print(f">>> doLogin() 回傳值: {result}")
    
    # 等待登入結果
    print(">>> 等待登入回應（最多 10 秒）...")
    for i in range(10):
        sleep(1)
        print(f"    等待中... {i+1}/10 秒")
        if is_logged_in:
            break
    
    if is_logged_in:
        print("\n" + "=" * 70)
        print("✓ 測試結果: 登入成功！")
        print("=" * 70)
        
        # 登出
        print("\n>>> 正在登出...")
        trader.logout()
        sleep(2)
    else:
        print("\n" + "=" * 70)
        print("✗ 測試結果: 登入失敗！")
        print("=" * 70)
        print("\n可能的原因:")
        print("1. 帳號或密碼錯誤")
        print("2. 帳號未開通 API 權限")
        print("3. 帳號已在其他地方登入")
        print("4. 網路連線問題")
        print("5. 非交易時段（某些功能受限）")
        print("\n建議:")
        print("- 檢查 money_config.py 的 LOGIN_ACCOUNT 和 PASSWORD")
        print("- 確認帳號已開通期貨 API 權限")
        print("- 聯絡營業員確認帳號狀態")
    
    # 清理
    trader.dispose()
    
except Exception as e:
    print(f"\n✗ 發生錯誤: {e}")
    import traceback
    traceback.print_exc()
    
print("\n測試結束")
