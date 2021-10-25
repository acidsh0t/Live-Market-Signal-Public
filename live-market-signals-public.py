#! python3

#Get live FOREX data
#Script triggered via .bat file through task scheduler on the hour every hour

# Raw Package
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

#Data Source
import yfinance as yf

#Data viz
import plotly.graph_objs as go

_time = datetime.utcnow()
_time = str(_time + timedelta(hours = 8))

#gmail function
def gmail(subject,body): #type(subject,body) == str
    from email.mime.text import MIMEText
    import smtplib

    gmail_username = ''
    recipients = ''

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
    session.login(gmail_username, '')
    session.sendmail(gmail_username, recipients, msg)
    session.quit()

#Currency pairs
eurusd = 'EURUSD=X'
eurjpy = 'EURJPY=X'
gbpusd = 'GBPUSD=X'
eurgbp = 'EURGBP=X'
cadjpy = 'CADJPY=X'
usdcad = 'CAD=X'
eurnzd = 'EURNZD=X'
audcad = 'AUDCAD=X'
audjpy = 'AUDJPY=X'
nzdjpy = 'NZDJPY=X'
usdchf = 'CHF=X'
nzdusd = 'NZDUSD=X'
euraud = 'EURAUD=X'
nzdcad = 'NZDCAD=X'
cadchf = 'CADCHF=X'
nzdchf = 'NZDCHF=X'
chfjpy = 'CHFJPY=X'
audnzd = 'AUDNZD=X'
audchf = 'AUDCHF=X'
eurchf = 'EURCHF=X'
gbpcad = 'GBPCAD=X'

#Crypto
btc = 'BTC-USD'
eth = 'ETH-USD'

#only analyses crypto on weekends
if datetime.today().weekday() >= 5: 
    trade_list = [btc,eth]
#Trade List
else:
    trade_list = [  eurusd,eurjpy,gbpusd,eurgbp,cadjpy,usdcad,eurnzd,audcad,audjpy,nzdjpy,\
                    usdchf,nzdusd,euraud,nzdcad,cadchf,nzdchf,chfjpy,audnzd,audchf,eurchf,gbpcad,\
                    btc,eth]

n=0
p=0

for i in trade_list:
    #download data
    data = yf.download(i,period='1mo',interval='1h')

    #Moving average
    data['100MA'] = data['Close'].rolling(window=100).mean()
    data['50MA'] = data['Close'].rolling(window=50).mean()

    #Bollinger bands
    data['Middle Band'] = data['Close'].rolling(window=21).mean()
    data['Upper Band'] = data['Middle Band'] + 1.96*data['Close'].rolling(window=21).std()
    data['Lower Band'] = data['Middle Band'] - 1.96*data['Close'].rolling(window=21).std()

    #ATR
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    data['ATR'] = true_range.rolling(14).sum()/14

    penult_row = data.iloc[-3]
    ult_row = data.iloc[-2]

    #Stop loss calculation (%)
    if i == eurjpy or i == cadjpy or i == audjpy or i == nzdjpy or i == chfjpy:
        stop_loss = ult_row['ATR'] * 100
    elif i == btc:
        stop_loss = ult_row['ATR'] / 100
    elif i == eth:
        stop_loss = ult_row['ATR'] / 10
    else:
        stop_loss = ult_row['ATR'] * 10000

    #Position Size
    cap =  #Total available capital == int
    risk =  #Total of 2% risk == float
    abs_risk = cap * risk #Absolute risk in PhP
    pos = abs_risk / (stop_loss/100) #Position size
   
    #send emails based on criteria
    #criteria:
        #Buy:    Lowest below Lower Band and close above Lowest, decreasing Middle Band
        #        50MA and 100MA cross
        #Sell: Highest above Higher Band and close below Higher Band, increasing Middle Band
        #       50MA and 100MA cross

    #Buy signal
    if penult_row['Close'] < penult_row['Lower Band'] and ult_row['Close'] > ult_row['Lower Band']\
        and penult_row['100MA'] < ult_row['100MA']: #bullish trend
        gmail('Buy signal for '+i,'Bollinger buy signal.\
            \nStop Loss (%) to be set at '+str(stop_loss)+\
            '\nPosition size: '+str(pos)+\
            '\nSent at '+_time+'.')
        n=n+1
    if penult_row['100MA'] > penult_row['50MA'] and ult_row['100MA'] < ult_row['50MA']: #trend reversal
        gmail('Buy signal for '+i,'Moving average buy signal.\
            \nStop Loss (%) to be set at '+str(stop_loss)+\
            '\nPosition size: '+str(pos)+\
            '\nSent at '+_time+'.')
        n=n+1
        
    #Sell signal
    if penult_row['Close'] > penult_row['Upper Band'] and ult_row['Close'] < ult_row['Upper Band']\
        and penult_row['100MA'] > ult_row['100MA']: #bearish trend
        gmail('Sell signal for '+i,'Bollinger sell signal.\
            \nStop Loss (%) to be set at '+str(stop_loss)+\
            '\nPosition size: '+str(pos)+\
            '\nSent at '+_time+'.')
        n=n+1
    if penult_row['100MA'] < penult_row['50MA'] and ult_row['100MA'] > ult_row['50MA']: #trend reversal
        gmail('Sell signal for '+i,'Moving average sell signal.\
            \nStop Loss (%) to be set at '+str(stop_loss)+\
            '\nPosition size: '+str(pos)+\
            '\nSent at '+_time+'.')
        n=n+1
    p=p+1

quit()