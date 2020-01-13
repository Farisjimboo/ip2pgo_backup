import os;os.environ['DJANGO_SETTINGS_MODULE']="ip2pdirect.settings"
from ip2pdirect import settings
import django;django.setup()
import requests, json
from directapp.models import Tokens, Currency, Erc20Wallet, UserProfile
from datetime import datetime, timedelta
from decimal import Decimal

users = UserProfile.objects.all()
tokenobjs = Tokens.objects.all()
get_wallet = None

for user in users:
    username = user.username
    try:
        get_wallet = Erc20Wallet.objects.get(username=username, token='USDT')
    except Exception:
        get_wallet = None

    if get_wallet:
        for tokenobj in tokenobjs:
            token = tokenobj.token
            try:
                Erc20Wallet.objects.get(username=username, token=token)
            except Exception:
                if token != 'ETH':
                    Erc20Wallet.objects.create(
                        username = username,
                        token = token,
                        address = get_wallet.address,
                        tx_hash = get_wallet.tx_hash
                    )
                
