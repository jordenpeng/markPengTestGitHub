#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import clr
import sys
import builtins

from System import UInt16
from TradeComFutPySample import TradecomPyFut
from time import sleep

"""
KGI期貨API的Python範例程式。

指令設定如下:

指令                    功能                  參數              說明及範例
----------------------------------------------------------------------------------------------
LOGIN                   登入                  ID,PW             Ex: LOGIN,A12345678,0000
LOGOUT                  登出                  無                EX: LOGOUT
EXIT                    關閉程式               無                EX: EXIT
GETACC                  登入帳號查詢                             EX: GETACC
DOWNLOAD                下載商品檔                               EX: DOWNLOAD
PBASE                   商品名稱查詢                             EX: PBASE,TXFG3
PINFO                   商品明細查詢                             EX: PINFO,TXFG3
FUTSYMBOL               期貨下單商品代碼查詢                      EX: FUTSYMBOL,TXF,202306
OPTSYMBOL               選擇權(單)下單商品代碼查詢                EX: OPTSYMBOL,TXO,202306,15600,C
OPTSYMBOL2              選擇權(複)下單商品代碼查詢                EX: OPTSYMBOL2,TXO,202307,15200,C,S,202307,15100,C,B
PBLIST                  取得所有商品列表                         EX: PBLIST
PBLISTDTL               取得某類別/名稱之商品列表                 EX: PBLISTDTL,TXF
PROLISTALL              取得期貨股票所有類別LIST                  EX: PROLISTALL
PROLISTDTL              取得股票商品資訊                         EX: PROLISTDTL,1704
ORDER                   國內期權下單                             EX: ORDER,O,F,F004000,9804474,TXFF3,B,SP,16500,F,1,A,AS
ORDERMDY                國內期權刪改單                           EX: ORDERMDY,C/M,F,F004000,9804474,TXFF3,B,SP,16500,F,1,A,AS,[WEBID],[CNT],[ORDER_NO]
COVER                   平倉查詢                                 EX: COVER,I,F004000,9804474
COVERD                  平倉明細查詢                             EX: COVERD,I,F004000,9804474
POSSUM                  最新部位彙總查詢(庫存彙總)                EX: POSSUM,I,F004000,9804474
POSDETAIL               部位明細(庫存明細) 查詢                   EX: POSDETAIL,I,F004000,9804474
FMARGIN                 權益數查詢                               EX: FMARGIN,I,F004000,9804474
ECURRENCY               台外幣互轉                               EX: ECURRENCY,F004000,9804474,1,5000
STRIKE_DETAIL           到期履約及無效履約查詢                    EX: STRIKE_DETAIL,I,F004000,9804474,1,20230611,20230711
RCDHIS                  歷史平倉查詢                             EX: RCDHIS,I,F004000,9804474,20230611,20230711
RECIPRO                 大小台互抵                               EX: RECIPRO,F004000,9804474,202306,B,1
HELP                    查詢API的說明                            EX: HELP
"""

host = 'itradetest.kgi.com.tw'  # 設定測試環境連結HOST
port = UInt16(8000) # 設定測試環境連結 PORT
sid = 'API'
q = None

def verion():
    """TradeStart 版本編號 V1.0.0
    V 1.0.0 初版範例程式
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
    q = TradecomPyFut(host, port, sid)
    while (True):
        sleep(1)
        command, args = getInput()
        if command == 'EXIT' or command == 'LOGOUT':
            # 登出
            q.logout()
            break
        elif command == "LOGIN":
            # 登入
            q.doLogin(args[1], args[2])
        elif command=="GETACC":
            res = q.getAccList()
            print('帳號查詢:')
            for v in dict(res).values():
                q.P001503(v)
        elif command=="DOWNLOAD":
            q.download()
        elif command=="PBASE":
            q.P001801(q.getProductBase(args[1]))
        elif command=="PINFO":
            q.P001802(q.getProductInfo(args[1]))
        elif command== "FUTSYMBOL":
            if len(args) >= 4:
                print(q.futSymbol(args[1], args[2]), args[3])
            else:
                print(q.futSymbol(args[1], args[2]))
        elif command== "OPTSYMBOL":
            print(q.optSymbol(args[1], args[2], args[3], args[4]))
        elif command== "OPTSYMBOL2":
            print(q.optSymbol2(args[1], args[2], args[3], args[4], args[5]
                              , args[6], args[7], args[8], args[9]))
        elif command== "PBLIST":
            res = q.pbList()
            for e in res:
                print(e)
        elif command== "PBLISTDTL":
            res = q.pbListDtl(args[1])
            for e in res:
                q.P001802(e)
        elif command== "PROLISTALL":
            res = q.proListAll()
            for e in res:
                print(e)
        elif command== "PROLISTDTL":
            res = q.proListDtl(args[1])
            for e in res:
                print(q.PIProList(e))
        elif command== "ORDER":
            q.order(args[1], args[2], args[3], args[4], args[5]
                    , args[6], args[7], args[8], args[9], args[10]
                    ,args[11], args[12])
        elif command== "ORDERMDY":
            q.order(args[1], args[2], args[3], args[4], args[5]
                    , args[6], args[7], args[8], args[9], args[10]
                    ,args[11], args[12], args[13], args[14], args[15])
        elif command== "COVER":
            res = q.cover(args[1], args[2], args[3])
            print("查詢成功" if res == 0 else "查詢失敗")
        elif command== "COVERD":
            res = q.coverDetail(args[1], args[2], args[3])
            print("查詢成功" if res == 0 else "查詢失敗")
        elif command== "POSSUM":
            res = q.posSum(args[1], args[2], args[3])
            print("查詢成功" if res == 0 else "查詢失敗")
        elif command== "POSDETAIL":
            res = q.posDetail(args[1], args[2], args[3])
            print("查詢成功" if res == 0 else "查詢失敗")
        elif command== "FMARGIN":
            res = q.fMargin(args[1], args[2], args[3])
            print("查詢成功" if res == 0 else "查詢失敗")
        elif command== "ECURRENCY":
            res = q.eCurrency(args[1], args[2], args[3], args[4])
            print(q.getMsg(res))
        elif command== "STRIKE_DETAIL":
            res = q.strikeDetail(args[1], args[2], args[3], args[4], args[5], args[6])
            print("查詢成功" if res == 0 else "查詢失敗")
        elif command== "RCDHIS":
            res = q.rcdHis(args[1], args[2], args[3], args[4], args[5])
            print("查詢成功" if res == 0 else "查詢失敗")
        elif command== "RECIPRO":
            res = q.reciprocate(args[1], args[2], args[3], args[4], args[5])
            print("查詢成功" if res == 0 else "查詢失敗")
        elif command== "HELP":
            help(TradecomPyFut)
        else:
            print("TradeStart 指令錯誤: ", command)
                     
    q.dispose()

if __name__ == '__main__' :
    #help(__name__)
    #help(QuotecomPyFut)
    verion()
    start() 
