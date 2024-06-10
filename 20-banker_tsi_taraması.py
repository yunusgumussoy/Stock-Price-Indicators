# -*- coding: utf-8 -*-
"""
Created on Fri Jun  7 14:22:28 2024

@author: Yunus
"""

# !pip install git+https://github.com/rongardF/tvdatafeed tradingview-screener

import numpy as np
import pandas as pd
from tvDatafeed import TvDatafeed, Interval
from tradingview_screener import get_all_symbols
import warnings
warnings.simplefilter(action='ignore')

def xsa(src, length, weight):
    sumf = np.zeros_like(src)
    ma = np.zeros_like(src)
    out = np.zeros_like(src)

    for i in range(length,len(src)):
        sumf[i] = np.nan_to_num(sumf[i - 1]) - np.nan_to_num(src[i - length]) + src[i]
        ma[i] = np.nan if np.isnan(src[i - length]) else sumf[i] / length
        out[i] = ma[i] if np.isnan(out[i - 1]) else (src[i] * weight + out[i - 1] * (length - weight)) / length

    return out

def ema(src, span):
    return src.ewm(span=span, adjust=False).mean()

def TSI_Signal(data, short_len, long_len, signal_len):
    df = data.copy()
    diff = df['close'].diff()
    abs_diff = diff.abs()

    short_ema_diff = ema(diff, short_len)
    long_ema_diff = ema(short_ema_diff, long_len)

    short_ema_abs_diff = ema(abs_diff, short_len)
    long_ema_abs_diff = ema(short_ema_abs_diff, long_len)

    df['tsi'] = 100 * (long_ema_diff / long_ema_abs_diff)
    df['tsi_signal'] = ema(df['tsi'], signal_len)

    df['Entry'] = df['tsi'] > df['tsi_signal']
    df['Exit'] = df['tsi'] < df['tsi_signal']
    return df

def Banker_Fund_Trend(data):
    df = data.copy()
    close = df['close']
    low = df['low']
    high = df['high']
    open_ = df['open']
    fundtrend =np.zeros_like(close)
    part_1 = (close - low.rolling(window=27).min()) / (high.rolling(window=27).max() - low.rolling(window=27).min()) * 100
    fundtrend = ((3 * xsa(part_1, 5, 1) - 2 * xsa(xsa(part_1, 5, 1), 3, 1) - 50) * 1.032 + 50)

    typ = (2 * close + high + low + open_) / 5
    lol = low.rolling(window=34).min()
    hoh = high.rolling(window=34).max()

    bullbearline = ema((typ - lol) / (hoh - lol) * 100, 13)
    bankerentry = (fundtrend > bullbearline) & (bullbearline < 25)
    df['bankerentry'] = bankerentry
    df['Entry1'] = df['bankerentry'] == 1
    df['Entry2'] = df['bankerentry'].shift(1) == 1
    df['Entry3'] = df['bankerentry'].shift(2) == 1
    return df


tv = TvDatafeed()
Hisseler = get_all_symbols(market='turkey')
Hisseler = [symbol.replace('BIST:', '') for symbol in Hisseler]
Hisseler = sorted(Hisseler)


#Raporlama için kullanılacak başlıklar
Titles = ['Hisse Adı', 'Son Fiyat' , 'Giriş Sinyali']
df_signals = pd.DataFrame(columns=Titles)

for hisse in Hisseler:
    try:
        data = tv.get_hist(symbol=hisse, exchange='BIST', interval=Interval.in_daily, n_bars=200)
        data = data.reset_index()
        Banker = Banker_Fund_Trend(data)
        Tsi = TSI_Signal(data,5,25,14)
        data['Entry'] = (Banker['Entry1'] & Tsi['Entry'])
        Signals = data.tail(2)
        Signals = Signals.reset_index()
        Entry = (Signals.loc[0, 'Entry'] == False) & (Signals.loc[1, 'Entry'] == True)
        Last_Price = Signals.loc[1, 'close']
        L1 = [hisse ,Last_Price, Entry]
        df_signals.loc[len(df_signals)] = L1
        print(L1)
    except:
        pass

df_True = df_signals[(df_signals['Giriş Sinyali'] == True)]
print(df_True)