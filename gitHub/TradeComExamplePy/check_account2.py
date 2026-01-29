#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改良版帳號查詢工具
使用與登入測試相同的方式查詢帳號資訊
"""

import clr
from System import UInt16
from TradeComFutPySample import TradecomPyFut
from time import sleep
import money_config as config

print("=" * 70)
print("凱基期貨帳號查詢工具 v2")
print("=" * 70)

# 儲存查詢結果
account_info = {}
login_success = False

def on_callback(data):
    """處理 API 回調"""
    global account_info, login_success
    dt = data.get('DT', '')
    
    print(f"\n[回調] 收到訊息類型: {dt}")
    
    # 登入回應
    if dt == 'P001503':
        code = data.get('Code', -1)
        if code == 0:
            print(f"\n✓ 登入成功！")
            print(f"  帳號: {data.get('ID')}")
            print(f"  姓名: {data.get('Name')}")
            login_success = True
            
            # 提取所有帳號資訊
            count = data.get('Count', 0)
            print(f"  子帳號數量: {count}")
            
            # 儲存所有資訊
            account_info['login_id'] = data.get('ID')
            account_info['name'] = data.get('Name')
            account_info['count'] = count
            account_info['accounts'] = []
            
            # 提取每個子帳號資訊
            for i in range(1, count + 1):
                acc = {
                    'index': i,
                    'broker': data.get(f'BROKER{i}', ''),
                    'account': data.get(f'ACC{i}', ''),
                    'accfl': data.get(f'ACCFL{i}', ''),
                    'ib': data.get(f'IB{i}', ''),
                }
                account_info['accounts'].append(acc)
                
                print(f"\n  子帳號 {i}:")
                print(f"    分公司代碼: {acc['broker']}")
                print(f"    帳號: {acc['account']}")
                print(f"    類型: {acc['accfl']}")
                print(f"    IB: {acc['ib'] if acc['ib'] else '(無)'}")
            
            # 顯示完整的原始資料（用於除錯）
            print(f"\n[完整回調資料]")
            for key, value in data.items():
                print(f"  {key}: {value}")
                
        else:
            print(f"\n✗ 登入失敗")
            print(f"  錯誤代碼: {code}")
            print(f"  錯誤訊息: {data.get('MSG')}")
    
    elif dt == 'STATUS':
        status = data.get('status', '')
        msg = data.get('msg', '')
        print(f"  [狀態] {status}: {msg}")
    
    else:
        print(f"  其他訊息: {data}")

try:
    print("\n>>> 當前設定:")
    print(f"  HOST: {config.HOST}")
    print(f"  PORT: {config.PORT}")
    print(f"  登入帳號: {config.LOGIN_ACCOUNT}")
    print(f"  設定檔中的 BROKER_ID: {config.BROKER_ID}")
    print(f"  設定檔中的 ACCOUNT: {config.ACCOUNT}")
    print(f"  設定檔中的 TRADER: {config.TRADER if config.TRADER else '(無)'}")
    
    print("\n>>> 正在連線...")
    trader = TradecomPyFut(
        config.HOST,
        UInt16(config.PORT),
        config.SID,
        timeout=10000,
        callback=on_callback
    )
    trader.debug = True
    
    print(">>> 正在登入...")
    trader.doLogin(config.LOGIN_ACCOUNT, config.PASSWORD)
    
    # 等待登入結果
    print(">>> 等待登入回應（最多 10 秒）...")
    for i in range(10):
        sleep(1)
        print(f"  等待中... {i+1}/10 秒")
        if login_success:
            break
    
    if not login_success:
        print("\n✗ 登入失敗，無法查詢帳號")
        trader.dispose()
        exit(1)
    
    # 顯示分析結果
    print("\n" + "=" * 70)
    print("帳號分析結果")
    print("=" * 70)
    
    if account_info.get('accounts'):
        print(f"\n找到 {len(account_info['accounts'])} 個帳號\n")
        
        for acc in account_info['accounts']:
            print(f"【帳號 {acc['index']}】")
            print(f"  分公司代碼: {acc['broker']}")
            print(f"  帳號: {acc['account']}")
            print(f"  IB/子帳號: {acc['ib'] if acc['ib'] else '(無)'}")
            
            print(f"\n  ✅ 建議的 money_config.py 設定:")
            print(f"  BROKER_ID = \"{acc['broker']}\"")
            print(f"  ACCOUNT = \"{acc['account']}\"")
            if acc['ib']:
                print(f"  TRADER = \"{acc['ib']}\"")
            else:
                print(f"  TRADER = ''")
            print()
        
        # 重點建議
        print("=" * 70)
        print("🎯 推薦設定（使用第一個帳號）")
        print("=" * 70)
        first_acc = account_info['accounts'][0]
        print(f"\n請將以下內容複製到 money_config.py：\n")
        print(f"BROKER_ID = \"{first_acc['broker']}\"")
        print(f"ACCOUNT = \"{first_acc['account']}\"")
        if first_acc['ib']:
            print(f"TRADER = \"{first_acc['ib']}\"")
        else:
            print(f"TRADER = ''")
        print("\n" + "=" * 70)
        
        # 下單測試格式
        print("\n📝 下單時使用的帳號格式:")
        print("-" * 70)
        if first_acc['ib']:
            print(f"  帳號: {first_acc['account']}")
            print(f"  子帳號: {first_acc['ib']}")
            print(f"  ⚠️ 注意: API 可能需要純帳號，不需要組合")
        else:
            print(f"  帳號: {first_acc['account']}")
        print("=" * 70)
        
    else:
        print("\n⚠️ 未從登入回應中找到帳號資訊")
        print("\n登入資訊:")
        print(f"  登入 ID: {account_info.get('login_id', 'N/A')}")
        print(f"  姓名: {account_info.get('name', 'N/A')}")
        print(f"  子帳號數量: {account_info.get('count', 0)}")
        
        print("\n建議:")
        print("1. 檢查回調資料中的 BROKER1, ACC1, IB1 等欄位")
        print("2. 聯絡營業員確認正確的帳號設定")
        print("3. 確認期貨帳戶已開通")
    
    # 登出
    print("\n>>> 正在登出...")
    trader.logout()
    sleep(1)
    trader.dispose()
    
    print("\n✓ 查詢完成！")
    
except Exception as e:
    print(f"\n✗ 發生錯誤: {e}")
    import traceback
    traceback.print_exc()

print("\n按 Enter 結束...")
input()
