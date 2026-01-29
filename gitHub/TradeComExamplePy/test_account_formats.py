#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試不同帳號格式的登入
用於找出正確的登入帳號格式
"""

import clr
from System import UInt16
from TradeComFutPySample import TradecomPyFut
from time import sleep
import money_config as config

print("=" * 70)
print("測試不同帳號格式")
print("=" * 70)

# 登入狀態
login_results = []

def on_callback(data):
    """處理 API 回調"""
    dt = data.get('DT', '')
    
    if dt == 'P001503':
        code = data.get('Code', -1)
        result = {
            'success': code == 0,
            'code': code,
            'msg': data.get('MSG', data.get('Msg', 'N/A')),
            'id': data.get('ID', ''),
            'name': data.get('Name', '')
        }
        login_results.append(result)
        
        if code == 0:
            print(f"    ✓ 登入成功！")
            print(f"      帳號: {result['id']}")
            print(f"      姓名: {result['name']}")
        else:
            print(f"    ✗ 登入失敗")
            print(f"      錯誤代碼: {code}")
            print(f"      錯誤訊息: {result['msg']}")
    
    elif dt == 'STATUS':
        status = data.get('status', '')
        msg = data.get('msg', '')
        print(f"    [狀態] {status}: {msg}")

def test_login(account, password):
    """測試登入"""
    global login_results
    login_results = []
    
    print(f"\n>>> 測試帳號: {account}")
    print(f"    密碼長度: {len(password)} 字元")
    
    try:
        trader = TradecomPyFut(
            config.HOST,
            UInt16(config.PORT),
            config.SID,
            timeout=10000,
            callback=on_callback
        )
        
        trader.doLogin(account, password)
        
        # 等待結果
        for i in range(5):
            sleep(1)
            if login_results:
                break
        
        trader.dispose()
        
        if login_results:
            return login_results[0]
        else:
            print(f"    ⚠️ 沒有收到回應")
            return None
            
    except Exception as e:
        print(f"    ✗ 發生錯誤: {e}")
        return None

# 準備測試的帳號格式
print("\n>>> 從設定檔讀取資訊:")
print(f"  LOGIN_ACCOUNT: {config.LOGIN_ACCOUNT}")
print(f"  ACCOUNT: {config.ACCOUNT}")
print(f"  BROKER_ID: {config.BROKER_ID}")
print(f"  TRADER: {config.TRADER if config.TRADER else '(空)'}")
print(f"  HOST: {config.HOST}")
print(f"  PORT: {config.PORT}")

# 測試各種可能的帳號格式
test_accounts = [
    (config.LOGIN_ACCOUNT, "設定檔中的 LOGIN_ACCOUNT"),
    (config.ACCOUNT, "設定檔中的 ACCOUNT"),
]

# 如果有分公司代碼和子帳號，嘗試組合格式
if config.BROKER_ID and config.TRADER:
    test_accounts.append((f"{config.BROKER_ID}{config.ACCOUNT}", "分公司+帳號"))
    test_accounts.append((f"{config.BROKER_ID}-{config.TRADER}", "分公司-子帳號"))
    test_accounts.append((f"{config.ACCOUNT}-{config.TRADER}", "帳號-子帳號"))

print("\n" + "=" * 70)
print("開始測試")
print("=" * 70)

results = []
for account, description in test_accounts:
    result = test_login(account, config.PASSWORD)
    results.append({
        'account': account,
        'description': description,
        'result': result
    })
    sleep(2)  # 避免太頻繁

# 顯示總結
print("\n" + "=" * 70)
print("測試結果總結")
print("=" * 70)

success_found = False
for r in results:
    if r['result'] and r['result']['success']:
        print(f"\n✓✓✓ 找到可用的帳號格式！")
        print(f"  帳號: {r['account']}")
        print(f"  說明: {r['description']}")
        print(f"  姓名: {r['result']['name']}")
        success_found = True
        
        print(f"\n>>> 請在 money_config.py 中設定:")
        print(f"LOGIN_ACCOUNT = \"{r['account']}\"")
        break

if not success_found:
    print("\n✗ 所有帳號格式都失敗")
    print("\n測試的帳號:")
    for r in results:
        status = "失敗" if not r['result'] or not r['result']['success'] else "成功"
        error = ""
        if r['result'] and not r['result']['success']:
            error = f" (錯誤碼: {r['result']['code']})"
        print(f"  ✗ {r['account']} ({r['description']}): {status}{error}")
    
    print("\n建議:")
    print("1. 聯絡營業員確認正確的 API 登入帳號格式")
    print("2. 確認 API 權限是否真的已開通（不只是簽署協議）")
    print("3. 確認密碼是否正確")
    print("4. 詢問是否需要其他設定步驟")

print("\n測試結束")
