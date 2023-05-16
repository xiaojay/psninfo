import requests, datetime
from dateutil import parser
import streamlit as st
import pandas as pd
import altair as alt
import utils
st.title('Permaswap Stats Info')

stats_host = 'https://stats.permaswap.network'
router_host = 'https://router.permaswap.network'
decimals = {
    'ar': 12,
    'usdc': 6,
    'usdt':6,
    'eth':18,
    'ardrive':18,
    'acnh':8,
    'ans': 18
}
pools = {
    'usdc-usdt': '0xdb7b3480f2d1f7bbe91ee3610664756b91bbe0744bc319db2f0b89efdf552064',
    'ar-usdc': '0x0750e26dbffb85e66891b71b9e1049c4be6d94dab938bbb06573ca6178615981',
    'ar-eth': '0x5f0ac5160cd3c105f9db2fb3e981907588d810040eb30d77364affd6f4435933',
    'eth-usdc': '0x7eb07d77601f28549ff623ad42a24b4ac3f0e73af0df3d76446fb299ec375dd5',
    #'ar-usdt': '0x13f0377029205a60b0e02aef985cbf91d854282c2d8064c810667ee3ebcde39f',
    #'eth-usdt':'0x9d9c7e102d741ec921c41567c34e751f021cd37df42befe702d84a6475fae90c',
    'ar-ardrive': '0xbb546a762e7d5f24549cfd97dfa394404790293277658e42732ab3b2c4345fa3',
    'usdc-acnh': '0x7200199c193c97012893fd103c56307e44434322439ece7711f28a8c3512c082',
    'ar-ans': '0x6e80137a5bbb6ae6b683fcd8a20978d6b4632dddc78aa61945adbcc5a197ca0f'
}

fee_ratios = {
    'usdc-usdt': 0.0005,
    'ar-usdc': 0.003,
    'ar-eth': 0.003,
    'eth-usdc': 0.003,
    'ar-usdt': 0.003,
    'eth-usdt': 0.003,
    'ar-ardrive': 0.003,
    'usdc-acnh':0.0005,
    'ar-ans': 0.003
}

@st.cache(ttl=300)
def get_prices():
    prices = {
        'usdc': 1,
        'usdt':1,
        #todo 
        'ardrive': 0.4,
        'acnh': 0.147,
        'ans': 1.5
    }
    prices['ar'] = utils.get_price_from_redstone('ar', 'usdc')
    prices['eth'] = utils.get_price_from_redstone('eth', 'usdc')
    return prices
prices = get_prices()
print('prices', prices)

@st.cache(ttl=300)
def get_info():
    url = '%s/info'%stats_host
    return requests.get(url).json()
info = get_info()
pool_count = len(pools)
#pool_count = 4

cur = parser.parse(info['curStats']['date'])
if datetime.datetime.now(datetime.timezone.utc).date() == cur.date():
    today_volume = sum(info['curStats']['user'].values())
else:
    today_volume = 0

def get_date(datetime_str):
    date_obj = datetime.datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
    return date_obj.date().isoformat()

@st.cache
def get_stats(end):
    stats = []
    start = end - datetime.timedelta(days=30)
    url = '%s/stats?start=%s&end=%s'%(stats_host, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))
    data = requests.get(url).json()
    for d in data:
        date = get_date(d['date'])
        stats.append({
            'date': date,
            'stats': d
        })
    stats.reverse()
    return stats

today = datetime.date.today()
stats = get_stats(today)

@st.cache(ttl=300)
def get_lps():
    lps = {}
    for k, v in pools.items():
        url = '%s/lps?poolid=%s'%(router_host, v)
        data = requests.get(url).json()
        lps[k] = data['lps']
    return lps
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
col1.metric(':green[Token X]', '%.2f %s'%(tvl[pool][x], x.upper()))
col2.metric(':green[Token Y]', '%.2f %s'%(tvl[pool][y], y.upper()))
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

st.subheader('Fees')

c = alt.Chart(df).mark_bar(color='green').encode(
  x='date',
  y=alt.Y('fees', title='Fee (usd)'))

st.altair_chart(c)    

