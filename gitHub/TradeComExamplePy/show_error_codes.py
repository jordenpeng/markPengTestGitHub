#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
凱基 TradeCom API 錯誤代碼查詢工具
"""

# TradeCom API 常見錯誤代碼對照表
ERROR_CODES = {
    # 登入相關錯誤
    '1': '帳號或密碼錯誤',
    '2': '帳號已登入',
    '3': '帳號已被鎖定',
    '4': '密碼錯誤次數過多',
    '5': '帳號不存在',
    '6': '帳號未開通',
    '7': '帳號已過期',
    '8': '非交易時段',
    '9': '系統維護中',
    '10': '連線逾時',
    
    # API 權限相關
    '70': 'API 未簽署或未生效',
    '71': 'API 權限未開通',
    '72': 'API 已過期',
    '73': 'API 被停用',
    '74': 'API 簽署但未完成後續流程',
    '75': 'IP 不在白名單中',
    '76': 'API 憑證無效',
    '77': 'API 版本不符',
    '78': 'API 權限不足或帳號格式錯誤',
    '79': 'API 呼叫頻率超過限制',
    
    # 下單相關錯誤
    '100': '委託失敗',
    '101': '帳號錯誤',
    '102': '商品代碼錯誤',
    '103': '委託價格錯誤',
    '104': '委託數量錯誤',
    '105': '帳戶餘額不足',
    '106': '超過可用額度',
    '107': '商品未開盤',
    '108': '商品已收盤',
    '109': '委託類型錯誤',
    '110': '買賣別錯誤',
    
    # 查詢相關錯誤
    '200': '查詢失敗',
    '201': '查無資料',
    '202': '查詢參數錯誤',
    '203': '查詢權限不足',
    
    # 其他錯誤
    '999': '系統錯誤',
    '1000': '未知錯誤',
}

def get_error_description(error_code):
    """
    取得錯誤代碼說明
    
    Args:
        error_code: 錯誤代碼（字串或數字）
        
    Returns:
        str: 錯誤說明
    """
    code_str = str(error_code)
    return ERROR_CODES.get(code_str, f'未知錯誤代碼: {code_str}')


def display_error_code_table():
    """顯示完整的錯誤代碼對照表"""
    print("=" * 80)
    print("凱基 TradeCom API 錯誤代碼對照表")
    print("=" * 80)
    
    categories = {
        '登入相關錯誤 (1-10)': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
        'API 權限相關 (70-79)': ['70', '71', '72', '73', '74', '75', '76', '77', '78', '79'],
        '下單相關錯誤 (100-110)': ['100', '101', '102', '103', '104', '105', '106', '107', '108', '109', '110'],
        '查詢相關錯誤 (200-203)': ['200', '201', '202', '203'],
        '其他錯誤': ['999', '1000'],
    }
    
    for category, codes in categories.items():
        print(f"\n【{category}】")
        print("-" * 80)
        for code in codes:
            if code in ERROR_CODES:
                print(f"  {code:>4} | {ERROR_CODES[code]}")
    
    print("\n" + "=" * 80)


def analyze_error_78():
    """分析錯誤代碼 78 的可能原因和解決方法"""
    print("\n" + "=" * 80)
    print("錯誤代碼 78 詳細分析")
    print("=" * 80)
    
    print("\n📌 錯誤訊息: 78:Unknow Code:78")
    print("📌 說明: API 權限不足或帳號格式錯誤\n")
    
    print("🔍 可能的原因:")
    print("-" * 80)
    
    reasons = [
        {
            'title': '1. API 協議已簽署但系統權限未開通',
            'probability': '★★★★★ (最可能)',
            'description': '簽署 API 協議後，需要後台人員手動開通權限，通常需要 1-2 個工作天',
            'solution': [
                '✓ 聯絡營業員確認「系統權限是否已開通」',
                '✓ 詢問「預計何時完成開通」',
                '✓ 請營業員檢查「後台權限設定」'
            ]
        },
        {
            'title': '2. 測試環境與正式環境權限分開',
            'probability': '★★★★☆',
            'description': '測試環境和正式環境的 API 權限需要分別申請和開通',
            'solution': [
                '✓ 確認您申請的是哪個環境（測試/正式）',
                '✓ 檢查 money_config.py 設定的環境是否一致',
                '✓ 如果只開通正式環境，請切換到正式環境測試',
                '✓ 注意：正式環境會實際下單！'
            ]
        },
        {
            'title': '3. 帳號格式錯誤',
            'probability': '★★★☆☆',
            'description': '不同券商/期貨商的 API 登入帳號格式不同',
            'solution': [
                '✓ 執行 test_account_formats.py 測試各種格式',
                '✓ 向營業員確認「API 登入時應該使用哪個帳號」',
                '✓ 可能的格式：H124017023 / 0200729 / F004022-022'
            ]
        },
        {
            'title': '4. IP 限制',
            'probability': '★★☆☆☆',
            'description': '某些 API 設定會限制只能從特定 IP 登入',
            'solution': [
                '✓ 詢問營業員是否有 IP 白名單設定',
                '✓ 如果在 AWS，提供 EC2 的固定 IP',
                '✓ 如果在本機，提供您的對外 IP'
            ]
        },
        {
            'title': '5. 子帳號設定問題',
            'probability': '★☆☆☆☆',
            'description': '您的帳號有子帳號 (IB: 022)，可能需要特殊格式',
            'solution': [
                '✓ 詢問營業員子帳號應該如何設定',
                '✓ 測試不同的帳號組合格式'
            ]
        }
    ]
    
    for reason in reasons:
        print(f"\n{reason['title']}")
        print(f"機率: {reason['probability']}")
        print(f"說明: {reason['description']}")
        print(f"\n解決方法:")
        for solution in reason['solution']:
            print(f"  {solution}")
        print()
    
    print("=" * 80)


def show_contact_script():
    """顯示聯絡營業員的對話腳本"""
    print("\n" + "=" * 80)
    print("📞 聯絡營業員的對話範本")
    print("=" * 80)
    
    print("""
