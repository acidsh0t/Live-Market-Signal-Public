#! python3

'''
Get live FOREX data
Configured on Heroku to run on the hour every hour

Trading Strategy:
- Only looks from last confirmed 1h candle
- Uses RSI, MACD and Stochastic Oscillator to determine trade entries
- Uses 100MA to determine trend direction
- If signal in direction of trend: no TP, only trailing SL. Else, TP = 2 * SL

'''

# Raw Package
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import pandas_ta as pta
from tinydb import TinyDB
from tinydb.queries import Query

#Data Source
import yfinance as yf

#gmail packages
import smtplib
from email.mime.text import MIMEText

_time = datetime.utcnow()
_time = str(_time + timedelta(hours = 8)) #Philippine timezone

#quits if after :30
half_hour = _time #converts time to string
half_hour = int(half_hour[14:-10]) #only retains minutes
if half_hour >= 30:
    quit()

_time = _time[:-7] #simplifies time expression

#Updates total investing capital from excel sheet
db = TinyDB('trading-capital.json')
capital = Query()
cap = db.search(capital['Name']=='Starting Capital')
cap = pd.DataFrame(cap)
cap = float(cap.iloc[-1]['Amount']) #isolates desired value and converts to float

risk = 0.02 #Total of 2% risk

#gmail function
def gmail(subject,body): #type(subject,body) == str
    gmail_username = ''
    recipients = ''
    pw = '' #password

    #message details
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = gmail_username
    msg['To'] = recipients
    msg = msg.as_string()

    #smtp settings
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.ehlo()
    session.starttls()
    print('Loging in to Gmail')
    session.login(gmail_username,pw)
    print('Login successful\nSending email')
    session.sendmail(gmail_username, recipients, msg)
    print('Email sent')
    session.quit()

#FOREX pairs and yf codes
audcad = 'AUDCAD=X'
audchf = 'AUDCHF=X'
audjpy = 'AUDJPY=X'
audnzd = 'AUDNZD=X'
audusd = 'AUDUSD=X'
cadchf = 'CADCHF=X'
cadjpy = 'CADJPY=X'
chfjpy = 'CHFJPY=X'
euraud = 'EURAUD=X'
eurcad = 'EURCAD=X'
eurchf = 'EURCHF=X'
eurgbp = 'EURGBP=X'
eurjpy = 'EURJPY=X'
eurnzd = 'EURNZD=X'
eurusd = 'EURUSD=X'
gbpcad = 'GBPCAD=X'
gbpjpy = 'GBPJPY=X'
gbpusd = 'GBPUSD=X'
nzdjpy = 'NZDJPY=X'
nzdusd = 'NZDUSD=X'
nzdcad = 'NZDCAD=X'
usdcad = 'CAD=X'
usdchf = 'CHF=X'
usdjpy = 'JPY=X'

#Crypto and yf codes
btc = 'BTC-USD'
eth = 'ETH-USD'

#analyses only crypto on weekends
if datetime.today().weekday() >= 5: 
    trade_list = [btc,eth]
#Trade List
else:
    trade_list = [  eurusd,eurjpy,gbpusd,eurgbp,cadjpy,usdcad,eurnzd,audcad,audjpy,nzdjpy,audusd,usdjpy,eurcad,\
                    usdchf,nzdusd,euraud,nzdcad,cadchf,chfjpy,audnzd,audchf,eurchf,gbpcad,gbpjpy,\
                    btc,eth]

n=0 #Trade signals detected
p=0 #Trade items analysed

