import requests
from datetime import datetime, timedelta
from twilio.rest import Client
import yaml
import os

def read_yaml(yaml_path):
    print(os.path.exists(yaml_path))
    with open(yaml_path, 'r',encoding='utf-8') as f:
        yaml_content = yaml.safe_load(f)
    return yaml_content

config_path = "configs/config.yaml"
configs = read_yaml(config_path)

#
STOCK = "MSFT"
COMPANY_NAME = "Microsoft"

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

STOCK_API_KEY = configs["STOCK_API_KEY"]
NEWS_API_KEY = configs["NEWS_API_KEY"]

TWILIO_ACCOUNT = 'AC1854b6578feac5255e9b9f845f4be119'
AUTH_TOKEN = configs["SMS_TOKEN"]
PHONE_NUMBER = configs["PHONE_NUMBER"]
SENDING_NUMBER = configs["SENDING_NUMBER"]


time_now = datetime.now()
year = time_now.year
month = time_now.month
day = time_now.day

#get date of t-1 and t-2 for stock data. If t-1 is on monday, t-2 is friday
previous_date = time_now - timedelta(days=1)
previous_date_2 = time_now - timedelta(days=2)

if previous_date.weekday() == 0:  # Monday has weekday value 0
    previous_date_2 -= timedelta(days=3)

previous_date = str(previous_date).split(" ")[0]
previous_date_2 = str(previous_date_2).split(" ")[0]


# STEP 1: Use https://newsapi.org/docs/endpoints/everything

parameters = {
    "function": "TIME_SERIES_DAILY_ADJUSTED",
    "symbol": STOCK,
    "outputsize": "compact",
    "datatype": "json",
    "apikey": STOCK_API_KEY
}

response = requests.get(url=STOCK_ENDPOINT, params=parameters)
response.raise_for_status()
stock_data = response.json()
print(stock_data)
stock_data_1_day = stock_data["Time Series (Daily)"][previous_date]
stock_data_2_days = stock_data["Time Series (Daily)"][previous_date_2]

print(stock_data_1_day)
print(stock_data_2_days)

# When STOCK price increase/decreases by 5% between yesterday and the day before yesterday then print("Get News").
# HINT 1: Get the closing price for yesterday and the day before yesterday. Find the positive difference between the two prices. e.g. 40 - 20 = -20, but the positive difference is 20.

#relative price change with formula: (New price - old price) / old price
stock_change = ((float(stock_data_1_day["4. close"]) - (float(stock_data_2_days["4. close"])))/float(stock_data_2_days["4. close"]))*100

stock_message=f' {STOCK}: 🔻 {stock_change:.1f}' if stock_change < 0 else f' {STOCK}: 🔺 {stock_change:.1f}'

print(stock_message)

## STEP 2: Use https://newsapi.org/docs/endpoints/everything
# Instead of printing ("Get News"), actually fetch the first 3 articles for the COMPANY_NAME. 
#HINT 1: Think about using the Python Slice Operator

parameters = {
    "apiKey": NEWS_API_KEY,
    "q": COMPANY_NAME,
    "from": previous_date,
    "sortBy": "popularity",
    "language": "en"
}

response = requests.get(url=NEWS_ENDPOINT, params=parameters)
response.raise_for_status()
news_data = response.json()
top_three_stories = news_data["articles"][0:3]
print(top_three_stories)

new_line = '\n'
message = f'{stock_message}{new_line}headline:{top_three_stories[0]["title"]}{new_line}brief:{top_three_stories[0]["description"]}'

print(message)

## STEP 3: Use twilio.com/docs/sms/quickstart/python

if stock_change <= -5 or stock_change >=5:

    client = Client(TWILIO_ACCOUNT, AUTH_TOKEN)

    message = client.messages.create(
        body=message,
        from_=SENDING_NUMBER,
        to=PHONE_NUMBER
    )

    print(message.sid)