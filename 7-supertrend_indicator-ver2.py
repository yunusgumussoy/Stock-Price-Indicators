# -*- coding: utf-8 -*-
"""
Created on Tue May 28 15:17:04 2024

@author: Yunus
"""

"""
This Python script fetches stock data from the Istanbul Stock Exchange (BIST) using the tvDatafeed library, 
applies the Supertrend indicator, and identifies stocks that generate entry and exit signals based on this indicator.
"""

# !pip install git+https://github.com/rongardF/tvdatafeed tradingview-screener backtesting

import pandas as pd
import numpy as np
from tvDatafeed import TvDatafeed, Interval
from backtesting import Backtest, Strategy
from tradingview_screener import get_all_symbols
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

#Exponential Moving Average
def ema(series, length):
    """
    Calculate the Exponential Moving Average (EMA) for a given series.
    """
    return series.ewm(span=length, adjust=False).mean()
#Relative Moving Average
def rma(series, length=None, offset=None, **kwargs):
    """
    Calculates the Relative Moving Average (RMA) of a given close price series.

    Parameters:
    - series: pandas Series containing price data.
    - length (int): The number of periods to consider. Default is 10.
    - offset (int): The offset from the current period. Default is None.
    - **kwargs: Additional keyword arguments.

    Returns:
    - pandas.Series: The Relative Moving Average (RMA) values.
    """
    # Validate Arguments
    length = int(length) if length and length > 0 else 10
    alpha = (1.0 / length) if length > 0 else 0.5

    # Calculate Result
    rma = series.ewm(alpha=alpha, min_periods=length).mean()
    return rma

#True Range
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

#Average True Range
def atr(high, low, close, period=14):
    """
    Calculates the Average True Range (ATR) using high, low, and close prices.

    Args:
    high (pd.Series or list): The high prices.
    low (pd.Series or list): The low prices.
    close (pd.Series or list): The close prices.
    period (int, optional): The period over which the ATR is calculated. Default is 14.

    Returns:
    pd.Series: The Average True Range (ATR) values.
    """
    # Calculate true range (TR)
    true_range = tr(high, low, close)
    atr = rma(true_range,period)
    return atr

def Supertrend(data,sens = 3,period = 14):
    df=data.copy()
    df['xATR'] = atr(data['High'], data['Low'], data['Close'], period)
    df['nLoss'] = sens * df['xATR']
    # Filling ATRTrailing Variable
    df['ATRTrailing'] = [0.0] + [np.nan for i in range(len(df) - 1)]

    for i in range(1, len(df)):
        if (df.loc[i, 'Close'] > df.loc[i - 1, 'ATRTrailing']) and (df.loc[i - 1, 'Close'] > df.loc[i - 1, 'ATRTrailing']):
            df.loc[i, 'ATRTrailing'] = max(df.loc[i - 1, 'ATRTrailing'],df.loc[i, 'Close']-df.loc[i,'nLoss'])

        elif (df.loc[i, 'Close'] < df.loc[i - 1, 'ATRTrailing']) and (df.loc[i - 1, 'Close'] < df.loc[i - 1, 'ATRTrailing']):
            df.loc[i, 'ATRTrailing'] = min(df.loc[i - 1, 'ATRTrailing'],df.loc[i, 'Close']+df.loc[i,'nLoss'])

        elif df.loc[i, 'Close'] > df.loc[i - 1, 'ATRTrailing']:
            df.loc[i, 'ATRTrailing']=df.loc[i, 'Close']-df.loc[i,'nLoss']
        else:
            df.loc[i, 'ATRTrailing']=df.loc[i, 'Close']+df.loc[i,'nLoss']

    # Calculating signals
    ema_ = ema(df['Close'], 1)
    df['Above'] = ema_ > (df['ATRTrailing'])
    df['Below'] = ema_ < (df['ATRTrailing'])
    df['Entry'] = (df['Close'] > df['ATRTrailing']) & (df['Above']==True)
    df['Exit'] = (df['Close'] < df['ATRTrailing']) & (df['Below']==True)
    return df


#Backtest için gerekli class yapısı
class Strategy(Strategy):
    def init(self):
        pass
    def next(self):
        if self.data['Entry'] == True and not self.position:
            self.buy()

        elif self.data['Exit'] == True:
            self.position.close()

tv = TvDatafeed()
Hisseler = get_all_symbols(market='turkey')
Hisseler = [symbol.replace('BIST:', '') for symbol in Hisseler]
Hisseler = sorted(Hisseler)

#Raporlama için kullanılacak başlıklar
Titles = ['Hisse Adı', 'Son Fiyat','Kazanma Oranı','Giriş Sinyali', 'Çıkış Sinyali']

df_signals = pd.DataFrame(columns=Titles)

for i in range(0,len(Hisseler)):
    #print(Hisseler[i])
    try:
        S=3
        ATR=14
        data = tv.get_hist(symbol=Hisseler[i], exchange='BIST', interval=Interval.in_1_hour, n_bars=500)
        data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        data = data.reset_index()
        Supert = Supertrend(data,S,ATR)
        Supert['datetime'] = pd.to_datetime(Supert['datetime'])
        Supert.set_index('datetime', inplace=True)
        bt = Backtest(Supert, Strategy, cash=100000, commission=0.002)
        Stats = bt.run()
        Buy = False
        Sell = False
        Signals = Supert.tail(2)
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
print(df_True)