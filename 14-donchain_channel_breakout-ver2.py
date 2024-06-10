# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 18:57:51 2024

@author: Yunus
"""

import pandas as pd
import numpy as np
from tvDatafeed import TvDatafeed, Interval
from backtesting import Backtest, Strategy
from tradingview_screener import get_all_symbols
import logging
import warnings

# Suppress future warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
WINDOW = 20
CASH = 100000
COMMISSION = 0.002
N_BARS = 1000
MARKET = 'turkey'
EXCHANGE = 'BIST'
INTERVAL = Interval.in_1_hour

# Function to compute Donchian Channel Breakout
def donchian_channel_breakout(data, window):
    df = data.copy()
    df['Upper Channel'] = df['High'].rolling(window=window).max()
    df['Lower Channel'] = df['Low'].rolling(window=window).min()
    df['Entry'] = df['Close'] > df['Upper Channel'].shift(1)
    df['Exit'] = df['Close'] < df['Lower Channel'].shift(1)
    return df

# Custom Strategy for Backtesting
class DonchianChannelStrategy(Strategy):
    def init(self):
        pass

    def next(self):
        if self.data['Entry']:
            self.buy()
        elif self.data['Exit']:
            self.position.close()

# Function to fetch and process data
def fetch_and_process_data(symbol, tv, window, interval, n_bars):
    data = tv.get_hist(symbol=symbol, exchange=EXCHANGE, interval=interval, n_bars=n_bars)
    if data is not None and not data.empty:
        data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        data.reset_index(inplace=True)
        data['datetime'] = pd.to_datetime(data['datetime'])
        data.set_index('datetime', inplace=True)
        processed_data = donchian_channel_breakout(data, window)
        return processed_data
    return None

# Main execution
def main():
    tv = TvDatafeed()
    symbols = get_all_symbols(market=MARKET)
    symbols = [symbol.replace('BIST:', '') for symbol in symbols]
    symbols = sorted(symbols)

    titles = ['Hisse Adı', 'Son Fiyat', 'Kazanma Oranı', 'Giriş Sinyali', 'Çıkış Sinyali']
    df_signals = pd.DataFrame(columns=titles)

    for symbol in symbols:
        try:
            data = fetch_and_process_data(symbol, tv, WINDOW, INTERVAL, N_BARS)
            if data is not None:
                bt = Backtest(data, DonchianChannelStrategy, cash=CASH, commission=COMMISSION)
                stats = bt.run()
                signals = data.tail(2).reset_index()
                buy_signal = signals.loc[0, 'Entry'] == False and signals.loc[1, 'Entry'] == True
                sell_signal = signals.loc[0, 'Exit'] == False and signals.loc[1, 'Exit'] == True
                last_price = signals.loc[1, 'Close']
                signal_row = [symbol, last_price, round(stats.loc['Win Rate [%]'], 2), str(buy_signal), str(sell_signal)]
                df_signals.loc[len(df_signals)] = signal_row
                logging.info(f'Processed {symbol}: {signal_row}')
        except Exception as e:
            logging.error(f'Error processing {symbol}: {e}')
    
    df_true = df_signals[df_signals['Giriş Sinyali'] == 'True']
    logging.info(f'Buy signals:\n{df_true}')
    print(df_true)

if __name__ == "__main__":
    main()
