import pytz

from django.conf import settings
from web3.auto.infura import w3

from directapp.models import UserProfile, Wallet, Erc20Wallet, Referral, Tokens, History
from django.utils.translation import ugettext_lazy as _
from datetime import datetime, timedelta
from .models import Comissions, Redemption
from decimal import Decimal

from infuraeth.interface import admin_transact,contract_transact
from infuraeth.contracts import (
    ZRX_contract,
    BTM_contract,
    SCC_contract,
    OMG_contract, 
    USDT_contract,
) 

def register_referral(username, referral):
    loop = True
    member = UserProfile.objects.get(username=username)
    member_id = member.member_id
    referee = member_id
    ref_level = 0
    max_level = 10
    if member.country == 'cn-wb':
        max_level = 3 
    while loop:
        user = None

        try:
            user = UserProfile.objects.get(member_id=referral)
        except Exception:
            loop = False

        if user:
            try:
                ref_data = Referral.objects.get(username=user.username)
            except Exception:
                Referral.objects.create(username=user.username)
                ref_data = Referral.objects.get(username=user.username)

        if loop:
            if ref_level == 0:
                if ref_data.first_line is not None:
                    ref_data.first_line = ref_data.first_line + ',' + referee
                else:
                    ref_data.first_line = referee
            elif ref_level == 1:
                if ref_data.second_line is not None:
                    ref_data.second_line = ref_data.second_line +','+ referee
                else:
                    ref_data.second_line = referee
            elif ref_level < max_level:
                if ref_data.others_line is not None:
                    ref_data.others_line = ref_data.others_line +','+ referee
                else:
                    ref_data.others_line = referee                
    
            else:
                loop = False
            ref_data.save()

            referral = user.referral_id
            member_id = user.member_id
            ref_level += 1      

    return True

def give_bonus(username, platform_fee, token):
    member = UserProfile.objects.get(username=username)
    member_id = member.member_id
    ft_bonus = 0.1   #10%
    sd_bonus = 0.06  # 6%
    os_bonus = 0.02  # 2%
    if member.country == 'cn-wb':
        sd_bonus = 0.05
        os_bonus = 0.05

    try:
        firstref=Referral.objects.get(first_line__contains=member_id).username
    except Exception:
        firstref = None

    try:    
        secondref=Referral.objects.get(second_line__contains=member_id).username
    except Exception:
        secondref = None

    otherrefs = Referral.objects.filter(others_line__contains=member_id)

    if firstref:
        if token == 'ETH':
            try:
                wallet = Wallet.objects.get(username=firstref)
            except Exception:
                wallet = None
        else:
            try:        
                wallet = Erc20Wallet.objects.get(username=firstref)
            except Exception:
                wallet = None
        
        if wallet:    
            wallet.balance += Decimal(platform_fee) * Decimal(ft_bonus)
            History.objects.create(
                username = firstref,
                amount = Decimal(platform_fee) * Decimal(ft_bonus),
                token = token,
                activity = _(u"Referral commission from {uname}").format(uname=username)
            )

    if secondref:
        if token == 'ETH':
            try:
                wallet = Wallet.objects.get(username=secondref)
            except Exception:
                wallet = None

        else:
            try:        
                wallet = Erc20Wallet.objects.get(username=secondref)
            except Exception:
                wallet = None

        if wallet:
            wallet.balance += Decimal(platform_fee) * Decimal(sd_bonus)
            History.objects.create(
                username = secondref,
                amount = Decimal(platform_fee) * Decimal(sd_bonus),
                token = token,
                activity =  _(u"Referral commission from {uname}").format(uname=username)
            )

    if len(otherrefs) > 0:
        for ref in otherrefs:
            if token == 'ETH':
                try:
                    wallet = Wallet.objects.get(username=ref.username)
                except Exception:
                    wallet = None
            else:   
                try:     
                    wallet = Erc20Wallet.objects.get(username=ref.username)
                except Exception:
                    wallet = None
            
            if wallet:
                wallet.balance += Decimal(platform_fee) * Decimal(os_bonus)
                History.objects.create(
                    username = ref.username,
                    amount = Decimal(platform_fee) * Decimal(os_bonus),
                    token = token,
                    activity =  _(u"Referral commission from {uname}").format(uname=username)
                )

    return True
