import os;os.environ['DJANGO_SETTINGS_MODULE']="ip2pdirect.settings"
from ip2pdirect import settings
import django;django.setup()
from directapp.models import Erc20Wallet, Tokens, History, Referral, Wallet, UserProfile
from infuraeth.interface import withdraw_erc20
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

count = 0
#select donor, change as needed
go = Tokens.objects.get(token='GO')
bonus = 100 * 10 ** go.decimal_places
donor = Erc20Wallet.objects.get(username='rad', token='GO')
second_donor = Erc20Wallet.objects.get(username='vyron123', token='GO')
referees = Erc20Wallet.objects.filter(token='GO')
for user in referees:
    check_country = UserProfile.objects.get(username=user.username)
    if check_country.country != 'cn-wb' and check_country.country != 'cn':
        refs = []
        first_line = None
        go_history = History.objects.filter(username=user.username, activity__contains='Deposit', amount=bonus, token='GO')
        try:
            first_line = Referral.objects.get(username=user.username).first_line
        except Exception:
            Referral.objects.create(username=user.username)
            first_line = Referral.objects.get(username=user.username).first_line
        if first_line and ',' in first_line:
            check = None
            fline = first_line.split(',')
            for line in fline:
                try:
                    line_user = UserProfile.objects.get(member_id=line)
                except Exception:
                    pass
                try:
                    check = Wallet.objects.get(username=line_user.username)
                except Exception:
                    print('%s has no wallet' % line_user.username)
                    pass

                if check:
                    refs.append(line)

        elif first_line and ',' not in first_line:
            check = None
            line_user = UserProfile.objects.get(member_id=first_line)
            try:
                check = Wallet.objects.get(username=line_user.username)
            except Exception:
                pass

            if check:
                refs.append(first_line)

        if len(refs) > 0 and check_country.country == 'otc':
            remaining_refs = len(refs) - len(go_history)
            if remaining_refs > 0:
                for x in range(remaining_refs):
                    print('Giving bonus to %s' % user.username)
                    second_donor.balance -= Decimal(bonus)
                    user.balance += Decimal(bonus)
                    second_donor.save()
                    user.save()
                    History.objects.create(
                        username = user.username,
                        activity = 'Deposit referral bonus',
                        token = 'GO',
                        amount = bonus
                    )
                    History.objects.create(
                        username = second_donor.username,
                        activity = 'Give referral bonus to %s' % user.username,
                        token = 'GO',
                        amount = bonus
                    )
                    #try:
                    #    withdraw_erc20(second_donor.username,user.address,bonus,'GO')
                    #except Exception as e:
                    #    print(e)
                    count += 1

print('Total referrals given: %s' % count)
print('Total GO distributed: %s' % (count * 100))
