import os;os.environ['DJANGO_SETTINGS_MODULE']="ip2pdirect.settings"
from ip2pdirect import settings
import django;django.setup()
from directapp.models import Erc20Wallet, Tokens, History, UserProfile
from infuraeth.interface import withdraw_erc20
from decimal import Decimal

#select donor, change as needed
nobonus = ['cn','cn-wb']
exclude_users = [
    'azlinoor',
    'aman_weboss',
    'g1m2000',
    'radzi.ip2p',
    'lbw666',
    'mrz',
    'norazli',
    'radzi.i',
    'radzi',
    'mri1972',
]
bonus_countries = ['za', 'tz', 'bw', 'otc', 'ph']
go = Tokens.objects.get(token='GO')
bonus = 200 * 10 ** go.decimal_places
donor = Erc20Wallet.objects.get(username='rad', token='GO')
all_new = Erc20Wallet.objects.filter(token='GO', balance=0)
for new_user in all_new:
    go_history = History.objects.filter(username=new_user.username, activity__contains='Deposit', amount=bonus, token='GO')
    go_history = []
    user_country = UserProfile.objects.get(username=new_user.username).country
    if len(go_history) == 0 and new_user.username not in exclude_users and user_country in bonus_countries:
        donor.balance -= Decimal(bonus)
        new_user.balance += Decimal(bonus)
        donor.save()
        new_user.save()
        History.objects.create(
            username = new_user.username,
            activity = 'Deposit of new registration bonus',
            token = 'GO',
            amount = bonus
        )
        History.objects.create(
            username = donor.username,
            activity = 'New registration bonus for %s' % new_user.username,
            token = 'GO',
            amount = bonus
        )
        #try:    
        #    withdraw_erc20(donor.username, new_user.address, bonus, 'GO')
        #except Exception:
        #    print(new_user.username)
