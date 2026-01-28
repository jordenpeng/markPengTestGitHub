#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import clr

clr.AddReference("Package")      #必要引用dll
clr.AddReference("PushClient")   #必要引用dll
clr.AddReference("QuoteCom")     #必要引用dll

from QuoteComFutPySample import QuotecomPyFut
from time import sleep
"""
KGI期貨API的Python範例程式。

指令設定如下:

指令                    功能                         參數                說明及範例
------------------------------------------------------------------------------------------------------------------
LOGIN                   登入                         ID,PW               Ex: LOGIN,A12345678,0000 
LOGOUT                  登出                         無
EXIT                    關閉程式                      無  
SUB                     訂閱報價                      商品代碼             EX: SUB,TXFF3
UNSUB                   解除訂閱報價                  商品代碼             EX: UNSUB,TXFF3
DOWNLOAD                下載可註冊商品基本資料         無   
LASTPRICE               查詢商品最後價格              商品代碼             EX: LASTPRICE,TXFF3
ASKTAIFEX               查詢商品盤別                  商品代碼             EX: ASKTAIFEX,TXFF3
CLOSEPRICE              查詢商品收盤資料              無                   EX: CLOSEPRICE
PBLIST                  查詢商品列表-市場別       F代表期貨，O代表選擇權     EX: PBLIST,F
PBase                   查詢單一商品基本資料           商品代碼             EX: PBase,TXFF3
RECOVER                 國內期權商品行情回補      商品代碼,開始,結束         EX: RECOVER,TXFF3,0900,0910
TFLIST                  國內期權商品查詢-下午盤(交易-XML下載)               EX: TFLIST,F
HELP

"""

host = 'iquotetest.kgi.com.tw' # 設定測試環境連結HOST
port = 8000 # 設定測試環境連結 PORT
token = 'b6eb'
sid = 'API'
q = None

def verion():
    """QuoteStart 版本編號 V1.0.1
    V 1.0.0 初版範例程式
    V 1.0.1 加入HELP提供FUNCTION的說明
    
    """
    help(verion)

def getInput():
    """讀取使用者的輸入資訊，並依規格讀取Command及參數。

    Returns:
        str: Command
        array: parameters
    """
    inputstr = input('#### 請輸入指令:')
    while (len(inputstr)<4):   
        inputstr = input('*** 請輸入指令:')
    args = inputstr.split(',')
    command = args[0].upper()
    return command, args

def start():
    """程式的控制區，負責分派使用者的指令
    """
    global q
    q =  QuotecomPyFut(host, port, sid, token)
    while (True):
        sleep(1)
        command, args = getInput()
        if command == 'EXIT' or command == 'LOGOUT':
            # 登出
            q.logout()
            break
        elif command=="LOGIN":
            # 登入
            q.doLogin(args[1], args[2])
        elif command=="SUB":
            # 訂閱報價     
            q.doSub(args[1])
        elif command=="UNSUB": 
            # 解除訂閱報價     
            q.doUnSub(args[1])
        elif command=="LASTPRICE":
            # 查詢商品最後價格         
            q.doLastPrice(args[1])
        elif command=="CLOSEPRICE": 
            # 查詢商品收盤資料        
            q.doClosePrice()
        elif command=="ASKTAIFEX": 
            # 查詢商品盤別      
            q.doAsk(args[1])
        elif command=="DOWNLOAD":
            # 下載可註冊商品基本資料    
            q.doDown()
        elif command=="PBLIST": 
            # 查詢商品列表-簡碼
            q.doPBList(args[1]) 
        elif command=="PBase": 
            # 查詢商品列表-簡碼
            q.doPBase(args[1])
        elif command=="RECOVER": 
            # 查詢商品列表-簡碼
            q.doRecover(args[1])
        elif command=="TFLIST": 
            # 查詢商品列表-簡碼
            q.doGetTFList(args[1])
        elif command=="HELP": 
            help(QuotecomPyFut)
        else:
            print("QuoteStart 指令錯誤: ", command)    
    q.dispose()

if __name__ == '__main__' :
    #help(__name__)
    #help(QuotecomPyFut)
    verion()
    start() 
