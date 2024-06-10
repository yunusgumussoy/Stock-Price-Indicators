# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 13:36:03 2024

@author: Yunus
"""


# !pip install tradingview_screener
import pandas as pd
from tradingview_screener import Query, Column

def Tarama_1():
    """Bu Tarama 2 Saatlik Periyotta
    Açılış Fiyatı Güncel Fiyatın Altında
    RSI 30 ila 40 arasında
    MACD Yukarı keser MACD Sinyal
    MACD Sinyal < 0
    Taramasıdır.
    #RSI 30 seviyesinin üzerinde al verirken Macd 0 'ın altında al veren tarama
    """
    Tarama = (Query().set_markets('crypto')
                .select('name', 'change','close','volume','Perf.W')
                .where(
                    Column('exchange')=='BINANCE',
                    Column('RSI|120').between(30,40),
                    Column('change|120').between(0,5.0),
                    Column('MACD.macd|120').crosses_above(Column('MACD.signal|120')),
                    Column('MACD.signal|120') < 0
                    )
        .get_scanner_data())[1]

    return Tarama

def Tarama_2():
    """Bu Tarama 2 Saatlik Periyotta
    Haftalık Performansı < 15%
    Göreceli Hacim > 1.5
    Üstel Haraketli Ortalama 5 < Fiyat
    Üstel Haraketli Ortalama 20 < Üstel Haraketli Ortalama 5
    Üstel Haraketli Ortalama 50 < Üstel Haraketli Ortalama 20
    MACD > MACD Sinyal
    Parabolik SAR Aşağı Keser Fiyat
    Emtia Kanal Endeksi >=90
    Taramasıdır.
    #Alternatif Düşeni kıran taraması olarak da bilinir.
    """
    Tarama = (Query().set_markets('crypto')
                .select('name', 'change','close','volume','Perf.W')
                .where(
                    Column('exchange')=='BINANCE',
                    Column('Perf.W') < 15,
                    Column('relative_volume_10d_calc|120') > 1.5,
                    Column('change|120') < 5.0,
                    Column('EMA5|120') < Column('close|120'),
                    Column('EMA20|120') < Column('EMA5|120'),
                    Column('EMA50|120') < Column('EMA20|120'),
                    Column('MACD.macd|120') > Column('MACD.signal|120'),
                    Column('P.SAR|120').crosses_below(Column('close|120')),
                    Column('CCI20|120') >= 90.0
                    )
        .get_scanner_data())[1]

    return Tarama

def Tarama_3():
    """Bu Tarama 2 Saatlik Periyotta
    Haftalık Performansı < 15%
    Göreceli Hacim > 1.0
    Fiyat >= Basit Haraketli Ortalama 5
    Basit Haraketli Ortalama 10 > Basit Haraketli Ortalama20
    Macd Yukarı Keser MACD Sinyali
    Taramasıdır.
    #Swint Trade 2 nolu stratejisine uyan tarama olarak da bilinir.
    """
    Tarama = (Query().set_markets('crypto')
                .select('name', 'change','close','volume','Perf.W')
                .where(
                    Column('exchange')=='BINANCE',
                    Column('Perf.W') < 15.0,
                    Column('change|120') < 5.0,
                    Column('relative_volume_10d_calc|120')>1.0,
                    Column('close|120') >= Column('SMA5|120'),
                    Column('SMA10|120') >Column('SMA20|120'),
                    Column('MACD.macd|120').crosses_above(Column('MACD.signal|120'))
                    )
        .get_scanner_data())[1]

    return Tarama

def Tarama_4():
    """Bu Tarama 2 Saatlik Periyotta
    Haftalık Performansı < 15%
    Göreceli Hacim > 1.0
    Macd Yukarı Keser Macd Sinyal
    Stokastik RSI Hızlı Yukarı keser Stokastik RSI Yavaş
    Taramasıdır.
    #Macd ve Stokastik RSI hanüz al vermiş olan tarama olarak da bilinir.
    """
    Tarama = (Query().set_markets('crypto')
                .select('name', 'change','close','volume','Perf.W')
                .where(
                    Column('exchange')=='BINANCE',
                    Column('Perf.W') < 15.0,
                    Column('change|120') < 5.0,
                    Column('relative_volume_10d_calc|120')>1.0,
                    Column('MACD.macd|120').crosses_above(Column('MACD.signal|120')),
                    Column('Stoch.RSI.K|120').crosses_above(Column('Stoch.RSI.D|120'))
                    )
        .get_scanner_data())[1]

    return Tarama

def Tarama_5():
    """Bu Tarama 2 Saatlik Periyotta
    Fiyat Yukarı Keser Hull Haraketl Ortalama
    Ortalama Gerçek Aralık 0 ila 10 arasında
    Basit Haraketli Ortalama Aşağı Keser Fiyat
    Taramasıdır.
    #Richards Dennis Kaplumbağası hull9 a göre olan taramalrak da bilinir.
    """
    Tarama = (Query().set_markets('crypto')
                .select('name', 'change','close','volume','Perf.W')
                .where(
                    Column('exchange')=='BINANCE',
                    Column('close|120').crosses_above('HullMA9|120'),
                    Column('change|120') < 5.0,
                    Column('ATR|120').between(0,10),
                    Column('SMA20|120').crosses_below('close|120'),
                    )
        .get_scanner_data())[1]

    return Tarama

def Tarama_6():
    """Bu Tarama 2 Saatlik Periyotta
    RSI14 > 55
    Üstel Hareketli Ortalama 5 < Kapanış Fiyatı
    Üstel Hareketli Ortalama 20 < Basit Hareketli Ortalama 5
    Üstel Hareketli Ortalama 50 < Basit Hareketli Ortalama 20
    Emtia Kanal Endeksi CCI(20)  Yukarı Keser 100
    Hacim x Fiyat > 2.5 Milyon
    Taramasıdır.
    """
    Tarama = (Query().set_markets('crypto')
                .select('name', 'change','close','volume','Perf.W')
                .where(
                    Column('exchange')=='BINANCE',
                    Column('RSI|120') > 55.0,
                    Column('change|120') < 5.0,
                    Column('EMA5|120') < Column('close|120'),
                    Column('EMA20|120') < Column('SMA5|120'),
                    Column('EMA50|120') < Column('SMA20|120'),
                    Column('CCI20|120').crosses_above(100),
                    Column('Value.Traded|120') > 2.5E6
                    )
        .get_scanner_data())[1]

    return Tarama

def Tarama_7():
    """
    ADX+CCI Taraması by Anka_Analiz
    """
    Tarama = (Query().set_markets('crypto')
                .select('name', 'change','close','volume','Perf.W',)
                .where(
                    Column('exchange')=='BINANCE',
                    Column('Perf.W') < 10,
                    Column('change|120') < 5.0,
                    Column('ADX|120') > 20,
                    Column('CCI20|120').crosses_above(100),
                    Column('relative_volume_10d_calc|120')>1.5,
                    )
        .get_scanner_data())[1]

    return Tarama

def Tarama_8():
    """
    MACD + Stokastik RSI Kesişimi by Anka_Analiz
    """
    Tarama = (Query().set_markets('crypto')
                .select('name', 'change','close','volume','Perf.W')
                .where(
                    Column('exchange')=='BINANCE',
                    Column('Perf.W') < 10.0,
                    Column('change|120') < 5.0,
                    Column('relative_volume_10d_calc|120')>1.3,
                    Column('MACD.macd|120').crosses_above(Column('MACD.signal|120')),
                    Column('Stoch.RSI.K|120').crosses_above(Column('Stoch.RSI.D|120'))
                    )
        .get_scanner_data())[1]

    return Tarama

def Tarama_9():
    """
    MACD 0 yukarı kesenler by Anka_Analiz
    """
    Tarama = (Query().set_markets('crypto')
                .select('name', 'change','close','volume','Perf.W')
                .where(
                    Column('exchange')=='BINANCE',
                    Column('Perf.W') < 10.0,
                    Column('change|120') < 5.0,
                    Column('relative_volume_10d_calc|120')>1.5,
                    Column('MACD.macd|120').crosses_above(0),
                    Column('MACD.macd|120') > (Column('MACD.signal|120')),
                    )
        .get_scanner_data())[1]

    return Tarama

def Tarama_10():
    """
    Düşeni Kıran by Anka_Analiz
    """
    Tarama = (Query().set_markets('crypto')
                .select('name', 'change','close','volume','Perf.W')
                .where(
                    Column('exchange')=='BINANCE',
                    Column('Perf.W') < 10,
                    Column('change|120') <5.0,
                    Column('relative_volume_10d_calc|120')>1.0,
                    Column('EMA5|120') < Column('close|120'),
                    Column('EMA20|120') < Column('EMA5|120'),
                    Column('MACD.macd|120') > Column('MACD.signal|120'),
                    Column('P.SAR|120').crosses_below(Column('close|120')),
                    Column('CCI20|120') >= 90,
                    )
        .get_scanner_data())[1]

    return Tarama

Tarama1 = Tarama_1()
Tarama2 = Tarama_2()
Tarama3 = Tarama_3()
Tarama4 = Tarama_4()
Tarama5 = Tarama_5()
Tarama6 = Tarama_6()
Tarama7 = Tarama_7()
Tarama8 = Tarama_8()
Tarama9 = Tarama_9()
Tarama10 = Tarama_10()


tarama_dict = {
    'Tarama 1': Tarama1, 'Tarama 2': Tarama2, 'Tarama 3': Tarama3, 'Tarama 4': Tarama4, 'Tarama 5': Tarama5, 'Tarama 6': Tarama6,
    'Tarama 7': Tarama7, 'Tarama 8': Tarama8, 'Tarama 9': Tarama9, 'Tarama 10': Tarama10}

for name, df in tarama_dict.items():
    df['Taramalar'] = name

tarama_list = [
    Tarama1, Tarama2, Tarama3, Tarama4, Tarama5, Tarama6, Tarama7, Tarama8,
    Tarama9, Tarama10]

combined_df = pd.concat(tarama_list, ignore_index=True)
print(combined_df.to_string())

combined_df = combined_df.groupby(['ticker', 'name', 'change', 'close', 'volume', 'Perf.W'], as_index=False).agg({'Taramalar': ','.join})
combined_df['close'] = round(combined_df['close'] ,2)
combined_df['Perf.W'] = round(combined_df['Perf.W'] ,2)

source_counts = combined_df['Taramalar'].value_counts()
combined_df['Tarama Sayısı'] = combined_df['Taramalar'].str.count('Tarama')
combined_df['Taramalar'] = combined_df['Taramalar'].str.replace('Tarama', 'T')
combined_df['change'] = round(combined_df['change'] ,2)

combined_df_2 = combined_df.sort_values(by='Tarama Sayısı', ascending=False).reset_index(drop=True)
print(combined_df_2.to_string())