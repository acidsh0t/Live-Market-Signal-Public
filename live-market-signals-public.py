#! python3

'''
Get live FOREX data
Configured on Heroku to run on the hour every hour
Works with IQ Option broker's leverage and settings
Base leverage = 50
Adjust SL proportionate to leverage difference

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

#graphing
import plotly.graph_objs as go

#gmail packages
import smtplib
from email.mime.text import MIMEText

_time = datetime.utcnow()
_time = str(_time + timedelta(hours = 8)) #Philippine timezone

hours = int(_time[11:-13]) #only retains hours
minutes = int(_time[14:-10]) #only retains minutes

if minutes >= 30: #quits if minutes > 30
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
nzdchf = 'NZDCHF=X'
usdcad = 'CAD=X'
usdchf = 'CHF=X'
usdjpy = 'JPY=X'

forex_list = [  eurusd,eurjpy,gbpusd,eurgbp,cadjpy,usdcad,eurnzd,audcad,audjpy,nzdjpy,audusd,usdjpy,\
                usdchf,nzdusd,euraud,nzdcad,cadchf,chfjpy,audnzd,audchf,eurchf,gbpcad,gbpjpy,eurcad]


#Crypto and yf codes
btc = 'BTC-USD'
eth = 'ETH-USD'

crypto_list = [btc,eth]

trade_list = []

#all time determination done in +8 timezone
if datetime.today().weekday() >= 5: 
    trade_list = crypto_list #analyses only crypto on weekends
else:
    trade_list = trade_list + forex_list + crypto_list

n=0 #Trade signals detected
p=0 #Trade items analysed

for i in trade_list:
    #download data
    print(i)
    data = yf.download(i,period='1mo',interval='1h')

    #100MA
    data['100MA'] = data['Close'].rolling(window=100).mean()

    #Stochastic oscillator
    k_period = 15
    d_period = 3
    
    data['n_high'] = data['High'].rolling(k_period).max()
    data['n_low'] = data['Low'].rolling(k_period).min()
    data['%K'] = (data['Close'] - data['n_low']) * 100 / (data['n_high'] -data['n_low'])
    data['%D'] = data['%K'].rolling(d_period).mean()

    #RSI
    data['RSI'] = pta.rsi(data['Close'], length = 14)

    #MACD
    slow_p = 21
    fast_p = 8
    sig_p = 5

    slow = data['Close'].ewm(span=slow_p, adjust=False, min_periods=slow_p).mean()
    fast = data['Close'].ewm(span=fast_p, adjust=False, min_periods=fast_p).mean()
    data['MACD'] = fast - slow
    data['MACD_S'] = data['MACD'].ewm(span=sig_p, adjust=False, min_periods=sig_p).mean()

    #ATR
    atr_p = 14 #ATR period

    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    data['ATR'] = true_range.rolling(atr_p).sum()/atr_p

    last_5 = data.iloc[-7:-2] #gets last 10 confirmed rows
    penum = data.iloc[-3] #2nd last confirmed
    last = data.iloc[-2] #last confirmed candle

    '''
    #Graphing
    stoch = go.Figure()
    macd = go.Figure()
    rsi = go.Figure()
    atr = go.Figure()

    stoch.add_trace(go.Scatter(x=data.index, y= data['%K'],line=dict(color='blue', width=.7), name = '%K'))
    stoch.add_trace(go.Scatter(x=data.index, y= data['%D'],line=dict(color='red', width=1.5), name = '%D'))

    macd.add_trace(go.Scatter(x=data.index, y= data['MACD'],line=dict(color='lightblue', width=1.5), name = 'MACD'))
    macd.add_trace(go.Scatter(x=data.index, y= data['MACD_S'],line=dict(color='lightgreen', width=1.5), name = 'Signal'))

    rsi.add_trace(go.Scatter(x=data.index, y= data['RSI'],line=dict(color='brown', width=1.5), name = 'RSI'))

    atr.add_trace(go.Scatter(x=data.index, y= data['ATR'],line=dict(color='orange', width=1.5), name = 'ATR'))

    stoch.update_layout(title='Stochastic for '+i)
    stoch.show()
    macd.update_layout(title='MACD for '+i)
    macd.show()
    rsi.update_layout(title='RSI for '+i)
    rsi.show()
    atr.update_layout(title='ATR for '+i)
    atr.show()
    '''

    #Stop loss calculation (%)
    if i == eurjpy or i == cadjpy or i == audjpy or i == nzdjpy or i == chfjpy or i == gbpjpy or i == usdjpy: #all JPY pairs
        stop_loss = last['ATR'] * 100
    elif i == btc:
        stop_loss = last['ATR'] / 100 * 2
    elif i == eth:
        stop_loss = last['ATR'] / 10 * 2
    else: #works with pairs with x50 leverage
        stop_loss = last['ATR'] * 10000
        if i == nzdchf: #for pairs with x100 leverage
            stop_loss = stop_loss * 2

    #Position Size
    abs_risk = cap * risk #Absolute risk
    pos = abs_risk / (stop_loss/100) #Position size

    '''
    Possible strategy alterations
    - double SL in no TP trades to ride trends with lower chance of being stopped out
    - or just double TP
    '''

    #Buy signal
    if last['%K'] >= last['%D'] and min(last_5['%K']) <= 20\
        and last['MACD'] >= last['MACD_S'] and last['MACD'] <= 0\
        and min(last_5['RSI']) <= 35 and last['RSI'] >=45:
        subject = 'Buy signal for '+i
        if last['100MA'] > penum['100MA']:
            body =  'SL(%) to be set at '+str(stop_loss)+\
                    '\nPosition size: '+str(pos)+ \
                    '\n\nSent at '+_time+'.'
        else:
            body =  'SL(%) to be set at '+str(stop_loss)+\
                    '\nTP(%) to be set at '+str(stop_loss*2)+\
                    '\nPosition size: '+str(pos)+\
                    '\n\nSent at '+_time+'.'
        print('Buy signal detected for '+i)
        gmail(subject,body)
        n=n+1
        
    #Sell signal
    elif last['%K'] <= last['%D'] and max(last_5['%K']) >= 80\
        and last['MACD'] <= last['MACD_S'] and last['MACD'] >= 0\
        and max(last_5['RSI']) >= 65 and last['RSI'] <= 55:
        subject = 'Sell signal for '+i
        if last['100MA'] < penum['100MA']:
            body =  'SL(%) to be set at '+str(stop_loss)+\
                    '\nPosition size: '+str(pos)+ \
                    '\n\nSent at '+_time+'.'
        else:
            body =  'SL(%) to be set at '+str(stop_loss)+\
                    '\nTP(%) to be set at '+str(stop_loss*2)+\
                    '\nPosition size: '+str(pos)+\
                    '\n\nSent at '+_time+'.'
        print('Sell signal detected for '+i)
        gmail(subject,body)
        n=n+1
    else:
        print('No signals detected for '+i)
    
    p=p+1

print('Securities analysed: '+str(p))
print('Signals detected: '+str(n))
print('Last run at '+_time)

#Summary email for sanity checks
#gmail('Market analyser ran at '+_time,str(p)+' trade items were analysed.\n' +str(n)+' trading signals were detected.')

quit()