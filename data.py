import requests, datetime
import pandas as pd
import streamlit as st
import utils

stats_host = 'https://stats.permaswap.network'
router_host = 'https://router.permaswap.network'

tokens_k = ['ar', 'eth', 'acnh', 'ardrive', 'ans']

symbol_to_tag = {
    'ar': 'arweave,ethereum-ar-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,0x4fadc7a98f2dc96510e42dd1a74141eeae0c1543',
    'usdc': 'ethereum-usdc-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
    'usdt': 'ethereum-usdt-0xdac17f958d2ee523a2206206994597c13d831ec7',
    'eth': 'ethereum-eth-0x0000000000000000000000000000000000000000',
    'ardrive': 'arweave-ardrive--8A6RexFkpfWwuyVO98wzSFZh0d6VJuI-buTJvlwOJQ',
    'acnh': 'everpay-acnh-0x72247989079da354c9f0a6886b965bcc86550f8a',
    'ans': 'ethereum-ans-0x937efa4a5ff9d65785691b70a1136aaf8ada7e62',
}

tag_to_symbol = {value: key for key, value in symbol_to_tag.items()}

decimals = {
    'ar': 12,
    'usdc': 6,
    'usdt':6,
    'eth':18,
    'ardrive':18,
    'acnh':8,
    'ans': 18
}

tags = {
    'ar': "arweave,ethereum-ar-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,0x4fadc7a98f2dc96510e42dd1a74141eeae0c1543",
    'usdc': "ethereum-usdc-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    'usdt': "ethereum-usdt-0xdac17f958d2ee523a2206206994597c13d831ec7",
    'eth': "ethereum-eth-0x0000000000000000000000000000000000000000",
    'ardrive':"arweave-ardrive--8A6RexFkpfWwuyVO98wzSFZh0d6VJuI-buTJvlwOJQ",
    'acnh': "everpay-acnh-0x72247989079da354c9f0a6886b965bcc86550f8a",
    'ans': "ethereum-ans-0x937efa4a5ff9d65785691b70a1136aaf8ada7e62"
}

min_amount = {
    'ar': "10000000000",
    'eth': "100000000000000",
    'acnh': "10000000",
    'ardrive': "100000000000000000",
    'ans': "100000000000000000"
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
    #'ar-usdt': 0.003,
    #'eth-usdt': 0.003,
    'usdc-usdt': 0.0005,
    'ar-usdc': 0.003,
    'ar-eth': 0.003,
    'eth-usdc': 0.003,
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
        'ans': 3
    }
    prices['ar'] = utils.get_price_from_redstone('ar', 'usdc')
    prices['ardrive'] = utils.get_price_from_redstone('ardrive', 'usdc')
    prices['acnh'] = utils.get_price_from_redstone('ardrive', 'usdc')
    prices['eth'] = utils.get_price_from_redstone('eth', 'usdc')
    return prices

@st.cache_data(ttl=600)
def get_prices2():
    prices = {
        'usdc': 1,
        'usdt':1,
    }
    for token in ['ar', 'eth', 'acnh', 'ardrive', 'ans']:
        print('get price for %s'%token)
        prices[token] = utils.get_price_from_ps(token, min_amount[token])
    
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

@st.cache_data(ttl=1200)
def get_lps():
    lps = {}
    for k, v in pools.items():
        url = '%s/lps?poolid=%s'%(router_host, v)
        data = requests.get(url).json()
        lps[k] = data['lps']
    return lps

