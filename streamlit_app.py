import requests, datetime
import streamlit as st
import pandas as pd
import altair as alt
import univ3 as uni

st.title('Permaswap Stats Info')

stats_host = 'https://stats.permaswap.network'
router_host = 'https://router.permaswap.network'
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

@st.cache
def get_stats():
    stats = []
    today = datetime.date.today()
    day = today
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
stats = get_stats()

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
# user volume
st.subheader('User volume')

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
st.subheader('User Count')

c = alt.Chart(df).mark_line().encode(
  x='date',
  y='user_counts')
st.altair_chart(c)    

# pool
pool = st.selectbox(
    '',
    pools.keys())


date = []
vs = []
fees = []
for s in stats:
    date.append(s['date'])
    v = s['stats']['pool'].get(pools[pool], 0)
    vs.append(v)
    fee_ratio = fee_ratios[pool]
    fees.append(v*fee_ratio)

st.subheader('Pool %s Volume'%pool.upper())

df = pd.DataFrame({'date': date,
                   'volumes': vs,
                   'fees': fees})

c = alt.Chart(df).mark_bar(color='green').encode(
  x='date',
  y='volumes')

st.altair_chart(c)    

st.subheader('Pool %s Fees'%pool.upper())

c = alt.Chart(df).mark_bar(color='green').encode(
  x='date',
  y='fees')

st.altair_chart(c)    

