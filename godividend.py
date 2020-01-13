import os;os.environ['DJANGO_SETTINGS_MODULE']="ip2pdirect.settings"
from ip2pdirect import settings
import django;django.setup()
from directapp.models import Erc20Wallet, Tokens, Offers, Wallet, History, Dividend
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
country_partners = {
    'my': Decimal(0.4),
    'au': Decimal(0.3),
    'gh': Decimal(0.4),
    'tz': Decimal(0.4),
    'za': Decimal(0.4),
    'ng': Decimal(0.36),
    'vn': Decimal(0.4),
    'bw': Decimal(0.4),
    'id': 0,
}
supply = Decimal(36135562 + 50000000 + 163864438)
supply = supply * 10 ** go.decimal_places
base_dividend = {}

holders = Erc20Wallet.objects.filter(token='GO', balance__gt=0).exclude(username__in=donors)
within_today = timezone.now() - timedelta(days=1)
trades_today = Offers.objects.filter(end__gte=within_today, completed=True, cancelled=False)
#get today's base dividend
if len(trades_today) > 0:
    for trade in trades_today:
        if trade.token == 'GO':
            if trade.maker_fees > 0:
                trade.fees = trade.amount * Decimal(0.0002)
            else:
                trade.fees = trade.amount * Decimal(0.0008)
        referral = 0
        maker_referral = 0

        taker_history = History.objects.filter(activity__contains=trade.taker)
        for history in taker_history:
            referral += history.amount

        maker_history = History.objects.filter(activity__contains=trade.maker)
        for history in maker_history:
            maker_referral += history.amount

        nett_fees = trade.fees * (1 - country_partners[trade.country]) - referral
        try:
            base_dividend[trade.token] += nett_fees * Decimal(0.3)
        except KeyError:
            base_dividend[trade.token] = nett_fees * Decimal(0.3)

        if trade.maker_fees > 0:
            maker_nett = trade.maker_fees * (1 - country_partners[trade.country]) - maker_referral
            base_dividend[trade.crypto] += maker_nett * Decimal(0.3)

# give today's dividend to all members
    import pdb;pdb.set_trace()
    for holder in holders:
        weight = holder.balance / supply
        for token in base_dividend:
            token_data = Tokens.objects.get(token=token)
            wallet = None
            amount = Decimal(int(weight * base_dividend[token]))

            if amount > 0:
                Dividend.objects.create(name=token, amount=amount)

            if token == 'ETH':
                if amount > 0:
                    try:
                        wallet = Wallet.objects.get(username=holder.username)
                    except Exception:
                        pass
                    if wallet:
                        wallet.balance += amount
                        wallet.save()
            else:
                if amount > 0:
                    try:
                        wallet = Erc20Wallet.objects.get(username=holder.username, token=token)
                    except Exception:
                        pass
                    if wallet:
                        wallet.balance += amount
                        wallet.save()

            History.objects.create(
                username = holder.username,
                activity = "GO holder %s dividend" % token,
                amount = amount / 10 ** token_data.decimal_places,
                token = token,
            ) 
            try:
                print("{dividend} {token} given to {user}".format(dividend=amount / 10 ** token_data.decimal_places, token=token, user=wallet.username))
            except Exception:
                pass
print(base_dividend)
