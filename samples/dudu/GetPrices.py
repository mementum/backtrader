import yfinance as yf
import sys
import pandas as pd
import time
import datetime



'''
tickerStrings = ['DNA', 'ENTX', 'EDIT', 'CLGN', 'EYES', 'EXAS', 'MITC', 'MDWD', 'CHEK', 
				'AQB','RCEL', 'NNOX','ENLV','ASML', 'ALCRB.PA', 'NXFR.TA', 'MTLF.TA', 'BMLK.TA', 
				'NXGN.TA', 'PHGE.TA',  'ICCM.TA', 'CRTX', 'SPCE', 'SEDG', 'APLP.TA', 'AQUA.TA', 'PLX.TA', 'ENLT.TA', 'ECPA.TA', 'FVRR', 'SLGN.TA', 'UAL', 'SRNG', 'PHGE', 'BVXV',
                'MMM','ATVI','GOOG','AMZN','AAPL','AVH.AX','BRK-B','BYND','CHKP','CTMX','EA','EQIX','FB','GE','GHDX','GILD','GSK','INTC','JUNO','KITE','LGND','MLNX',
                'MU','NTGN','NFLX','ORBK','QCOM','RWLK','SGMO','TTWO','TSLA','TEVA','UPS','URGN','ENLV.TA','TEVA.TA','PSTI.TA']
'''
tickerStrings = ['ICCM.TA']

filePath = 'c:/prices/ICCM.TA.csv'
#open(filePath, 'w').close()

original_stdout = sys.stdout # Save a reference to the original standard output

df_list = list()

first = True
for ticker in tickerStrings:
    df_list.clear()
    filePath =  'c:/prices/' + ticker + '.csv'
    multiplier = 1.0
    if ticker.find(".TA") > -1:
        multiplier = 0.01
    
    try:
        data = yf.download(ticker, group_by="Ticker", start="2016-01-01", end="2021-11-30", interval="1d")
        df_list.append(data)
        dataIndex = 0

        with open(filePath, 'w') as f:
            sys.stdout = f # Change the standard output to the file we created.

            print('Datetime,Open,High,Low,Close,Adj Close,Volume')
            for dataFrame in df_list:
                
                for dataIndex in range(0,len(dataFrame['Open'])-1):
                    startTime = dataFrame['Open'].index[dataIndex] + datetime.timedelta(hours = 9)
                    for minute in range(1,25):
                        startTime = startTime + datetime.timedelta(minutes = 20)
                        print("%s,%s,%s,%s,%s,%s,%s"%(startTime, 
                                                      round(dataFrame['Open'][dataIndex]*multiplier,2), 
                                                      round(dataFrame['High'][dataIndex]*multiplier,2),
                                                      round(dataFrame['Low'][dataIndex]*multiplier,2), 
                                                      round(dataFrame['Close'][dataIndex]*multiplier,2), 
                                                      round(dataFrame['Close'][dataIndex]*multiplier,2),
                                                      round(dataFrame['Volume'][dataIndex]*multiplier,2)
                                                      ))
                
    except:
        print("Error with: ", ticker)