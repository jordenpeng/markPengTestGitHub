import clr
import sys

clr.AddReference("Package")      #必要引用dll
clr.AddReference("PushClient")   #必要引用dll
clr.AddReference("QuoteCom")     #必要引用dll

from Intelligence import QuoteCom   #from namespace import class
from Intelligence import MARKET_FLAG   #from namespace import class
from Intelligence import COM_STATUS #from namespace import class
from time import sleep
"""
QuoteCom是凱基整合行情報價的API元件，使用者可藉由QuoteCom達到即時接收行情及報價查詢功能等目的。
使用QuoteCom元件前需要先安裝Pythonnet，指令如下:
pip install Pythonnet

使用QuoteCom元件須引用以下檔案，請檢查檔案是否存在。
1.	QuoteCom.dll
2.	PushClient.dll
3.	Package.dll

"""
class QuotecomPyFut:
    """KGI期貨國內報價的Python API範例程式。
    """
    def __init__(self, host, port, sid, token, callback=None) -> None:
        """程式初始化

        Args:
            host (str): 主機連線的host
            port (num): 主機連線的port
            sid (str):  主機連線的sid
            token (str): 主機連線的token
        """
        self.host = host
        self.port = port
        self.sid = sid
        self.token = token
        if callback == None:
             self.callback = lambda dic: print(dic)
        else:
            self.callback = callback
        self.quoteCom =  QuoteCom("", port, sid, token)
        print("TradeCom API 初始化 Version (%s) ........" % (self.quoteCom.version))
        # register event handler
        #狀態通知事件KGI QuoteCom API message event
        self.quoteCom.OnRcvMessage += self.onQuoteRcvMessage
        #資料接收事件KGI QuoteCom API status event
        self.quoteCom.OnGetStatus += self.onQuoteGetStatus
        #資料回補事件KGI QuoteCom API status event
        self.quoteCom.OnRecoverStatus += self.onQuoteRecoverStatus
    
    def __str__(self):
        return 'KGI期貨國內報價的Python API範例程式。'
    
    def logout(self) -> None:
        """登出API平台
        """
        self.quoteCom.Logout()
    
    def dispose(self) -> None:
        """關閉API的元件
        """
        self.quoteCom.Dispose()
    
    def doGetTFList(self, type) -> None:
        """查詢商品列表-市場別

        Args:
            type (_type_): F:期貨，O:選擇權
        """
        if type == 'F':
            res = self.quoteCom.GetTaifexProductListT1(MARKET_FLAG.MF_FUT)
            if len(res) == 0 :
                print('請先執行DOWNLOAD')
                return
        elif type == 'O':
            res = self.quoteCom.GetTaifexProductListT1(MARKET_FLAG.MF_OPT)
            if len(res) == 0 :
                print('請先執行DOWNLOAD')
                return
        else:
            res = self.quoteCom.GetTaifexProductListT1(type)
            if len(res) == 0 :
                print('請先執行DOWNLOAD')
                return
        for v in res:
            print('doGetTFList: ', v)
    
    def doRecover(self, symbolId, stime='0900', etime='0910'):
        """國內期權商品行情回補

        Args:
            symbolId (_type_): _description_
            stime (_type_): _description_
            etime (_type_): _description_
        """
        res = self.quoteCom.RetriveRecover(symbolId, stime, etime)
        self.checkres(res)
        
    def doPBase(self, symbolId) -> None:
        """查詢單一商品基本資料

        Args:
            symbolId (_type_): 查詢商品代碼
        """
        res = self.quoteCom.GetProductBase(symbolId)
        self.checkres(res)
    
    def doPBList(self, type) -> None:
        """查詢商品列表-市場別

        Args:
            type (_type_): F:期貨，O:選擇權
        """
        if type == 'F':
            res = self.quoteCom.GetProductBaseList(MARKET_FLAG.MF_FUT)
            if len(res) == 0 :
                print('請先執行DOWNLOAD')
                return
        elif type == 'O':
            res = self.quoteCom.GetProductBaseList(MARKET_FLAG.MF_OPT)
            if len(res) == 0 :
                print('請先執行DOWNLOAD')
                return
        else:
            res = self.quoteCom.GetProductBaseList(type)
            if len(res) == 0 :
                print('請先執行DOWNLOAD')
                return
        for v in res:
            print('PBLIST: ', v)
        return res

    def doDown(self) -> None:
        """下載可註冊商品基本資料
        """
        res = self.quoteCom.RetriveQuoteList()
        self.checkres(res, 2)
        self.quoteCom.LoadTaifexProductXMLT1()
        sleep(5)
        
        

    def doAsk(self, symbolId) -> None:
        """查詢商品盤別

        Args:
            symbolId (_type_): 查詢商品代碼
        """
        res = self.quoteCom.AskTaifexSession(symbolId)
        self.checkres(res)

    def doClosePrice(self) -> None:
        """查詢商品收盤資料
        """
        res = self.quoteCom.RetriveClosePrice()
        self.checkres(res)

    def doLastPrice(self, symbolId) -> None:
        """查詢商品最後價格

        Args:
            symbolId (_type_): 查詢商品代碼
        """
        res = self.quoteCom.RetriveLastPrice(symbolId)
        self.checkres(res)

    def doUnSub(self, symbolId) -> None:
        """單一商品取消註冊

        Args:
            symbolId (_type_): 商品代碼
        """
        print(symbolId)
        self.quoteCom.UnsubQuotes(symbolId)
        sleep(1)

    def doSub(self, symbolId) -> None:
        """單一商品註冊

        Args:
            symbolId (_type_): 商品代碼
        """
        res = self.quoteCom.SubQuote(symbolId)
        self.checkres(res)

    def doLogin(self, uid, pwd) -> None:
        """處理登入作業。

        Args:
            uid (str): uid
            pwd (array): PWD
        """
        self.quoteCom.Connect2Quote(self.host, self.port, uid, pwd, ' ', '')
        sleep(2)

    def checkres(self, res, time=1) -> None:
        """統一處理回傳結果.

        Args:
            res (_type_): quoteCom function的執行結果
            time (int, optional): 非同步的等待時間，預設1秒.
        """
        if res == 0:
            sleep(time)
        else:
            print('執行失敗: ', self.quoteCom.GetSubQuoteMsg(res))

    """
    ######################

    以下是處理主機回應的程式
    ######################
    """
    def __P001503(self, pkg):
        """處理登入成功後的資訊

        Args:
            pkg (P001503): 請參考附錄P001503
        """
        res = {'DT': 'P001503',
         'Code': pkg.Code, #0: 代表登入成功
         'MSG': self.quoteCom.GetSubQuoteMsg(pkg.Code),
         'ID': pkg.ID,
         'Name': pkg.Name,
         'CA_YMD': pkg.CA_YMD,
         'Qnum': pkg.Qnum,
         'LoginType': pkg.LoginType,
         'ActCntMatch': pkg.ActCntMatch,
         'QIdx':pkg.QIdx,
         'Count': pkg.Count}
        i = 1
        for sub in pkg.p001503_2:
            res['BROKER' + str(i)] = sub.BrokeId
            res['ACC' + str(i)] = sub.Account
            i += 1

        self.callback(res)
        
    def __P20008(self, pkg):
        """期貨商品定義檔

        Args:
            pkg (PI20008): 請參考附錄PI20008
        """
        res = {'DT': 'PI20008',
         'Market': pkg.Market,
         'Symbol': pkg.Symbol,
         'SymbolIdx': pkg.SymbolIdx,
         '_RISE_LIMIT_PRICE1': float(pkg._RISE_LIMIT_PRICE1),
         '_REFERENCE_PRICE': float(pkg._REFERENCE_PRICE),
         '_PROD_KIND': pkg._PROD_KIND,
         '_FALL_LIMIT_PRICE1': float(pkg._FALL_LIMIT_PRICE1.ToString()),
         '_RISE_LIMIT_PRICE2': float(pkg._RISE_LIMIT_PRICE2.ToString()),
         '_FALL_LIMIT_PRICE1': float(pkg._FALL_LIMIT_PRICE1.ToString()),
         '_RISE_LIMIT_PRICE3': float(pkg._RISE_LIMIT_PRICE3.ToString()),
         '_FALL_LIMIT_PRICE3': float(pkg._FALL_LIMIT_PRICE3.ToString()),
         '_PROD_KIND': pkg._PROD_KIND,
         '_PROD_KIND': pkg._PROD_KIND,
         'PriceDecimal': pkg.PriceDecimal,
         'StrikePriceDecimal': pkg.StrikePriceDecimal,
         '_PROD_NAME': pkg._PROD_NAME,
         'END_DATE': pkg.END_DATE}
        self.callback(res)

    def __P20026(self, pkg):
        """查詢商品最後價格

        Args:
            pkg (P20026): 請參考附錄P20026
        """
        res = {'DT': 'P20026',
         'Symbol': pkg.Symbol,
         'PriceDecimal': pkg.PriceDecimal,
         '_MatchPrice': pkg._MatchPrice,
         'MatchPrice': pkg.MatchPrice,
         'DayHighPrice': float(pkg.DayHighPrice.ToString()),
         'MatchTotalQty': pkg.MatchTotalQty,
         'Break_Mark': pkg.Break_Mark,
         'FirstDerivedBuyPrice': float(pkg.FirstDerivedBuyPrice.ToString()),
         'FirstDerivedBuyQty': pkg.FirstDerivedBuyQty,
         'Session':pkg.Session,
         'DayLowPrice': float(pkg.DayLowPrice.ToString()),
         'FirstMatchPrice': float(pkg.FirstMatchPrice.ToString()),
         'FirstMatchQty': pkg.FirstMatchQty,
         'ReferencePrice': float(pkg.ReferencePrice.ToString()),
         'BUY_DEPTH': pkg.BUY_DEPTH,
         'SELL_DEPTH': pkg.SELL_DEPTH,
         'FirstDerivedSellPrice': float(pkg.FirstDerivedSellPrice.ToString()),
         'FirstDerivedSellQty': pkg.FirstDerivedSellQty}
        i = 1
        for v in pkg.BUY_DEPTH:
            print('BUY_DEPTH' + str(i), ": " ,v.PRICE, " ### ", v.QUANTITY)
            res['BUY_DEPTH_PR' + str(i)] = float(v.PRICE.ToString())
            res['BUY_DEPTH_QTY' + str(i)] = v.QUANTITY
            i += 1
        
        i = 1
        for v in pkg.BUY_DEPTH:
            res['SELL_DEPTH_PRI' + str(i)] = float(v.PRICE.ToString())
            res['SELL_DEPTH_QTY' + str(i)] = v.QUANTITY
        self.callback(res)

    def __P20070(self, pkg):
        """收盤行情料訊息

        Args:
            pkg (PI20070): 請參考附錄PI20070
        """
        res = {'DT': 'PI20070',
         'Market': pkg.Market,
         'PROD_ID': pkg.PROD_ID,
         'TERM_HIGH_PRICE': pkg.TERM_HIGH_PRICE,
         'TERM_LOW_PRICE': pkg.TERM_LOW_PRICE,
         'DAY_HIGH_PRICE': pkg.DAY_HIGH_PRICE,
         'DAY_LOW_PRICE': pkg.DAY_LOW_PRICE,
         'OPEN_PRICE': pkg.OPEN_PRICE,
         'BUY_PRICE':pkg.BUY_PRICE,
         'SELL_PRICE': pkg.SELL_PRICE,
         'CLOSE_PRICE': pkg.CLOSE_PRICE,
         'BO_COUNT_TAL': pkg.BO_COUNT_TAL,
         'BO_QNTY_TAL': pkg.BO_QNTY_TAL,
         'SO_COUNT_TAL': pkg.SO_COUNT_TAL,
         'SO_QNTY_TAL': pkg.SO_QNTY_TAL,
         'TOTAL_COUNT': pkg.TOTAL_COUNT,
         'TOTAL_QNTY': pkg.TOTAL_QNTY,
         'COMBINE_BO_COUNT_TAL': pkg.COMBINE_BO_COUNT_TAL,
         'COMBINE_BO_QNTY_TAL': pkg.COMBINE_BO_QNTY_TAL,
         'COMBINE_SO_COUNT_TAL': pkg.COMBINE_SO_COUNT_TAL,
         'COMBINE_SO_QNTY_TAL': pkg.COMBINE_SO_QNTY_TAL,
         'COMBINE_TOTAL_QNTY': pkg.COMBINE_TOTAL_QNTY,
         'DECIMAL_LOCATOR': pkg.DECIMAL_LOCATOR}
        self.callback(res)

    def __P20020(self, pkg):
        """成交價量揭示

        Args:
            pkg (PI20020): 請參考附錄PI20020
        """
        res = {'DT': 'PI20020',
         'Market': pkg.Market,
         'Symbol': pkg.Symbol,
         'MatchTime': pkg.MatchTime,
         'InfoSeq': pkg.InfoSeq,
         'LastItem': pkg.LastItem,
         'PriceSign': pkg.PriceSign,
         'MatchQuantity': pkg.MatchQuantity,
         'PriceDecimal':pkg.PriceDecimal,
         'MatchTotalQty': pkg.MatchTotalQty,
         'MatchBuyCnt': pkg.MatchBuyCnt,
         'MatchSellCnt': pkg.MatchSellCnt,
         'Price': float(pkg.Price.ToString())}
        self.callback(res)

    def __P20021(self, pkg):
        """盤中最高(低)價揭示

        Args:
            pkg (PI20021): 請參考附錄PI20021
        """
        res = {'DT': 'PI20021',
         'Market': pkg.Market,
         'Symbol': pkg.Symbol,
         'DayLowPrice': float(pkg.DayLowPrice.ToString()),
         'DayHighPrice': float(pkg.DayHighPrice.ToString()),
         'MatchTime': pkg.MatchTime,
         'PriceDecimal': pkg.PriceDecimal}
        self.callback(res)

    def __P20022(self, pkg):
        """成交價量揭示

        Args:
            pkg (PI20022): 請參考附錄PI20022
        """
        res = {'DT': 'PI20022',
         'Market': pkg.Market,
         'Symbol': pkg.Symbol,
         'MatchTime': pkg.MatchTime,
         'InfoSeq': pkg.InfoSeq,
         'LastItem': pkg.LastItem,
         'PriceSign': pkg.PriceSign,
         'MatchQuantity': pkg.MatchQuantity,
         'PriceDecimal': pkg.PriceDecimal,
         'MatchTotalQty': pkg.MatchTotalQty,
         'MatchBuyCnt': pkg.MatchBuyCnt,
         'MatchSellCnt': pkg.MatchSellCnt,
         'Price': float(pkg.Price.ToString())}
        self.callback(res)

    def __P20023(self, pkg):
        """定時開盤價量揭示

        Args:
            pkg (PI20023): 請參考附錄PI20023
        """
        res = {'DT': 'PI20023',
         'Market': pkg.Market,
         'Symbol': pkg.Symbol,
         'FirstMatchPrice': pkg.FirstMatchPrice,
         'FirstMatchQty': pkg.FirstMatchQty,
         'MatchTime': pkg.MatchTime,
         'PriceDecimal': pkg.PriceDecimal}
        self.callback(res)

    def __P20030(self, pkg):
        """單一商品委託量累計

        Args:
            pkg (PI20030): 請參考附錄PI20030
        """
        res = {'DT': 'PI20030',
         'Market': pkg.Market,
         'Symbol': pkg.Symbol,
         'BUY_ORDER': pkg.BUY_ORDER,
         'BUY_QUANTITY': pkg.BUY_QUANTITY,
         'SELL_ORDER': pkg.SELL_ORDER,
         'SELL_QUANTITY': pkg.SELL_QUANTITY}
        self.callback(res)

    def __P20080(self, pkg):
        """委託簿揭示訊息

        Args:
            pkg (PI20080): 請參考附錄PI20080
        """
        res = {'DT': 'PI20080',
         'Market': pkg.Market,
         'Symbol': pkg.Symbol,
         'BUY_DEPTH': pkg.BUY_DEPTH,
         'SELL_DEPTH': pkg.SELL_DEPTH,
         'FIRST_DERIVED_BUY_PRICE': pkg.FIRST_DERIVED_BUY_PRICE,
         'FIRST_DERIVED_BUY_DTY': pkg.FIRST_DERIVED_BUY_DTY,
         'FIRST_DERIVED_SELL_PRICE': pkg.FIRST_DERIVED_SELL_PRICE,
         'FIRST_DERIVED_SELL_QTY': pkg.FIRST_DERIVED_SELL_QTY,
         'DATA_TIME': pkg.DATA_TIME}
        self.callback(res)

    def __P20082(self, pkg):
        """委託簿揭示訊息-盤前

        Args:
            pkg (PI20082): 請參考附錄PI20082
        """
        res = {'DT': 'PI20082',
         'Market': pkg.Market,
         'Symbol': pkg.Symbol,
         'BUY_DEPTH': pkg.BUY_DEPTH,
         'SELL_DEPTH': pkg.SELL_DEPTH,
         'FIRST_DERIVED_BUY_PRICE': pkg.FIRST_DERIVED_BUY_PRICE,
         'FIRST_DERIVED_BUY_DTY': pkg.FIRST_DERIVED_BUY_DTY,
         'FIRST_DERIVED_SELL_PRICE': pkg.FIRST_DERIVED_SELL_PRICE,
         'FIRST_DERIVED_SELL_QTY': pkg.FIRST_DERIVED_SELL_QTY,
         'DATA_TIME': pkg.DATA_TIME}
        self.callback(res)

    def __P20090(self, pkg):
        """台灣期貨交易所編制指數資訊揭示訊息

        Args:
            pkg (PI20090): 請參考附錄PI20090
        """
        res = {'DT': 'PI20090',
         'Market': pkg.Market,
         'INDEX_ID': pkg.INDEX_ID,
         'INDEX_PRICE': pkg.INDEX_PRICE,
         'INDEX_TIME': pkg.INDEX_TIME}
        self.callback(res)
        
    def __PI05005(self, pkg):
        """盤別資訊

        Args:
            pkg (PI05005): 請參考附錄PI05005
        """
        res = {'DT': 'PI05005',
         'Market': pkg.Market,
         'Symbol': pkg.Symbol,
         'FallLimitPrice': pkg.FallLimitPrice,
         'RiseLimitPrice': pkg.RiseLimitPrice,
         'RefPrice': pkg.RefPrice,
         'PriceDecimal': pkg.PriceDecimal,
         'Session': pkg.Session,
         'Status': pkg.Status}
        self.callback(res)

    def __PI05005(self, pkg):
        """盤別資訊

        Args:
            pkg (PI05005): 請參考附錄PI05005
        """
        res = {'DT': 'PI05005',
         'Market': pkg.Market,
         'Symbol': pkg.Symbol,
         'FallLimitPrice': float(pkg.FallLimitPrice.ToString()),
         'RiseLimitPrice': float(pkg.RiseLimitPrice.ToString()),
         'RefPrice': float(pkg.RefPrice.ToString()),
         'PriceDecimal': pkg.PriceDecimal,
         'Session': pkg.Session,
         'Status': pkg.Status}
        self.callback(res)

    def __P21020(self, pkg):
        """回補成交價量揭示

        Args:
            pkg (PI20020): 請參考附錄PI20020
        """
        res = {'DT': 'PI21020',
         'Market': pkg.Market,
         'Symbol': pkg.Symbol,
         'MatchTime': pkg.MatchTime,
         'InfoSeq': pkg.InfoSeq,
         'LastItem': pkg.LastItem,
         'PriceSign': pkg.PriceSign,
         'MatchQuantity': pkg.MatchQuantity,
         'PriceDecimal':pkg.PriceDecimal,
         'MatchTotalQty': pkg.MatchTotalQty,
         'MatchBuyCnt': pkg.MatchBuyCnt,
         'MatchSellCnt': pkg.MatchSellCnt,
         'Price': float(pkg.Price.ToString())}
        self.callback(res)

    def onQuoteRcvMessage(self, sender, pkg):
        """接收KGI QuoteCom API message event

        Args:
            sender (_type_): _description_
            pkg (_type_): _description_
        """
        if pkg.DT == 1503 : # 處理登入成功後的資訊
            self.__P001503(pkg)
        elif pkg.DT == 20020 : # 成交價量揭示
            self.__P20020(pkg)
        elif pkg.DT == 20021 : # 盤中最高(低)價揭示
            self.__P20021(pkg)
        elif pkg.DT == 20022 : # 成交價量揭示 – 盤前 (格式同 PI20020)
            self.__P20022(pkg)
        elif pkg.DT == 20023 : # 定時開盤價量揭示
            self.__P20023(pkg)
        elif pkg.DT == 20030 : # 單一商品委託量累計
            self.__P20030(pkg)
        elif pkg.DT == 20080 : # 委託簿揭示訊息
            self.__P20080(pkg)
        elif pkg.DT == 20082 : # 委託簿揭示訊息-盤前 (格式同PI20080)
            self.__P20082(pkg)
        elif pkg.DT == 20090 : # 台灣期貨交易所編制指數資訊揭示訊息
            self.__P20090(pkg)
        elif pkg.DT == 20026 : #查詢商品最後價格
            self.__P20026(pkg)
        elif pkg.DT == 20070 : #收盤行情料訊息
            self.__P20070(pkg)
        elif pkg.DT == 5005 :  #盤別資訊
            self.__PI05005(pkg)
        elif pkg.DT == 21020 : #查詢單一商品基本資料
            self.__P21020(pkg)
        elif pkg.DT == 20008 : #期貨商品定義檔
            self.__P20008(pkg)
        else:
            print('UNKOWN pkg: ', pkg, ', val: ', pkg.DT)
            
                
    def onQuoteRecoverStatus(self, sender, topic, status, count):
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
        
    def onQuoteGetStatus(self, sender, status, msg) :
        """接收KGI QuoteCom API status event

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

if __name__ == '__main__' :
    help(__name__)