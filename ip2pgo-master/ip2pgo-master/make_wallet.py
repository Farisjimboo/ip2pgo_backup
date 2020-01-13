import os;os.environ['DJANGO_SETTINGS_MODULE']="ip2pdirect.settings"
from ip2pdirect import settings
import django;django.setup()
from infuraeth.interface import create_user_wallet
from directapp.models import Wallet
import sys

username = sys.argv[1]
wallet = Wallet.objects.get(username=username)
wallet.address = None
wallet.tx_hash = None
wallet.save()
create = create_user_wallet(username)
if create:
    print('making %s\'s wallet' % username)
else:
    print('oops! wrong username!')
