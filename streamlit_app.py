import datetime
from dateutil import parser
import streamlit as st
import pandas as pd
import altair as alt
import utils
from data import *
import plotly.graph_objs as go
from plotly.subplots import make_subplots

st.title('Permaswap Stats Info')

prices = get_prices2()
print('prices', prices)
info = get_info()
pool_count = len(pools)

cur = parser.parse(info['curStats']['date'])
if datetime.datetime.now(datetime.timezone.utc).date() == cur.date():
    today_volume = sum(info['curStats']['user'].values())
else:
    today_volume = 0

today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
stats = get_stats(today)

lps = get_lps()
lp_count = sum([len(v) for k, v in lps.items()])
print('lps:', lps)

# tvl
tvl = {}
total_tvl = 0
for pair, lps in lps.items():
    x, y = pair.split('-')
    tvl[pair] = {}
    tvl[pair]['lp_count'] = len(lps)
    dx = decimals[x]
    dy = decimals[y]
    for lp in lps:
        ax, ay = utils.liquidity_to_amount2(lp['liquidity'], lp['lowSqrtPrice'], lp['highSqrtPrice'], lp['currentSqrtPrice'])
        ax, ay = int(ax)/10**dx, int(ay)/10**dy
        print(ax, ay)
        tvl[pair][x] = tvl[pair].get(x, 0) + ax
        tvl[pair][y] = tvl[pair].get(y, 0) + ay
        total_tvl += prices[x] * ax 
        total_tvl += prices[y] * ay
print('total_tvl:', total_tvl)
print('tvl:', tvl)

col1, col2 = st.columns(2)
col1.metric(':green[Today (%s UTC) Volume]'%today.strftime('%Y-%m-%d'), '%.2f $'%today_volume)
col2.metric(":green[Current Total TVL]", '%.2f $'%total_tvl)

col1, col2 = st.columns(2)
col1.metric(':green[Current Pool Count]', pool_count)
col2.metric(':green[Current LP Count]', lp_count)

# user volume
st.subheader('Everyday User Volume')

date = []
router_fees = []
tx_counts = []
user_counts = []
user_volumes = []
for s in stats:
    date.append(s['date'])
    router_fees.append(s['stats'].get('fee', 0))
    tx_counts.append(s['stats'].get('txCount', 0))
    user_counts.append(len(s['stats']['user']))
    user_volumes.append(sum(s['stats']['user'].values()))

df = pd.DataFrame({'date': date,
                   'router_fees': router_fees,
                   'user_counts': user_counts,
                   'user_volumes': user_volumes,
                   })
                   

base = alt.Chart(df).encode(x='date')

bar = base.mark_bar(color='green').encode(
    y=alt.Y('user_volumes', title='Trading Volume (usd)')) 

# line =  base.mark_line(color='green').encode(
#     y=alt.Y('user_counts', title='User Count'))
st.altair_chart(bar)    

# user count
st.subheader('Everyday User Count')

c = alt.Chart(df).mark_line(color='green').encode(
    x='date',
    y=alt.Y('user_counts', title='User Count'))
st.altair_chart(c)    

# pool
#st.header('PooL')
#pool = st.selectbox(
#    '',
#    pools.keys())

col1, col2 = st.columns(2)
col1.header('PooL')
pool = col2.selectbox(
    '',
    pools.keys())

# tvl
st.subheader('Current Pool %s TVL'%pool.upper())
#st.text('Lp count: %i'%tvl[pool]['lp_count'])
x, y = pool.split('-')
#st.text('%s: %s'%(x, tvl[pool][x]))
#st.text('%s: %s'%(y, tvl[pool][y]))

col1, col2, col3 = st.columns(3)
col1.metric(':green[Token X]', '%.1f %s'%(tvl[pool][x], x))
col2.metric(':green[Token Y]', '%.1f %s'%(tvl[pool][y], y))
col3.metric(":green[LP count]", tvl[pool]['lp_count'])

date = []
vs = []
fees = []
for s in stats:
    date.append(s['date'])
    v = s['stats']['pool'].get(pools[pool], 0)
    vs.append(v)
    fee_ratio = fee_ratios[pool]
    fees.append(v*fee_ratio)

st.subheader('Volume')

df = pd.DataFrame({'date': date,
                   'volumes': vs,
                   'fees': fees})

c = alt.Chart(df).mark_bar(color='green').encode(
  x='date',
  y=alt.Y('volumes', title='Trading Volume (usd)'))

st.altair_chart(c)    

# st.subheader('Fees')

# c = alt.Chart(df).mark_bar(color='green').encode(
#   x='date',
#   y=alt.Y('fees', title='Fee (usd)'))

# st.altair_chart(c)    

st.header('Price')
col1, col2, col3 = st.columns(3)
token = col1.selectbox('', tokens_k)
period = col2.selectbox('', ['D', '8H', '4H', 'H'])

st.text("")

col1, col2 = st.columns(2)
col1.metric(':green[Current Price]', '%.2f usd/%s '%(prices[token], token))
col2.metric('', '%.4f %s/usd '%(1/prices[token], token))

orders = get_today_orders()
orders.extend(get_orders(yesterday, duration=30))
orders = process_orders(orders)
print(len(orders))

kline = get_kline(orders, token, period)

print('kline:', kline.head())
trace = go.Candlestick(x=kline.index,
                       open=kline['price']['first'],
                       high=kline['price']['max'],
                       low=kline['price']['min'],
                       close=kline['price']['last'])

fig = make_subplots(rows=2,
    cols=1,
    row_heights=[0.8, 0.2],
    shared_xaxes=True,
    vertical_spacing=0.02)

fig.add_trace(trace, row=1, col=1)
fig.add_trace(go.Bar(x=kline.index, y=kline['volume']['sum'], marker=dict(color='green')),
               row=2,
               col=1)

fig.update_layout(title = token.upper()+'/USD Klines',
    yaxis1_title = 'Price (usd)',
    yaxis2_title = 'Volume (usd)',
    xaxis2_title = 'Time',
    xaxis1_rangeslider_visible = False,
    xaxis2_rangeslider_visible = False,
    yaxis2_showgrid = False,
    showlegend=False
)
st.plotly_chart(fig)
