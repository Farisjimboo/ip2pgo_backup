import os;os.environ['DJANGO_SETTINGS_MODULE']="ip2pdirect.settings"
from ip2pdirect import settings
import django;django.setup()
from directapp.models import Wallet, Erc20Wallet, Tokens
from infuraeth.interface import get_eth_balance, get_erc20_balance
from decimal import Decimal

all_wallets = Wallet.objects.filter(address__isnull=False)

for wallet in all_wallets:
    get_eth_balance(wallet.address)
    all_erc = Erc20Wallet.objects.filter(username=wallet.username)
    if len(all_erc) > 0:
        for erc in all_erc:
            try:
                get_erc20_balance(erc.address, erc.token)
            except Exception as e:
                print(erc.token)
                print(e)
 
