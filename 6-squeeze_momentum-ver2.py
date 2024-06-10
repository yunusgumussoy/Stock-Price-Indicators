# -*- coding: utf-8 -*-
"""
Created on Tue May 28 15:10:01 2024

@author: Yunus
"""
"""
This Python script fetches stock data from the Istanbul Stock Exchange (BIST) using the tvDatafeed library, 
applies the Squeeze Momentum Indicator, and identifies stocks that have entered a squeeze condition.
"""

# !pip install git+https://github.com/rongardF/tvdatafeed tradingview-screener

import pandas as pd
import numpy as np
from tvDatafeed import TvDatafeed, Interval
from tradingview_screener import get_all_symbols
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


#Standart Moving Average
def sma(series, length):
    """
    Calculate the Simple Moving Average (SMA) for a given series.
    """
    return series.rolling(window=length).mean()

#Standard Deviations
def stdev(series, length):
    """
    Calculates the rolling standard deviation of a series.

    Args:
    series (pd.Series): The input series for which the rolling standard deviation is calculated.
    length (int): The window length for the rolling standard deviation calculation.

    Returns:
    pd.Series: The rolling standard deviation values.
    """
    deviation = series.rolling(window=length).std()
    return deviation

def SqueezeMomentum(data,mult=2,length=20,multKC=1.5,lengthKC=20):
    df=data.copy()
    df['basis']=sma(data['Close'],length)
    df['dev']=multKC*stdev(data['Close'],length)
    df['upperBB']=df['basis']+df['dev']
    df['lowerBB']=df['basis']-df['dev']
    df['ma']=sma(df['Close'],lengthKC)
    df['tr0'] = abs(df["High"] - df["Low"])
    df['tr1'] = abs(df["High"] - df["Close"].shift())
    df['tr2'] = abs(df["Low"] - df["Close"].shift())
    df['range'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
    df['rangema']=sma(df['range'],lengthKC)
    df['upperKC']=df['ma']+df['rangema']*multKC
    df['lowerKC']=df['ma']-df['rangema']*multKC
    df['Squeeze'] = (df['lowerBB'] < df['lowerKC']) & (df['upperBB'] > df['upperKC'])
    return df

tv = TvDatafeed()
Hisseler = get_all_symbols(market='turkey')
Hisseler = [symbol.replace('BIST:', '') for symbol in Hisseler]
Hisseler = sorted(Hisseler)

#Raporlama için kullanılacak başlıklar
Titles = ['Hisse Adı', 'Son Fiyat', 'Squeeze']
df_signals = pd.DataFrame(columns=Titles)

for i in range(0,len(Hisseler)):
    #print(Hisseler[i])
    try:
        data = tv.get_hist(symbol=Hisseler[i], exchange='BIST', interval=Interval.in_1_hour, n_bars=100)
        data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        data = data.reset_index()
        Squeeze = SqueezeMomentum(data,2,20,1.5,20)
        Squeeze['datetime'] = pd.to_datetime(Squeeze['datetime'])
        Squeeze.set_index('datetime', inplace=True)
        Signals = Squeeze.tail(2)
        Signals = Signals.reset_index()
        Sq_Signal = Signals.loc[0, 'Squeeze'] == False and Signals.loc[1, 'Squeeze'] ==True

        Last_Price = Signals.loc[1, 'Close']
        L1 = [Hisseler[i],Last_Price, Sq_Signal]
        df_signals.loc[len(df_signals)] = L1
        print(L1)
    except:
        pass

df_True = df_signals[(df_signals['Squeeze'] == True)]
print(df_True)