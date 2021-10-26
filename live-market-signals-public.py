#! python3

#Get live FOREX data
#Configured on Heroku to run on the hour every hour

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

#gets total investing capital from tinyDB
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
    session.login(gmail_username,pw)
    session.sendmail(gmail_username, recipients, msg)
    session.quit()

#FOREX PAIRS
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
nzdchf = 'NZDCHF=X'
usdcad = 'CAD=X'
usdchf = 'CHF=X'
usdjpy = 'JPY=X'

#Crypto
btc = 'BTC-USD'
eth = 'ETH-USD'

#analyses only crypto on weekends
if datetime.today().weekday() >= 5: 
    trade_list = [btc,eth]
#Trade List
else:
    trade_list = [  eurusd,eurjpy,gbpusd,eurgbp,cadjpy,usdcad,eurnzd,audcad,audjpy,nzdjpy,audusd,usdjpy,eurcad,\
                    usdchf,nzdusd,euraud,nzdcad,cadchf,nzdchf,chfjpy,audnzd,audchf,eurchf,gbpcad,gbpjpy,\
                    btc,eth]

n=0 #Trade signals detected
p=0 #Trade items analysed

for i in trade_list:
    #download data
    data = yf.download(i,period='1mo',interval='1h')

    #Stochastic oscillator
    # Define periods
    k_period = 15
    d_period = 3
    #max value of previous 14 periods
    n_high = data['High'].rolling(k_period).max()
    #min value of previous 14 periods
    n_low = data['Low'].rolling(k_period).min()
    # Uses the min/max values to calculate the %k (as a percentage)
    data['%K'] = (data['Close'] - n_low) * 100 / (n_high - n_low)
    # Uses the %k to calculates a SMA over the past 3 values of %k
    data['%D'] = data['%K'].rolling(d_period).mean()

    #RSI
    data['RSI'] = pta.rsi(data['Close'], length = 14)

    #MACD
    # Get the 21-period EMA of the closing price
    k = data['Close'].ewm(span=21, adjust=False, min_periods=21).mean()
    # Get the 8-period EMA of the closing price
    d = data['Close'].ewm(span=8, adjust=False, min_periods=8).mean()
    # Subtract the 21-period EMA from the 8-period EMA to get the MACD
    data['MACD'] = d - k
    # Get the 5-period EMA of the MACD for the Trigger line
    data['MACD_S'] = data['MACD'].ewm(span=5, adjust=False, min_periods=5).mean()

    #ATR
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    data['ATR'] = true_range.rolling(14).sum()/14

    last_5 = data.tail(6) #gets last 5 confirmed rows
    penult_row = data.iloc[-3] #2nd last confirmed candle
    ult_row = data.iloc[-2] #last confirmed candle

    #Stop loss calculation (%)
    if i == eurjpy or i == cadjpy or i == audjpy or i == nzdjpy or i == chfjpy or i == gbpjpy or i == usdjpy: #all JPY pairs
        stop_loss = ult_row['ATR'] * 100
    elif i == btc:
        stop_loss = 10
    elif i == eth:
        stop_loss = 20
    else:
        stop_loss = ult_row['ATR'] * 10000

    #Position Size
    abs_risk = cap * risk #Absolute risk
    pos = abs_risk / (stop_loss/100) #Position size

    #Buy signal
    if ult_row['%D'] < 50 and ult_row['%K'] > ult_row['%D'] and max(last_5['%D']) > 80 and \
        penult_row['RSI'] <= 50 and ult_row['RSI'] >= 50 and max(last_5['RSI']) > 70 and \
        ult_row['MACD'] > ult_row['MACD_S'] and ult_row['MACD'] < 0:
        gmail('Buy signal for '+i,\
            '\nStop Loss (%) to be set at '+str(stop_loss)+\
            '\nPosition size: '+str(pos)+\
            '\nSent at '+_time+'.')
        n=n+1
        
    #Sell signal
    if ult_row['%D'] > 50 and ult_row['%K'] < ult_row['%D'] and min(last_5['%D']) < 20 and \
        penult_row['RSI'] >= 50 and ult_row['RSI'] <= 50 and min(last_5['RSI']) < 30 and \
        ult_row['MACD'] < ult_row['MACD_S'] and ult_row['MACD'] > 0:
        gmail('Sell signal for '+i,\
            '\nStop Loss (%) to be set at '+str(stop_loss)+\
            '\nPosition size: '+str(pos)+\
            '\nSent at '+_time+'.')
        n=n+1
    p=p+1

#gmail('Market analyser ran at '+_time,str(p)+' trade items were analysed.\n' +str(n)+' trading signals were detected.')

quit()