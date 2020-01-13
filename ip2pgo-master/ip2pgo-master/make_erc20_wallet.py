import os;os.environ['DJANGO_SETTINGS_MODULE']="ip2pdirect.settings"
from ip2pdirect import settings
import django;django.setup()
from infuraeth.interface import create_erc20_wallet
from directapp.models import Erc20Wallet
import sys

username = sys.argv[1]
wallets = Erc20Wallet.objects.filter(username=username)
for wallet in wallets:
    wallet.address = None
    wallet.tx_hash = None
    wallet.save()
create = create_erc20_wallet(username)
if create:
    print('making %s\'s erc20 wallet' % username)
else:
    print('oops! wrong username!')
