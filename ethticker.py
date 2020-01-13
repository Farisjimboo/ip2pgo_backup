import os;os.environ['DJANGO_SETTINGS_MODULE']="ip2pdirect.settings"
from ip2pdirect import settings
import django;django.setup()
import requests, json
from directapp.models import Tokens, Currency
from datetime import datetime, timedelta
from decimal import Decimal

# ETH, USDT
bittrex_tokens = ['OMG', 'ZRX']
hitbtc_tokens = ['BTM', 'TEL']
indodax_tokens = ['SCC']
coingecko_tokens = ['TMB']
#base = 'USD'

hitbtc = "https://api.hitbtc.com/api/2/public/ticker/"
#bitfinex = "https://api.bitfinex.com/v1/pubticker/"
bittrex = "https://bittrex.com/api/v1.1/public/getticker/?market="
indodax = "https://indodax.com/api/"
coingecko = "https://api.coingecko.com/api/v3/coins/"

base = ['ETH', 'USDT', 'TUSD']
for token in base:
    apiurl = bittrex+'USD-'+token
    response = requests.get(apiurl)
    if response.status_code == 200:
        try:
            get_base = Tokens.objects.get(token=token)
        except Exception:
            get_base = None

        if get_base:
            token_data = response.json()
            get_base.bid_usd = token_data['result']['Bid']
            get_base.ask_usd = token_data['result']['Ask']
            get_base.save() 

usd_base = Tokens.objects.get(token='USDT')
eth_base = Tokens.objects.get(token='ETH')

for token in bittrex_tokens:
    apiurl = bittrex+'USDT-'+token
    response = requests.get(apiurl)
    if response.status_code == 200:
        tokendb = None
        try:
            tokendb = Tokens.objects.get(token=token)
        except Exception:
            pass

        if tokendb:
            token_data = response.json()
        
            tokendb.bid_usd = Decimal(token_data['result']['Bid']) * usd_base.bid_usd
            tokendb.ask_usd = Decimal(token_data['result']['Ask']) * usd_base.ask_usd
            tokendb.save() 

for token in hitbtc_tokens:
    apiurl = None
    if token == 'TEL':
        apiurl = hitbtc+token+'ETH'
    else:
        apiurl = hitbtc+token+'USD'
    response = requests.get(apiurl)
    if response.status_code == 200:
        tokendb = None
        try:
            tokendb = Tokens.objects.get(token=token)
        except Exception:
            pass

        if tokendb:
            token_data = response.json()
   
            if token == 'TEL':
                tokendb.bid_usd = Decimal(token_data['bid']) * eth_base.bid_usd
                tokendb.ask_usd = Decimal(token_data['ask']) * eth_base.ask_usd
            else:
                tokendb.bid_usd = Decimal(token_data['bid']) * usd_base.bid_usd
                tokendb.ask_usd = Decimal(token_data['ask']) * usd_base.ask_usd
            tokendb.save() 

usd_indo = Currency.objects.get(country='id')

for token in indodax_tokens:
    apiurl = indodax+token.lower()+'_idr/ticker'
    response = requests.get(apiurl)
    if response.status_code == 200:
        tokendb = None
        try:
            tokendb = Tokens.objects.get(token=token)
        except Exception:
            pass

        if tokendb:
            token_data = response.json()
            try:
                tokendb.bid_usd = Decimal(token_data['ticker']['buy']) / usd_indo.rate
                tokendb.ask_usd = Decimal(token_data['ticker']['sell']) / usd_indo.rate
                tokendb.save()
            except Exception:
                tokendb.bid_usd = 1 / usd_indo.rate
                tokendb.ask_usd = 1 / usd_indo.rate
                tokendb.save()

for token in coingecko_tokens:
    ticker = None
    if token == 'TMB':
        ticker = 'tembocoin'
    apiurl = coingecko+ticker+'/tickers'
    response = requests.get(apiurl)
    if response.status_code == 200:
        tokendb = None
        try:
            tokendb = Tokens.objects.get(token=token)
        except Exception:
            pass

        if tokendb:
            token_data = response.json()

            # until a more reliable bid/ask pricing is available
            common_price = token_data['tickers'][0]['converted_last']['usd']

            tokendb.bid_usd = Decimal(common_price)
            tokendb.ask_usd = Decimal(common_price)
            tokendb.save()

#IP2PR
ip2pr_token = None
try:
    ip2pr_token = Tokens.objects.get(token='GO')
except Exception:
    pass

if ip2pr_token:
    ip2pr_token.ask_usd = Decimal(0.01)
    ip2pr_token.bid_usd = Decimal(0.0095)
    ip2pr_token.save()

#REGO
rego_token = None
try:
    rego_token = Tokens.objects.get(token='REGO')
except Exception:
    pass

if rego_token:
    rego_token.ask_usd = eth_base.ask_usd * Decimal(0.000625)
    rego_token.bid_usd = eth_base.bid_usd * Decimal(0.000525)
    rego_token.save()

#PLS
pls_token = None
try:
    pls_token = Tokens.objects.get(token='PLS')
except Exception:
    pass

if pls_token:
    pls_token.ask_usd = eth_base.ask_usd * Decimal(0.002)
    pls_token.bid_usd = pls_token.ask_usd
    pls_token.save()

"""
ico = '1CT'
try:
    onecity_token = Tokens.objects.get(token='1CT')
except Exception:
    Tokens.objects.create(token='1CT')
    onecity_token = Tokens.objects.get(token='1CT')

cny_rate = Currency.objects.get(country='cn').rate
onecity_token.ask_usd = 1 / cny_rate
onecity_token.save()
"""
