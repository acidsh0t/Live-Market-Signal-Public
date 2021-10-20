#! python3

#Get live FOREX data

# Raw Package
from datetime import datetime

#Data Source
import yfinance as yf

#Data viz
import plotly.graph_objs as go

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

#quits if saturday or sunday
if datetime.today().weekday() == 5 or datetime.today().weekday() == 6:
    quit()

#Currency list
curr_list = [eurusd,eurjpy,gbpusd,eurgbp,cadjpy,usdcad,eurnzd,audcad,audjpy,nzdjpy,usdchf,nzdusd,euraud,nzdcad,cadchf,nzdchf,chfjpy,audnzd,audchf,eurchf,gbpcad]
n=0
p=0

for curr_pair in curr_list:
#download data
    data = yf.download(curr_pair,period='1mo',interval='1h')

    #Moving average
    data['MA'] = data['Close'].rolling(window=50).mean()

    #Bollinger bands
    data['Middle Band'] = data['Close'].rolling(window=21).mean()
    data['Upper Band'] = data['Middle Band'] + 1.96*data['Close'].rolling(window=21).std()
    data['Lower Band'] = data['Middle Band'] - 1.96*data['Close'].rolling(window=21).std()
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
        title=curr_pair) 

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
        #Buy: Lowest below Lower Band and close above Lowest
        #Sell: Highest above Higher Band and close below Higher Band
        
    penult_row = data.iloc[-3]
    ult_row = data.iloc[-2]

    #Buy signal
    if penult_row['Low'] < penult_row['Lower Band']  and ult_row['Close'] > ult_row['Open']\
        and penult_row['MA'] < ult_row['MA']:
        gmail('Buy signal for '+curr_pair,'')
        n=n+1
        
    #Sell signal
    if penult_row['High'] > penult_row['Upper Band'] and ult_row['Close'] < ult_row['Open']\
        and penult_row['MA'] > ult_row['MA']:
        gmail('Sell signal for '+curr_pair,'')
        n=n+1
    p=p+1

_time = datetime.now()
gmail('Market analyser ran at '+(str(_time)),str(p)+' currency pairs were analysed.\n' +str(n)+' trading signals were detected.')