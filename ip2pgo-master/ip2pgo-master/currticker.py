import os;os.environ['DJANGO_SETTINGS_MODULE']="ip2pdirect.settings"
from ip2pdirect import settings
import django;django.setup()
import requests, json
from directapp.models import Tokens, Currency
from datetime import datetime, timedelta

currencies = {
    'my': 'MYR', 
    'cn': 'CNY',
    'cn-wb': 'CNY',
    'id': 'IDR',
    'au': 'AUD',
    'vn': 'VND',
    'ng': 'NGN',
    'gh': 'GHS',
    'za': 'ZAR',
    'tz': 'TZS',
    'bw': 'BWP',
    'otc': 'USD',
    'ph': 'PHP',
}
base = 'USD'
clayer = "http://www.apilayer.net/api/live?access_key=4f75c9ecc60374a98c054e74af68ea8c"

response = requests.get(clayer)
if response.status_code == 200:
    for country in currencies:
        try:
            currency = Currency.objects.get(country=country)
        except Exception:
            Currency.objects.create(country=country, currency=currencies[country])
            currency = Currency.objects.get(country=country)

        exchangedata = response.json()
        currency.rate = exchangedata['quotes'][base+currencies[country]]
        currency.save()  