您好，我是客戶 H124017023，有關 TradeCom API 使用問題：

1. 我已簽署 API 協議，但登入時出現錯誤代碼 78
   錯誤訊息：78:Unknow Code:78

2. 請幫我確認以下事項：
   ✓ 我的 API 「系統權限」是否已開通？（不只是簽署）
   ✓ 測試環境和正式環境的權限狀態？
   ✓ API 登入時應該使用哪個帳號？
      (H124017023 / 0200729 / 其他格式？)
   ✓ 是否有 IP 限制？

3. 我的帳號資訊：
   - 登入帳號: H124017023
   - 交易帳號: 0200729
   - 分公司: F004022
   - 子帳號: 022
   - 使用 API: TradeCom (期貨)
   - 目前連線環境: [測試環境/正式環境]
   - 連線主機: [itradetest.kgi.com.tw / itrade.kgi.com.tw]

請協助查詢，謝謝！
""")
    
    print("=" * 80)


def show_quick_checks():
    """顯示快速檢查清單"""
    print("\n" + "=" * 80)
    print("✅ 快速檢查清單")
    print("=" * 80)
    
    checks = [
        ("API 協議已簽署", "已完成"),
        ("API 系統權限已開通", "❓ 需確認"),
        ("測試環境權限狀態", "❓ 需確認"),
        ("正式環境權限狀態", "❓ 需確認"),
        ("登入帳號格式正確", "❓ 需測試"),
        ("密碼正確", "✓ 應該正確（一般交易軟體可登入）"),
        ("網路連線正常", "✓ 顯示 CONNECT_READY"),
        ("沒有重複登入", "❓ 需確認"),
        ("是否在交易時段", "❓ 視測試時間"),
        ("IP 是否在白名單", "❓ 需確認"),
    ]
    
    print("\n當前狀態:")
    print("-" * 80)
    for check, status in checks:
        print(f"  {check:<30} : {status}")
    
    print("\n" + "=" * 80)


def main():
    """主程式"""
    import sys
    
    if len(sys.argv) > 1:
        # 如果有提供錯誤代碼參數
        error_code = sys.argv[1]
        print(f"\n錯誤代碼 {error_code}: {get_error_description(error_code)}")
        
        if error_code == '78':
            analyze_error_78()
            show_contact_script()
            show_quick_checks()
    else:
        # 顯示完整資訊
        display_error_code_table()
        analyze_error_78()
        show_contact_script()
        show_quick_checks()
        
        print("\n" + "=" * 80)
        print("💡 使用方法")
        print("=" * 80)
        print("  查詢特定錯誤代碼:")
        print("    python show_error_codes.py 78")
        print("  顯示完整資訊:")
        print("    python show_error_codes.py")
        print("=" * 80)


if __name__ == '__main__':
    main()
