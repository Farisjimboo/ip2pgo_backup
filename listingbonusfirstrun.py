import os;os.environ['DJANGO_SETTINGS_MODULE']="ip2pdirect.settings"
from ip2pdirect import settings
import django;django.setup()
from directapp.models import Erc20Wallet, Tokens, Offers, Wallet, History
from infuraeth.interface import withdraw_erc20
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
"""
This script is run daily
"""

#select donor, change as needed
go = Tokens.objects.get(token='GO')
donors = ['vyron123', 'rad']
bonus = 50 * 10 ** go.decimal_places
offers = Offers.objects.all()
total = 0
for offer in offers:
    if offer.maker not in donors:
        try:
            wallet = Erc20Wallet.objects.get(username=offer.maker, token='GO')
        except Exception:
            wallet = None
        if wallet:
            if offer.start:
                taken_datetime = offer.start
            else:
                taken_datetime = timezone.now()
            days = (taken_datetime - offer.datetime).days 
            for x in range(days):
                withdraw_erc20(donors[1], wallet.address, bonus, 'GO')
                print("{bonusgo} GO given to {username}".format(bonusgo=bonus / 10 ** go.decimal_places, username=offer.maker))
                total += 1

print("Total bonus for offers given: %s" % total)
print("Total GO given: %s" % (int(total) * 50))
