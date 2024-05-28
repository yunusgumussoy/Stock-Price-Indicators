# -*- coding: utf-8 -*-
"""
Created on Tue May 28 16:19:52 2024

@author: Yunus
"""

# !pip install pandas_ta
# !pip install mplcyberpunk
# !pip install git+https://github.com/rongardF/tvdatafeed
# !pip install tradingview-screener
# !pip install backtesting


import pandas as pd
import pandas_ta as ta
import numpy as np
from tvDatafeed import TvDatafeed, Interval
from backtesting import Backtest, Strategy
from tradingview_screener import get_all_symbols
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def WaveTrend(data, n1=10, n2=21):
    df = data.copy()
    df['ap'] = ta.hlc3(df['High'], df['Low'], df['Close'])
    df['esa'] = ta.ema(df['ap'], length=n1)
    df['d'] = ta.ema((df['ap'] - df['esa']).abs(), length=n1)
    df['ci'] = (df['ap'] - df['esa']) / (0.015 * df['d'])
    df['tci1'] = ta.ema(df['ci'], length=n2)
    df['tci2'] = ta.ema(df['tci1'], length=n2)
    df['Entry'] = (df['tci1'] > df['tci2'])
    df['Exit'] = (df['tci1'] < df['tci2'])
    return df

tv = TvDatafeed()
Hisseler = get_all_symbols(market='turkey')
Hisseler = [symbol.replace('BIST:', '') for symbol in Hisseler]
Hisseler = sorted(Hisseler)

# Raporlama için kullanılacak başlıklar
Titles = ['Hisse Adı', 'Son Fiyat', 'Kazanma Oranı', 'Giriş Sinyali', 'Çıkış Sinyali']
df_signals = pd.DataFrame(columns=Titles)

# Backtest için gerekli class yapısı
class WaveTrendStrategy(Strategy):
    def init(self):
        pass
    
    def next(self):
        if self.data['Entry'] and not self.position:
            self.buy()
        elif self.data['Exit'] and self.position:
            self.position.close()

for symbol in Hisseler:
    try:
        data = tv.get_hist(symbol=symbol, exchange='BIST', interval=Interval.in_1_hour, n_bars=1000)
        data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        data = data.reset_index()
        
        WT_Oscillator = WaveTrend(data)
        WT_Oscillator['datetime'] = pd.to_datetime(WT_Oscillator['datetime'])
        WT_Oscillator.set_index('datetime', inplace=True)
        
        bt = Backtest(WT_Oscillator, WaveTrendStrategy, cash=100000, commission=0.002)
        Stats = bt.run()
        
        Signals = WT_Oscillator.tail(2).reset_index()
        Buy = Signals.loc[0, 'Entry'] == False and Signals.loc[1, 'Entry'] == True
        Sell = Signals.loc[0, 'Exit'] == False and Signals.loc[1, 'Exit'] == True
        Last_Price = Signals.loc[1, 'Close']
        
        L1 = [symbol, Last_Price, round(Stats.loc['Win Rate [%]'], 2), Buy, Sell]
        df_signals.loc[len(df_signals)] = L1
        
        print(L1)
    except Exception as e:
        print(f"Error processing {symbol}: {e}")

# Filter and print all stocks that have an entry signal
df_True = df_signals[df_signals['Giriş Sinyali']]
print(df_True)

"""
# Optionally save the results to a CSV file
df_True.to_csv('entry_signals.csv', index=False)
"""