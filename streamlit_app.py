import requests, datetime
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
    'eth':18
}
pools = {
    'usdc-usdt': '0xdb7b3480f2d1f7bbe91ee3610664756b91bbe0744bc319db2f0b89efdf552064',
    'ar-usdc': '0x0750e26dbffb85e66891b71b9e1049c4be6d94dab938bbb06573ca6178615981',
    'ar-eth': '0x5f0ac5160cd3c105f9db2fb3e981907588d810040eb30d77364affd6f4435933',
    'eth-usdc': '0x7eb07d77601f28549ff623ad42a24b4ac3f0e73af0df3d76446fb299ec375dd5'
}

fee_ratios = {
    'usdc-usdt': 0.0005,
    'ar-usdc': 0.003,
    'ar-eth': 0.003,
    'eth-usdc': 0.003
}

@st.cache(ttl=300)
def get_prices():
    prices = {
        'usdc': 1,
        'usdt':1,
    }
    prices['ar'] = utils.get_price_from_redstone('ar', 'usdc')
    prices['eth'] = utils.get_price_from_redstone('eth', 'usdc')
    return prices
prices = get_prices()

@st.cache
def get_stats(start):
    stats = []
    day = start
    for i in range(1, 31):
        day = day - datetime.timedelta(days=1)
        date = day.strftime('%Y-%m-%d')
        url = '%s/stats?date=%s'%(stats_host, date)
        data = requests.get(url).json()
        stats.append({
            'date': date,
            'stats':data
        })
        print(date)
    stats.reverse()
    return stats

today = datetime.date.today()
stats = get_stats(today)

@st.cache
def get_lps():
    lps = {}
    for k, v in pools.items():
        url = '%s/lps?poolid=%s'%(router_host, v)
        data = requests.get(url).json()
        lps[k] = data['lps']
    return lps
lps = get_lps()
print('lps:', lps)

# tvl
tvl = {}
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

print('tvl:', tvl)
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

bar = base.mark_bar().encode(
  y='user_volumes')

line =  base.mark_line(color='red').encode(
    y='user_counts'
)
st.altair_chart(bar)    

# user count
st.subheader('Everyday User Count')

c = alt.Chart(df).mark_line().encode(
  x='date',
  y='user_counts')
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
col1.metric(":green[LP count]", tvl[pool]['lp_count'])
col2.metric(':green[Token X]', '%.2f %s'%(tvl[pool][x], x))
col3.metric(':green[Token Y]', '%.2f %s'%(tvl[pool][y], y))

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
  y='volumes')

st.altair_chart(c)    

st.subheader('Fees')

c = alt.Chart(df).mark_bar(color='green').encode(
  x='date',
  y='fees')

st.altair_chart(c)    

