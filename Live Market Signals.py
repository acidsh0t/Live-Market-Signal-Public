#! python3

#Get live FOREX data
#Script triggered via .bat file through task scheduler on the hour every hour

# Raw Package
from datetime import datetime
import numpy as np
import pandas as pd

#Data Source
import yfinance as yf

#Data viz
import plotly.graph_objs as go

#quits if saturday or sunday
if datetime.today().weekday() == 5 or datetime.today().weekday() == 6:
    quit()

_time = str(datetime.today())

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

#Currency list
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
   
    #Stop loss calculation (%)
    if i == eurjpy or i == cadjpy or i == audjpy or i == nzdjpy or i == chfjpy:
        data['stop_loss'] = data['ATR'] * 100
    elif i == btc:
        data['stop_loss'] = data['ATR'] / 100
    elif i == eth:
        data['stop_loss'] = data['ATR'] / 10
    else:
        data['stop_loss'] = data['ATR'] * 10000
       
    '''
    #declare figure
    fig = go.Figure()

    #add Bollinger to graph
    fig.add_trace(go.Scatter(x=data.index, y= data['Middle Band'],line=dict(color='blue', width=.7), name = 'Middle Band'))
    fig.add_trace(go.Scatter(x=data.index, y= data['Upper Band'],line=dict(color='red', width=1.5), name = 'Upper Band (Sell)'))
    fig.add_trace(go.Scatter(x=data.index, y= data['Lower Band'],line=dict(color='green', width=1.5), name = 'Lower Band (Buy)'))

    #candlesticks
    fig.add_trace(go.Candlestick(   x=data.index,
                                    open=data['Open'],
                                    high=data['High'],
                                    low = data['Low'],
                                    close=data['Close'],
                                    name='market data'))

    #add titles
    fig.update_layout(
        title=i) 

    # X-Axes
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=15, label="15m", step="minute", stepmode="backward"),
                dict(count=45, label="45m", step="minute", stepmode="backward"),
                dict(count=1, label="HTD", step="hour", stepmode="todate"),
                dict(count=3, label="3h", step="hour", stepmode="backward"),
                dict(step="all")
            ])
        )
    )

    fig.show()
    '''
    #send emails based on criteria
    #criteria:
        #Buy:    Lowest below Lower Band and close above Lowest, decreasing Middle Band
        #        50MA and 100MA cross
        #Sell: Highest above Higher Band and close below Higher Band, increasing Middle Band
        #       50MA and 100MA cross
        
    penult_row = data.iloc[-3]
    ult_row = data.iloc[-2]

    #Buy signal
    if penult_row['Close'] < penult_row['Lower Band'] and ult_row['Close'] > ult_row['Lower Band']\
        and penult_row['100MA'] < ult_row['100MA']: #bullish trend
        gmail('Buy signal for '+i,'Bollinger buy signal.\
            \nStop Loss (%) to be set at '+str(ult_row['stop_loss'])+\
            '\nSent at '+_time+'.')
        n=n+1
    if penult_row['100MA'] > penult_row['50MA'] and ult_row['100MA'] < ult_row['50MA']:
        gmail('Buy signal for '+i,'Moving average buy signal.\
            \nStop Loss (%) to be set at '+str(ult_row['stop_loss'])+\
            '\nSent at '+_time+'.')
        n=n+1
        
    #Sell signal
    if penult_row['Close'] > penult_row['Upper Band'] and ult_row['Close'] < ult_row['Upper Band'] \
        and penult_row['100MA'] > ult_row['100MA']: #bearish trend
        gmail('Sell signal for '+i,'Bollinger sell signal.\
            \nStop Loss (%) to be set at '+str(ult_row['stop_loss'])+\
            '\nSent at '+_time+'.')
        n=n+1
    if penult_row['100MA'] < penult_row['50MA'] and ult_row['100MA'] > ult_row['50MA']:
        gmail('Sell signal for '+i,'Moving average sell signal.\
            \nStop Loss (%) to be set at '+str(ult_row['stop_loss'])+\
            '\nSent at '+_time+'.')
        n=n+1
    p=p+1

gmail('Market analyser ran at '+_time,str(p)+' trade items were analysed.\n' +str(n)+' trading signals were detected.')
quit()