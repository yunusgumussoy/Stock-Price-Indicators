"""
Created on Mon May 27 21:28:14 2024

@author: Yunus
"""

# pip install yahooquery

import pandas as pd 
from yahooquery import Ticker #data from Yahoo Finance
import requests 
from io import StringIO

url= "https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/Temel-Degerler-Ve-Oranlar.aspx?endeks=01#page-1"

# fetches the HTML content of the webpage as a string
html_text=requests.get(url).text

# allows this string to be treated as a file-like object
html_io=StringIO(html_text)

# reads all HTML tables from the string
tablo=pd.read_html(html_io)[2]["Kod"] # selects the third table (index 2) and extracts the "Kod" column, which contains stock codes.

# Istanbul Stock Exchange - IS
# Iterates through the stock codes and appends ".IS" to each code to match the format used by Yahoo Finance
for i in range(len(tablo)):
    tablo[i] +=".IS"

hissekod=tablo.to_list()

# Creates a Ticker object with the list of stock codes.
ticker = Ticker(hissekod)

# Fetches financial data for these stocks and stores it in data_dict.
data_dict=ticker.financial_data

# Converts the dictionary to a DataFrame, transposing it so that each stock's data is a row
df=pd.DataFrame.from_dict(data_dict, orient="index").T

# Selects specific rows and columns, renames columns to more descriptive names.
df=df.iloc[1:6].T.reset_index()
df.columns=["Hisse Adı", "Güncel Fiyat", "En Yüksek Tahmin", "En Düşük Tahmin", "Ortalama Tahmin", "Medyan Tahmin"]

# Removes the ".IS" suffix from the stock name
df["Hisse Adı"] = df["Hisse Adı"].str.replace(".IS", "", regex=False)

# Removes rows with any missing values
df.dropna(axis=0, inplace=True)

# Resets the DataFrame index for a cleaner output.
df.reset_index(drop=True, inplace=True)

print(df)