for i in trade_list:
    #download data
    data = yf.download(i,period='1mo',interval='1h')

    #100MA
    data['100MA'] = data['Close'].rolling(window=100).mean()

    #Stochastic oscillator
    # Define periods
    k_period = 15
    d_period = 3
    # Adds a "n_high" column with max value of previous 14 periods
    n_high = data['High'].rolling(k_period).max()
    # Adds an "n_low" column with min value of previous 14 periods
    n_low = data['Low'].rolling(k_period).min()
    # Uses the min/max values to calculate the %k (as a percentage)
    data['%K'] = (data['Close'] - n_low) * 100 / (n_high - n_low)
    # Uses the %k to calculates a SMA over the past 3 values of %k
    data['%D'] = data['%K'].rolling(d_period).mean()

    #RSI
    data['RSI'] = pta.rsi(data['Close'], length = 14)

    #MACD
    # Get the 21-period EMA of the closing price
    slow = data['Close'].ewm(span=21, adjust=False, min_periods=21).mean()
    # Get the 8-period EMA of the closing price
    fast = data['Close'].ewm(span=8, adjust=False, min_periods=8).mean()
    # Subtract the 21-period EMA from the 8-period EMA to get the MACD
    data['MACD'] = fast - slow
    # Get the 5-period EMA of the MACD for the Signal line
    data['MACD_S'] = data['MACD'].ewm(span=5, adjust=False, min_periods=5).mean()
    #get difference between MACD and Signal line
    data['MACD_dif'] = abs(data['MACD']-data['MACD_S'])

    #ATR
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    data['ATR'] = true_range.rolling(14).sum()/14

    last_7 = data.tail(8) #gets last 7 confirmed rows
    _2nd_last = data.iloc[-3]
    last = data.iloc[-2] #last confirmed candle

    #Stop loss calculation (%)
    if i == eurjpy or i == cadjpy or i == audjpy or i == nzdjpy or i == chfjpy or i == gbpjpy or i == usdjpy: #all JPY pairs
        stop_loss = last['ATR'] * 100
    elif i == btc:
        stop_loss = 10
    elif i == eth:
        stop_loss = 20
    else:
        stop_loss = last['ATR'] * 10000

    #Position Size
    abs_risk = cap * risk #Absolute risk
    pos = abs_risk / (stop_loss/100) #Position size

    '''
    Possible strategy alterations
    - double SL in no TP trades to ride trends with lower chance of being stopped out
    - or just double TP
    '''

    #Buy signal no TP
    if last['%K'] > last['%D'] and min(last_7['%K']) < 20 and \
        last['RSI'] >= 50 and _2nd_last['RSI'] <= 50 and min(last_7['RSI']) < 30 and \
        (last['MACD'] > last['MACD_S'] or _2nd_last['MACD_dif'] > last['MACD_dif']) and last['MACD'] < 0 and\
        min(last_7['100MA']) < last['100MA']:
        gmail('Buy signal for '+i,\
            '\nStop Loss (%) to be set at '+str(stop_loss)+ \
            '\nPosition size: '+str(pos)+ \
            '\n\nSent at '+_time+'.')
        n=n+1
        
    #Sell signal no TP
    elif last['%K'] < last['%D'] and max(last_7['%K']) > 80 and \
        last['RSI'] <= 50 and  _2nd_last['RSI'] >= 50 and max(last_7['RSI']) > 70 and \
        (last['MACD'] < last['MACD_S'] or _2nd_last['MACD_dif'] > last['MACD_dif']) and last['MACD'] > 0 and\
        max(last_7['100MA']) > last['100MA']:
        gmail('Sell signal for '+i,\
            '\nStop Loss (%) to be set at '+str(stop_loss)+ \
            '\nPosition size: '+str(pos)+\
            '\n\nSent at '+_time+'.')
        n=n+1

    #Buy signal with TP
    elif last['%K'] > last['%D'] and min(last_7['%K']) < 20 and \
        last['RSI'] >= 50 and _2nd_last['RSI'] <= 50 and min(last_7['RSI']) < 30 and \
        (last['MACD'] > last['MACD_S'] or _2nd_last['MACD_dif'] > last['MACD_dif']) and last['MACD'] < 0:
        gmail('Buy signal for '+i,\
            '\nStop Loss (%) to be set at '+str(stop_loss)+ \
            '\nTake Profit (%) to be set at '+str(stop_loss * 2)+ \
            '\nPosition size: '+str(pos)+ \
            '\n\nSent at '+_time+'.')
        n=n+1
        
    #Sell signal with TP
    elif last['%K'] < last['%D'] and max(last_7['%K']) > 80 and \
        last['RSI'] <= 50 and  _2nd_last['RSI'] >= 50 and max(last_7['RSI']) > 70 and \
        (last['MACD'] < last['MACD_S'] or _2nd_last['MACD_dif'] > last['MACD_dif']) and last['MACD'] > 0:
        gmail('Sell signal for '+i,\
            '\nStop Loss (%) to be set at '+str(stop_loss)+ \
            '\nTake Profit (%) to be set at '+str(stop_loss * 2)+ \
            '\nPosition size: '+str(pos)+\
            '\n\nSent at '+_time+'.')
        n=n+1
    else:
        print('No signals detected for '+i)
    p=p+1
print('Securities analysed: '+str(p))
print('Signals detected: '+str(n))
#Summary email for sanity checks
#gmail('Market analyser ran at '+_time,str(p)+' trade items were analysed.\n' +str(n)+' trading signals were detected.')

quit()