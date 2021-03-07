import config
from binance.client import Client
from binance.enums import *
from talib import EMA,SMA, ATR
import threading
import math
import csv
import itertools
import time
import datetime 
from scipy import stats
import numpy as np
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from IPython.display import clear_output

client = Client(config.API_KEY, config.API_SECRET, tld='com')
balanceBRL = client.get_asset_balance(asset='BRL')
TotalBRL = float(balanceBRL['free'])
symbolTicker = 'BTCBRL'
symbolPrice = 0
ma5 = 0
ma11 = 0
ma33 = 0
ma50 = 0
auxPrice = 0.0
flag = 0
trailing = 0
Percentual = float(0.90) # 0.20 seria 20% do balanço total

# conexão com os servidores do google
smtp_ssl_host = 'smtp.gmail.com'
smtp_ssl_port = 465
# username ou email para logar no servidor GMAIL
username = 'seu_email@gmail.com' #substitua pelo seu e-mail
password = 'sua_senha' #substitua pela sua senha
from_addr = 'seu_email@gmail.com' #substitua pelo seu e-mail
to_addrs = ['seu_email@gmail.com'] #substitua pelo seu e-mail

klines = client.get_historical_klines(symbolTicker, Client.KLINE_INTERVAL_15MINUTE, "15 hour ago UTC")
df = pd.DataFrame(klines)
df = df.iloc[:, 0:6]
df.columns = ['open time', 'open', 'high', 'low', 'close', 'volume']
dfclose = df['close']

ma5 = EMA(dfclose, timeperiod=5)
ma11 = EMA(dfclose, timeperiod=11) 
ma33 = EMA(dfclose, timeperiod=33)
ma50 = SMA(dfclose, timeperiod=50)

def qtd_formatada(n, r):
    if r <= 0:
        return str(int(n))
    s = str(float(n))
    if 'e' in s:
        s1 = s.split('e-')
        s2 = ''
        for i in range(int(s1[1]) - 1):
            if i == '.':
                continue
            s2 = s2 + '0'
        s3 = ''
        for i in  s1[0]:
            if i == '.':
                continue
            s3 = s3 + i
        s = '0.' + s2 + s3
        return s[:r+2]
    else:
        s = s.split('.')
        return s[0] + '.' + s[1][:r]

def orderStatus(orderToCkeck):
    try:
        status = client.get_order(
            symbol = symbolTicker,
            orderId = orderToCkeck.get('orderId')
        )
        return status.get('status')
    except Exception as e:
        print(e)
        return 7

def _tendencia_ma50_4hs_15minCandles_():
    x = []
    y = []
    sum = 0
    ma50_i = 0

    time.sleep(1)

    resp = False

    klines = client.get_historical_klines(symbolTicker, Client.KLINE_INTERVAL_15MINUTE, "18 hour ago UTC")

    if (len(klines) != 72):
        return False
    for i in range(56,72):
        for j in range(i-50,i):
            sum = sum + float(klines[j][4])
        ma50_i = round(sum / 50,2)
        sum = 0
        x.append(i)
        y.append(float(ma50_i))

    modelo = np.polyfit(x, y, 1)

    if (modelo[0]>0):
        resp = True
    return resp
    
