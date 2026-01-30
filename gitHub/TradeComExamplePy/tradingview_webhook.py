#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingView Webhook 接收服務
接收 TradingView 發送的交易訊號並執行期貨交易
"""

from flask import Flask, request, jsonify
from datetime import datetime
import threading
import json
import os
from execute import TradeExecutor
from money_config import REQUIRE_CONFIRMATION

app = Flask(__name__)

# 全域執行器實例
executor = None
executor_lock = threading.Lock()

# 簡單的驗證密鑰（建議在環境變數中設置）
WEBHOOK_SECRET = os.getenv("TV_SECRET")

# 安全設定：是否要求密鑰驗證
# True = 必須提供正確的 secret（生產環境建議）
# False = 不驗證密鑰（僅限開發測試）
REQUIRE_SECRET = os.environ.get('REQUIRE_SECRET', 'true').lower() == 'true'


def init_trader():
    """初始化交易執行器（線程安全）"""
    global executor
    with executor_lock:
        if executor is None:
            try:
                executor = TradeExecutor()
                return True
            except Exception as e:
                print(f"✗ 初始化交易執行器失敗: {e}")
                return False
    return True


@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'trader_initialized': executor is not None and executor.trader.is_logged_in
    })


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    TradingView Webhook 端點
    
    預期 JSON 格式:
    {
        "secret": "your-secret-key-here",
        "action": "buy" / "sell" / "close",
        "symbol": "TMF",
        "qty": 1,
        "price": 23000.0  (可選)
    }
    """
    try:
        # 驗證請求
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '無效的 JSON 格式'}), 400
        
        # 驗證密鑰
        if data.get('secret') != WEBHOOK_SECRET:
            print(f"⚠️ 未授權的 webhook 請求")
            return jsonify({'error': '未授權'}), 401
        
        # 解析交易訊號
        action = data.get('action', '').lower()
        qty = data.get('qty', 1)
        price = data.get('price')
        
        # 記錄請求
        print("\n" + "=" * 70)
        print(f"📥 接收到 TradingView 訊號")
        print(f"   時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   動作: {action}")
        print(f"   數量: {qty}")
        if price:
            print(f"   參考價格: {price}")
        print("=" * 70)
        
        # 確保交易執行器已初始化
        if executor is None or not executor.trader.is_logged_in:
            if not init_trader():
                return jsonify({
                    'success': False,
                    'error': '交易執行器未就緒'
                }), 500
        
        # 執行交易指令
        result = execute_trade_signal(action, price, qty)
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        print(f"\n✗ 處理 webhook 時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def execute_trade_signal(action, price=None, qty=1):
    """
    執行交易訊號
    
    Args:
        action: 交易動作 ('buy', 'sell', 'close')
        price: 參考價格（可選）
        qty: 交易數量
        
    Returns:
        dict: 執行結果
    """
    try:
        if action == 'buy' or action == 'long':
            # 執行買入訊號（類似黃金交叉）
            result = executor.execute_golden_cross_signal(price)
            return {
                'success': result['success'],
                'action': 'buy',
                'actions': result['actions'],
                'message': '買入訊號執行完成'
            }
            
        elif action == 'sell' or action == 'short':
            # 執行賣出訊號（類似死亡交叉）
            result = executor.execute_death_cross_signal(price)
            return {
                'success': result['success'],
                'action': 'sell',
                'actions': result['actions'],
                'message': '賣出訊號執行完成'
            }
            
        elif action == 'close' or action == 'exit':
            # 平掉所有倉位
            success = executor.close_all_positions(price)
            return {
                'success': success,
                'action': 'close',
                'message': '平倉訊號執行完成'
            }
            
        else:
            return {
                'success': False,
                'error': f'不支援的交易動作: {action}',
                'message': '支援的動作: buy, sell, close'
            }
            
    except Exception as e:
        print(f"✗ 執行交易訊號時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


@app.route('/long', methods=['POST'])
def long_position():
    """
    做多（買入）接口
    
    可選參數:
    {
        "qty": 1,
        "price": 23000.0,
        "secret": "your-secret-key"
    }
    """
    try:
        # 修正：允許沒有 Content-Type 的請求
        data = request.get_json(silent=True) or {}
        
        # 驗證密鑰（如果有提供）
        if 'secret' in data and data['secret'] != WEBHOOK_SECRET:
            return jsonify({'error': '未授權'}), 401
        
        qty = data.get('qty', 1)
        price = data.get('price')
        
        print("\n" + "=" * 70)
        print(f"📈 接收到做多訊號")
        print(f"   時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   數量: {qty}")
        if price:
            print(f"   參考價格: {price}")
        print("=" * 70)
        
        if executor is None or not executor.trader.is_logged_in:
            if not init_trader():
                return jsonify({
                    'success': False,
                    'error': '交易執行器未就緒'
                }), 500
        
        # 步驟1: 先平掉所有倉位
        # print("\n>>> 步驟1: 先平掉所有倉位...")
        # executor.close_all_positions()
        
        # 步驟2: 執行做多開倉
        print("\n>>> 步驟2: 執行做多開倉...")
        result = executor.execute_golden_cross_signal(price)
        return jsonify({
            'success': result['success'],
            'action': 'long',
            'actions': result['actions'],
            'message': '做多訊號執行完成'
        }), 200 if result['success'] else 500
        
    except Exception as e:
        print(f"\n✗ 執行做多時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/short', methods=['POST'])
def short_position():
    """
    做空（賣出）接口
    
    可選參數:
    {
        "qty": 1,
        "price": 23000.0,
        "secret": "your-secret-key"
    }
    """
    try:
        # 修正：允許沒有 Content-Type 的請求
        data = request.get_json(silent=True) or {}
        
        # 安全驗證：檢查密鑰
        if REQUIRE_SECRET:
            provided_secret = data.get('secret', '')
            if provided_secret != WEBHOOK_SECRET:
                print(f"⚠️ 未授權的請求（密鑰不正確）")
                return jsonify({'error': '未授權：密鑰錯誤或未提供'}), 401
        
        qty = data.get('qty', 1)
        price = data.get('price')
        
        print("\n" + "=" * 70)
        print(f"📉 接收到做空訊號")
        print(f"   時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   數量: {qty}")
        if price:
            print(f"   參考價格: {price}")
        print("=" * 70)
        
        if executor is None or not executor.trader.is_logged_in:
            if not init_trader():
                return jsonify({
                    'success': False,
                    'error': '交易執行器未就緒'
                }), 500
        
        # 步驟1: 先平掉所有倉位
        # print("\n>>> 步驟1: 先平掉所有倉位...")
        # executor.close_all_positions()
        
        # 步驟2: 執行做空開倉
        print("\n>>> 步驟2: 執行做空開倉...")
        result = executor.execute_death_cross_signal(price)
        return jsonify({
            'success': result['success'],
            'action': 'short',
            'actions': result['actions'],
            'message': '做空訊號執行完成'
        }), 200 if result['success'] else 500
        
    except Exception as e:
        print(f"\n✗ 執行做空時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/close', methods=['POST'])
def close_position():
    """
    平倉接口
    
    可選參數:
    {
        "price": 23000.0,
        "secret": "your-secret-key"
    }
    """
    try:
        # 修正：允許沒有 Content-Type 的請求
        data = request.get_json(silent=True) or {}
        
        # 安全驗證：檢查密鑰
        if REQUIRE_SECRET:
            provided_secret = data.get('secret', '')
            if provided_secret != WEBHOOK_SECRET:
                print(f"⚠️ 未授權的請求（密鑰不正確）")
                return jsonify({'error': '未授權：密鑰錯誤或未提供'}), 401
        
        price = data.get('price')
        
        print("\n" + "=" * 70)
        print(f"⏹️ 接收到平倉訊號")
        print(f"   時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if price:
            print(f"   平倉價格: {price}")
        print("=" * 70)
        
        if executor is None or not executor.trader.is_logged_in:
            if not init_trader():
                return jsonify({
                    'success': False,
                    'error': '交易執行器未就緒'
                }), 500
        
        success = executor.close_all_positions(price)
        return jsonify({
            'success': success,
            'action': 'close',
            'message': '平倉訊號執行完成'
        }), 200 if success else 500
        
    except Exception as e:
        print(f"\n✗ 執行平倉時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def run_server(host='0.0.0.0', port=5000, debug=False):
    """
    啟動 Flask 伺服器
    
    Args:
        host: 監聽地址（0.0.0.0 表示接受所有來源）
        port: 監聽埠號
        debug: 是否啟用 debug 模式
    """
    print("\n" + "=" * 70)
    print("🚀 TradingView Webhook 服務啟動中...")
    print("=" * 70)
    
    # 初始化交易執行器
    print("\n>>> 正在初始化交易執行器...")
    if not init_trader():
        print("✗ 無法啟動服務：交易執行器初始化失敗")
        return
    
    print(f"\n✓ 服務已就緒!")
    print(f"  監聽地址: http://{host}:{port}")
    print(f"\n📍 可用端點:")
    print(f"  健康檢查: GET  http://{host}:{port}/health")
    print(f"  倉位查詢: GET  http://{host}:{port}/position")
    print(f"  做多交易: POST http://{host}:{port}/long")
    print(f"  做空交易: POST http://{host}:{port}/short")
    print(f"  平倉操作: POST http://{host}:{port}/close")
    print(f"  通用接口: POST http://{host}:{port}/webhook")
    print(f"\n🔒 安全設定:")
    print(f"  密鑰驗證: {'啟用' if REQUIRE_SECRET else '停用（⚠️ 僅供測試）'}")
    if REQUIRE_SECRET:
        print(f"  Webhook Secret: {WEBHOOK_SECRET}")
        print(f"  ⚠️ 所有請求必須提供正確的 secret 參數")
    else:
        print(f"  ⚠️ 警告：目前不驗證密鑰，任何人都可以下單！")
        print(f"  ⚠️ 生產環境請設定 REQUIRE_SECRET=true")
    print("=" * 70 + "\n")
    
    # 啟動 Flask
    app.run(host=host, port=port, debug=debug, use_reloader=False)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='TradingView Webhook 接收服務')
    parser.add_argument('--host', default='0.0.0.0', help='監聽地址 (預設: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='監聽埠號 (預設: 5000)')
    parser.add_argument('--debug', action='store_true', help='啟用 debug 模式')
    
    args = parser.parse_args()
    
    try:
        run_server(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n\n>>> 正在關閉服務...")
        if executor:
            executor.dispose()
        print(">>> 服務已關閉")
    except Exception as e:
        print(f"\n✗ 服務發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        if executor:
            executor.dispose()
