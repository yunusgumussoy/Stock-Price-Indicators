"""
Created on Tue May 28 14:31:07 2024

@author: Yunus
"""
""" 
This Python script aims to identify potential buy and sell signals for stocks listed on the Istanbul Stock Exchange (BIST) using an "Alpha Trend" indicator 
and then backtests these signals to determine their effectiveness.
"""

# !pip install git+https://github.com/rongardF/tvdatafeed tradingview-screener backtesting

import pandas as pd
import numpy as np
from tvDatafeed import TvDatafeed, Interval
from backtesting import Backtest, Strategy
from tradingview_screener import get_all_symbols
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

#Standart Moving Average
def sma(series, length):
    """
    Calculate the Simple Moving Average (SMA) for a given series.
    """
    return series.rolling(window=length).mean()

def mfi(high, low, close, volume, window=14):
    """
    Calculates the Money Flow Index (MFI).

    Args:
    high (pd.Series): High prices.
    low (pd.Series): Low prices.
    close (pd.Series): Closing prices.
    volume (pd.Series): Volume data.
    window (int): Window size for calculating MFI (default is 14).

    Returns:
    pd.Series: Money Flow Index values.
    """
    typical_price = (high + low + close) / 3
    money_flow = typical_price * volume
    positive_money_flow = (money_flow * (close > close.shift(1))).rolling(window=window).sum()
    negative_money_flow = (money_flow * (close < close.shift(1))).rolling(window=window).sum()
    money_ratio = positive_money_flow / negative_money_flow
    mfi = 100 - (100 / (1 + money_ratio))
    return mfi

def tr(high, low, close):
    """
    Calculates the True Range (TR).

    Args:
    high (pd.Series): High prices.
    low (pd.Series): Low prices.
    close (pd.Series): Closing prices.

    Returns:
    pd.Series: True Range values.
    """
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr

def Alpha_Trend(df, mult=1, n1=14):
    df['TR'] = tr(df['High'],df['Low'],df['Close'])
    df['ATR'] = sma(df['TR'], length=n1)
    df['mfi'] = mfi(df['High'],df['Low'],df['Close'], df['Volume'], n1)
    df['upT'] = df['Low'] - df['ATR'] * mult
    df['downT'] = df['High'] + df['ATR'] * mult
    df['AlphaTrend'] = 0.0
    alpha_trend_values = [0.0]

    for i in range(1, len(df)):
        if df['mfi'].iloc[i] >= 50:
            alpha_trend_values.append(max(df['upT'].iloc[i], alpha_trend_values[i-1]))
        else:
            alpha_trend_values.append(min(df['downT'].iloc[i], alpha_trend_values[i-1]))

    df['AlphaTrend'] = alpha_trend_values
    df['Entry']=False
    prev_signal = False
    for i in range(2, len(df)):
        if df.loc[i, 'AlphaTrend'] > df.loc[i-2, 'AlphaTrend']:
            df.loc[i, 'Entry'] = True
            prev_signal = True
        elif df.loc[i, 'AlphaTrend'] == df.loc[i-2, 'AlphaTrend'] and prev_signal:
            df.loc[i, 'Entry'] = True
        else:
            prev_signal = False
    df['Exit'] = df['Entry'] == False
    return df

tv = TvDatafeed()
Hisseler = get_all_symbols(market='turkey')
Hisseler = [symbol.replace('BIST:', '') for symbol in Hisseler]
Hisseler = sorted(Hisseler)

#Raporlama için kullanılacak başlıklar
Titles = ['Hisse Adı', 'Son Fiyat','Kazanma Oranı','Giriş Sinyali', 'Çıkış Sinyali']

df_signals = pd.DataFrame(columns=Titles)

#Backtest için gerekli class yapısı
class Strategy(Strategy):
    def init(self):
        pass
    def next(self):
        if self.data['Entry'] == True and not self.position:
            self.buy()

        elif self.data['Exit'] == True:
            self.position.close()

for i in range(0,len(Hisseler)):
    #print(Hisseler[i])
    try:
        mult=1
        n1=14
        data = tv.get_hist(symbol=Hisseler[i], exchange='BIST', interval=Interval.in_1_hour, n_bars=1000)
        data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        data = data.reset_index()
        AlphaTrend = Alpha_Trend(data,mult,n1)
        AlphaTrend['datetime'] = pd.to_datetime(AlphaTrend['datetime'])
        AlphaTrend.set_index('datetime', inplace=True)
        bt = Backtest(AlphaTrend, Strategy, cash=100000, commission=0.002)
        Stats = bt.run()
        Buy = False
        Sell = False
        Signals = AlphaTrend.tail(2)
        Signals = Signals.reset_index()
        Buy = Signals.loc[0, 'Entry'] == False and Signals.loc[1, 'Entry'] ==True
        Sell = Signals.loc[0, 'Exit'] == False and Signals.loc[1, 'Exit'] == True
        Last_Price = Signals.loc[1, 'Close']
        L1 = [Hisseler[i],Last_Price, round(Stats.loc['Win Rate [%]'], 2), str(Buy), str(Sell)]
        df_signals.loc[len(df_signals)] = L1
        print(L1)
    except:
        pass

df_True = df_signals[(df_signals['Giriş Sinyali'] == 'True')]
print(df_True.to_string())