while 1:

    time.sleep(3)
    sum = 0

    # BEGIN GET PRICE
    try:
        list_of_tickers = client.get_all_tickers()
    except Exception as e:
        with open("BTCBRL_scalper.txt", "a") as myfile:
            myfile.write(str(datetime.datetime.now()) +" - an exception occured - {}".format(e)+ " Oops 1 ! \n")
        client = Client(config.API_KEY, config.API_SECRET, tld='com')
        continue

    for tick_2 in list_of_tickers:
        if tick_2['symbol'] == symbolTicker:
            symbolPrice = float(tick_2['price'])
    # END GET PRICE  
   
     # Atualiza os dados históricos
    klines = client.get_historical_klines(symbolTicker, Client.KLINE_INTERVAL_15MINUTE, "15 hour ago UTC")
    df = pd.DataFrame(klines)
    df = df.iloc[:, 0:6]
    df.columns = ['open time', 'open', 'high', 'low', 'close', 'volume']
    dfhigh = df['high']
    dflow = df['low']
    dfclose = df['close']
    
    #if (ma50 == 0): continue  
    
    ma5 = EMA(dfclose, timeperiod=5).iloc[-1]
    ma11 = EMA(dfclose, timeperiod=11).iloc[-1] 
    ma33 = EMA(dfclose, timeperiod=33).iloc[-1]    
    ma50 = SMA(dfclose, timeperiod=50).iloc[-1]
    atrstop = ATR(dfhigh, dflow, dfclose, timeperiod=16).iloc[-1]
    
    balanceBTC = client.get_asset_balance(asset='BTC')
    TotalBTC = float(balanceBTC['free'])
    qtd = qtd_formatada (TotalBTC,8)     
    clear_output(wait=True)
    print("********** " + symbolTicker + " **********")
    print("      PreçoAtual: " + str(symbolPrice))   
    if ((str(round(ma5,2))) > (str(round(ma11,2)))):
        print("      EMA05 > EMA11 = Ok")
    else:
        print("      EMA05 > EMA11 = Não")
    if ((str(round(ma5,2))) > (str(round(ma33,2)))):
        print("      EMA05 > EMA33 = Ok")
    else:
        print("      EMA05 > EMA33 = Não")    
    if ((str(round(ma11,2))) > (str(round(ma33,2)))):
        print("      EMA11 > EMA33 = Ok")
    else:
        print("      EMA11 > EMA33 = Não")    
    print('      ATR: ', str(round(atrstop,2)))
    print('      Saldo: ', str(round(TotalBRL,2)))
    print('      Percentual: ', str(Percentual*100),'%')
    print('      Valor da compra: ',  'R$',str(round(TotalBRL*Percentual,2)),' (',str(round(TotalBRL/symbolPrice * Percentual,6)),')')      
    
    ordQtd = float(round(float((TotalBRL/symbolPrice * Percentual)),6))
    
    if flag == 0:
        print("      AGUARDANDO ENTRADA")
    if flag == 1:
        print("      COMPRADO: ", str(ordQtdVenda))            
    try:
        orders = client.get_open_orders(symbol=symbolTicker)
    except Exception as e:
        print(e)
        client = Client(config.API_KEY, config.API_SECRET, tld='com')
        continue

    if (len(orders) != 0):
        print("      Há ordem em aberto")
        time.sleep(10)
        continue 
        
    if (len(orders) == 0):
        trailing = 0 
        flag = 0
        time.sleep(5)
        
    if (not _tendencia_ma50_4hs_15minCandles_()):    
        print("      Tentência: Baixa")
        time.sleep(10)
        continue
    else:
        print("      Tendência: Alta")    
        if ((len(orders) == 0) & (ma5 > ma33) & (ma11 > ma33) & (ma5 > ma11) & (flag == 0)):        
            flag = 1
            ordQtdVenda = ordQtd
            print("      Compra-Cruzamento-Tendência")            
            order = client.order_market_buy(
                symbol=symbolTicker,
                quantity = float(round(float((TotalBRL/symbolPrice * Percentual)),6))
            )            
           
            # envia e-mail, somente texto
            message = MIMEText('Compra-Cruzamento-Tendência - BTCBRL')
            message['subject'] = 'Compra BTC'
            message['from'] = from_addr
            message['to'] = ', '.join(to_addrs)

            # conectaremos de forma segura usando SSL
            server = smtplib.SMTP_SSL(smtp_ssl_host, smtp_ssl_port)
            # para interagir com um servidor externo precisaremos
            # fazer login nele
            server.login(username, password)
            server.sendmail(from_addr, to_addrs, message.as_string())
            server.quit()
            
            time.sleep(10)

            #for tick_2 in list_of_tickers:
                #if tick_2['symbol'] == symbolTicker:
                    #symbolPrice = float(tick_2['price'])         
               
            sellOrder = client.create_order(
                symbol = symbolTicker,
                side = 'SELL',
                type = 'STOP_LOSS_LIMIT',            
                quantity = float(round(float((TotalBRL/symbolPrice * Percentual)),6)),
                price = float(round(float(symbolPrice-atrstop-310),0)),
                stopPrice = float(round(float(symbolPrice-atrstop-300),0)),            
                timeInForce = 'GTC'
            )  
            
            # envia e-mail, somente texto
            message = MIMEText('Venda-Stop Trailling - BTCBRL')
            message['subject'] = 'Venda BTC'
            message['from'] = from_addr
            message['to'] = ', '.join(to_addrs)               
            server = smtplib.SMTP_SSL(smtp_ssl_host, smtp_ssl_port)               
            server.login(username, password)
            server.sendmail(from_addr, to_addrs, message.as_string())
            server.quit()
            
        time.sleep(5)
