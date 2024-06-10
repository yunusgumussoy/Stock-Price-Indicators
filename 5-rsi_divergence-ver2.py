"""
Created on Tue May 28 15:07:49 2024

@author: Yunus
"""
"""
This Python script integrates a strategy for detecting RSI divergences, 
then backtests the strategy and finally identifies buy and sell signals for stocks listed on the Istanbul Stock Exchange (BIST).
"""

# !pip install git+https://github.com/rongardF/tvdatafeed tradingview-screener backtesting

import warnings
import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
from scipy import stats
from urllib import request
from tvDatafeed import TvDatafeed, Interval
from backtesting import Backtest, Strategy
from tradingview_screener import get_all_symbols
warnings.simplefilter(action='ignore', category=FutureWarning)

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

#Relative Strength Index
def rsi(series, length=14):
    """
    Calculate the Relative Strength Index (RSI) for a given series.

    Parameters:
    - series: pandas Series containing price data.
    - length: Length of the RSI period (default is 14).
    - scalar: Scalar factor to adjust RSI values (default is 100).
    - drift: Number of periods for price changes (default is 1).

    Returns:
    - pandas Series containing RSI values calculated based on the input parameters.
    """
    # Calculate price changes
    scalar=100
    drift=1
    negative = series.diff(drift)
    positive = negative.copy()

    # Make negatives 0 for the positive series
    positive[positive < 0] = 0
    # Make positives 0 for the negative series
    negative[negative > 0] = 0

    # Calculate average gains and losses
    positive_avg = rma(positive, length=length)
    negative_avg = rma(negative, length=length)

    # Calculate RSI
    rsi = scalar * positive_avg / (positive_avg + negative_avg.abs())
    return rsi


def rsi_divergence(data, window, order):
    df = data.copy()
    #calculating RSI with talib
    df['RSI']=rsi(df['Close'], window)
    hh_pairs=argrelextrema(df['Close'].values, comparator=np.greater, order=order)[0]
    hh_pairs=[hh_pairs[i:i+2] for i in range(len(hh_pairs)-1)]
    ll_pairs=argrelextrema(df['Close'].values, comparator=np.less, order=order)[0]
    ll_pairs=[ll_pairs[i:i+2] for i in range(len(ll_pairs)-1)]

    bear_div=[]
    bull_div=[]

    for p in hh_pairs:
        x_price=p
        y_price=[df['Close'].iloc[p[0]], df['Close'].iloc[p[1]]]
        slope_price=stats.linregress(x_price, y_price).slope
        x_rsi=p
        y_rsi=[df['RSI'].iloc[p[0]], df['RSI'].iloc[p[1]]]
        slope_rsi=stats.linregress(x_rsi, y_rsi).slope

        if slope_price>0:
            if np.sign(slope_price)!=np.sign(slope_rsi):
                bear_div.append(p)

    for p in ll_pairs:
        x_price=p
        y_price=[df['Close'].iloc[p[0]], df['Close'].iloc[p[1]]]
        slope_price=stats.linregress(x_price, y_price).slope
        x_rsi=p
        y_rsi=[df['RSI'].iloc[p[0]], df['RSI'].iloc[p[1]]]
        slope_rsi=stats.linregress(x_rsi, y_rsi).slope

        if slope_price<0:
            if np.sign(slope_price)!=np.sign(slope_rsi):
                bull_div.append(p)

    bear_points=[df.index[a[1]] for a in bear_div]
    bull_points=[df.index[a[1]] for a in bull_div]
    pos=[]

    for idx in df.index:
        if idx in bear_points:
            pos.append(-1)
        elif idx in bull_points:
            pos.append(1)
        else:
            pos.append(0)

    df['position']=pos
    df['position']=df['position'].replace(0, method='ffill')
    return df


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
Titles = ['Hisse Adı', 'Son Fiyat', 'Kazanma Oranı','Giriş Sinyali', 'Çıkış Sinyali']

df_signals = pd.DataFrame(columns=Titles)

for i in range(0,len(Hisseler)):
    try:
        data = tv.get_hist(symbol=Hisseler[i], exchange='BIST', interval=Interval.in_1_hour, n_bars=500)
        data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        data = data.reset_index()
        RSIDiv=rsi_divergence(data,14,1)
        RSIDiv['datetime'] = pd.to_datetime(RSIDiv['datetime'])  # Assuming 'Date' is the name of your datetime column
        RSIDiv.set_index('datetime', inplace=True)
        RSIDiv['Entry'] = (RSIDiv['position'] == 1)
        RSIDiv['Exit'] = (RSIDiv['position'] == -1)
        bt = Backtest(RSIDiv, Strategy, cash=100000, commission=0.002)
        Stats = bt.run()
        Buy=False
        Sell=False
        Signals = RSIDiv.tail(2)
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