@st.cache_data
def get_orders(end, start='', duration=30):
    orders = []
    if start == '':
        start = end - datetime.timedelta(days=duration)
    for page in range(1, 50000):
        url = '%s/orders?start=%s&end=%s&count=200&page=%i'%(router_host, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'), page)
        print(url)
        data = requests.get(url).json()
        orders.extend(data['orders'])
        if len(data['orders']) < 200:
            break
    return orders

@st.cache_data(ttl=300)
def get_today_orders():
    start = datetime.datetime.today()
    return get_orders(start, start)

def get_volume(order, order_ref):
    token_in = tag_to_symbol[order['tokenInTag']]
    token_out = tag_to_symbol[order['tokenOutTag']]
    amount_in = float(order['tokenInAmount'])
    amount_out = float(order['tokenOutAmount'])
    
    token_in_ref = tag_to_symbol[order_ref['tokenInTag']]
    token_out_ref = tag_to_symbol[order_ref['tokenOutTag']]
    amount_in_ref = float(order_ref['tokenInAmount'])
    amount_out_ref = float(order_ref['tokenOutAmount'])
    
    if token_in == token_in_ref and token_out_ref in ['usdc', 'usdt']:
        price_token_in = amount_out_ref/amount_in_ref
        volume = price_token_in * amount_in
        return volume
    
    if token_out == token_in_ref and token_out_ref in ['usdc', 'usdt']:
        price_token_out = amount_out_ref/amount_in_ref
        volume = price_token_out * amount_out
        return volume
           
                
    if token_in == token_out_ref and token_in_ref in ['usdc', 'usdt']:
        price_token_in = amount_in_ref/amount_out_ref
        volume = price_token_in * amount_in
        return volume
       
    if token_out == token_out_ref and token_in_ref in ['usdc', 'usdt']:
        price_token_out = amount_in_ref/amount_out_ref
        volume = price_token_out * amount_out
        return volume
    
    return -1
            
def process_orders(orders):
    new_orders = []
    n = len(orders)
    
    for index, order in enumerate(orders):
        token_in = tag_to_symbol[order['tokenInTag']]
        token_out = tag_to_symbol[order['tokenOutTag']]
        amount_in = float(order['tokenInAmount'])
        amount_out = float(order['tokenOutAmount'])
        volume = 0

        new_order = {
            'time': order['timestamp'],
            'address': order['address'],
            'ever_hash': order['everHash'],
            'token_in': token_in,
            'token_out': token_out,
            'amount_in': amount_in,
            'amount_out': amount_out,
        }
        
        if token_in in ['usdc', 'usdt']:
            volume = float(order["tokenInAmount"])
            new_order['volume'] = volume
            new_orders.append(new_order)
            continue

        if token_out in ['usdc', 'usdt']:
            volume = float(order["tokenOutAmount"])
            new_order['volume'] = volume
            new_orders.append(new_order)
            continue
            
        for i in range(100):
            if index + i < n - 1:
                order_next = orders[index + i]
                volume = get_volume(order, order_next)
                if volume > 0:
                    new_order['volume'] = volume
                    new_orders.append(new_order)
                    break
                
            if index - i > 0:
                order_prev = orders[index - i]
                volume = get_volume(order, order_prev)
                if volume > 0:
                    new_order['volume'] = volume
                    new_orders.append(new_order)
                    break
    
    return new_orders

def get_kline(orders, token, period):
    df = pd.DataFrame(orders)
    print(df.head())
    df.set_index('time', inplace=True)
    df.index = pd.to_datetime(df.index, unit='ms')
    # df1 = df[(df['token_in']==token)]
    # df1['price'] = df.loc['volume'] / df.loc['amount_in']
    # df2 = df[(df['token_out']==token)]
    # df2['price'] = df.loc['volume'] / df.loc['amount_out']

    df1 = df[(df['token_in'] == token)].copy()
    df1.loc[:, 'price'] = df1['volume'] / df1['amount_in']
    df2 = df[(df['token_out'] == token)].copy()
    df2.loc[:, 'price'] = df2['volume'] / df2['amount_out']

    df3 = pd.concat([df1,df2])
    df4 = df3.resample(rule=period).agg(
        {'price': ['first', 'max', 'min', 'last'],     
        'volume': 'sum'
    })
    # df4.reset_index(inplace=True)
  
    # prev = df4['price']['last'].shift(1)
    # df4['price']['last'].fillna(prev, inplace=True)
    # df4['price']['min'].fillna(prev, inplace=True)
    # df4['price']['max'].fillna(prev, inplace=True)
    # df4['price']['first'].fillna(prev, inplace=True)
    # df4.fillna(method='ffill', inplace=True)

    prev = df4['price']['last'].shift(1)
    df4['price', 'last'] = df4['price']['last'].fillna(prev)
    df4['price', 'min'] = df4['price']['min'].fillna(prev)
    df4['price', 'max'] = df4['price']['max'].fillna(prev)
    df4['price', 'first'] = df4['price']['first'].fillna(prev)
    df4 = df4.fillna(method='ffill')

    
    return df4