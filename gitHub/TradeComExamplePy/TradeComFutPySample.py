import clr
import sys
import uuid
from datetime import datetime
from System import Decimal
from System import UInt16
from System import Int64

clr.AddReference("Package")      #必要引用dll
clr.AddReference("PushClient")   #必要引用dll
clr.AddReference("TradeCom")     #必要引用dll


from Smart import TaiFexCom
from Intelligence import MARKET_FLAG
from Intelligence import ProListQueryField 
from Intelligence import ORDER_TYPE
from Intelligence import MARKET_FLAG
from Intelligence import SIDE_FLAG
from Intelligence import PRICE_FLAG
from Intelligence import TIME_IN_FORCE
from Intelligence import POSITION_EFFECT
from Intelligence import TIME_IN_FORCE
from Intelligence import OFFICE_FLAG
from Intelligence import Currency_Excode

from time import sleep
"""
TradeCom是凱基提供交易的API元件，使用者可藉由TradeCom達到即時下單及帳務查詢功能等目的。
使用TradeCom元件前需要先安裝Pythonnet，指令如下:
pip install Pythonnet

使用TradeCom元件須引用以下檔案，請檢查檔案是否存在。
1.	TradeCom.dll
2.	PushClient.dll
3.	Package.dll
"""
class TradecomPyFut:
    """KGI期貨國內交易的Python API範例程式。
    """
    def __init__(self, host, port, sid, timeout=5000, callback = lambda dic: print(dic)) -> None:
        """程式初始化

        Args:
            host (str): 主機連線的host
            port (num): 主機連線的port
            sid (str):  主機連線的sid
        """
        self.host = host
        self.port = port
        self.sid = sid
        self.callback = callback
        self.tradecom =  TaiFexCom("", port, sid)
        self.tradecom.ConnectTimeout = timeout
        print("TradeCom API 初始化 Version (%s) ........" % (self.tradecom.version))
        # register event handler
        #狀態通知事件KGI Tradecom API message event
        self.tradecom.OnRcvMessage += self.onTradeRcvMessage
        #資料接收事件KGI Tradecom API status event
        self.tradecom.OnGetStatus += self.onTradeGetStatus
        #資料回補事件KGI Tradecom API Recover event
        self.tradecom.OnRecoverStatus += self.onTradeRecoverStatus
         #資料回補事件KGI Tradecom API Server Time event
        self.tradecom.OnRcvServerTime += self.onTradeRcvServerTime
        self.debug = True

    def reciprocate(self, brokerId, account, month, txside, txqty):
        """大小台互抵

        Args:
            brokerId (_type_): 分公司
            account (_type_):  帳號
            month (_type_):    互抵年月
            txside (_type_):   大台互抵買賣別
            txqty (_type_):    台互抵口數( 0表示全部)

        Returns:
            _type_: 0=送出查詢  -1=非合法帳號/Trader
            OnRcvMessage 回傳P001647
        """
        _txside = self.sideFlag(txside)
        return self.tradecom.SendReciprocateRequest(brokerId, account, month, _txside, int(txqty))

    def rcdHis(self, market, brokerId, account
               , qsdate, qedate, trader= ''):
        """歷史平倉查詢

        Args:
            market (_type_): 市場別。I=國內   O=國外
            brokerId (_type_): 分公司
            account (_type_): 帳號
            qsdate (_type_): 查詢日期-起
            qedate (_type_): 查詢日期-迄 : 目前:日期區間不可超過1個月
            trader (str, optional): 一般帳號登入時帶 ''.
            
        Returns:
            _type_: 0=送出查詢  -1=非合法帳號/Trader
            OnRcvMessage 回傳P001645
        """
        return self.tradecom.RetriveCoverDHistory(market, brokerId, account, trader, '', qsdate, qedate)

    def strikeDetail(self, market, brokerId, account
                    , dtype, qsdate, qedate, exchange= ''
                    , comId= '' , trader= ''):
        """到期履約及無效履約查詢

        Args:
            market (_type_): 市場別。I=國內   O=國外
            brokerId (_type_): 分公司
            account (_type_): 帳號
            dtype (_type_): 查詢類別 1=到期履約  2=無效履約
            qsdate (_type_): 查詢日期-起
            qedate (_type_): 查詢日期-迄 : 目前:日期區間不可超過1個月
            exchange (str, optional): 空白代表全部 ''.
            comId (str, optional): 商品代碼，空白表全部 ''.
            trader (str, optional): 一般帳號登入時帶''.

        Returns:
            _type_: 0=送出查詢  -1=非合法帳號/Trader
            OnRcvMessage 回傳P001643
        """
        return self.tradecom.RetriveStrikeDetail(market, brokerId, account, 
                                                 trader, '', dtype, qsdate, qedate
                                                 , exchange, comId)


    def eCurrency(self, brokerId, account
              , excode, amt):
        """台外幣互轉

        Args:
            brokerId (_type_): 分公司
            account (_type_): 帳號
            excode (_type_): 類別(1: 台轉外/2: 外轉台) 
            amt (_type_): 金額

        Raises:
            TypeError: excode錯誤

        Returns:
            _type_: 0=送出查詢  -1=非合法帳號/Trader
            OnRcvMessage 回傳P001628
        """
        code = Currency_Excode.CE_TONTD
        if excode == '1':
            code = Currency_Excode.CE_TOFOREIGN
        elif excode == '2':
            code = Currency_Excode.CE_TONTD
        else:
            raise TypeError("%s is not an excode" % (excode))
        return self.tradecom.ExchangeCurrency(brokerId, account, code, Decimal(float(amt)))

    def fMargin(self, market, brokerId, account
              , trader= ''):
        """權益數查詢

        Args:
            market (_type_): 市場別。I=國內   O=國外
            brokerId (_type_): 分公司
            account (_type_): 帳號
            trader (str, optional): 一般帳號登入時帶''.

        Returns:
            _type_: 0=送出查詢  -1=非合法帳號/Trader
            OnRcvMessage 回傳P001626 
        """
        return self.tradecom.RetriveFMargin(market, brokerId, account, trader)

    def posDetail(self, market, brokerId, account
              , trader= ''):
        """部位明細(庫存明細) 查詢

        Args:
            market (_type_): 市場別。I=國內   O=國外
            brokerId (_type_): 分公司
            account (_type_): 帳號
            trader (str, optional): 一般帳號登入時帶 ''.

        Returns:
            _type_: 0=送出查詢  -1=非合法帳號/Trader
            OnRcvMessage 回傳P001618
        """
        return self.tradecom.RetrivePositionDetail(market, brokerId, account, trader)
    
    def posSum(self, market, brokerId, account
              , trader= ''):
        """最新部位彙總查詢(庫存彙總)

        Args:
            market (_type_): 市場別。I=國內   O=國外
            brokerId (_type_): 分公司
            account (_type_): 帳號
            trader (str, optional): 一般帳號登入時帶 ''.

        Returns:
            _type_: 0=送出查詢  -1=非合法帳號/Trader
            OnRcvMessage 回傳P001616
        """
        return self.tradecom.RetrivePositionSum(market, brokerId, account, trader)
    
    def coverDetail(self, market, brokerId, account
              , trader= '', comId= '', comYm= '', strikePrice= ''
              , cp= '', exchange= '', requestid= 0, group= ''):
        """平倉明細查詢

        Args:
            market (_type_): 市場別。I=國內   O=國外
            brokerId (_type_): 分公司
            account (_type_): 帳號
            trader (str, optional): 一般帳號登入時帶 ''.
            comId (str, optional): 商品代碼. Defaults to ''.
            comYm (str, optional): 商品年月. Defaults to ''.
            strikePrice (str, optional): 履約價. Defaults to ''.
            cp (str, optional): 買賣權. Defaults to ''.
            exchange (str, optional): 交易所. Defaults to ''.
            requestid (int, optional): 查詢序號，USER可自行帶入，不重複即可. Defaults to 0.
            group (str, optional): 一般帳號登入時帶 ''.

        Returns:
            _type_: 0=送出查詢  -1=非合法帳號/Trader
            OnRcvMessage 回傳P001624
        """
        return self.tradecom.RetriveCOVERDetail(market, brokerId, account
                                          , trader, comId, comYm, strikePrice
                                          , cp, exchange, requestid, group= '')
    
    def cover(self, market, brokerId, account
              , trader= '', comId= '', comYm= '', strikePrice= ''
              , cp= '', exchange= ''):
        """_summary_

        Args:
            market (_type_): 市場別。I=國內   O=國外
            brokerId (_type_): 分公司
            account (_type_): 帳號
            trader (str, optional): 一般帳號登入時帶 ''.
            comId (str, optional): 商品代碼. Defaults to ''.
            comYm (str, optional): 商品年月. Defaults to ''.
            strikePrice (str, optional): 履約價. Defaults to ''.
            cp (str, optional): 買賣權. Defaults to ''.
            exchange (str, optional): 交易所. Defaults to ''.

        Returns:
            _type_: 0=送出查詢  -1=非合法帳號/Trader
            OnRcvMessage 回傳P001614
        """
        return self.tradecom.RetriveCOVER(market, brokerId, account
                                          , trader, comId, comYm, strikePrice
                                          , cp, exchange)
        
    def order(self, type, market, brokerId, account
              , symbolId, bs, pricefl, price, tif
              , qty, pf, off, webid = '', cnt= '', orderno= ''):
        """國內期權下單

        Args:
            type (_type_): O: 新單，C: 刪單，M: 改單，P: 改價，Q: 改量
            market (_type_):  F: FUT, O: OPT
            brokerId (_type_): 分公司
            account (_type_): 帳號
            symbolId (_type_): 商品代碼( 20碼);必須大(等)於5碼 & 小於20碼 (回傳-15)。必須為文數字
            bs (_type_): B: BUY，S: SELL
            pricefl (_type_): SP: 限價，M: 市價，SM: 停損市價，SS: 停損限價，MR: 範圍
            price (_type_): 價格;非市價單不可為0
            tif (_type_): R:ROD, I: IOC, F: FOC
            qty (_type_): 口數
            pf (_type_): O:新倉，C:平倉，D:當沖，A:自動
            off (_type_): SP: SPEEDY, AS: AS400
            webid (str, optional): 主機別(3碼). 新單帶 ''.
            cnt (str, optional): 電子單號(8碼). 新單帶 ''.
            orderno (str, optional): 委託書號(5碼). 新單帶 ''.

        Returns:
            _type_: 回傳代碼說明查詢，請使用GetOrderErrMsg(long) 來查詢。
            OnGetStatus: 下單或改單第一次回覆。COM_STATUS=ACK_REQUESTID 若(msg[8] = 1) 收單成功，反之失敗。
            OnRcvMessage: 
                        下單第二回覆	FUT_ORDER_ACK	PT02002
                            委託回報	FUT_ORDER_RPT	PT02010
                            成交回報	FUT_DEAL_RPT	PT02011
        """
        print(f'type: {type}, market: {market}, brokerId: {brokerId}, account: {account}')
        print(f'symbolId: {symbolId}, bs: {bs}, pricefl: {pricefl}, price: {price}, tif: {tif}')
        print(f'qty: {qty}, pf: {pf}, off: {off}, webid: {webid}, cnt: {cnt}, orderno: {orderno}')
        TYPE = self.orderType(type)
        MARKET = self.marketType(market)
        BS = self.sideFlag(bs)
        PRF = self.priceFlag(pricefl)
        TF = self.timeInForce(tif)
        PF = self.positionEffect(pf)
        OFF = self.officeFlag(off)
        QTY = UInt16(int(qty))
        PRICE = Decimal(float(price))
        
        rid = self.tradecom.GetRequestId()
        REQID = Int64(rid)
        print(f"送單 RequestId=[{rid}]")
        if type == 'O':
            res = self.tradecom.Order(TYPE, MARKET, REQID, brokerId, account, '', symbolId, BS, PRF, PRICE, TF, QTY, PF, OFF)
        else:
            res = self.tradecom.Order(TYPE, MARKET, REQID, brokerId, account, '', symbolId, BS, PRF, PRICE, TF, QTY, PF, OFF, webid, cnt, orderno)
        if res != 0:
            print("委託失敗: ", self.tradecom.GetOrderErrMsg(res))
            return False
        else:
            print("委託成功: ")
            sleep(1)
            return True
     
    def officeFlag(self, off):
        """風控(目前沒有作用)

        Args:
            off (_type_): SP: SPEEDY, AS: AS400

        Raises:
            TypeError: _description_

        Returns:
            _type_: _description_
        """
        off = off.upper()
        if off == 'SP':
            return OFFICE_FLAG.OF_SPEEDY
        elif off == 'AS':
            return OFFICE_FLAG.OF_AS400
        else:
            raise TypeError("%s is not a order officeFlag" % (off))
    
    def positionEffect(self, pf):
        """新/平/當沖

        Args:
            pf (_type_): O:新倉，C:平倉，D:當沖，A:自動

        Raises:
            TypeError: _description_

        Returns:
            _type_: _description_
        """
        pf = pf.upper()
        if pf == 'O':
            return POSITION_EFFECT.PE_OPEN
        elif pf == 'C':
            return POSITION_EFFECT.PE_CLOSE
        elif pf == 'D':
            return POSITION_EFFECT.PE_DAY_TRADE
        elif pf == 'A':
            return POSITION_EFFECT.PE_AUTO
        else:
            raise TypeError("%s is not a order positionEffect" % (pf))
        
    
    def timeInForce(self, tif):
        """ROD/IOC/FOK

        Args:
            tif (_type_): R:ROD, I: IOC, F: FOC

        Raises:
            TypeError: _description_

        Returns:
            _type_: _description_
        """
        tif = tif.upper()
        if tif == 'R':
            return TIME_IN_FORCE.TIF_ROD
        elif tif == 'I':
            return TIME_IN_FORCE.TIF_IOC
        elif tif == 'F':
            return TIME_IN_FORCE.TIF_FOK
        else:
            raise TypeError("%s is not a order timeInForce" % (tif))
    
    def priceFlag(self, pricefl):
        """限價/市價

        Args:
            pricefl (_type_): SP: 限價，M: 市價，SM: 停損市價，SS: 停損限價，MR: 範圍市價 

        Raises:
            TypeError: _description_

        Returns:
            _type_: _description_
        """
        pricefl = pricefl.upper()
        if pricefl == 'SP':
            return PRICE_FLAG.PF_SPECIFIED
        elif pricefl == 'M':
            return PRICE_FLAG.PF_MARKET
        elif pricefl == 'SM':
            return PRICE_FLAG.PF_STOP_MARKET
        elif pricefl == 'SS':
            return PRICE_FLAG.PF_STOP_SPECIFID
        elif pricefl == 'MR':
            return PRICE_FLAG.PF_MARKET_RANGE
        else:
            raise TypeError("%s is not a order priceFlag" % (pricefl))
    
    
    def sideFlag(self, bs):
        """買賣別

        Args:
            bs (_type_): B: BUY，S: SELL

        Raises:
            TypeError: _description_

        Returns:
            _type_: _description_
        """
        bs = bs.upper()
        if bs == 'B':
            return SIDE_FLAG.SF_BUY
        elif bs == 'S':
            return SIDE_FLAG.SF_SELL
        else:
            raise TypeError("%s is not a order sideFlag" % (bs))
    
    def marketType(self, market):
        """期/選

        Args:
            market (_type_): F: FUT, O: OPT

        Raises:
            TypeError: _description_

        Returns:
            _type_: _description_
        """
        market = market.upper()
        if market == 'F':
            return MARKET_FLAG.MF_FUT
        elif market == 'O':
            return MARKET_FLAG.MF_OPT
        else:
            raise TypeError("%s is not a order market" % (market))
    
    def orderType(self, type):
        """下單類別

        Args:
            type (_type_): O: 新單，C: 刪單，M: 改單，P: 改價，Q: 改量

        Raises:
            TypeError: _description_

        Returns:
            _type_: _description_
        """
        type = type.upper()
        if type == 'O':
            return ORDER_TYPE.OT_NEW
        elif type == 'C':
            return ORDER_TYPE.OT_CANCEL
        elif type == 'M':
            return ORDER_TYPE.OT_MODIFY
        elif type == 'P':
            return ORDER_TYPE.OT_MODIFY_PRICE
        elif type == 'Q':
            return ORDER_TYPE.OT_MODIFY_QTY
        else:
            raise TypeError("%s is not a order type" % (type))
    
    def proListDtl(self, stockNo):
        """取得股票商品資訊

        Args:
            stockNo (_type_): 股票商品待馬

        Returns:
            PIProList: PIProList資訊
        """
        return self.tradecom.GetProListByStockKind(ProListQueryField.PLQF_STOCKNO, stockNo)

    def proListAll(self):
        """取得期貨股票所有類別LIST

        Returns:
            list[str]: 取得所有類別LIST
        """
        return self.tradecom.GetProListAllKind()
    
    def pbListDtl(self, symbolId):
        """取得某類別/名稱之商品列表

        Args:
            symbolId (str): 輸入大類(Ex:TXO) 或名稱(Ex非金電期)

        Returns:
            List<P001802>: 輸入大類時則輸出該類所有商品列表，輸入名稱時則輸出該名稱之明細。格式請參照附件P001802。
        """
        return self.tradecom.GetProcuctDetailList(symbolId)
    
    def pbList(self):
        """取得所有商品列表

        Returns:
            list[str]: 回傳所有商品(商品代碼+商品名稱)列表
        """
        return self.tradecom.GetProcuctBaseList()
    
    def optSymbol2(self, symbolId, date1, stkprc1, cp1, bs1
                   , date2, stkprc2, cp2, bs2):
        """選擇權(複)

        Args:
            symbolId (_type_): 選擇權商品
            date1 (_type_): 月份1
            stkprc1 (_type_): 履約價1
            cp1 (_type_): 買賣權1
            bs1 (_type_): 買賣別1
            date2 (_type_): 月份2
            stkprc2 (_type_): 履約價2
            cp2 (_type_): 買賣權2
            bs2 (_type_): 買賣别2

        Returns:
            str: 完整商品代碼
        """
        return self.tradecom.GenOptDoubleSymbol(symbolId, date1, stkprc1, cp1, bs1
                                                , date2, stkprc2, cp2, bs2)
    
    def optSymbol(self, symbolId, date, stkprc, cp):
        """選擇權(單)

        Args:
            symbolId (_type_): 選擇權商品
            date (_type_): 月份
            stkprc (_type_): 履約價
            cp (_type_): 買賣權

        Returns:
            str: 完整商品代碼
        """
        return self.tradecom.GenOptSymbol(symbolId, date, stkprc, cp)
    
    def futSymbol(self, symbolId, date1, date2 = ''):
        """期貨下單商品代碼
        Args:
            symbolId (_type_): 期貨商品代碼
            date1 (_type_): 月份:第一隻腳
            date2 (str, optional): 月份:第二隻腳

        Returns:
            str: 期貨價差商品代號
        """
        return self.tradecom.GenFutSymbol(symbolId, date1, date2)

    def getProductInfo(self, symbolId):
        """商品明細查詢
        Args:
            symbolId (_type_): 商品代碼(Ex:TXO08900C1)
            
        Returns:
            P001802: 商品基本資料，格式請參照附件P001802。
        """
        return self.tradecom.GetProductInfo(symbolId)

    
    def getProductBase(self, symbolId):
        """商品名稱查詢
        Args:
            symbolId (_type_): 商品代碼(Ex:TXO)
        """
        return self.tradecom.GetProductBase(symbolId)
    
    def download(self):
        """下載商品檔
        """
        self.tradecom.RetriveProductDetail()
    
    def dispose(self) -> None:
        """關閉API的元件
        """
        self.tradecom.Dispose()
    
    def logout(self) -> None:
        """登出API平台
        """
        self.tradecom.Logout()
    
    def doLogin(self, uid, pwd):
        """自行登入
        Args:
            uid (_type_): _description_
            pwd (_type_): _description_
        """
        #是否註冊即時回報
        self.tradecom.AutoSubReport=True
        #是否回補回報
        self.tradecom.AutoRecoverReport=True
        #是否回下載商品檔
        self.tradecom.AutoRetriveProductInfo=True
        self.tradecom.LoginDirect(self.host, self.port, uid, pwd, ' ')
        sleep(2)
        
    def getAccList(self):
        """登入帳號查詢
        """
        return self.tradecom.GetAccountList()
    
    
    def getMsg(self, code):
        return self.tradecom.GetMessageMap(code)
    
    def PIProList(self, pkg):
        res = {'DT': 'PIProList',
         'CODE': pkg.StockCode,
         'StockNo': pkg.StockNo,
         'StockName': pkg.StockName,
         'StockKind': pkg.StockKind,
         'StockEName': pkg.StockEName,
         'StockEKind': pkg.StockEKind
        }
        self.callback(res)
        
    def logD(self, msg):
        if self.debug :
            print(str(datetime.now()), " ", msg)
    
    """
    ######################

    以下是處理主機回應的程式
    ######################
    """
    def P001503(self, pkg):
        """處理登入成功後的資訊

        Args:
            pkg (P001503): 請參考格式附件P001503
        """
        res = {'DT': 'P001503',
         'Code': pkg.Code, #0: 代表登入成功
         'MSG': self.getMsg(pkg.Code),
         'ID': pkg.ID,
         'Name': pkg.Name,
         'CA_YMD': pkg.CA_YMD,
         'CA_FLAG': pkg.CA_FLAG,
         'CA_TYPE': pkg.CA_TYPE,
         'CA_YMDW': pkg.CA_YMDW,
         'Qnum': pkg.Qnum,
         'Count': pkg.Count
        }
        i = 1
        for sub in pkg.p001503_2:
            num = str(i)
            res['BROKER' + num] = sub.BrokeId
            res['ACC' + num] = sub.Account
            res['ACCFL' + num] = sub.AccountFlag
            res['IB' + num] = sub.IB
            i += 1
        self.callback(res)
    
    def P001701(self, pkg):
        """_summary_

        Args:
            pkg (P001701): 請參考格式附件P001801
        """
        res = {'DT': 'P001701',
         'CODE': pkg.CODE,
         'Market': pkg.Market,
         'PostDate': pkg.PostDate,
         'Content': pkg.Content,
         'ROW': pkg.ROW,
         'Kind': pkg.Kind,
         'PostTime': pkg.PostTime
        }
        self.callback(res)
        
    def P001702(self, pkg):
        res = {'DT': 'P001702',
         'Market': pkg.Market,
         'Content': pkg.Content
        }
        self.callback(res)
        
    def P001801(self, pkg):
        """商品名稱
        Args:
            pkg (P001801): 請參考格式附件P001801
        """
        res = {'DT': 'P001801',
         'ComId': pkg.ComId,
         'ComType': pkg.ComType,
         'PriceDecimal': pkg.PriceDecimal,
         'StkPriceDecimal': pkg.StkPriceDecimal,
         'ContractType': pkg.ContractType,
         'ContractValue': float(pkg.ContractValue.ToString()),
         'TaxRate': float(pkg.TaxRate.ToString()),
         'Tick': float(pkg.Tick.ToString()),
         'ComCName': pkg.ComCName
        }
        self.callback(res)
        
    def P001802(self, pkg):
        """商品明細
        Args:
            pkg (P001802): 請參考格式附件P001802
        """
        res = {'DT': 'P001802',
         'ComId': pkg.ComId,
         'ComType': pkg.ComType,
         'PriceDecimal': pkg.PriceDecimal,
         'StkPriceDecimal': pkg.StkPriceDecimal,
         'Hot': pkg.Hot,
         'RisePrice': float(pkg.RisePrice.ToString()),
         'FallPrice': float(pkg.FallPrice.ToString()),
         'EndDate': pkg.EndDate
        }
        self.callback(res)
    
    def PT02002(self, pkg):
        """期權下單
        Args:
            pkg (PT02002): 請參考格式附件PT02002
        """
        res = {'DT': 'PT02002',
         'RequestId': pkg.RequestId,
         'WEBID': pkg.WEBID,
         'CNT': pkg.CNT,
         'OrderNo': pkg.OrderNo,
         'FrontOffice': pkg.FrontOffice,
         'ErrorCode': pkg.ErrorCode,
         'ErrorMsg': self.getMsg(pkg.ErrorCode)
        }
        self.callback(res)
        
    def PT02006(self, pkg):
        """期/選刪改單
        Args:
            pkg (PT02006): 請參考格式附件PT02006
        """
        res = {'DT': 'PT02006',
         'RequestId': pkg.RequestId,
         'WEBID': pkg.WEBID,
         'CNT': pkg.CNT,
         'OrderNo': pkg.OrderNo,
         'FrontOffice': pkg.FrontOffice,
         'ErrorCode': pkg.ErrorCode,
         'ErrorMsg': self.getMsg(pkg.ErrorCode)
        }
        self.callback(res)
        
    def PT02010(self, pkg):
        """委託回報
        Args:
            pkg (PT02010): 請參考格式附件PT02010
        """
        res = {'DT': 'PT02010',
         'OrderFunc': pkg.OrderFunc,
         'FrontOffice': pkg.FrontOffice,
         'BrokerId': pkg.BrokerId,
         'OrderNo': pkg.OrderNo,
         'Account': pkg.Account,
         'TradeDate': pkg.TradeDate,
         'ReportTime': pkg.ReportTime,
         'ClientOrderTime': pkg.ClientOrderTime,
         'WebID': pkg.WebID,
         'CNT': pkg.CNT,
         'TaiDelCode': pkg.TaiDelCode,
         'TimeInForce': pkg.TimeInForce,
         'Symbol': pkg.Symbol,
         'Side': pkg.Side,
         'PriceMark': pkg.PriceMark,
         'Price': pkg.Price,
         'PositionEffect': pkg.PositionEffect,
         'BeforeQty': pkg.BeforeQty,
         'AfterQty': pkg.AfterQty,
         'Code': pkg.Code,
         'ErrMsg': pkg.ErrMsg,
         'Trader': pkg.Trader
        }
        self.callback(res)
    
    def PT02011(self, pkg):
        """成交回報
        Args:
            pkg (PT02011): 請參考格式附件PT02011
        """
        res = {'DT': 'PT02011',
         'OrderFunc': pkg.OrderFunc,
         'BrokerId': pkg.BrokerId,
         'OrderNo': pkg.OrderNo,
         'Account': pkg.Account,
         'TradeDate': pkg.TradeDate,
         'ReportTime': pkg.ReportTime,
         'WEBID': pkg.WEBID,
         'CNT': pkg.CNT,
         'Symbol': pkg.Symbol,
         'Side': pkg.Side,
         'Market': pkg.Market,
         'DealPrice': pkg.DealPrice,
         'DealQty': pkg.DealQty,
         'CumQty': pkg.CumQty,
         'LeaveQty': pkg.LeaveQty,
         'MarketNo': pkg.MarketNo,
         'Symbol1': pkg.Symbol1,
         'DealPrice1': pkg.DealPrice1,
         'Qty1': pkg.Qty1,
         'BS1': pkg.BS1,
         'Symbol2': pkg.Symbol2,
         'DealPrice2': pkg.DealPrice2,
         'Qty2': pkg.Qty2,
         'BS2': pkg.BS2
        }
        self.callback(res)
    
    def P001614(self, pkg):
        """分帳客戶平倉查詢
        Args:
            pkg (P001614): 請參考格式附件P001614
        """
        res = {'DT': 'P001614',
            'Code': pkg.Code,
            'Rows': pkg.Rows
        }
        if pkg.Rows > 0 : 
            i = 1
            for sub in pkg.p001614_2:
                num = str(i)
                res['BrokerId' + num] =  pkg.BrokerId
                res['Account' + num] =  pkg.Account
                res['Group' + num] =  pkg.Group
                res['Trader' + num] =  pkg.Trader
                res['Exchange' + num] =  pkg.Exchange
                res['ComID' + num] =  pkg.ComID
                res['ComYM' + num] =  pkg.ComYM
                res['StrikePrice' + num] =  pkg.StrikePrice
                res['CP' + num] =  pkg.CP
                res['CURRENCY' + num] =  pkg.CURRENCY
                res['PRTLOS' + num] =  pkg.PRTLOS
                res['CTAXAMT' + num] =  pkg.CTAXAMT
                res['ORIGNFEE' + num] =  pkg.ORIGNFEE
                res['OSPRTLOS' + num] =  pkg.OSPRTLOS
                res['QTY' + num] =  pkg.QTY
                i += 1
        self.callback(res)
        
    def P001616(self, pkg):
        """分帳客戶最新部位彙總
        Args:
            pkg (P001616): 請參考格式附件P001616
        """
        res = {'DT': 'P001616',
         'Code': pkg.Code,
         'Rows': pkg.Rows
        }
        if pkg.Rows > 0 : 
            i = 1
            for sub in pkg.p001616_2:
                num = str(i)
                # 使用 getattr 安全地獲取屬性
                res['BrokerId' + num] =  getattr(sub, 'BrokerId', '')
                res['Account' + num] =  getattr(sub, 'Account', '')
                res['Group' + num] =  getattr(sub, 'Group', '')
                res['Trader' + num] =  getattr(sub, 'Trader', '')
                res['Exchange' + num] =  getattr(sub, 'Exchange', '')
                res['ComType' + num] =  getattr(sub, 'ComType', '')
                res['ComID' + num] =  getattr(sub, 'ComID', '')
                res['ComYM' + num] =  getattr(sub, 'ComYM', '')
                res['StrikePrice' + num] =  getattr(sub, 'StrikePrice', '')
                res['CloseDate' + num] =  getattr(sub, 'CloseDate', '')
                res['CP' + num] =  getattr(sub, 'CP', '')
                res['BS' + num] =  getattr(sub, 'BS', '')
                res['DeliveryDate' + num] =  getattr(sub, 'DeliveryDate', '')
                res['Currency' + num] =  getattr(sub, 'Currency', '')
                res['OTQty' + num] =  getattr(sub, 'OTQty', 0)
                res['TrdPrice' + num] =  getattr(sub, 'TrdPrice', 0)
                res['MPrice' + num] =  getattr(sub, 'MPrice', 0)
                res['PRTLOS' + num] =  getattr(sub, 'PRTLOS', 0)
                res['DealPrice' + num] =  getattr(sub, 'DealPrice', 0)
                i += 1
        self.callback(res)
        
    def P001618(self, pkg):
        """分帳客戶部位明細
        Args:
            pkg (P001618): 請參考格式附件P001618
        """
        res = {'DT': 'P001618',
         'Code': pkg.Code,
         'Rows': pkg.Rows
        }
        if pkg.Rows > 0 : 
            i = 1
            for sub in pkg.p001618_2:
                num = str(i)
                res['BrokerId' + num] =  pkg.BrokerId
                res['Account' + num] =  pkg.Account
                res['Group' + num] =  pkg.Group
                res['Trader' + num] =  pkg.Trader
                res['Exchange' + num] =  pkg.Exchange
                res['SeqNO' + num] =  pkg.SeqNO
                res['tradeType' + num] =  pkg.tradeType
                res['FCM' + num] =  pkg.FCM
                res['DeliveryDate' + num] =  pkg.DeliveryDate
                res['CloseDate' + num] =  pkg.CloseDate
                res['WEB' + num] =  pkg.WEB
                res['Cnt' + num] =  pkg.Cnt
                res['OrdNO' + num] =  pkg.OrdNo
                res['MarketNo' + num] =  pkg.MarketNo
                res['sNo' + num] =  pkg.sNo
                res['TradeDate' + num] =  pkg.TradeDate
                res['ComID' + num] =  pkg.ComID
                res['BS' + num] =  pkg.BS
                res['ComType' + num] =  pkg.ComType
                res['StrikePrice' + num] =  pkg.StrikePrice
                res['CP' + num] =  pkg.CP
                res['Qty' + num] =  pkg.Qty
                res['Currency' + num] =  pkg.Currency
                res['MixQty' + num] =  pkg.MixQty
                res['TrdPrice' + num] =  pkg.TrdPrice
                res['MPrice' + num] =  pkg.MPrice
                res['PRTLOS' + num] =  pkg.PRTLOS
                res['InitialMargin' + num] =  pkg.InitialMargin
                res['DayTrade' + num] =  pkg.DayTrade
                res['MTMargin' + num] =  pkg.MTMargin
                res['SPREAD' + num] =  pkg.SPREAD
                res['spKey' + num] =  pkg.spKey
                res['DealPrice' + num] =  pkg.DealPrice
                res['OrdNO2' + num] =  pkg.OrdNo2
                res['MarketNo2' + num] =  pkg.MarketNo2
                res['sNO2' + num] =  pkg.sNo2
                res['TradeDate2' + num] =  pkg.TradeDate2
                res['ComID2' + num] =  pkg.ComID2
                res['BS2' + num] =  pkg.BS2
                res['ComType2' + num] =  pkg.ComType2
                res['CP2' + num] =  pkg.CP2
                res['StrikePrice2' + num] =  pkg.StrikePrice2
                res['Qty2' + num] =  pkg.Qty2
                res['TrdPrice2' + num] =  pkg.TrdPrice2
                res['MPrice2' + num] =  pkg.MPrice2
                res['PRTLOS2' + num] =  pkg.PRTLOS2
                res['InitialMargin2' + num] =  pkg.InitialMargin2
                res['MTMargin2' + num] =  pkg.MTMargin2
                res['Currency2' + num] =  pkg.Currency2
                res['DealPrice2' + num] =  pkg.DealPrice2
                res['mixQty2' + num] =  pkg.mixQty2
                res['DayTrade2' + num] =  pkg.DayTrade2
                res['ComYM2' + num] =  pkg.ComYM2
                i += 1
        self.callback(res)
    
    def P001624(self, pkg):
        """平倉明細查詢
        Args:
            pkg (P001624): 請參考格式附件P001624
        """
        res = {'DT': 'P001624',
            'Code': pkg.Code,
            'Rows': pkg.Rows
        }
        if pkg.Rows > 0 : 
            i = 1
            for sub in pkg.p001624_2:
                num = str(i)
                res['BrokerId' + num] =  pkg.BrokerId
                res['Account' + num] =  pkg.Account
                res['Group' + num] =  pkg.Group
                res['Trader' + num] =  pkg.Trader
                res['Exchange' + num] =  pkg.Exchange
                res['OccDT' + num] =  pkg.OccDT
                res['TrdDT1' + num] =  pkg.TrdDT1
                res['OrdNo1' + num] =  pkg.OrdNo1
                res['FirmOrd1' + num] =  pkg.FirmOrd1
                res['OffsetSpliteSeqNo' + num] =  pkg.OffsetSpliteSeqNo
                res['TrdDT2' + num] =  pkg.TrdDT2
                res['OrdNo2' + num] =  pkg.OrdNo2
                res['FirmOrd2' + num] =  pkg.FirmOrd2
                res['OffsetSpliteSeqNo2' + num] =  pkg.OffsetSpliteSeqNo2
                res['OffsetCode' + num] =  pkg.OffsetCode
                res['offset' + num] =  pkg.offset
                res['BS' + num] =  pkg.BS
                res['ComID' + num] =  pkg.ComID
                res['ComYM' + num] =  pkg.ComYM
                res['StrikePrice' + num] =  pkg.StrikePrice
                res['CP' + num] =  pkg.CP
                res['ComID' + num] =  pkg.ComID
                res['Qty1' + num] =  pkg.Qty1
                res['Qty2' + num] =  pkg.Qty2
                res['TrdPrice1' + num] =  pkg.TrdPrice1
                res['TrdPrice2' + num] =  pkg.TrdPrice2
                res['PRTLOS' + num] =  pkg.PRTLOS
                res['AENO' + num] =  pkg.AENO
                res['Currency' + num] =  pkg.Currency
                res['CTAXAMT' + num] =  pkg.CTAXAMT
                res['ORIGNFEE' + num] =  pkg.ORIGNFEE
                res['Premium1' + num] =  pkg.Premium1
                res['Premium2' + num] =  pkg.Premium2
                res['InNo1' + num] =  pkg.InNo1
                res['InNo2' + num] =  pkg.InNo2
                res['Cnt1' + num] =  pkg.Cnt1
                res['Cnt2' + num] =  pkg.Cnt2
                res['OSPRTLOS' + num] =  pkg.OSPRTLOS
                i += 1
        self.callback(res)
    
    def P001626(self, pkg):
        """分帳客戶權益數查詢_NEW
        Args:
            pkg (P001626): 請參考格式附件P001626
        """
        res = {'DT': 'P001626',
         'Code': pkg.Code,
         'Count': pkg.Count
        }
        if pkg.Count > 0 :
            i = 1
            for sub in pkg.p001626_2:
                num = str(i)
                res['BrokerId' + num] = sub.BrokerId
                res['Account' + num] = sub.Account
                res['Group' + num] = sub.Group
                res['Trader' + num] = sub.Trader
                res['Currency' + num] = sub.Currency
                res['LCTDAB' + num] = sub.LCTDAB
                res['ORIGNFEE' + num] = sub.ORIGNFEE
                res['TAXAMT' + num] = sub.TAXAMT
                res['CTAXAMT' + num] = sub.CTAXAMT
                res['DWAMT' + num] = sub.DWAMT
                res['OSPRTLOS' + num] = sub.OSPRTLOS
                res['PRTLOS' + num] = sub.PRTLOS
                res['BMKTVAL' + num] = sub.BMKTVAL
                res['SMKTVAL' + num] = sub.SMKTVAL
                res['OPREMIUM' + num] = sub.OPREMIUM
                res['TPREMIUM' + num] = sub.TPREMIUM
                res['EQUITY' + num] = sub.EQUITY
                res['IAMT' + num] = sub.IAMT
                res['MAMT' + num] = sub.MAMT
                res['EXCESS' + num] = sub.EXCESS
                res['ORDEXCESS' + num] = sub.ORDEXCESS
                res['ORDAMT' + num] = sub.ORDAMT
                res['ExProfit' + num] = sub.ExProfit
                res['ORDAMTNOCN' + num] = sub.ORDAMTNOCN
                res['WithdrawMnt' + num] = sub.WithdrawMnt
                res['Premium' + num] = sub.Premium
                res['PTime' + num] = sub.PTime
                res['FloatProfit' + num] = sub.FloatProfit
                res['LASSPRTLOS' + num] = sub.LASSPRTLOS
                res['CLOSEAMT' + num] = sub.CLOSEAMT
                res['ORDIAMT' + num] = sub.ORDIAMT
                res['ORDMAMT' + num] = sub.ORDMAMT
                res['DayTradeAMT' + num] = sub.DayTradeAMT
                res['ReductionAMT' + num] = sub.ReductionAMT
                res['CreditAMT' + num] = sub.CreditAMT
                res['Balance' + num] = sub.balance
                res['IPremium' + num] = sub.IPremium
                res['OPremium' + num] = sub.OPremium
                res['Securities' + num] = sub.Securities
                res['SecuritiesOffset' + num] = sub.SecuritiesOffset
                res['OffsetAMT' + num] = sub.OffsetAMT
                res['Offset' + num] = sub.Offset
                res['FULLMTRISK' + num] = sub.FULLMTRISK
                res['FULLRISK' + num] = sub.FULLRISK
                res['MarginCall' + num] = sub.MarginCall
                res['SellVerticalSpread' + num] = sub.SellVerticalSpread
                res['StrikePrice' + num] = sub.StrikePrice
                res['ActMarketValue' + num] = sub.ActMarketValue
                res['TPRTLOS' + num] = sub.TPRTLOS
                res['MarginCall1' + num] = sub.MarginCall1
                res['AddMargin' + num] = sub.AddMargin
                i += 1
        self.callback(res)
    
    def P001628(self, pkg):
        """台外幣互轉作業
        Args:
            pkg (P001628): 請參考格式附件P001628
        """
        res = {'DT': 'P001628',
         'Code': pkg.Code,
         'ErrorMsg': pkg.ErrorMsg
        }
        self.callback(res)

    def P001643(self, pkg):
        """到期&無效履約查詢
        Args:
            pkg (P001643): 請參考格式附件P001643
        """
        res = {'DT': 'P001643',
         'Rows': pkg.Rows,
        }
        if pkg.Rows > 0 :
            i = 1
            for sub in pkg.Detail:
                num = str(i)
                res['BrokerId' + num] = sub.BrokerId
                res['Account' + num] = sub.Account
                res['Group' + num] = sub.Group
                res['Trader' + num] = sub.Trader
                res['DueDate' + num] = sub.DueDate
                res['TrdDate' + num] = sub.TrdDate
                res['OrdNo' + num] = sub.OrdNo
                res['FirmOrd' + num] = sub.FirmOrd
                res['SeqNo' + num] = sub.SeqNo
                res['Exchange' + num] = sub.Exchange
                res['ComID' + num] = sub.ComID
                res['ComYM' + num] = sub.ComYM
                res['StrikePrice' + num] = sub.StrikePrice
                res['CP' + num] = sub.CP
                res['BS' + num] = sub.BS
                res['QTY' + num] = sub.QTY
                res['TaxCurr' + num] = sub.TaxCurr
                res['TaxAmt' + num] = sub.TaxAmt
                res['FeeCurr' + num] = sub.FeeCurr
                res['FeeAmt' + num] = sub.FeeAmt
                res['Premium' + num] = sub.Premium
                res['TrdPre' + num] = sub.TrdPre
                i += 1
        self.callback(res)

    def P001645(self, pkg):
        """
        Args:
            pkg (P001645): 請參考格式附件P001645
        """
        res = {'DT': 'P001645',
         'Code': pkg.Code,
          'Rows': pkg.Rows,
        }
        if pkg.Rows > 0 :
            i = 1
            for sub in pkg.Detail:
                num = str(i)
                res['Market' + num] = sub.Market
                res['BrokerId' + num] = sub.BrokerId
                res['Account' + num] = sub.Account
                res['Group' + num] = sub.Group
                res['Trader' + num] = sub.Trader
                res['RtnCode' + num] = sub.RtnCode
                res['Exchange' + num] = sub.Exchange
                res['OrdNo' + num] = sub.OrdNo
                res['FirmOrd' + num] = sub.FirmOrd
                res['SeqNo' + num] = sub.SeqNo
                res['Exchange' + num] = sub.Exchange
                res['OccDT' + num] = sub.OccDT
                res['TrdDT1' + num] = sub.TrdDT1
                res['OrdNo1' + num] = sub.OrdNo1
                res['FirmOrd1' + num] = sub.FirmOrd1
                res['OffsetSpliteSeqNo' + num] = sub.OffsetSpliteSeqNo
                res['OrdNo2' + num] = sub.OrdNo2
                res['FirmOrd2' + num] = sub.FirmOrd2
                res['OffsetSpliteSeqNo2' + num] = sub.OffsetSpliteSeqNo2
                res['OffsetCode' + num] = sub.OffsetCode
                res['offset' + num] = sub.offset
                res['BS' + num] = sub.BS
                res['ComID' + num] = sub.ComID
                res['ComYM' + num] = sub.ComYM
                res['StrikePrice' + num] = sub.StrikePrice
                res['CP' + num] = sub.CP
                res['ComID2' + num] = sub.ComID2
                res['Qty1' + num] = sub.Qty1
                res['Qty2' + num] = sub.Qty2
                res['TrdPrice1' + num] = sub.TrdPrice1
                res['TrdPrice2' + num] = sub.TrdPrice2
                res['PRTLOS' + num] = sub.PRTLOS
                res['AENO' + num] = sub.AENO
                res['Currency' + num] = sub.Currency
                res['CTAXAMT' + num] = sub.CTAXAMT
                res['ORIGNFEE' + num] = sub.ORIGNFEE
                res['Premium1' + num] = sub.Premium1
                res['Premium2' + num] = sub.Premium2
                res['InNo1' + num] = sub.InNo1
                res['InNo2' + num] = sub.InNo2
                res['Cnt1' + num] = sub.Cnt1
                res['Cnt2' + num] = sub.Cnt2
                i += 1
        self.callback(res)       
        
    def P001647(self, pkg):
        """大小台互抵
        Args:
            pkg (P001647): 請參考格式附件P001647
        """
        res = {'DT': 'P001647',
         'Code': pkg.Code,
         'BrokerId': pkg.BrokerId,
         'Account': pkg.Account,
         'Qty1': pkg.Qty1,
         'Qty2': pkg.Qty2,
         'Status': pkg.Status
        }
        self.callback(res)
        
    def onTradeRcvMessage(self, sender, pkg): 
        """接收KGI QuoteCom API message event

        Args:
            sender (_type_): _description_
            pkg (_type_): _description_
        """
        if pkg.DT == 1503 : # 處理登入成功後的資訊
            self.logD('IN 1503')
            self.P001503(pkg)
        elif pkg.DT == 1701 : # 成交價量揭示
            self.logD('IN 1701')
            self.P001701(pkg)
        elif pkg.DT == 1702 : # 成交價量揭示
            self.logD('IN 1702')
            self.P001702(pkg)
        elif pkg.DT == 1801 : # 成交價量揭示
            self.logD('IN 1801')
            self.P001801(pkg)
        elif pkg.DT == 2002 : # 期權下單
            self.logD('IN 2002')
            self.PT02002(pkg)
        elif pkg.DT == 2006 : # 期/選刪改單
            self.logD('IN 2006')
            self.PT02006(pkg)
        elif pkg.DT == 2010 : # 委託回報
            self.logD('IN 2010')
            self.PT02010(pkg)
        elif pkg.DT == 2011 : # 成交回報
            self.logD('IN 2011')
            self.PT02011(pkg)
        elif pkg.DT == 1614 : # 分帳客戶平倉查詢
            self.logD('IN 1614')
            self.P001614(pkg)
        elif pkg.DT == 1624 : # 平倉明細查詢
            self.logD('IN 1624')
            self.P001624(pkg)
        elif pkg.DT == 1616 : # 分帳客戶最新部位彙總
            self.logD('IN 1616')
            self.P001616(pkg)
        elif pkg.DT == 1618 : # 分帳客戶部位明細
            self.logD('IN 1618')
            self.P001618(pkg)
        elif pkg.DT == 1626 : # 分帳客戶權益數查詢_NEW
            self.logD('IN 1626')
            self.P001626(pkg)
        elif pkg.DT == 1628 : # 台外幣互轉作業
            self.logD('IN 1628')
            self.P001628(pkg)
        elif pkg.DT == 1643 : # 到期&無效履約查詢
            self.logD('IN 1643')
            self.P001643(pkg)
        elif pkg.DT == 1645 : # 歷史平倉查詢
            self.logD('IN 1645')
            self.P001645(pkg)
        elif pkg.DT == 1647 : # 大小台互抵
            self.logD('IN 1647')
            self.P001647(pkg)
        else:
            print('UNKOWN pkg: ', pkg, ', val: ', pkg.DT)
    
    def onTradeGetStatus(self, sender, status, msg): 
        """接收KGI Trade API status event
        Args:請參考事件說明
            sender (_type_): _description_
            status (_type_): _description_
            msg (_type_): _description_
        """
        smsg = bytes(msg).decode('UTF-8','strict')
        res = {'DT': 'STATUS',
         'status': status.ToString(),
         'msg': smsg
        }
        self.callback(res)
    
    def onTradeRecoverStatus(self, sender, topic, status, count): 
        """資料回補事件
        Args:
            sender (_type_): _description_
            topic (_type_): _description_
            status (_type_): _description_
            count (_type_): _description_
        """
        res = {'DT': 'RECOVER',
         'topic': topic,
         'status': status.ToString(),
         'count': count
        }
        self.callback(res)
        
    def onTradeRcvServerTime(self, time, quality):
        res = {'DT': 'SERVERTIME',
         'time': time,
         'quality': quality
        }
        self.callback(res)
        

if __name__ == '__main__' :
    help(__name__)