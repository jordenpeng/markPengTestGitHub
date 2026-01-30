#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期貨下單程式
提供簡易的期貨交易介面，包含下單、查詢、風險控制等功能
"""

import clr
import sys
from datetime import datetime
from time import sleep
from System import UInt16

# 匯入設定檔
import money_config as config

# 匯入交易API
from TradeComFutPySample import TradecomPyFut


class FuturesTrader:
    """期貨交易系統主類別"""
    
    def __init__(self, logger=None):
        """初始化交易系統
        
        Args:
            logger: TradeLogger實例，用於記錄交易日誌
        """
        self.trader = None
        self.is_logged_in = False
        self.daily_order_count = 0
        self.order_history = []
        self.logger = logger
        
        # 追蹤當前委託：用 RequestId 追蹤
        self.pending_orders = {}  # {RequestId: {'side': 'B'/'S', 'position_effect': 'O'/'C', 'qty': int}}
        self.order_no_map = {}  # {OrderNo: RequestId} 用於成交回報時查找
        self.request_id_counter = 0
        
        print("=" * 60)
        print("期貨交易系統啟動中...")
        print("=" * 60)
        
        # 初始化交易API
        self.trader = TradecomPyFut(
            config.HOST,
            UInt16(config.PORT),
            config.SID,
            timeout=5000,
            callback=self.on_callback
        )
        self.trader.debug = config.DEBUG_MODE
        
    def on_callback(self, data):
        """處理API回調資料"""
        dt = data.get('DT', '')
        
        # 登入回應
        if dt == 'P001503':
            if data.get('Code') == 0:
                print(f"\n✓ 登入成功！")
                print(f"  帳號: {data.get('ID')}")
                print(f"  姓名: {data.get('Name')}")
                self.is_logged_in = True
            else:
                print(f"\n✗ 登入失敗: {data.get('MSG')}")
                self.is_logged_in = False
        
        # 下單回應
        elif dt == 'PT02002':
            request_id = data.get('RequestId')
            order_no = data.get('OrderNo')
            
            print(f"\n下單回應:")
            print(f"  RequestId: {request_id}")
            print(f"  委託書號: {order_no}")
            if data.get('ErrorCode') == 0:
                print(f"  狀態: ✓ 下單成功")
                # 建立 OrderNo 到 RequestId 的映射
                if request_id and order_no:
                    self.order_no_map[order_no] = request_id
            else:
                print(f"  狀態: ✗ 下單失敗 - {data.get('ErrorMsg')}")
        
        # 委託回報
        elif dt == 'PT02010' and config.SHOW_ORDER_REPORT:
            print(f"\n委託回報:")
            print(f"  委託書號: {data.get('OrderNo')}")
            print(f"  商品代碼: {data.get('Symbol')}")
            print(f"  買賣別: {'買進' if data.get('Side') == 'B' else '賣出'}")
            print(f"  委託價: {data.get('Price')}")
            print(f"  委託量: {data.get('AfterQty')}")
            print(f"  回報時間: {data.get('ReportTime')}")
        
        # 成交回報
        elif dt == 'PT02011' and config.SHOW_DEAL_REPORT:
            order_no = data.get('OrderNo')
            deal_price = data.get('DealPrice')
            deal_qty = data.get('DealQty')
            side = data.get('Side')
            
            print(f"\n成交回報:")
            print(f"  委託書號: {order_no}")
            print(f"  商品代碼: {data.get('Symbol')}")
            print(f"  買賣別: {'買進' if side == 'B' else '賣出'}")
            print(f"  成交價: {deal_price}")
            print(f"  成交量: {deal_qty}")
            print(f"  累計成交: {data.get('CumQty')}")
            print(f"  回報時間: {data.get('ReportTime')}")
            
            # 記錄到交易日誌
            if self.logger and order_no in self.order_no_map:
                request_id = self.order_no_map[order_no]
                if request_id in self.pending_orders:
                    order_info = self.pending_orders[request_id]
                    position_effect = order_info.get('position_effect')
                    
                    # 開倉記錄
                    if position_effect in ['O', 'A']:  # 新倉或自動
                        if side == 'B':
                            self.logger.open_long(deal_price, deal_qty)
                        elif side == 'S':
                            self.logger.open_short(deal_price, deal_qty)
                    
                    # 平倉記錄
                    elif position_effect == 'C':
                        if self.logger.current_position:
                            self.logger.close_position(deal_price, deal_qty)
                    
                    # 移除已處理的委託
                    del self.pending_orders[request_id]
                    del self.order_no_map[order_no]
        
        # 權益數查詢
        elif dt == 'P001626':
            count = data.get('Count', 0)
            if config.DEBUG_MODE:
                print(f"\n[DEBUG] 權益數回報: Count={count}")
                if count == 0:
                    print(f"[DEBUG] 完整數據: {data}")
            
            if count > 0:
                print(f"\n權益數查詢結果:")
                print(f"  權益總值: {data.get('EQUITY1', 'N/A')}")
                print(f"  原始保證金: {data.get('IAMT1', 'N/A')}")
                print(f"  維持保證金: {data.get('MAMT1', 'N/A')}")
                print(f"  可用餘額: {data.get('EXCESS1', 'N/A')}")
                print(f"  浮動損益: {data.get('FloatProfit1', 'N/A')}")
            else:
                print(f"\n權益數查詢結果: 無資料（可能帳戶未開通或無資金）")
        
        # 部位彙總
        elif dt == 'P001616':
            if data.get('Rows', 0) > 0:
                print(f"\n部位彙總查詢結果:")
                for i in range(1, data.get('Rows', 0) + 1):
                    print(f"  部位 {i}:")
                    print(f"    商品: {data.get(f'ComID{i}', 'N/A')}")
                    print(f"    買賣別: {data.get(f'BS{i}', 'N/A')}")
                    print(f"    數量: {data.get(f'OTQty{i}', 'N/A')}")
                    print(f"    均價: {data.get(f'TrdPrice{i}', 'N/A')}")
                    print(f"    損益: {data.get(f'PRTLOS{i}', 'N/A')}")
            else:
                print(f"\n目前無持倉部位")
        
        # 狀態訊息
        elif dt == 'STATUS':
            if config.DEBUG_MODE:
                print(f"[狀態] {data.get('status')}: {data.get('msg')}")
    
    def login(self):
        """登入交易系統"""
        print(f"\n正在登入...")
        # 使用 LOGIN_ACCOUNT 登入，如果沒有則使用 ACCOUNT
        login_account = getattr(config, 'LOGIN_ACCOUNT', config.ACCOUNT)
        print(f"登入帳號: {login_account}")
        print(f"交易帳號: {config.ACCOUNT}")
        
        # 設定自動訂閱回報
        self.trader.tradecom.AutoSubReport = True
        self.trader.tradecom.AutoRecoverReport = True
        self.trader.tradecom.AutoRetriveProductInfo = True
        
        # 執行登入
        self.trader.doLogin(login_account, config.PASSWORD)
        sleep(3)  # 等待登入完成
        
        if self.is_logged_in and config.AUTO_CHECK_MARGIN:
            self.query_margin()
    
    def logout(self):
        """登出交易系統"""
        print("\n正在登出...")
        self.trader.logout()
        self.trader.dispose()
        print("已登出")
    
    def place_order(self, symbol=None, side='B', price_type=None, price=0, 
                   qty=1, tif=None, position_effect=None):
        """
        下單功能
        
        Args:
            symbol: 商品代碼 (預設使用設定檔)
            side: 'B'=買進, 'S'=賣出
            price_type: 'SP'=限價, 'M'=市價, 'MR'=範圍市價, 'SM'=停損市價, 'SS'=停損限價
            price: 委託價格
            qty: 委託口數
            tif: 'R'=ROD, 'I'=IOC, 'F'=FOK
            position_effect: 'O'=新倉, 'C'=平倉, 'D'=當沖, 'A'=自動
        """
        if not self.is_logged_in:
            print("✗ 請先登入")
            return False
        
        # 正式環境警告
        if hasattr(config, 'SHOW_PRODUCTION_WARNING') and config.SHOW_PRODUCTION_WARNING:
            print("\n" + "="*60)
            print("⚠️⚠️⚠️  正式環境警告  ⚠️⚠️⚠️")
            print("此為正式環境，下單會實際成交並產生費用！")
            print("="*60)
        
        # 使用預設值
        if symbol is None:
            # 生成完整商品代碼
            symbol = self.trader.futSymbol(config.DEFAULT_SYMBOL, config.DEFAULT_MONTH)
        if price_type is None:
            price_type = config.DEFAULT_PRICE_TYPE
        if tif is None:
            tif = config.DEFAULT_TIME_IN_FORCE
        if position_effect is None:
            position_effect = config.DEFAULT_POSITION_EFFECT
        
        # ⚠️ 重要：市價單和範圍市價單不允許 ROD，必須使用 IOC 或 FOK
        if price_type in ['M', 'MR'] and tif == 'R':
            tif = 'I'  # 市價單自動改為 IOC
            if config.DEBUG_MODE:
                print(f"[提示] {price_type}單不允許 ROD，已自動改為 IOC")
        
        # 風險檢查
        if qty > config.MAX_ORDER_QTY:
            print(f"✗ 委託口數 {qty} 超過單筆最大限制 {config.MAX_ORDER_QTY}")
            return False
        
        if self.daily_order_count + qty > config.MAX_DAILY_QTY:
            print(f"✗ 今日累計口數將超過限制 {config.MAX_DAILY_QTY}")
            return False
        
        # 顯示下單資訊
        price_type_text = {
            'SP': '限價',
            'M': '市價',
            'MR': '範圍市價',
            'SM': '停損市價',
            'SS': '停損限價'
        }.get(price_type, price_type)
        
        print(f"\n準備下單:")
        print(f"  商品代碼: {symbol}")
        print(f"  買賣別: {'買進' if side == 'B' else '賣出'}")
        print(f"  價格類型: {price_type_text}")
        print(f"  委託價格: {price if price_type == 'SP' else price_type_text}")
        print(f"  委託口數: {qty}")
        print(f"  有效期限: {'ROD' if tif == 'R' else ('IOC' if tif == 'I' else 'FOK')}")
        print(f"  倉位類型: {position_effect}")
        
        # 檢查是否需要確認（從設定檔讀取）
        require_confirm = getattr(config, 'REQUIRE_CONFIRMATION', False)
        if require_confirm:
            confirm = input("\n確認下單? (y/n): ")
            if confirm.lower() != 'y':
                print("✗ 已取消下單")
                return False
        else:
            print("\n>> 自動送出下單...")
        
        # 生成 RequestId
        self.request_id_counter += 1
        request_id = f"REQ{self.request_id_counter:06d}"
        
        # 記錄待處理委託
        self.pending_orders[request_id] = {
            'side': side,
            'position_effect': position_effect,
            'qty': qty
        }
        
        # 執行下單
        # 根據 TradeStart.py 範例：ORDER,O,F,F004000,9804474,TXFF3,B,SP,16500,F,1,A,AS
        # 參數順序（12個）：type, market, brokerId, account, symbolId, bs, pricefl, price, tif, qty, pf, off
        # 使用位置參數，不支援 trader 關鍵字參數
        
        result = self.trader.order(
            'O',        # 1. type: O=新單, C=取消, M=修改
            'F',        # 2. market: F=期貨
            config.BROKER_ID,   # 3. brokerId: 分公司代碼
            config.ACCOUNT,     # 4. account: 帳號
            symbol,     # 5. symbolId: 商品代碼
            side,       # 6. bs: B=買, S=賣
            price_type, # 7. pricefl: SP=限價, MR=範圍市價
            price,      # 8. price: 價格
            tif,        # 9. tif: R=ROD, I=IOC, F=FOK
            qty,        # 10. qty: 數量
            position_effect,  # 11. pf: O=新倉, C=平倉, D=當沖, A=自動
            config.DEFAULT_OFFICE_FLAG  # 12. off: SP=SPEEDY, AS=AS400
        )
        
        if result:
            self.daily_order_count += qty
            self.order_history.append({
                'time': datetime.now(),
                'symbol': symbol,
                'side': side,
                'qty': qty,
                'price': price,
                'request_id': request_id
            })
            print(f"\n✓ 下單請求已送出 (RequestId: {request_id})")
        else:
            # 下單失敗，移除記錄
            if request_id in self.pending_orders:
                del self.pending_orders[request_id]
        
        return result
    
    def close_position(self, side='B', price_type='MR', price=0, qty=1, symbol=None):
        """
        平倉功能
        
        Args:
            side: 'B'=買進平倉(平空單), 'S'=賣出平倉(平多單)
            price_type: 'SP'=限價, 'M'=市價, 'MR'=範圍市價
            price: 委託價格 (市價時可為0)
            qty: 平倉口數
            symbol: 商品代碼 (預設使用設定檔)
        
        Returns:
            bool: 平倉成功與否
        """
        if not self.is_logged_in:
            print("✗ 請先登入")
            return False
        
        # 正式環境警告
        if hasattr(config, 'SHOW_PRODUCTION_WARNING') and config.SHOW_PRODUCTION_WARNING:
            print("\n" + "="*60)
            print("⚠️⚠️⚠️  正式環境警告  ⚠️⚠️⚠️")
            print("此為正式環境，平倉會實際成交並產生費用！")
            print("="*60)
        
        # 使用預設值
        if symbol is None:
            symbol = self.trader.futSymbol(config.DEFAULT_SYMBOL, config.DEFAULT_MONTH)
        
        # 確定委託價格類型和有效期限
        tif = config.DEFAULT_TIME_IN_FORCE
        
        # ⚠️ 重要：市價單和範圍市價單不允許 ROD，必須使用 IOC 或 FOK
        if price_type in ['M', 'MR'] and tif == 'R':
            tif = 'I'  # 市價單自動改為 IOC
            if config.DEBUG_MODE:
                print(f"[提示] {price_type}單不允許 ROD，已自動改為 IOC")
        
        # 風險檢查
        if qty > config.MAX_ORDER_QTY:
            print(f"✗ 平倉口數 {qty} 超過單筆最大限制 {config.MAX_ORDER_QTY}")
            return False
        
        if self.daily_order_count + qty > config.MAX_DAILY_QTY:
            print(f"✗ 今日累計口數將超過限制 {config.MAX_DAILY_QTY}")
            return False
        
        # 顯示平倉資訊
        price_type_text = {
            'SP': '限價',
            'M': '市價',
            'MR': '範圍市價',
            'SM': '停損市價',
            'SS': '停損限價'
        }.get(price_type, price_type)
        
        print(f"\n準備平倉:")
        print(f"  商品代碼: {symbol}")
        print(f"  買賣別: {'買進平倉(平空單)' if side == 'B' else '賣出平倉(平多單)'}")
        print(f"  價格類型: {price_type_text}")
        print(f"  委託價格: {price if price_type == 'SP' else price_type_text}")
        print(f"  平倉口數: {qty}")
        print(f"  有效期限: {'ROD' if tif == 'R' else ('IOC' if tif == 'I' else 'FOK')}")
        print(f"  倉位類型: C (平倉)")
        
        # 檢查是否需要確認
        require_confirm = getattr(config, 'REQUIRE_CONFIRMATION', False)
        if require_confirm:
            confirm = input("\n確認平倉? (y/n): ")
            if confirm.lower() != 'y':
                print("✗ 已取消平倉")
                return False
        else:
            print("\n>> 自動送出平倉...")
        
        # 生成 RequestId
        self.request_id_counter += 1
        request_id = f"REQ{self.request_id_counter:06d}"
        
        # 記錄待處理委託
        self.pending_orders[request_id] = {
            'side': side,
            'position_effect': 'C',  # 平倉
            'qty': qty
        }
        
        # 執行平倉
        # 根據 TradeStart.py 範例使用位置參數
        result = self.trader.order(
            'O',        # 1. type: O=新單
            'F',        # 2. market: F=期貨
            config.BROKER_ID,   # 3. brokerId
            config.ACCOUNT,     # 4. account
            symbol,     # 5. symbolId
            side,       # 6. bs
            price_type, # 7. pricefl
            price,      # 8. price
            tif,        # 9. tif
            qty,        # 10. qty
            'C',        # 11. pf: C=平倉
            config.DEFAULT_OFFICE_FLAG  # 12. off
        )
        
        if result:
            self.daily_order_count += qty
            self.order_history.append({
                'time': datetime.now(),
                'symbol': symbol,
                'side': side,
                'qty': qty,
                'price': price,
                'type': '平倉',
                'request_id': request_id
            })
            print(f"\n✓ 平倉請求已送出 (RequestId: {request_id})")
        else:
            # 下單失敗，移除記錄
            if request_id in self.pending_orders:
                del self.pending_orders[request_id]
        
        return result
    
    def cancel_order(self, webid, cnt, orderno, symbol=None):
        """
        刪單功能
        
        Args:
            webid: 主機別
            cnt: 電子單號
            orderno: 委託書號
            symbol: 商品代碼
        """
        if not self.is_logged_in:
            print("✗ 請先登入")
            return False
        
        if symbol is None:
            symbol = self.trader.futSymbol(config.DEFAULT_SYMBOL, config.DEFAULT_MONTH)
        
        print(f"\n準備刪單:")
        print(f"  委託書號: {orderno}")
        
        trader = getattr(config, 'TRADER', '')
        result = self.trader.order(
            type='C',  # 刪單
            market='F',
            brokerId=config.BROKER_ID,
            account=config.ACCOUNT,
            symbolId=symbol,
            bs='B',  # 刪單時可以任意
            pricefl='SP',
            price=0,
            tif='R',
            qty=1,
            pf='A',
            off=config.DEFAULT_OFFICE_FLAG,
            trader=trader,
            webid=webid,
            cnt=cnt,
            orderno=orderno
        )
        
        return result
    
    def query_position(self):
        """查詢部位彙總"""
        if not self.is_logged_in:
            print("✗ 請先登入")
            return
        
        print("\n查詢部位彙總...")
        trader = getattr(config, 'TRADER', '')
        result = self.trader.posSum('I', config.BROKER_ID, config.ACCOUNT, trader)
        if result == 0:
            sleep(1)  # 等待回應
        else:
            print(f"✗ 查詢失敗 (錯誤碼: {result})")
            if result == -1:
                print("  可能原因: 非合法帳號/Trader")
    
    def query_position_detail(self):
        """查詢部位明細"""
        if not self.is_logged_in:
            print("✗ 請先登入")
            return
        
        print("\n查詢部位明細...")
        trader = getattr(config, 'TRADER', '')
        result = self.trader.posDetail('I', config.BROKER_ID, config.ACCOUNT, trader)
        if result == 0:
            sleep(1)
        else:
            print(f"✗ 查詢失敗 (錯誤碼: {result})")
            if result == -1:
                print("  可能原因: 非合法帳號/Trader")
    
    def query_margin(self):
        """查詢權益數"""
        if not self.is_logged_in:
            print("✗ 請先登入")
            return
        
        print("\n查詢權益數...")
        trader = getattr(config, 'TRADER', '')
        result = self.trader.fMargin('I', config.BROKER_ID, config.ACCOUNT, trader)
        if result == 0:
            sleep(1)
        else:
            print(f"✗ 查詢失敗 (錯誤碼: {result})")
            if result == -1:
                print("  可能原因: 非合法帳號/Trader")
                print("  建議:")
                print("  1. 檢查 money_config.py 中的 BROKER_ID 是否正確")
                print("  2. 檢查 TRADER 設定（一般帳號應為空字串 ''）")
                print("  3. 執行 check_account.py 確認帳號資訊")
            else:
                print(f"  請參考 TradeCom 說明文件，錯誤碼: {result}")
    
    def query_cover(self):
        """查詢平倉資訊"""
        if not self.is_logged_in:
            print("✗ 請先登入")
            return
        
        print("\n查詢平倉資訊...")
        trader = getattr(config, 'TRADER', '')
        result = self.trader.cover('I', config.BROKER_ID, config.ACCOUNT, trader)
        if result == 0:
            sleep(1)
        else:
            print(f"✗ 查詢失敗 (錯誤碼: {result})")
            if result == -1:
                print("  可能原因: 非合法帳號/Trader")
    
    def query_product_list(self):
        """查詢所有商品列表"""
        print("\n查詢商品列表...")
        try:
            # 取得所有商品列表
            products = self.trader.pbList()
            
            if products and len(products) > 0:
                print(f"\n共有 {len(products)} 個商品類別")
                print("=" * 80)
                
                # 將商品分類顯示
                futures = []  # 期貨
                options = []  # 選擇權
                others = []   # 其他
                
                for i in range(len(products)):
                    prod_str = str(products[i])
                    # 簡單分類
                    if '期貨' in prod_str or 'TXF' in prod_str or 'MTX' in prod_str or 'TMF' in prod_str:
                        futures.append(prod_str)
                    elif '選擇權' in prod_str or 'TXO' in prod_str:
                        options.append(prod_str)
                    else:
                        others.append(prod_str)
                
                # 顯示期貨商品
                if futures:
                    print("\n【期貨商品】")
                    print("-" * 80)
                    for i in range(min(20, len(futures))):
                        print(f"{i+1:2d}. {futures[i]}")
                    if len(futures) > 20:
                        print(f"... 還有 {len(futures) - 20} 個期貨商品")
                
                # 顯示選擇權商品
                if options:
                    print("\n【選擇權商品】")
                    print("-" * 80)
                    for i in range(min(10, len(options))):
                        print(f"{i+1:2d}. {options[i]}")
                    if len(options) > 10:
                        print(f"... 還有 {len(options) - 10} 個選擇權商品")
                
                # 顯示其他商品
                if others:
                    print("\n【其他商品】")
                    print("-" * 80)
                    for i in range(min(10, len(others))):
                        print(f"{i+1:2d}. {others[i]}")
                    if len(others) > 10:
                        print(f"... 還有 {len(others) - 10} 個其他商品")
                
                print("=" * 80)
            else:
                print("✗ 無法取得商品列表")
        except Exception as e:
            print(f"✗ 查詢失敗: {e}")
    
    def query_product_detail(self, symbol=None):
        """查詢特定商品詳細資訊"""
        if symbol is None:
            symbol = input("請輸入商品代碼 (如 TXF, MTX, TMF, TXO): ").strip().upper()
        
        if not symbol:
            print("✗ 商品代碼不能為空")
            return
        
        print(f"\n查詢商品 {symbol} 的詳細資訊...")
        try:
            # 先查詢商品基本資料
            base_info = self.trader.getProductBase(symbol)
            if base_info:
                print("\n" + "=" * 80)
                print(f"【{symbol} 商品基本資料】")
                print("=" * 80)
                print(f"商品代碼: {base_info.ComId}")
                print(f"商品名稱: {base_info.ComCName}")
                print(f"商品類型: {base_info.ComType}")
                print(f"價格小數位數: {base_info.PriceDecimal}")
                print(f"履約價小數位數: {base_info.StkPriceDecimal}")
                print(f"契約類型: {base_info.ContractType}")
                print(f"契約價值: {base_info.ContractValue}")
                print(f"稅率: {base_info.TaxRate}")
                print(f"最小跳動點: {base_info.Tick}")
                print("=" * 80)
            
            # 再查詢商品詳細列表
            detail_list = self.trader.pbListDtl(symbol)
            if detail_list and len(detail_list) > 0:
                print(f"\n【{symbol} 可交易合約列表】（顯示前 20 個）")
                print("=" * 80)
                print(f"{'序號':<4} {'商品代碼':<20} {'到期日':<12} {'漲停價':<10} {'跌停價':<10}")
                print("-" * 80)
                
                max_items = min(20, len(detail_list))
                for i in range(max_items):
                    detail = detail_list[i]
                    print(f"{i+1:<4} {detail.ComId:<20} {detail.EndDate:<12} "
                          f"{float(detail.RisePrice.ToString()):<10.2f} "
                          f"{float(detail.FallPrice.ToString()):<10.2f}")
                
                if len(detail_list) > 20:
                    print(f"\n... 還有 {len(detail_list) - 20} 個合約")
                print("=" * 80)
            else:
                print(f"✗ 無法取得 {symbol} 的詳細資料")
                
        except Exception as e:
            print(f"✗ 查詢失敗: {e}")
            if config.DEBUG_MODE:
                import traceback
                traceback.print_exc()
    
    def query_all_categories(self):
        """查詢所有商品類別"""
        print("\n查詢所有商品類別...")
        try:
            categories = self.trader.proListAll()
            if categories and len(categories) > 0:
                print("\n" + "=" * 80)
                print("【所有商品類別】")
                print("=" * 80)
                for i, cat in enumerate(categories, 1):
                    print(f"{i:2d}. {cat}")
                print("=" * 80)
                print(f"共 {len(categories)} 個類別")
            else:
                print("✗ 無法取得商品類別")
        except Exception as e:
            print(f"✗ 查詢失敗: {e}")
    
    def search_product(self):
        """搜尋商品（互動式）"""
        print("\n" + "=" * 60)
        print("商品搜尋")
        print("=" * 60)
        print("常見商品代碼：")
        print("  TXF  - 台指期貨")
        print("  MTX  - 小型台指期貨") 
        print("  TMF  - 微型台指期貨")
        print("  TXO  - 台指選擇權")
        print("  EXF  - 電子期貨")
        print("  FXF  - 金融期貨")
        print("=" * 60)
        
        keyword = input("請輸入商品代碼或關鍵字: ").strip().upper()
        if not keyword:
            print("✗ 搜尋關鍵字不能為空")
            return
        
        self.query_product_detail(keyword)
    
    def show_product_menu(self):
        """顯示商品查詢子選單"""
        print("\n" + "=" * 60)
        print("商品查詢選單")
        print("=" * 60)
        print("1. 查詢所有商品列表")
        print("2. 查詢特定商品詳情")
        print("3. 查詢所有商品類別")
        print("4. 搜尋商品")
        print("0. 返回主選單")
        print("=" * 60)
    
    def show_menu(self):
        """顯示主選單"""
        print("\n" + "=" * 60)
        print("期貨交易系統選單")
        print("=" * 60)
        print("1. 買進期貨 (市價)")
        print("2. 買進期貨 (限價)")
        print("3. 賣出期貨 (市價)")
        print("4. 賣出期貨 (限價)")
        print("5. 平倉 (市價)")
        print("6. 平倉 (限價)")
        print("7. 查詢部位彙總")
        print("8. 查詢部位明細")
        print("9. 查詢權益數")
        print("A. 查詢平倉資訊")
        print("H. 顯示今日下單紀錄")
        print("P. 商品查詢 (Product Query)")
        print("0. 登出並結束")
        print("=" * 60)
    
    def show_order_history(self):
        """顯示今日下單紀錄"""
        print("\n" + "=" * 60)
        print("今日下單紀錄")
        print("=" * 60)
        if not self.order_history:
            print("今日尚無下單紀錄")
        else:
            for i, order in enumerate(self.order_history, 1):
                order_type = order.get('type', '')
                side_text = '買進' if order['side'] == 'B' else '賣出'
                if order_type == '平倉':
                    side_text += f"({order_type})"
                print(f"{i}. {order['time'].strftime('%H:%M:%S')} | "
                      f"{order['symbol']} | "
                      f"{side_text} | "
                      f"{order['qty']}口 @ {order['price']}")
        print(f"\n今日累計下單口數: {self.daily_order_count}")
        print("=" * 60)
    
    def run(self):
        """運行主程式"""
        try:
            # 顯示正式環境警告（但不需要確認）
            if hasattr(config, 'SHOW_PRODUCTION_WARNING') and config.SHOW_PRODUCTION_WARNING:
                print("\n" + "="*60)
                print("⚠️  正式交易環境")
                print("所有下單操作都會實際成交並產生交易費用！")
                print("="*60)
            
            # 登入
            self.login()
            
            if not self.is_logged_in:
                print("登入失敗，程式結束")
                return
            
            # 主迴圈
            while True:
                self.show_menu()
                choice = input("\n請選擇功能 (0-9, A, H, P): ").strip().upper()
                
                if choice == '1':
                    # 買進期貨 (市價)
                    qty = int(input("請輸入口數: "))
                    self.place_order(side='B', price_type='M', qty=qty)
                
                elif choice == '2':
                    # 買進期貨 (限價)
                    qty = int(input("請輸入口數: "))
                    price = float(input("請輸入價格: "))
                    self.place_order(side='B', price_type='SP', price=price, qty=qty)
                
                elif choice == '3':
                    # 賣出期貨 (市價)
                    qty = int(input("請輸入口數: "))
                    self.place_order(side='S', price_type='M', qty=qty)
                
                elif choice == '4':
                    # 賣出期貨 (限價)
                    qty = int(input("請輸入口數: "))
                    price = float(input("請輸入價格: "))
                    self.place_order(side='S', price_type='SP', price=price, qty=qty)
                
                elif choice == '5':
                    # 平倉 (市價)
                    print("\n選擇平倉方向:")
                    print("B. 買進平倉 (平空單)")
                    print("S. 賣出平倉 (平多單)")
                    side = input("請選擇 (B/S): ").strip().upper()
                    if side not in ['B', 'S']:
                        print("✗ 無效的選項")
                        continue
                    qty = int(input("請輸入平倉口數: "))
                    self.close_position(side=side, price_type='M', qty=qty)
                
                elif choice == '6':
                    # 平倉 (限價)
                    print("\n選擇平倉方向:")
                    print("B. 買進平倉 (平空單)")
                    print("S. 賣出平倉 (平多單)")
                    side = input("請選擇 (B/S): ").strip().upper()
                    if side not in ['B', 'S']:
                        print("✗ 無效的選項")
                        continue
                    qty = int(input("請輸入平倉口數: "))
                    price = float(input("請輸入價格: "))
                    self.close_position(side=side, price_type='SP', price=price, qty=qty)
                
                elif choice == '7':
                    # 查詢部位彙總
                    self.query_position()
                
                elif choice == '8':
                    # 查詢部位明細
                    self.query_position_detail()
                
                elif choice == '9':
                    # 查詢權益數
                    self.query_margin()
                
                elif choice == 'A':
                    # 查詢平倉資訊
                    self.query_cover()
                
                elif choice == 'H':
                    # 顯示今日下單紀錄
                    self.show_order_history()
                
                elif choice == 'P':
                    # 商品查詢子選單
                    while True:
                        self.show_product_menu()
                        prod_choice = input("\n請選擇功能 (0-4): ").strip()
                        
                        if prod_choice == '1':
                            # 查詢所有商品列表
                            self.query_product_list()
                        elif prod_choice == '2':
                            # 查詢特定商品詳情
                            self.query_product_detail()
                        elif prod_choice == '3':
                            # 查詢所有商品類別
                            self.query_all_categories()
                        elif prod_choice == '4':
                            # 搜尋商品
                            self.search_product()
                        elif prod_choice == '0':
                            # 返回主選單
                            break
                        else:
                            print("✗ 無效的選項，請重新選擇")
                        
                        sleep(1)
                
                elif choice == '0':
                    # 登出並結束
                    break
                
                else:
                    print("✗ 無效的選項，請重新選擇")
                
                sleep(1)
        
        except KeyboardInterrupt:
            print("\n\n收到中斷信號...")
        
        except Exception as e:
            print(f"\n發生錯誤: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 清理資源
            if self.is_logged_in:
                self.logout()
            print("\n程式結束")


def main():
    """主程式入口"""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║                   期貨交易系統 v1.0                        ║
    ║                                                            ║
    ║            ⚠️  警告：這是正式環境系統！                    ║
    ║            ⚠️  所有下單都會實際成交！                      ║
    ║            請確保已設定好 money_config.py                 ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    trader = FuturesTrader()
    trader.run()


if __name__ == '__main__':
    main()
