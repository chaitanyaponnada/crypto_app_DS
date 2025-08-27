import streamlit as st
from PIL import Image
import pandas as pd
import matplotlib.pyplot as plt
import requests
import base64
import os

# Set Page to expand to full width
st.set_page_config(layout="wide")

# Image
try:
    image = Image.open('logo.png')
    st.image(image, width=500)
except FileNotFoundError:
    st.warning("Logo image ('logo.png') not found. Skipping image display.")

# Title
st.title('Crypto Web App')
st.markdown("""
This app retrieves prices along with other information regarding different cryptocurrencies from **CoinMarketCap** using their API!
""")

# About
expander_bar = st.expander('About')
expander_bar.markdown("""
* **Made By:** Chaitanya Ponnada
* **Data source:** [CoinMarketCap API](https://coinmarketcap.com/api/documentation/v1/).
* **Credit:** Adapted from original scraping-based app.
""")

# Divide Page into columns
col1 = st.sidebar
col2, col3 = st.columns((1,1))

col1.header('Input Options')

## Sidebar - Select currency price unit
currency_price_unit = col1.selectbox('Select currency for price',
                                     ('USD', 'BTC'))

# API Key
API_KEY = '863315fd-0f70-4411-892c-44cf6fc86706'
BASE_URL = 'https://pro-api.coinmarketcap.com'

headers = {
    'Accept': 'application/json',
    'X-CMC_PRO_API_KEY': API_KEY
}

#---------------------------------#

def load_data(currency=currency_price_unit):
    try:
        # Fetch listings
        listings_url = f'{BASE_URL}/v1/cryptocurrency/listings/latest'
        params = {
            'start': 1,
            'limit': 100,  # Top 100 coins
            'convert': currency
        }
        response = requests.get(listings_url, headers=headers, params=params)
        response.raise_for_status()  # Raise exception for bad status codes
        data = response.json()['data']

        coin_name = []
        coin_symbol = []
        market_cap = []
        percent_change_1h = []
        percent_change_24h = []
        percent_change_7d = []
        price = []
        volume_24h = []

        for coin in data:
            coin_name.append(coin['name'])
            coin_symbol.append(coin['symbol'])
            quote = coin['quote'][currency]
            price.append(quote['price'])
            percent_change_1h.append(quote['percent_change_1h'])
            percent_change_24h.append(quote['percent_change_24h'])
            percent_change_7d.append(quote['percent_change_7d'])
            market_cap.append(quote['market_cap'])
            volume_24h.append(quote['volume_24h'])

        df = pd.DataFrame({
            'coin_name': coin_name,
            'coin_symbol': coin_symbol,
            'market_cap': market_cap,
            'percent_change_1h': percent_change_1h,
            'percent_change_24h': percent_change_24h,
            'percent_change_7d': percent_change_7d,
            'price': price,
            'volume_24h': volume_24h
        })

        # Fetch global metrics
        global_url = f'{BASE_URL}/v1/global-metrics/quotes/latest'
        global_params = {'convert': 'USD'}
        global_response = requests.get(global_url, headers=headers, params=global_params)
        global_response.raise_for_status()
        global_data = global_response.json()['data']

        total_marketcap = global_data['quote']['USD']['total_market_cap']
        btc_market_share = global_data['btc_dominance']
        eth_market_share = global_data['eth_dominance']

        return df, total_marketcap, btc_market_share, eth_market_share
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch data from CoinMarketCap API: {e}")
        return pd.DataFrame(), 0, 0, 0

df, total_marketcap, btc_market_share, eth_market_share = load_data()

#---------------------------------#

# Sidebar - Select cryptocurrencies
sorted_coin = sorted(df['coin_symbol'])
selected_coin = col1.multiselect('Cryptocurrency', sorted_coin,
                                 ['BTC', 'ETH', 'ADA', 'DOGE', 'BNB'])

# Filtering data
selected_coin_df = df[(df['coin_symbol'].isin(selected_coin))] 

# Sidebar - Select Percent change timeframe
percent_timeframe = col1.selectbox('Percent change time frame',
                                   ['7d','24h', '1h'])

#---------------------------------#

percent_dict = {"7d":'percent_change_7d',
                "24h":'percent_change_24h',
                "1h":'percent_change_1h'}
selected_percent_timeframe = percent_dict[percent_timeframe]

# Preparing data for plotting
top_5_positive_change = df.nlargest(5, selected_percent_timeframe)
top_5_negative_change = df.nsmallest(5, selected_percent_timeframe)

