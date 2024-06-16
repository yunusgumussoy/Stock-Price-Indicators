# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 19:26:52 2024

@author: Yunus
"""
# pip install deep-translator
# pip install transformers


# Stock Market News Sentiment Analysis

import pandas as pd
from bs4 import BeautifulSoup
import requests
from deep_translator import GoogleTranslator
from transformers import pipeline

# News Headlines
url = "https://www.cnbce.com/piyasalar"

response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')
post_cards = soup.find_all('div', class_='post-card-title')

titles = []
for post_card in post_cards:
    a_tag = post_card.find('a')
    if a_tag:
        text = a_tag.get_text().strip()
        titles.append(text)

# Translation
translated_titles = []
for title in titles:
    translated_title = GoogleTranslator(source='auto', target='en').translate(title)
    translated_titles.append(translated_title)

df = pd.DataFrame({'Turkish': titles, 'English': translated_titles})

# Sentiment analysis
# Financial-RoBERTa is a good fit for financial documents sentiments
sentiment_analysis = pipeline(
    'sentiment-analysis',
    model='soleimanian/financial-roberta-large-sentiment'
)

# Sentiment Form
results = []
for english_title in df['English']:
    result = sentiment_analysis(english_title)
    results.append(result[0])

df['Label'] = [res['label'].title() for res in results]
df['Score'] = [res['score'] for res in results]

# Results Colorization and Presentation
def color_label(val):
    color = ''
    if val == 'Positive':
        color = 'background-color: skyblue; color: black'
    elif val == 'Negative':
        color = 'background-color: lightcoral; color: black'
    elif val == 'Neutral':
        color = 'background-color: lightgrey; color: black'
    return color

styled_df = df.style.map(color_label, subset=['Label'])

# Display the styled DataFrame
styled_df

# Save the styled DataFrame to an HTML file
styled_df.to_html('styled_dataframe.html')

# Optionally, open the HTML file in the default web browser
import webbrowser
webbrowser.open('styled_dataframe.html')
