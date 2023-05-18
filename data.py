import requests, datetime
import streamlit as st
import utils

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
    #'ar-usdt': '0x13f0377029205a60b0e02aef985cbf91d854282c2d8064c810667ee3ebcde39f',
    #'eth-usdt':'0x9d9c7e102d741ec921c41567c34e751f021cd37df42befe702d84a6475fae90c',
    'usdc-usdt': '0xdb7b3480f2d1f7bbe91ee3610664756b91bbe0744bc319db2f0b89efdf552064',
    'ar-usdc': '0x0750e26dbffb85e66891b71b9e1049c4be6d94dab938bbb06573ca6178615981',
    'ar-eth': '0x5f0ac5160cd3c105f9db2fb3e981907588d810040eb30d77364affd6f4435933',
    'eth-usdc': '0x7eb07d77601f28549ff623ad42a24b4ac3f0e73af0df3d76446fb299ec375dd5',
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

@st.cache_data(ttl=600)
def get_prices():
    prices = {
        'usdc': 1,
        'usdt':1,
        #todo 
        'ardrive': 0.3,
        'acnh': 0.147,
        'ans': 3
    }
    prices['ar'] = utils.get_price_from_redstone('ar', 'usdc')
    prices['eth'] = utils.get_price_from_redstone('eth', 'usdc')
    return prices

@st.cache_data(ttl=600)
def get_info():
    url = '%s/info'%stats_host
    return requests.get(url).json()

def get_date(datetime_str):
    date_obj = datetime.datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
    return date_obj.date().isoformat()

@st.cache_data
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

@st.cache_data(ttl=300)
def get_lps():
    lps = {}
    for k, v in pools.items():
        url = '%s/lps?poolid=%s'%(router_host, v)
        data = requests.get(url).json()
        lps[k] = data['lps']
    return lps