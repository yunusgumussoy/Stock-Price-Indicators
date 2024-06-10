# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 19:16:17 2024

@author: Yunus
"""

# !pip install git+https://github.com/rongardF/tvdatafeed tradingview-screener

import numpy as np
import pandas as pd
from tvDatafeed import TvDatafeed, Interval
from tradingview_screener import get_all_symbols
import logging
import warnings

# Suppress warnings
warnings.simplefilter(action='ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
WINDOW_XSA = 5
WINDOW_FUND_TREND = 27
WINDOW_EMA = 13
WINDOW_BULLBEAR = 34
MARKET = 'turkey'
EXCHANGE = 'BIST'
INTERVAL = Interval.in_daily
N_BARS = 100

def xsa(src, length, weight):
    sumf = np.zeros_like(src)
    ma = np.zeros_like(src)
    out = np.zeros_like(src)

    for i in range(length, len(src)):
        sumf[i] = np.nan_to_num(sumf[i - 1]) - np.nan_to_num(src[i - length]) + src[i]
        ma[i] = np.nan if np.isnan(src[i - length]) else sumf[i] / length
        out[i] = ma[i] if np.isnan(out[i - 1]) else (src[i] * weight + out[i - 1] * (length - weight)) / length

    return out

def ema(src, span):
    return src.ewm(span=span, adjust=False).mean()

def banker_fund_trend(data):
    df = data.copy()
    close = df['Close']
    low = df['Low']
    high = df['High']
    open_ = df['Open']

    part_1 = (close - low.rolling(window=WINDOW_FUND_TREND).min()) / (high.rolling(window=WINDOW_FUND_TREND).max() - low.rolling(window=WINDOW_FUND_TREND).min()) * 100
    fundtrend = ((3 * xsa(part_1, WINDOW_XSA, 1) - 2 * xsa(xsa(part_1, WINDOW_XSA, 1), 3, 1) - 50) * 1.032 + 50)

    typ = (2 * close + high + low + open_) / 5
    lol = low.rolling(window=WINDOW_BULLBEAR).min()
    hoh = high.rolling(window=WINDOW_BULLBEAR).max()

    bullbearline = ema((typ - lol) / (hoh - lol) * 100, WINDOW_EMA)
    bankerentry = (fundtrend > bullbearline) & (bullbearline < 25)

    df['FundTrend'] = fundtrend
    df['BullBearLine'] = bullbearline
    df['BankerEntry'] = bankerentry.astype(int)  # Convert to integer

    return df

def fetch_and_process_data(symbol, tv):
    data = tv.get_hist(symbol=symbol, exchange=EXCHANGE, interval=INTERVAL, n_bars=N_BARS)
    if data is not None and not data.empty:
        data = data.reset_index()
        data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        processed_data = banker_fund_trend(data)
        return processed_data
    return None

def main():
    tv = TvDatafeed()
    symbols = get_all_symbols(market=MARKET)
    symbols = [symbol.replace('BIST:', '') for symbol in symbols]
    symbols = sorted(symbols)

    titles = ['Hisse Adı', 'Son Fiyat', 'Dip Sinyali']
    df_signals = pd.DataFrame(columns=titles)

    for symbol in symbols:
        try:
            data = fetch_and_process_data(symbol, tv)
            if data is not None:
                signals = data.tail(2).reset_index()
                entry = (signals.loc[0, 'BankerEntry'] == 0) & (signals.loc[1, 'BankerEntry'] == 1)
                last_price = signals.loc[1, 'Close']
                signal_row = [symbol, last_price, entry]
                df_signals.loc[len(df_signals)] = signal_row
                logging.info(f'Processed {symbol}: {signal_row}')
        except Exception as e:
            logging.error(f'Error processing {symbol}: {e}')

    df_true = df_signals[df_signals['Dip Sinyali'] == True]
    logging.info(f'Dip signals:\n{df_true}')
    print(df_true)

if __name__ == "__main__":
    main()
