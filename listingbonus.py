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
within_today = timezone.now() - timedelta(days=1)
offers = Offers.objects.filter(taker=None)
total = 0
recipients = 0
for offer in offers:
    if not offer.start or offer.start <= within_today:
        if offer.maker not in donors:
            wallet = None
            try:
                wallet = Erc20Wallet.objects.get(username=offer.maker, token='GO')
            except Exception as e:
                pass

            if wallet:
                if offer.trade_type == 'buy':
                    bonus = 100 * 10 ** go.decimal_places
                else:
                    bonus = 50 * 10 ** go.decimal_places
                donor = Erc20Wallet.objects.get(username=donors[1], token='GO')
                donor.balance -= Decimal(bonus)
                wallet.balance += Decimal(bonus)
                donor.save()
                wallet.save()
                History.objects.create(
                    username = wallet.username,
                    activity = 'Listing bonus',
                    token = 'GO',
                    amount = bonus
                )
                History.objects.create(
                    username = donor.username,
                    activity = 'Give listing bonus to %s' % wallet.username,
                    token = 'GO',
                    amount = bonus
                )
 
                #withdraw_erc20(donors[1], wallet.address, bonus, 'GO')
                print("{bonusgo} GO given to {username}".format(bonusgo=bonus / 10 ** go.decimal_places, username=offer.maker))
                recipients += 1
                total += bonus

print("Total recipients: %s" % recipients)
print("Total GO given: %s" % (total / 10 ** go.decimal_places))