positive_change_selected_coins = \
    selected_coin_df[selected_coin_df[selected_percent_timeframe] > 0]
negative_change_selected_coins = \
    selected_coin_df[selected_coin_df[selected_percent_timeframe] < 0]

bar_chart_df = pd.concat([top_5_positive_change,
                         positive_change_selected_coins,
                         top_5_negative_change,
                         negative_change_selected_coins], axis=0)
bar_chart_df['positive_percent_change'] = \
    bar_chart_df[selected_percent_timeframe] > 0

# Heading for Horizontal Bar Chart
col2.subheader(f'Bar plot of % Price Change')
col2.write(f'*Last {percent_timeframe} period*')

# Plotting Horizontal Bar Chart
try:
    plt.style.use('seaborn-v0_8')  # Updated style for Matplotlib 3.6+
except ValueError:
    plt.style.use('default')  # Fallback to default style if seaborn-v0_8 unavailable

fig, ax = plt.subplots()
ax.barh(bar_chart_df['coin_symbol'],
        bar_chart_df[selected_percent_timeframe], 
        color=bar_chart_df.positive_percent_change\
        .map({True: 'lightblue', False: 'pink'}))

ax.set_xlabel('Percent Change', fontsize=17, labelpad=15)
ax.tick_params(axis='both', labelsize=13)

fig.tight_layout()

# Display figure
col2.pyplot(fig)

#---------------------------------#

def get_unit(max_market_cap):
  
    unit = 'less than ten million'
    number_of_digits = len(str(int(max_market_cap)))

    if number_of_digits == 8:
        unit = 'tens of millions'
    elif number_of_digits == 9:
        unit = 'hundreds of millions'
    elif number_of_digits == 10:
        unit = 'billions'
    elif number_of_digits == 11:
        unit = 'tens of billions'
    elif number_of_digits == 12:
        unit = 'hundreds of billions'
  
    return unit

# Heading for Bar Chart
col3.subheader(f'Bar plot of Market Cap (Selected Cryptos)')
col3.write(f'*Last {percent_timeframe} period*')

# Plotting Bar Chart
fig, ax = plt.subplots()
ax.bar(selected_coin_df['coin_symbol'],
        selected_coin_df['market_cap'])
ax.tick_params(axis='both', labelsize=15)

# Increasing size of exponent
exponent = ax.yaxis.get_offset_text()
exponent.set_size(16)

# Changing y-axis label based on the number of digits
max_market_cap = selected_coin_df['market_cap'].max()
unit = get_unit(max_market_cap)
if unit == 'less than ten million':
    ax.set_ylabel(f'Market Cap', fontsize=15, labelpad=15)
else:
    ax.set_ylabel(f'Market Cap ({unit})', fontsize=15, labelpad=15)

fig.tight_layout()

# Display figure
col3.pyplot(fig)

#---------------------------------#

col2.markdown("""
_________________________
""")

# Heading for Pie Chart
col2.header('**Market Share of Cryptos**')

# Preparing data for plotting
alt_coins_market_share = 100 - (btc_market_share + eth_market_share)

percentages = [btc_market_share, eth_market_share, alt_coins_market_share]
labels = ['Bitcoin', 'Ethereum', 'Alt Coins']

# Plot Pie Chart
fig, ax = plt.subplots()
colors = ['#80dfff', 'pink', '#ffe699']
ax.pie(percentages, labels=labels, colors=colors, autopct='%.1f%%')
plt.legend(loc="upper right", bbox_to_anchor=(1.2, 1), fontsize=10)

# Display figure
col2.pyplot(fig)

#---------------------------------#

col2.markdown("""
_________________________
""")

col2.header('**Tables**')

# Price Data Table
columns = ['coin_name', 'coin_symbol', 'market_cap', 'price', 'volume_24h']
selected_coin_price_info_df = selected_coin_df[columns]

col2.subheader('Price Data of Selected Cryptocurrencies')
col2.write(selected_coin_price_info_df)

# Download CSV data
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    href = f'<a href="data:file/csv;base64,{b64}" download="crypto.csv">Download CSV File</a>'
    return href

col2.markdown(filedownload(selected_coin_price_info_df),
              unsafe_allow_html=True)

# Table of Percentage Change
selected_coin_percent_change_df = \
    selected_coin_df.drop(columns=['market_cap', 'price', 'volume_24h'])

col2.subheader('Percent Change Data of Select Cryptocurrencies')
col2.write(selected_coin_percent_change_df)