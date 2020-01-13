from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader, Context, RequestContext
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from .models import (
    UserProfile, 
    BankReference, 
    Passcode, 
    Wallet, 
    Notification, 
    Tokens,
    Currency,
    Conversation,
    Offers,
    BaseTxnFee,
    Erc20Wallet,
    Ico,
    Referral,
    OTC,
    History,
    IEO_Sales,
)
from .forms import (
    LoginForm,
    SecurityForm,
    OfferSell,
    OfferBuy,
    OfferSellAU,
    OfferBuyAU,
    PasscodeForm,
    resetPasscodeForm,
    UpdateForm,
    WithdrawalForm,
    Buying,
    Selling,
    RatingForm,
    ChatForm,
    DisputeForm,
    DepositForm,
)
import random, string, requests
from email.mime.image import MIMEImage
from django.contrib.staticfiles import finders
from django.template import Context
from django.template.loader import render_to_string, get_template
from django.core.mail import EmailMessage
import os, smtplib, base64, pytz
import email.encoders
import email.mime.text
import email.mime.base
import email.utils
from datetime import datetime, timedelta
from web3.auto.infura import w3
from infuraeth.interface import (
    withdraw,
    withdraw_erc20,
    create_user_wallet,
    create_erc20_wallet,
    get_eth_balance,
    get_erc20_balance,
    trade_data_call,
    take_trade,
    release,
    cancel,
)
from promotions.models import Comissions, Redemption
from promotions.referral import give_bonus
from django.dispatch import Signal, receiver
from time import sleep
from decimal import Decimal
from django.http import JsonResponse
from dispute.models import DisputeSession, DisputeChat
from django.core.mail import send_mail
from django.utils import timezone
from . import banlist, ieo

basket = Signal(providing_args=["currency", "username", "offer_id", "amount", "fiat"])

def shared_data(country, token, security_code, crypto):
    data = {}
    try:
        user = UserProfile.objects.get(security_code=security_code)
    except Exception:
        return False

    if user.username in banlist.USERNAMES:
        return False

    data['country'] = country
    data['username'] = user.username
    data['tokens'] = []
    tokens = Tokens.objects.all()
    if country == 'bw' or country == 'ng':
        if crypto == 'FIAT' or crypto == 'ETH':
            others_token = Tokens.objects.all().exclude(token='1CT').exclude(token='USDT')
        else:
            others_token = Tokens.objects.all().exclude(token='1CT').exclude(token='USDT')
    else:
        if crypto == 'ETH':
            others_token = Tokens.objects.all().exclude(token='1CT').exclude(token='USDT')
        else:
            others_token = Tokens.objects.all().exclude(token='1CT').exclude(token='USDT')

    cnwb_tokens = Tokens.objects.all().exclude(token='GO')    

    for t in tokens:
        data[t.token] = t.token
 
    
    fiat = Currency.objects.get(country=country)
    name = Tokens.objects.get(token=token).name
    
    if country == 'bw' or country == 'ng':

        if token == 'PLS':
 
            if user.verified and country != 'otc': 
                otc = OTC.objects.all()
            else:
                otc = OTC.objects.all().exclude(name='FIAT').exclude(name='GO').exclude(name='TUSD')
        else:
            if user.verified and country != 'otc':
                otc = OTC.objects.all()
            else:
                otc = OTC.objects.all().exclude(name='FIAT')
    else:
        
        if token == 'PLS':
            if user.verified and country != 'otc':
                otc = OTC.objects.all()
            else:
                otc = OTC.objects.all().exclude(name='FIAT').exclude(name='GO').exclude(name='TUSD') 

        else:
            if user.verified and country != 'otc':
                otc = OTC.objects.all()
            else:
                otc = OTC.objects.all().exclude(name='FIAT')
    
    data['fiat'] = fiat 
    data['otc'] = otc 
    data['crypto'] = crypto
    data['name'] = name
    data['currency'] = fiat.currency
    data['user'] = user
    data['security_code'] = security_code
    data['english'] = ['my', 'au', 'ng', 'gh', 'za', 'tz', 'bw', 'otc', 'ph']
    data['chinese'] = ['cn', 'cn-wb']
    data['tokens'] = tokens
    data['others_token'] = others_token
    data['cnwb_token'] = cnwb_tokens
    data['token'] =  token

    
 
    return data


def index(request, country):
    data = {}
    data['username'] = None
    email = None
    data['country'] = country
    message = ''
    token = 'ETH' #for now
    data['token'] = token
    data['currency'] = Currency.objects.get(country=country).currency

    if 'login' in request.POST:

        retry = True
        while retry:
            retry = False
            security_code = ''
            for n in range(6):
                security_code += random.choice(string.digits)
            testget = UserProfile.objects.filter(security_code=security_code)
            if len(testget) > 0:
                retry = True

        login_form = LoginForm(request.POST)
        email = str(login_form['email'].value())
        passcode = str(login_form['code'].value())
        login_status = True
        if email in banlist.USERS:
            login_status = False
        if login_status:
            try:
                user = UserProfile.objects.get(email=email)
            except Exception:
                message = _(u'Email is incorrect. Please make sure your email have been registered.')
                login_form = LoginForm()
                data['login_form'] = login_form
                data['message'] = message
                return render(request, 'index.html', data)
            user_country = user.country
            if passcode == user.passcode:
                request.session['username'] = user.username
            else:
                message = _(u'Incorrect Passcode. Please enter your correct passcode.')
                login_form = LoginForm()
                data['login_form'] = login_form
                data['message'] = message
                return render(request, 'index.html', data)
            user.security_code = security_code
            user.save() 
            if user_country == country:
                if country != 'otc':
                    return HttpResponseRedirect(
                        reverse('home', 
                            kwargs={'country': country, 'token': 'ETH', 'security_code': security_code, 'crypto': 'FIAT'},
                        )      
                    )
                else:
                    return HttpResponseRedirect(
                        reverse('home',
                            kwargs={'country': country, 'token': 'ETH', 'security_code': security_code, 'crypto': 'GO'},
                        )
                    )
            else:
                message = _(u'Email is incorrect. Please make sure your email have been registered.')

        else:
            message = _(u'Email is incorrect. Please make sure your email have been registered.')
    
    else:
        login_form = LoginForm()

    data['login_form'] = login_form
    data['message'] = message
    
    return render(request, 'index.html', data)

def web(request, country):
    data = {}
    data['username'] = None
    email = None
    data['country'] = country
    message = ''
    token = 'ETH' #for now
    data['token'] = token
    data['currency'] = Currency.objects.get(country=country).currency

    if 'login' in request.POST:
        retry = True
        while retry:
            retry = False
            security_code = ''
            for n in range(6):
                security_code += random.choice(string.digits)
            testget = UserProfile.objects.filter(security_code=security_code)
            if len(testget) > 0:
                retry = True

        login_form = LoginForm(request.POST)

        email = str(login_form['email'].value())
        passcode = str(login_form['code'].value())

        login_status = True
        if login_status:
            try:
                user = UserProfile.objects.get(email=email)
            except Exception:
                message = _(u'Email is incorrect. Please make sure your email have been registered.')
                login_form = LoginForm()
                data['login_form'] = login_form
                data['message'] = message
                return render(request, 'web_index.html', data)
            user_country = user.country
            if passcode == user.passcode:
                request.session['username'] = user.username
            else:
                message = _(u'Incorrect Passcode. Please enter your correct passcode.')
                login_form = LoginForm()
                data['login_form'] = login_form
                data['message'] = message
                return render(request, 'web_index.html', data)
            user.security_code = security_code
            user.save() 
            if user_country == country:
                return HttpResponseRedirect(
                    reverse('home', 
                        kwargs={'country': country, 'token': 'ETH', 'security_code': security_code, 'crypto': 'FIAT'},
                    )      
                )
            else:
                message = _(u'Email is incorrect. Please make sure your email have been registered.')

        else:
            message = _(u'Email is incorrect. Please make sure your email have been registered.')
    
    else:
        login_form = LoginForm()

    data['login_form'] = login_form
    data['message'] = message


    return render(request, 'web_index.html', data)

def login_security(request, country):
    data = {}
    data['username'] = None
    email = None
    data['country'] = country
    message = ''
    token = 'ETH' #for now
    data['token'] = token
    data['currency'] = Currency.objects.get(country=country).currency

    if 'login' in request.POST:
        login_form = LoginForm(request.POST)
        login_status, username = login(login_form, country)
        if login_status:
            user = UserProfile.objects.get(username=username)
            user_country = user.country
            if user_country == country:
                return HttpResponseRedirect(
                    reverse('security',
                        kwargs={'username': username, 'country': country},
                    )
                )
            else:
                message = _(u'Email is incorrect. Please make sure your email have been registered.')

        else:
            message = _(u'Email is incorrect. Please make sure your email have been registered.')

    else:
        login_form = LoginForm()

    data['login_form'] = login_form
    data['message'] = message

    return render(request, 'index2.html', data)

def login(login_data, country):
    status = False    
    security_code = ''
    text = ''
    file = ''
    username = None

    if country == 'my' or country == 'otc':
        country_support = 'malaysia'
    elif country == 'au':
        country_support = 'australia'
    elif country == 'ng':
        country_support = 'nigeria'
    elif country == 'cn':
        country_support = 'china'
    elif country == 'cn-wb':
        country_support = 'onecity'
    elif country == 'vn':
        country_support = 'vietnam'
    elif country == 'id':
        country_support = 'indonesia'
    elif country == 'gh':
        country_support = 'ghana'
    elif country == 'za':
        country_support = 'southafrica'
    elif country == 'tz':
        country_support = 'tanzania'
    elif country == 'bw':
        country_support = 'botswana'
    elif country == 'ph':
        country_support = 'philippines'

    email = str(login_data['email'].value())
 
    try:
        user = UserProfile.objects.get(email=email, country=country)
    except Exception:
        return status, username 

    retry = True
    while retry:
        retry = False
        security_code = ''
        for n in range(6):
            security_code += random.choice(string.digits)
        testget = UserProfile.objects.filter(security_code=security_code)
        if len(testget) > 0:            
            retry = True
    
        

    user.security_code = security_code
    recipient = user.email
    user.save()
    username = user.username
    
    english_speakers = ['my', 'au', 'ng', 'gh', 'za', 'tz', 'bw', 'otc', 'ph']
    if country in english_speakers:
        country = 'en'
    elif country == 'cn-wb':
        country = 'cn'
    
    subject = _(u"This is your security code")
    to = [recipient]
    from_email = settings.EMAIL_HOST_USER

    ctx = {
        'securitycode': security_code,
        'myusername' : username,
        'country' : country_support
    }

    message = get_template('email/login-%s.html' % country).render(ctx)
    msg = EmailMessage(subject, message, to=to, from_email=from_email)
    msg.content_subtype = 'html'
    msg.send()


    status = True
 
    return (status, username)

def security(request, country, username):
    data = {}
    token = 'ETH' #for now
    data['token'] = token
    data['token'] = token
    data['currency'] = Currency.objects.get(country=country).currency
    message = ''
    data['username'] = username
    data['country'] = country
    user = UserProfile.objects.get(username=username)
       
 
    if 'login' in request.POST:
        security_form = SecurityForm(request.POST)
        code = str(security_form['code'].value())
        if code == user.security_code:
            request.session['username'] = user.username
            if country == 'otc':
                return HttpResponseRedirect(
                    reverse('update_profile', 
                        kwargs={'country': country, 'token': 'ETH', 'security_code': user.security_code, 'crypto': 'GO'},
                    )
                )
            else:
                return HttpResponseRedirect(
                    reverse('update_profile',
                        kwargs={'country': country, 'token': 'ETH', 'security_code': user.security_code, 'crypto': 'FIAT'},
                    )
                )
        else:
            message = _(u'Incorrect Security Code. Please enter your correct security code.')
   
    else:
        security_form = SecurityForm()

    data['security_form'] = security_form
    data['message'] = message

    return render(request, 'security.html', data)


def home(request, country, token, security_code, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    

    if user.first_login:
        return HttpResponseRedirect(reverse('update_profile', kwargs={
            'country': country,
            'token': token,
            'security_code': security_code,
            'crypto': crypto}))
    else:
        return HttpResponseRedirect(reverse('mainpage', kwargs={
            'country': country,
            'token': token,
            'security_code': security_code,
            'crypto': crypto}))

def menu(request, country, token, security_code, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:
        return render(request, 'relog.html')
    data = check
    username = data['username']
    user = data['user']
    crypto = None

    user = UserProfile.objects.get(username=username)
    wallet = Wallet.objects.filter(username=username)

    if len(wallet) == 0:
        data['no_wallet'] = True
    else:
       data['no_wallet'] = False

    if user.verified == True :
        data['verified_user'] = True
    else:
        data['verified_user'] = False
        

    return render(request, 'menu.html', data)


def mainpage(request, country, token, security_code, crypto):
    #check = shared_data(country, token, security_code, crypto)
    #if not check:
    #    return render(request, 'relog.html')
    #data = check
    data = referral(country, token, security_code, crypto) 
    username = data['username']
    user = data['user']
    data['notifications'] = notification(username=username, token=token)
   
    tokendata = Tokens.objects.get(token=token) 
    bid = tokendata.bid_usd
    ask = tokendata.ask_usd
    rate = Currency.objects.get(country=country).rate
    price_bid = round(bid * rate, 2)
    price_ask = round(ask * rate, 2)

    price = round((price_bid + price_ask)/2,2)

    try:
        wallet = Wallet.objects.get(username=username)
    except Exception as e:
        data['no_wallet'] = True

    try:
        wallet = Erc20Wallet.objects.get(username=username)
    except Exception as e:
        data['no_erc20wallet'] = True    
   
    all_tokens = Tokens.objects.all()
    for token_data in all_tokens:

        tokendata = Tokens.objects.get(token=token_data.token)
        ask_offer = tokendata.ask_usd
        bid_offer = tokendata.bid_usd
        ask_offer = round(ask_offer, 10)

        bid_offer = round(bid_offer, 10)
        price = 0
        rate = 0

        if crypto == 'FIAT':
            ask_rate = Currency.objects.get(country=country).rate
            bid_rate = Currency.objects.get(country=country).rate
        else:
            otc = Tokens.objects.get(token=crypto)
            mid_otc = (otc.bid_usd + otc.ask_usd)/2
            ask_rate = 1 / otc.ask_usd
            bid_rate = 1 / otc.ask_usd

        eth = Tokens.objects.get(token='ETH')
        mid_eth = (eth.bid_usd + eth.ask_usd)/2

        non_pay_list = ['1CT']

        if token in non_pay_list:
            min_token = round(mid_eth/tokendata.ask_usd) * 0.05
        else:
            mid_token = (tokendata.bid_usd + tokendata.ask_usd)/2
            min_token = round(mid_eth/mid_token, 2) * Decimal(0.05)

        price_ask = token_data.token.lower() + '_ask'
        price_bid = token_data.token.lower() + '_bid'

        if crypto == 'FIAT':
            data[price_ask] = round(ask_offer * ask_rate, 2)
            data[price_bid] = round(bid_offer * bid_rate, 2)
        else:
            data[price_ask] = round(ask_offer * ask_rate, 5)
            data[price_bid] = round(bid_offer * bid_rate, 5)
        
        data[token_data.token.lower()] = token_data


        fiat_price = Currency.objects.get(country=country).rate
        pls_token = Tokens.objects.get(token='PLS')
        pls_price = pls_token.ask_usd
        eth_price = 1 / eth.ask_usd
        data['eth_price'] = round(pls_price * eth_price, 5) 
        data['fiat_price'] = round(pls_price * fiat_price, 2)       


    
    

    return render(request, 'mainpage.html', data)


def update_profile(request, country, token, security_code, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    
    if 'update' in request.POST:
        form = UpdateForm(request.POST, initial={'country': country,})
        
        user.phone_number = str(form['phone_number'].value())
        user.bank_name = str(form['bank_name'].value())
        user.bank_account = str(form['bank_account'].value())
        user.bank_holder = str(form['holder_name'].value())

        try:
            int(form['passcode'].value())
        except Exception as e:
            form = UpdateForm(request.POST, request.FILES, initial={'country': country,})
            message = _(u"Passcode must be numbers")
            data['form'] = form
            data['message'] = message
            return render(request, 'update_profile.html', data)

        passcode = str(form['passcode'].value())
        repasscode = str(form['passcode'].value())
        if passcode == repasscode:
            user.passcode = passcode
            user.save()
        else:
            message = _(u"Passcode does not match")
            form = UpdateForm(request.POST, request.FILES, initial={'country': country,})
            data['form'] = form
            data['message'] = message
            return render(request, 'update_profile.html', data)

        
        if country == 'au':
            user.bsb = str(form['bsb'].value())
            user.payid = str(form['payid'].value())
        
        user.first_login = False
        user.save()
    
        if user.first_login:
            return HttpResponseRedirect(reverse('create_wallet', kwargs={
                'country': country,
                'token': token, 
                'security_code': security_code,
                'crypto': crypto}))
        else:
            return HttpResponseRedirect(reverse('mainpage', kwargs={
                'country': country,
                'token': token,
                'security_code': security_code,
                'crypto': crypto}))
    else:
        form = UpdateForm(
            initial={
                'country': country,
                'phone_number': user.phone_number,
                'bank_name': user.bank_name,
                'bank_account': user.bank_account,
                'holder_name': user.bank_holder,
                'bsb': user.bsb,
                'payid': user.payid,
            },
        )
    data['form'] = form
    data['first_login'] = user.first_login 
    data['notifications'] = notification(username=username, token=token)

    return render(request, 'update_profile.html', data)

def create_wallet(request, country, token, security_code, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:
        return render(request, 'relog.html')
    data = check
    username = data['username']
    user = data['user']
    data['notifications'] = notification(username=username, token=token)

    wallet = Wallet.objects.filter(username=username)

    if len(wallet) == 0:
        data['no_wallet'] = True
    else:
        data['no_wallet'] = False


    if 'update' in request.POST:
        form = UpdateForm(request.POST, request.FILES , initial={'country': country})
        
        user.upload_ic = form['upload_ic'].value()
        user.upload_selfie = form['upload_selfie'].value()
        user.first_login = False
        user.save()

        wallet = None
        erc20_wallet = None

        #eth
        try:
            wallet = Wallet.objects.get(username=username)
        except Exception:
            Wallet.objects.create(username=username)
            wallet = Wallet.objects.get(username=username)

        return render(request, 'wallet_thankyou.html', data)

    else:
        form = UpdateForm(
            initial={
                'country': country,
            },
        )
    data['form'] = form
    data['first_login'] = user.first_login

    return render(request, 'create_wallet.html', data)

def profile(request, country, token, security_code, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']   
    data['notifications'] = notification(username=username, token=token)
    data['member_id'] = user.member_id
    data['email'] = user.email
    data['phone_number'] = user.phone_number
    
    make_trades = Offers.objects.filter(maker=username, completed=True)
    take_trades = Offers.objects.filter(taker=username, completed=True)
    cancel_make_trades = Offers.objects.filter(maker=username, cancelled=True)
    cancel_take_trades = Offers.objects.filter(taker=username, cancelled=True)   
    data['success'] = len(make_trades) + len(take_trades)
    data['cancelled'] = len(cancel_make_trades) + len(cancel_take_trades)
    data['feedback'] = user.feedback
    data['created'] = user.created
    data['last_on'] = user.last_online

    data['bank_name'] = user.bank_name
    data['bank_account'] = user.bank_account
    data['bank_holder'] = user.bank_holder

    if country == 'au':
        data['bsb'] = user.bsb
        data['payid'] = user.payid
 
    return render(request, 'profile.html', data)


def deposit(request, country, token, security_code, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    erc20wallet = None
    wallet = None

    if token == 'ETH':
        try:   
            wallet = Wallet.objects.get(username=username)
        except Exception as e:
            data['process_message'] = _(u"It seems that you have not made your wallet yet. Click the Wallet icon to create one.")
            return render(request, 'process_error.html', data) 
    
    else:
        try:
            erc20wallet = Erc20Wallet.objects.get(username=username, token='USDT')
        except Exception as e:
            return HttpResponseRedirect(reverse('wallet', kwargs={
                'country': country,
                'token': token,
                'security_code': security_code,
                'crypto': crypto
            }))
 
    if not token=='ETH':   
        if not erc20wallet.address:
            data['process_message'] = _(u"Your ERC20 Wallet is still being created in the blockchain. Please check again after 30 minutes if you have just pressed the Create button.")
            return render(request, 'process_error.html', data) 

    if token == 'ETH':
        if not wallet.address:
            data['message'] = _(u"Please wait for verification by our admin. You will be notified via e-mail once your wallet is ready")

    if token == 'ETH':
        data['address'] = wallet.address
        data['qr'] = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=%s" % wallet.address
    else:
        data['erc20_address'] = erc20wallet.address
        data['qr_erc20'] = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=%s" % erc20wallet.address 

    data['notifications'] = notification(username=username,  token=token)
    form = DepositForm()
    data['form'] = form 
    if request.POST:
        tx_hash = DepositForm(request.POST)
        tx_hash = str(tx_hash['txhash'].value())
        if token == 'ETH' and '0x' in tx_hash:
            tx_receipt = False
            try:
                tx_receipt = w3.eth.getTransaction(tx_hash)
            except Exception: 
                data['message'] = _(u'Transaction is not ready yet or invalid. Please enter a confirmed tx hash.')
            if tx_receipt:
                history = None
                try:
                    history = History.objects.get(activity__contains=tx_hash)
                except Exception:
                    pass
                if wallet.address == tx_receipt.to and not history and tx_receipt.value > 0:
                    wallet.balance += Decimal(tx_receipt.value)
                    wallet.save()
                    History.objects.create(
                        username = username,
                        token = token,
                        amount = tx_receipt.value,
                        activity = "Deposit from external wallet. Tx Hash: %s" % tx_hash,
                    )
                    return HttpResponseRedirect(reverse('wallet', kwargs={
                        'country': country,
                        'token': token,
                        'security_code': security_code,
                        'crypto': crypto
                    }))
                else:
                    data['message'] = _(u'This tx hash is not valid for this wallet.')
            else:
                data['message'] = _(u'Transaction is not ready yet or invalid. Please enter a confirmed tx hash.')
        elif token != 'ETH' and '0x' in tx_hash:
            tx_receipt = False
            try:
                tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
            except Exception:
                data['message'] = _(u'Transaction is not ready yet or invalid. Please enter a confirmed tx hash.')
    
            if tx_receipt:
                try:
                    get_address = tx_receipt.logs[0].topics[2]
                except Exception:
                    get_address = None
                sift_address = erc20wallet.address.split('x')[1]
                history = None
                token_deposit = None
                try:
                    token_deposit = Tokens.objects.get(address=tx_receipt.logs[0].address)
                except Exception:
                    data['message'] = _(u'Token deposited not supported by iP2PGo')
                try:
                    history = History.objects.get(activity__contains=tx_hash)
                except Exception:
                    pass
                if get_address and sift_address.lower() in str(get_address.hex()) and not history and token_deposit:
                    amount = int(tx_receipt.logs[0]['data'], 0)
                    amount = Decimal(amount)
                    transfer = False
                    try:
                        transfer = get_erc20_balance(username, amount, token_deposit.token)
                    except Exception:
                        pass
                    if transfer:
                        deposit_wallet = Erc20Wallet.objects.get(username=username, token=token_deposit.token)
                        deposit_wallet.balance += amount
                        deposit_wallet.save()
                        History.objects.create(
                            username = username,
                            token = token_deposit.token,
                            amount = amount,
                            activity = "Deposit from external wallet. Tx Hash: %s" % tx_hash,
                        )
                        return HttpResponseRedirect(reverse('wallet', kwargs={
                            'country': country,
                            'token': token_deposit.token,
                            'security_code': security_code,
                            'crypto': crypto
                        }))
                    else:
                        data['message'] = _(u'Please contact our team with your transaction hash, complete with your token deposit details.')
                else:
                    data['message'] = _(u'This tx hash is not valid for this wallet.')
        else:
            data['message'] = _(u'Please provide a valid transaction hash')
    return render(request, 'deposit.html', data)


def withdrawal(request, country, token, security_code, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    data['notifications'] = notification(username=username, token=token)
    locked_tokens = 0
    locked_crypto = 0
    tokendata = Tokens.objects.get(token=token)
    
    withdraw_limit = 10
    within24h = timezone.now() - timedelta(days=1)
    #get history
    withdraw_qt = History.objects.filter(username=username, activity__contains="Withdrawal", time__gte=within24h)
    if len(withdraw_qt) > withdraw_limit:
        data['process_message'] = _(u"You have exceeded your daily withdraw limit. Please try again tomorrow")
        return render(request, 'process_error.html', data)

    try:
        if token == 'ETH':
            wallet = Wallet.objects.get(username=username)
        else:
            erc20wallet = Erc20Wallet.objects.get(username=username, token=token)
    except Exception:
        if token == 'ETH':
            data['process_message'] = _(u"It seems that you have not made your wallet yet. Click the Wallet icon to create one.")
            data['no_wallet'] = True
            return render(request, 'process_error.html', data)
        else:
            return HttpResponseRedirect(reverse('wallet', kwargs={
                'country': country,
                'token': token,
                'security_code': security_code,
                'crypto': crypto
            }))   
 

    # must get the trade values here later.
    sell_offers = Offers.objects.filter(maker=username, token=token,
        trade_type='sell').exclude(completed=True).exclude(cancelled=True)
    
    for offer in sell_offers:
        locked_tokens += offer.maximum

    
    buy_offers = Offers.objects.filter(maker=username, crypto=token, trade_type='buy').exclude(completed=True).exclude(cancelled=True).exclude(crypto=None)


    
    for offer in buy_offers:
       
        eth = Tokens.objects.get(token=offer.token) 
        otc = Tokens.objects.get(token=offer.crypto)
        ask_otc = otc.ask_usd

        rate = 1 / otc.ask_usd

        if token == 'SCC' or token == 'TEL':
            price_ask_otc = round(ask_otc * rate, 8)
        else:
            price_ask_otc = round(ask_otc * rate, 2)

        price = round(price_ask_otc + price_ask_otc * offer.spread, 2)

        price_max = 0
        
        if offer.crypto == token: 
            if offer.token == 'ETH':       
                offer.maximum = w3.fromWei(offer.maximum,'ether')
 
                tokendata = Tokens.objects.get(token=offer.token) 
                otc = Tokens.objects.get(token=offer.crypto)
                mid_otc = (otc.ask_usd + otc.ask_usd)/2
    
                mid_token = (tokendata.ask_usd + tokendata.ask_usd)/2
                maximum = round(mid_token/mid_otc, 5) * offer.maximum

                offer_max = maximum * price
                price_max = w3.toWei(offer_max,'ether')


            else:
                offer.maximum = offer.maximum/10 ** eth.decimal_places

                tokendata = Tokens.objects.get(token=offer.token)
                otc = Tokens.objects.get(token=offer.crypto)
                mid_otc = (otc.ask_usd + otc.ask_usd)/2

                mid_token = (tokendata.ask_usd + tokendata.ask_usd)/2
                maximum = round(mid_token/mid_otc, 5) * offer.maximum

                offer_max = maximum * price
                price_max = offer_max * 10 ** eth.decimal_places

        locked_crypto += price_max            


    if token == 'ETH':
        nett = wallet.balance - (locked_tokens + locked_crypto)
    else:
        nett = erc20wallet.balance - (locked_tokens + locked_crypto)

    if nett < 0:
        nett = 0
    
    tx_hash = None

    if token == 'GO':
        fees = 0
    else:
        if user.verified:
            fees = 0.005
        else:
            fees = 0.01 
        token_info = Tokens.objects.get(token=token)
        eth = Tokens.objects.get(token='ETH')
        eth_mid = (eth.bid_usd + eth.ask_usd) / 2
        token_mid = (token_info.bid_usd + token_info.ask_usd) / 2
        token_per_eth = (eth_mid / token_mid)
        fees = (token_per_eth) * Decimal(fees * 10 ** token_info.decimal_places)

    if user.verified:
        withdrawal_minimum = 0.05
    else:
        withdrawal_minimum = 0.1
    token_info = Tokens.objects.get(token=token)
    eth = Tokens.objects.get(token='ETH')
    eth_mid = (eth.bid_usd + eth.ask_usd) / 2
    token_mid = (token_info.bid_usd + token_info.ask_usd) / 2
    token_per_eth = (eth_mid / token_mid)
    withdrawal_minimum = (token_per_eth) * Decimal(withdrawal_minimum * 10 ** token_info.decimal_places)

    if 'withdraw' in request.POST:
        form = WithdrawalForm(request.POST)
        form_address = str(form['address'].value())
        try:
            form_address = w3.toChecksumAddress(form_address)
        except Exception:
            data['message'] = _(u'Please provide a valid 0x address')
        if form_address in banlist.WALLETS:
            data['process_message'] = _(u'The wallet is in our ban list for previous fraudalent activities and will not be allowed.')
            return render(request, 'process_error.html', data)
        if form_address[0]=='0' and form_address[1]=='x' and len(form_address.strip()) == 42 and token != 'TMB':

            address = form['address'].value()
            address = str(address)
            if token == 'ETH':
                amount = w3.toWei(Decimal(form['amount'].value()), 'ether')
            else:
                amount = Decimal(form['amount'].value()) * 10 ** tokendata.decimal_places
            if amount <= nett and amount >= withdrawal_minimum:
                if fees <= amount:
                    try:
                        if token == 'ETH' and form_address != wallet.address:
                            tx_hash = withdraw(username, address, amount)
                        elif token != 'ETH' and form_address != erc20wallet.address:
                            tx_hash = withdraw_erc20(username, address, amount, token)
                        else:
                            data['message'] = _(u'You may not withdraw to your own address')                     
                    except Exception:
                        data['message'] = _(u"Your balance could not be withdrawn at this time. Please try again at a later time.")
      
                    if tx_hash:
                        if tx_hash == 'Success':
                            data['address'] = address
                            data['complete_message'] = _(u"Your token is successfully transferred to %s") % address
                        else:
                            data['complete_message'] = _(u"Your withdrawal request is sent to the Ethereum blockchain. You can check the transaction status with this transaction hash: ")
                        data['tx_hash'] = tx_hash
                        return render(request, 'complete_withdraw.html', data)
                else:
                    data['message'] = _(u"You have insufficient available %s for withdrawal. Please withdraw the suggested amount or lower") % token
                    data['form'] = WithdrawalForm(request.POST)
            else: 
                if amount < withdrawal_minimum:
                    data['message'] = _(u"Please withdraw at least {withdraw} {tkn}").format(withdraw=withdrawal_minimum / 10 ** tokendata.decimal_places, tkn=token)
                else:
                    data['message'] = _(u"You have insufficient available %s for withdrawal. Please withdraw the suggested amount or lower") % token
                data['form'] = WithdrawalForm(request.POST)
            return render(request, 'withdrawal.html', data)
        else:
            if token != 'TMB':
                data['message'] = _(u"Please supply a valid Ethereum wallet address.")
            elif token == 'TMB':
                data['message'] = _(u"TMB withdrawal is temporarily locked at this moment while we resolve an issue relating to the token's rate and actual values in each member's wallet.")

            data['form'] = WithdrawalForm(request.POST)
            return render(request, 'withdrawal.html', data) 
 
    elif 'all' in request.POST:
        form = WithdrawalForm(initial={'amount': nett})
    else:
        form = WithdrawalForm()
   
    data['form'] = form 
    if token == 'ETH':
        data['nett'] = w3.fromWei(nett, 'ether')
    else:
        data['nett'] = nett/10 ** tokendata.decimal_places
    
    return render(request, 'withdrawal.html', data)

    
def referral(country, token, security_code, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    #data['notifications'] = notification(username=username, token=token)

    current_balance = 0
 
    data['member_id'] = user.member_id

    lang_dict = {
        'cn': 'zh-hans',
        'my': 'en-us',
        'id': 'id',
        'cn-wb': 'zh-hans',
        'au': 'en-us',
        'vn': 'vi',
        'ng': 'en-us',
        'za': 'en-us',
        'gh': 'en-us',
        'tz': 'en-us',
        'bw': 'en-us',
        'otc': 'en-us',
        'ph': 'en-us',
    }

    ref_country = user.country
    
    if ref_country == 'cn-wb':
        ref_country = 'www'
    data['referral_link'] = "http://%s.ip2pgo.com/%s/registration/%s/%s" % (
        ref_country,
        lang_dict[country],
        user.country,
        user.member_id,
    )

    data['qr'] = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=%s" % data['referral_link']  

    data['friends'] = []
    try:
        ref = Referral.objects.get(username=username)
    except Exception:
        Referral.objects.create(username=username)
        ref = Referral.objects.get(username=username)

    history = History.objects.filter(username=username, activity__contains='Referral')
    
    for his in history:
        tokendata = Tokens.objects.get(token=his.token)
        setattr(his, 'norm_amount', his.amount / 10 ** tokendata.decimal_places)        
 
    data['history'] = history
    first_line = None
    second_line = None
    others_line = None
    nowallets = []
   
    if ref.first_line and ',' in ref.first_line:
        first_line = ref.first_line.split(',')
    else:
        first_line = [ref.first_line]
    if first_line:
        data['firstlevels'] = first_line
        for referral_id in first_line:
            if referral_id:
                ref_user = UserProfile.objects.get(member_id=referral_id)
                wallet = None
                if ref_user:
                    try:
                        wallet = Wallet.objects.get(username=ref_user.username)
                    except Exception:
                        nowallets.append(referral_id)
                    if wallet and not wallet.tx_hash:
                        nowallets.append(referral_id)
 
    if ref.second_line and ',' in ref.second_line:
        second_line = ref.second_line.split(',')
    else:
        second_line = [ref.second_line]
    if second_line:
        data['secondlevels'] = second_line
        for referral_id in second_line:
            if referral_id:
                ref_user = UserProfile.objects.get(member_id=referral_id)
                wallet = None
                if ref_user:
                    try:
                        wallet = Wallet.objects.get(username=ref_user.username)
                    except Exception:
                        nowallets.append(referral_id)
                    if wallet and not wallet.tx_hash:
                        nowallets.append(referral_id)
 
    if ref.others_line and ',' in ref.others_line:
        others_line = ref.others_line.split(',')
    else:
        others_line = [ref.others_line]
    if others_line:
        data['otherlevels'] = others_line
        for referral_id in others_line:
            if referral_id:
                ref_user = UserProfile.objects.get(member_id=referral_id)
                wallet = None
                if ref_user:
                    try:
                        wallet = Wallet.objects.get(username=ref_user.username)
                    except Exception:
                        nowallets.append(referral_id)
                    if wallet and not wallet.tx_hash:
                        nowallets.append(referral_id)
    
    data['nowallets'] = nowallets    
 
    return data
    #return render(request, 'referral.html', data)


def passcode(request, country, token, security_code, offer_id, amount, fiat, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    data['notifications'] = notification(username=username, token=token)

    data['passcode'] = True
    
    user_passcode = user.passcode 

    form = PasscodeForm() 
    
    if 'cancel' in request.POST:
        offer = Offers.objects.get(offer_id=offer_id)
        offer.taker = None
        offer.save()

        try:
            Notification.objects.get(offer_id=offer_id, event="cancel take")
        except Exception:
            Notification.objects.create(
                username=offer.maker, offer_id=offer_id, event="cancel take")
        
        return HttpResponseRedirect(reverse('wallet', kwargs={
            'country': country,
            'token': token,
            'security_code': security_code,
            'crypto': crypto
        }))
    elif 'code' in request.POST:
        form = PasscodeForm(request.POST)
        #passcode = str(request.POST['code'])
        if request.POST['code'] == user_passcode:
        #if passcode == user_passcode:
            basket.send(sender=passcode.__name__, offer_id=offer_id, 
                amount=amount, fiat=fiat, taker=username, token=token, crypto=crypto)            
            if crypto == 'FIAT':
                return HttpResponseRedirect(reverse('payment_confirm', kwargs={
                    'country': country,
                    'token': token,
                    'security_code': security_code,
                    'crypto': crypto,
                    'offer_id': offer_id,
                }))
            else:
                return HttpResponseRedirect(reverse('otc_confirm', kwargs={
                    'country': country,
                    'token': token,
                    'security_code': security_code,
                    'crypto': crypto,
                    'offer_id': offer_id,
                }))

        else:
            if passcode != '':
                data['message'] = _(u"Passcode is incorrect.")

    data['form'] = form
   
    return render(request, 'passcode.html', data)


def buy_list(request, country, token, security_code, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    data['notifications'] = notification(username=username, token=token)
    eth = Tokens.objects.get(token=token)
    bid = eth.bid_usd
    tokendata = Tokens.objects.get(token=token)
    rate = Currency.objects.get(country=country).rate
    
    if token == 'SCC' or token == 'TEL':
        price_bid = round(bid * rate, 8)
    else:
        price_bid = round(bid * rate, 2) 

    data['buy_offers'] = []
    if crypto == 'FIAT':
        if user.verified: 
            buy_offers = Offers.objects.filter(country=country, trade_type='buy', taker=None, token=token, crypto=None).exclude(completed=True).exclude(cancelled=True).exclude(token='TMB')
        else:
            buy_offers = []
    else:
        if user.verified:
            buy_offers = Offers.objects.filter(trade_type='buy', taker=None, token=token, crypto=crypto).exclude(completed=True).exclude(cancelled=True).exclude(token='TMB')   
        else:
            buy_offers = Offers.objects.filter(trade_type='buy', taker=None, token=token, crypto=crypto).exclude(completed=True).exclude(cancelled=True).exclude(token='TMB')

    if len(buy_offers) == 0:
        data['no_buylist'] = True
    else:
        data['no_buylist'] = False
        
    for buy_offer in buy_offers:
        if buy_offer.threshold == 0:
            data['buy_offers'].append(buy_offer)
        elif buy_offer.threshold >= price_bid + (price_bid * buy_offer.spread):
            data['buy_offers'].append(buy_offer)
        elif buy_offer.maker == username:
            data['buy_offers'].append(buy_offer)
        else:
            pass
      
        maker = UserProfile.objects.get(username = buy_offer.maker)

        if maker.verified == True:
            ver_maker = UserProfile.objects.get(username = buy_offer.maker, verified=True)
            data['verified'] = ver_maker.username
    

    if crypto == 'FIAT':   
        for offer in data['buy_offers']:
            setattr(offer, 'price', '%s%s' % (data['currency'], round(price_bid + price_bid * offer.spread, 2)))
            if token == 'SCC' or token == 'TEL':
                price = round(price_bid + price_bid * offer.spread, 4)
            else:
                price = round(price_bid + price_bid * offer.spread, 2)
            # want to get the rating for the user too
            maker = UserProfile.objects.get(username=offer.maker)
            setattr(offer, 'rating', maker.feedback) 
            if token == 'ETH':
                offer.minimum = w3.fromWei(offer.minimum,'ether')
                offer.maximum = w3.fromWei(offer.maximum,'ether')
                price_max =  offer.maximum * price
                price_min = offer.minimum  * price
                setattr(offer, 'price_max', price_max)
                setattr(offer, 'price_min', price_min)
            else:
                offer.maximum = offer.maximum/10 ** eth.decimal_places
                offer.minimum = offer.minimum/ 10 ** eth.decimal_places
                price_max =  offer.maximum * price
                price_min = offer.minimum  * price
                setattr(offer, 'price_max', price_max)
                setattr(offer, 'price_min', price_min)
            setattr(offer, 'bank_name', maker.bank_name)
            if offer.threshold < price_bid + (price_bid * offer.spread) and offer.threshold != 0:
                setattr(offer, 'limit_up', True)

    else:
        for offer in data['buy_offers']:
            otc = Tokens.objects.get(token=crypto)
            ask_otc = otc.ask_usd

            rate = 1 / otc.ask_usd

            if token == 'SCC' or token == 'TEL':
                price_ask_otc = round(ask_otc * rate, 8)
            else:
                price_ask_otc = round(ask_otc * rate, 2)

            setattr(offer, 'price', '%s%s' % (data['currency'],
                round(price_ask_otc + price_ask_otc * offer.spread, 2)))
            maker = UserProfile.objects.get(username=offer.maker)
            setattr(offer, 'rating', maker.feedback)
            price = round(price_ask_otc + price_ask_otc * offer.spread, 2)
         
            if token == 'ETH':       
                offer.maximum = w3.fromWei(offer.maximum,'ether')
                offer.minimum = w3.fromWei(offer.minimum,'ether')
 
                tokendata = Tokens.objects.get(token=token) 
                otc = Tokens.objects.get(token=crypto)
                mid_go = (otc.ask_usd + otc.ask_usd)/2
    
                mid_token = (tokendata.ask_usd + tokendata.ask_usd)/2
                maximum = round(mid_token/mid_go, 5) * offer.maximum
                minimum =  round(mid_token/mid_go, 5) * offer.minimum

                price_max = maximum * price
                price_min = minimum * price

                setattr(offer, 'price_max', price_max)
                setattr(offer, 'price_min', price_min)

            else:
                offer.maximum = offer.maximum/10 ** eth.decimal_places
                offer.minimum = offer.minimum/ 10 ** eth.decimal_places

                tokendata = Tokens.objects.get(token=token)
                otc = Tokens.objects.get(token=crypto)
                mid_go = (otc.ask_usd + otc.ask_usd)/2

                mid_token = (tokendata.ask_usd + tokendata.ask_usd)/2
                if token == 'SCC' or token == 'TEL':
                    maximum = round(mid_token/mid_go, 8) * offer.maximum
                    minimum = round(mid_token/mid_go, 8) * offer.minimum
                else:
                    maximum = round(mid_token/mid_go, 5) * offer.maximum
                    minimum = round(mid_token/mid_go, 5) * offer.minimum                

                price_max = maximum * price
                price_min = minimum * price

                setattr(offer, 'price_max', price_max)
                setattr(offer, 'price_min', price_min)
            if offer.threshold < price_bid + (price_bid * offer.spread) and offer.threshold != 0:
                setattr(offer, 'limit_up', True)
        
    

    data['taken'] = []

    taken = Offers.objects.filter(taker=username, token=token, trade_type='buy').exclude(completed=True, released=True).exclude(cancelled=True)
    for offer in taken:
        offer.amount = offer.amount / 10 ** tokendata.decimal_places  
        data['taken'].append(offer)

    made = Offers.objects.filter(maker=username).exclude(
        completed=True, released=True).exclude(cancelled=True)
    for offer in made:
        if offer.taker:
            offer.amount = offer.amount / 10 ** tokendata.decimal_places  
            data['taken'].append(offer)
    
    if len(data['taken']) == 0:
        data['no_taken'] = True 
      
    data['price_bid'] = price_bid
    data['rate'] = rate
    
    return render(request, 'buy_list.html', data)


def sell_list(request, country, token, security_code, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    data['notifications'] = notification(username=username, token=token)
    eth = Tokens.objects.get(token=token)
    ask = eth.ask_usd
    tokendata = Tokens.objects.get(token=token) 
    rate = Currency.objects.get(country=country).rate

    if token == 'SCC' or token == 'TEL':
        price_ask = round(ask * rate, 8)
    else:
        price_ask = round(ask * rate, 2)

    data['sell_offers'] = []

    if crypto == 'FIAT':
        if user.verified:
            sell_offers = Offers.objects.filter(country=country, trade_type='sell', taker=None, token=token, crypto=None).exclude(completed=True).exclude(cancelled=True).exclude(token='TMB')
        else:
            sell_offers = None
    else:
        if user.verified:
            sell_offers = Offers.objects.filter(trade_type='sell', taker=None, token=token, crypto=crypto).exclude(completed=True).exclude(cancelled=True).exclude(token='TMB')
        else:
            sell_offers = Offers.objects.filter(trade_type='sell', taker=None, token=token, crypto=crypto).exclude(completed=True).exclude(cancelled=True).exclude(country='otc').exclude(token='TMB')
    
    for sell_offer in sell_offers:
        if sell_offer.threshold == 0:
            data['sell_offers'].append(sell_offer)
        elif sell_offer.threshold <= price_ask + (price_ask * sell_offer.spread):
            data['sell_offers'].append(sell_offer)
        elif sell_offer.maker == username:
            data['sell_offers'].append(sell_offer)
        else:
            pass
 
        maker = UserProfile.objects.get(username = sell_offer.maker)
        
        if maker.verified == True: 
            ver_maker = UserProfile.objects.get(username = sell_offer.maker, verified=True)
            data['verified'] = ver_maker.username

    if len(sell_offers) == 0:
        data['no_selllist'] = True
    else:
        data['no_selllist'] = False

    if crypto == 'FIAT':    
        for offer in data['sell_offers']:
            setattr(offer, 'price', '%s%s' % (data['currency'], 
                round(price_ask + price_ask * offer.spread, 2)))
            maker = UserProfile.objects.get(username=offer.maker)
            setattr(offer, 'rating', maker.feedback)
            if token == 'SCC' or token == 'TEL':
                price = round(price_ask + price_ask * offer.spread, 4)
            else:
                price = round(price_ask + price_ask * offer.spread, 2)
            if token == 'ETH':
                offer.minimum = w3.fromWei(offer.minimum,'ether')
                offer.maximum = w3.fromWei(offer.maximum,'ether')
                price_max =  offer.maximum * price
                price_min = offer.minimum  * price
                setattr(offer, 'price_max', price_max)
                setattr(offer, 'price_min', price_min)
            else:
                offer.maximum = offer.maximum/10 ** eth.decimal_places
                offer.minimum = offer.minimum/ 10 ** eth.decimal_places
                price_max =  offer.maximum * price
                price_min = offer.minimum  * price
                setattr(offer, 'price_max', price_max)
                setattr(offer, 'price_min', price_min)
            setattr(offer, 'bank_name', maker.bank_name)
            if offer.threshold > price_ask + (price_ask * offer.spread) and offer.threshold != 0:
                setattr(offer, 'limit_up', True)

    else:
        for offer in data['sell_offers']:
            otc = Tokens.objects.get(token=crypto)
            ask_otc = otc.ask_usd

            rate = 1 / otc.ask_usd

            if token == 'SCC' or token == 'TEL':
                price_ask_otc = round(ask_otc * rate, 8)
            else:
                price_ask_otc = round(ask_otc * rate, 2)

            setattr(offer, 'price', '%s%s' % (data['currency'],
                round(price_ask_otc + price_ask_otc * offer.spread, 2)))
            maker = UserProfile.objects.get(username=offer.maker)
            setattr(offer, 'rating', maker.feedback)
            price = round(price_ask_otc + price_ask_otc * offer.spread, 2)
         
            if token == 'ETH':       
                offer.maximum = w3.fromWei(offer.maximum,'ether')
                offer.minimum = w3.fromWei(offer.minimum,'ether')
 
                tokendata = Tokens.objects.get(token=token) 
                otc = Tokens.objects.get(token=crypto)
                mid_go = (otc.ask_usd + otc.ask_usd)/2
    
                mid_token = (tokendata.ask_usd + tokendata.ask_usd)/2
                maximum = round(mid_token/mid_go, 5) * offer.maximum
                minimum =  round(mid_token/mid_go, 5) * offer.minimum

                price_max = maximum * price
                price_min = minimum * price

                setattr(offer, 'price_max', price_max)
                setattr(offer, 'price_min', price_min)

            else:
                offer.maximum = offer.maximum/10 ** eth.decimal_places
                offer.minimum = offer.minimum/ 10 ** eth.decimal_places

                tokendata = Tokens.objects.get(token=token)
                otc = Tokens.objects.get(token=crypto)
                mid_go = (otc.ask_usd + otc.ask_usd)/2

                mid_token = (tokendata.ask_usd + tokendata.ask_usd)/2
                if token == 'SCC' or token == 'TEL':
                    maximum = round(mid_token/mid_go, 8) * offer.maximum
                    minimum =  round(mid_token/mid_go, 8) * offer.minimum
                else:
                    maximum = round(mid_token/mid_go, 5) * offer.maximum
                    minimum =  round(mid_token/mid_go, 5) * offer.minimum

                price_max = maximum * price
                price_min = minimum * price

                setattr(offer, 'price_max', price_max)
                setattr(offer, 'price_min', price_min)
            if offer.threshold < price_ask + (price_ask * offer.spread) and offer.threshold != 0:
                setattr(offer, 'limit_up', True)


    data['taken'] = []

    taken = Offers.objects.filter(taker=username, token=token, trade_type='sell').exclude(completed=True, released=True).exclude(cancelled=True)
    for offer in taken:
        offer.amount = offer.amount / 10 ** tokendata.decimal_places      
        data['taken'].append(offer)

    made = Offers.objects.filter(maker=username, token=token, trade_type='sell').exclude(completed=True, released=True).exclude(cancelled=True)
    for offer in made:
        if offer.taker:
            offer.amount = offer.amount / 10 ** tokendata.decimal_places
            data['taken'].append(offer)
     
    if len(data['taken']) == 0:
        data['no_taken'] = True  
 
    data['price_ask'] = price_ask
    data['rate'] = rate


    
    
    return render(request, 'sell_list.html', data)

def buying(request, token, security_code, offer_id, country, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    tokendata = Tokens.objects.get(token=token)
    data['notifications'] = notification(username=username, token=token)
    try:
        if token == 'ETH':
            wallet_address = Wallet.objects.get(username=username).address
        else:
            wallet_address = Erc20Wallet.objects.get(username=username, token=token).address
    except Exception:
        if token == 'ETH':
            data['process_message'] = _(u"It seems that you have not made your wallet yet. Click the Wallet icon to create one.")
            data['no_wallet'] = True
            return render(request, 'process_error.html', data) 
        else:
            return HttpResponseRedirect(reverse('wallet', kwargs={
                'country': country,
                'token': token,
                'security_code': security_code,
                'crypto': crypto
            }))
            

    data['offer_id'] = offer_id
    buy_offer = Offers.objects.get(offer_id=offer_id)

    
    if token == 'ETH':
        seller_wallet = Wallet.objects.get(username=buy_offer.maker)
    else:
        seller_wallet = Erc20Wallet.objects.get(username=buy_offer.maker, token=token)
    

    data['maximum'] = buy_offer.maximum / 10 ** tokendata.decimal_places
    data['minimum'] = buy_offer.minimum / 10 ** tokendata.decimal_places
    data['buyer'] = buy_offer.maker
    data['payment_window'] = buy_offer.paymentwindow
    
    seller = UserProfile.objects.get(username=buy_offer.maker)
    data['rating'] = seller.feedback

    data['bank_name'] = seller.bank_name
    data['bank_account'] = seller.bank_account
    data['holder_name'] = seller.bank_holder
    if country == 'au':
        data['bsb'] = seller.bsb
        data['payid'] = seller.payid

    ask = tokendata.ask_usd
    rate = 0

    if crypto == 'FIAT':
        rate = Currency.objects.get(country=country).rate
    else:
        otc = Tokens.objects.get(token=crypto)
        rate = 1 / otc.ask_usd
    
    if token == 'SCC' or token == 'TEL':    
        price_ask = round(ask * rate, 8)
    else:
        price_ask = round(ask * rate, 5)
    form = Buying()

    eth_token = Tokens.objects.get(token='ETH')
    mid_eth = (eth_token.bid_usd + eth_token.ask_usd)/2
    mid_token = (tokendata.bid_usd + tokendata.ask_usd)/2
    min_token = round(mid_eth/mid_token) * 0.05
    fees_token = round(mid_eth/mid_token) * 0.005

    if crypto != 'FIAT':
        if crypto != 'ETH':
            otc_wallet = Erc20Wallet.objects.get(username=username, token=crypto)
        else:
            otc_wallet = Wallet.objects.get(username=username)

        otc_balance = Decimal(otc_wallet.balance)/10 ** eth_token.decimal_places
    
    if token == 'ETH':
        wallet = Wallet.objects.get(username=username)
    else:        
        wallet = Erc20Wallet.objects.get(username=username, token=token)        

    offer = Offers.objects.get(offer_id=offer_id)
    
    if request.method == 'POST':
        if not user.verified and crypto == 'FIAT':
            data['process_message'] = _(u"You must be a verified user to buy a fiat order.")
            data['no_wallet'] = True
            return render(request, 'process_error.html', data)

        purpose = "click buy"
        form = Buying(request.POST, initial={'country': country})

        if offer.verified_offer == True:
            if offer.verified_offer != user.verified:
                data['process_message'] = _(u"This offer is for verified user only. Please click on Be A Verified User on the side menu to verified your profile")
                return render(request, 'process_error.html', data)

        if wallet.balance < 0:
            data['process_message'] =_(u"You still have outstanding balance to clear from your account. Please deposit {tkn} into your wallet, keeping in mind of the {fee} {tkn} deposit fee, and click \"Clear Outstanding\". You'll be able to trade again afterwards.").format(tkn=token, fee=fees_token)
            return render(request, 'process_error.html', data)
        if crypto != 'FIAT':
            fiat = str(request.POST['fiat'])
            if country == 'id' or country == 'vn':
                fiat = fiat.split(',')
                fiat = '.'.join(fiat)
            if otc_balance < Decimal(fiat):
                data['process_message'] = _(u"You don't have enough {crypto} balance in your wallet to buy from the seller. Please deposit {crypto} into your wallet, then try again.").format(crypto=crypto)
                return render(request, 'process_error.html', data)
               

        buy_amount = 0
        if token == 'ETH':
            buy_amount = w3.toWei(Decimal(form['amount'].value()),'ether')
        else:
            buy_amount = Decimal(form['amount'].value()) * 10 ** tokendata.decimal_places 

        if buy_amount < buy_offer.minimum:
            data['message'] = _(u"The amount is lower than the trade offer's minimum.")
        elif buy_amount > buy_offer.maximum:
            data['message'] = _(u"The amount is higher than the trade offer's maximum.") 
        else:
            buy_offer.taker = username
            buy_offer.save()

            if crypto == 'FIAT':
                mail_notifications(username, offer_id, "click take", country)

                try:
                    Notification.objects.get(
                        username=buy_offer.maker, offer_id=offer_id, event="trade")
                except Exception:
                    Notification.objects.create(
                        username=buy_offer.maker, offer_id=offer_id, event="trade")

            else:
                try:
                    Notification.objects.get(
                        username=buy_offer.maker, offer_id=offer_id, event="trade_otc")
                except Exception:
                    Notification.objects.create(
                        username=buy_offer.maker, offer_id=offer_id, event="trade_otc") 

            return HttpResponseRedirect(
                reverse(
                    'passcode',
                    kwargs={
                        'country':country,
                        'token': token, 
                        'security_code': security_code,
                        'crypto': crypto,
                        'offer_id':offer_id,
                        'amount':form['amount'].value(),
                        'fiat':request.POST['fiat'],
                    },
                )
            )  

    tokendata = Tokens.objects.get(token=token)
    mid_otc = 0
    if crypto == 'GO':
        tokenotc = Tokens.objects.get(token='GO')
        mid_otc = (tokenotc.bid_usd + tokenotc.ask_usd)/2

    elif crypto == 'TUSD':
        tokenotc = Tokens.objects.get(token='TUSD')
        mid_otc = (tokenotc.bid_usd + tokenotc.ask_usd)/2

    mid_token = (tokendata.bid_usd + tokendata.ask_usd)/2

    if crypto == 'FIAT':
        if token == 'SCC' or token == 'TEL':
            final_price = round(price_ask + price_ask * buy_offer.spread, 8)
        else:
            final_price = round(price_ask + price_ask * buy_offer.spread, 2)
    else:
        if token == 'SCC' or token == 'TEL':
            final_price = round(price_ask + price_ask * buy_offer.spread, 8) 
        else:
            final_price = round(price_ask + price_ask * buy_offer.spread, 5)
    data['offer_price'] = final_price
    data['rate'] = rate
    data['form'] = form

    return render(request, 'buying.html', data)


def selling(request, token, security_code, offer_id, country, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    tokendata = Tokens.objects.get(token=token)
    data['notifications'] = notification(username=username, token=token)
  
    try:
        if token == 'ETH':
            wallet_address = Wallet.objects.get(username=username).address
        else:
            wallet_address = Erc20Wallet.objects.get(username=username, token=token).address
    except Exception:
        if token == 'ETH':
            data['process_message'] = _(u"It seems that you have not made your wallet yet. Click the Wallet icon to create one.")
            data['no_wallet'] = True
            return render(request, 'process_error.html', data)
        else:
            return HttpResponseRedirect(reverse('wallet', kwargs={
                'country': country,
                'token': token,
                'security_code': security_code,
                'crypto': crypto,
            }))
            
 
    data['offer_id'] = offer_id
    sell_offer = Offers.objects.get(offer_id=offer_id)
    if token == 'ETH':
        buyer_wallet = Wallet.objects.get(username=sell_offer.maker)
    else:
        buyer_wallet = Erc20Wallet.objects.get(username=sell_offer.maker, token=token)

    data['maximum'] = sell_offer.maximum / 10 ** tokendata.decimal_places
    data['minimum'] = sell_offer.minimum / 10 ** tokendata.decimal_places
    data['seller'] = sell_offer.maker
    data['payment_window'] = sell_offer.paymentwindow
    
    buyer = UserProfile.objects.get(username=sell_offer.maker)
    data['rating'] = buyer.feedback

    data['bank_name'] = buyer.bank_name
    data['bank_account'] = buyer.bank_account
    data['holder_name'] = buyer.bank_holder
    if country == 'au':    
        data['bsb'] = buyer.bsb
        data['payid'] = buyer.payid

    bid = tokendata.bid_usd

    rate = 0

    if crypto == 'FIAT':
        rate = Currency.objects.get(country=country).rate
    else:
        otc = Tokens.objects.get(token=crypto)
        rate = 1 / otc.bid_usd

    if token == 'SCC' or token == 'TEL':
        price_bid = round(bid * rate, 8)
    else:
        price_bid = round(bid * rate, 5)

    form = Selling()
    
    eth_token = Tokens.objects.get(token='ETH')
    mid_eth = (eth_token.bid_usd + eth_token.ask_usd)/2
    mid_token = (tokendata.bid_usd + tokendata.ask_usd)/2
    min_token = round(mid_eth/mid_token) * 0.05
    fees_token = round(mid_eth/mid_token) * 0.005
    
    offer = Offers.objects.get(offer_id = offer_id)

    if token == 'ETH':
        wallet = Wallet.objects.get(username=username)
        balance = wallet.balance 
    else:
        wallet = Erc20Wallet.objects.get(username=username, token=token)
        balance = wallet.balance
    if request.method == 'POST':
        if not user.verified and crypto == 'FIAT':
            data['process_message'] = _(u"You must be a verified user to sell on a fiat order.")
            data['no_wallet'] = True
            return render(request, 'process_error.html', data)

        if offer.verified_offer == True:
            if offer.verified_offer != user.verified:
                data['process_message'] = _(u"This offer is for verified user only. Please click on Be A Verified User on the side menu to verified your profile")
                return render(request, 'process_error.html', data) 
            
        if crypto == 'FIAT':
            purpose = "click sell"
        form = Selling(request.POST, initial={'country': country})
        if token == 'ETH':
            if wallet.balance < 0:
                data['process_message'] = _(u"You still have outstanding balance to clear from your account. Please deposit more {token} into your wallet, keeping in mind of the {fees_token} {token} deposit fee. You'll be able to trade again afterwards.").format(token=token, fees_token=fees_token)
                return render(request, 'process_error.html', data)
            elif balance < w3.toWei(float(form['amount'].value()),'ether'):
                data['process_message'] = _(u"You don't have enough balance in your wallet to sell to the buyer. Please deposit {tkn} into your wallet, keeping in mind of the {fee} {tkn} deposit fee, then try again.").format(tkn=token, fee=fees_token)
                return render(request, 'process_error.html', data)

        else:
            if wallet.balance < 0:
                data['process_message'] = _(u"You still have outstanding balance to clear from your account. Please deposit more {token} into your wallet, keeping in mind of the {fees_token} {token} deposit fee. You'll be able to trade again afterwards.").format(token=token, fees_token=fees_token)
                return render(request, 'process_error.html', data)
            elif balance < float(form['amount'].value()) * 10 ** tokendata.decimal_places:
                data['process_message'] = _(u"You don't have enough balance in your wallet to sell to the buyer. Please deposit {tkn} into your wallet, keeping in mind of the {fee} {tkn} deposit fee, then try again.").format(tkn=token, fee=fees_token)
                return render(request, 'process_error.html', data)        

        
        sell_amount = 0
        if token == 'ETH':
            sell_amount = w3.toWei(Decimal(form['amount'].value()),'ether')
        else:
            sell_amount = Decimal(form['amount'].value()) * 10 ** tokendata.decimal_places

        if sell_amount < sell_offer.minimum:
            data['message'] = _(u"The amount is lower than the trade offer's minimum.")
        elif sell_amount > sell_offer.maximum:
            data['message'] = _(u"The amount is higher than the trade offer's maximum.")
        else:
            sell_offer.taker = username
            sell_offer.save()
           
            if crypto == 'FIAT': 
                mail_notifications(username, offer_id, "click take", country)
                       
                try:
                    Notification.objects.get(
                        username=sell_offer.maker, offer_id=offer_id, event="trade")
                except Exception:
                    Notification.objects.create(
                        username=sell_offer.maker, offer_id=offer_id, event="trade")

            else:
                try:
                    Notification.objects.get(
                        username=sell_offer.maker, offer_id=offer_id, event="trade_otc")
                except Exception:
                    Notification.objects.create(
                        username=sell_offer.maker, offer_id=offer_id, event="trade_otc")

            
            return HttpResponseRedirect(
                reverse(
                    'passcode',
                    kwargs={
                        'country': country,
                        'token': token,
                        'security_code': security_code,
                        'crypto': crypto,
                        'offer_id': offer_id,
                        'amount': form['amount'].value(),
                        'fiat': request.POST['fiat'],
                    },
                )
            )


    mid_otc = 0
    tokendata = Tokens.objects.get(token=token)
    if crypto == 'GO':
        tokenotc = Tokens.objects.get(token='GO')
        mid_otc = (tokenotc.bid_usd + tokenotc.ask_usd)/2
     
    elif crypto == 'TUSD':
        tokenotc = Tokens.objects.get(token='TUSD')
        mid_otc = (tokenotc.bid_usd + tokenotc.ask_usd)/2
    
    mid_token = (tokendata.bid_usd + tokendata.ask_usd)/2
    
     
    if crypto == 'FIAT':
        if token == 'SCC' or token == 'TEL':
            final_price = round(price_bid + price_bid * sell_offer.spread, 8)
        else:
            final_price = round(price_bid + price_bid * sell_offer.spread, 2)
    else:
        if token == 'SCC' or token == 'TEL':
            final_price = round(price_bid + price_bid * sell_offer.spread, 8)
        else:
            final_price = round(price_bid + price_bid * sell_offer.spread, 5)

    data['offer_price'] = final_price
    data['rate'] = rate
    data['form'] = form
    data['notifications'] = notification(username=username, token=token)

    return render(request, 'selling.html', data)

@receiver(basket)
def prep_trade(sender, **kwargs):
    token = kwargs['token']
    crypto = kwargs['crypto']

    tokendata = Tokens.objects.get(token=token)

    if token == 'ETH':    
        taker_wallet = Wallet.objects.get(username=kwargs['taker'])
    else:
        taker_wallet = Erc20Wallet.objects.get(username=kwargs['taker'], token=kwargs['token'])
    data = {}

    if token == 'ETH':
        trade_data = {
            'amount': w3.toWei(float(kwargs['amount']),'ether'),
            'fiat': kwargs['fiat'],
        }
    else:
        trade_data = {
             'amount': float(kwargs['amount']) * 10 ** tokendata.decimal_places,
              'fiat' : kwargs['fiat'],
        }
  
    offer_id = kwargs['offer_id']

    try:
        take = take_trade(offer_id, trade_data)
    except Exception:
        data['message'] = _(u"The trade could not be taken.") 
        return data   

    offer = Offers.objects.get(offer_id=offer_id)


def otc_confirm(request, country, token, security_code, offer_id, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:
        return render(request, 'relog.html')
    data = check
    username = data['username']
    user = data['user']
    data['notifications'] = notification(username=username, token=token)

    subject = None
    data['offer_id'] = offer_id
    offer = Offers.objects.get(offer_id=offer_id)
    data['offer'] = offer
    
    if offer.crypto == 'GO':
        token_info = Tokens.objects.get(token='GO')
    elif offer.crypto == 'TUSD':
        token_info = Tokens.objects.get(token='TUSD')
    elif offer.crypto == 'ETH':
        token_info = Tokens.objects.get(token='ETH')
    else:
        pass
   
    if username == offer.taker:
        subject_name = offer.maker
    else:
        subject_name = offer.taker

    if token == 'ETH':
        wallet = Wallet.objects.get(username=subject_name)
    else:
        wallet = Erc20Wallet.objects.get(username=subject_name, token=token)
 
    trade_info = trade_data_call(offer_id)
    data['fiat'] = trade_info['fiat']
    tokendata = Tokens.objects.get(token=token)

    subject = UserProfile.objects.get(username=subject_name)
    data['subject'] = subject
    
    if token == 'ETH':
        data['amount'] = w3.fromWei(trade_info['amount'],'ether')
    else:
        data['amount'] = trade_info['amount'] / 10 ** tokendata.decimal_places
 
    fiat = offer.fiat
    if country == 'id' or country == 'vn':
        fiat = offer.fiat.split(',')
        fiat = '.'.join(fiat)
    fiat_amount = Decimal(fiat) * 10 ** 18
    otc_fees = Decimal(fiat_amount) * 2 / 1000

    if offer.token == 'PLS' and offer.crypto == 'ETH':
        otc_fees = Decimal(fiat_amount) * 8 / 1000

    if "confirm" in request.POST:
        if offer.crypto != 'ETH': 
            taker_otcwallet = Erc20Wallet.objects.get(username=offer.taker, token=offer.crypto)
            maker_otcwallet = Erc20Wallet.objects.get(username=offer.maker, token=offer.crypto)
        else:
            taker_otcwallet = Wallet.objects.get(username=offer.taker)
            maker_otcwallet = Wallet.objects.get(username=offer.maker)

        if offer.crypto == 'GO':
            paying = Decimal(fiat) * 10 ** token_info.decimal_places
            buying = Decimal(fiat) * 10 ** token_info.decimal_places

            if offer.trade_type == 'sell' and taker_otcwallet.balance > paying:
                receivedhash = release(offer_id)
                taker_otcwallet.balance -= Decimal(fiat) *10 ** token_info.decimal_places
                taker_otcwallet.save()
                History.objects.create(
                    username = taker_otcwallet.username,
                    amount = Decimal(fiat) *10 ** token_info.decimal_places,
                    token = 'GO',
                    activity='Paid GO. Offer %s' % (offer_id),
                )
       
                maker_otcwallet.balance += Decimal(fiat) *10 ** token_info.decimal_places
                maker_otcwallet.save()
                History.objects.create(
                    username = maker_otcwallet.username,
                    amount = Decimal(fiat) *10 ** token_info.decimal_places,
                    token = 'GO',
                    activity='Received GO. Offer %s' % (offer_id),
                )
     
            elif offer.trade_type == 'buy' and maker_otcwallet.balance > buying:
                receivedhash = release(offer_id)
                taker_otcwallet.balance += Decimal(fiat) *10 ** token_info.decimal_places
                taker_otcwallet.save()
                History.objects.create(
                    username = taker_otcwallet.username,
                    amount = Decimal(fiat) *10 ** token_info.decimal_places,
                    token = 'GO',
                    activity='Received GO. Offer %s' % (offer_id),
                )
       
                maker_otcwallet.balance -= Decimal(fiat) *10 ** token_info.decimal_places
                maker_otcwallet.save()
                History.objects.create(
                    username = maker_otcwallet.username,
                    amount = Decimal(fiat) *10 ** token_info.decimal_places,
                    token = 'GO',
                    activity='Paid GO. Offer %s' % (offer_id),
                )
            else:
                data['process_message'] = _(u"Not enough balance to conduct trade")
                return render(request, 'process_error.html', data)
                

        elif offer.crypto != 'GO':
            if offer.token == 'PLS' and offer.crypto != 'ETH':
                data['process_message'] = "PLS can only be traded for fiat or ETH"
                return render(request, 'process_error.html', data)

            paying = Decimal(fiat) * 10 ** token_info.decimal_places
            buying = Decimal(fiat) * 10 ** token_info.decimal_places
            if offer.trade_type == 'sell' and taker_otcwallet.balance > paying:
                receivedhash = release(offer_id)
                taker_otcwallet.balance -= Decimal(fiat) *10 ** token_info.decimal_places
                taker_otcwallet.save()
                History.objects.create(
                    username = taker_otcwallet.username,
                    amount = Decimal(fiat) *10 ** token_info.decimal_places,
                    token = crypto,
                    activity='Paid %s. Offer #%s' % (offer.crypto, offer_id),
                )
                
                maker_otcwallet.balance += Decimal(fiat) *10 ** token_info.decimal_places - Decimal(otc_fees)
                if offer.token == 'PLS' and offer.crypto == 'ETH':
                    ieo_sales = (fiat_amount * Decimal(ieo.IEO['PLS']['base_fee'])) - Decimal(otc_fees) 
                    maker_otcwallet.balance -= ieo_sales
                    History.objects.create(
                        username = offer.maker,
                        amount = ieo_sales,
                        token = 'ETH',
                        activity = "IEO sale fee for %s PLS." % str(offer.amount / 10 ** tokendata.decimal_places),
                    )
                    IEO_Sales.objects.create(token=offer.token,amount=ieo_sales)
                maker_otcwallet.save()
                give_bonus(offer.maker, otc_fees, offer.crypto)
                History.objects.create(
                    username = maker_otcwallet.username,
                    amount = Decimal(fiat_amount) - Decimal(otc_fees),
                    token = crypto,
                    activity='Received %s. Offer #%s' % (offer.crypto, offer_id),
                )

            elif offer.trade_type == 'buy' and maker_otcwallet.balance > buying:
                receivedhash = release(offer_id)
                taker_otcwallet.balance += Decimal(fiat) *10 ** token_info.decimal_places - Decimal(otc_fees)
                taker_otcwallet.save()
                give_bonus(offer.maker, otc_fees, crypto)
                History.objects.create(
                    username = taker_otcwallet.username,
                    amount = Decimal(fiat) *10 ** token_info.decimal_places - Decimal(otc_fees),
                    token = crypto,
                    activity="Received %s. Offer #%s" % (offer.crypto, offer_id),
                )

                maker_otcwallet.balance -= Decimal(fiat) *10 ** token_info.decimal_places 
                maker_otcwallet.save()
                History.objects.create(
                    username = maker_otcwallet.username,
                    amount = Decimal(fiat) *10 ** token_info.decimal_places,
                    token = crypto,
                    activity="Paid %s. Offer #%s" % (offer.crypto, offer_id),
                )    
            else:
                data['process_message'] = _(u"Not enough balance to conduct trade")
                return render(request, 'process_error.html', data)
       
        offer.released = True
        offer.completed = True
        offer.end = timezone.now()
        offer.save()
        maker = UserProfile.objects.get(username=offer.maker)
        taker = UserProfile.objects.get(username=offer.taker)
        if maker.feedback == 0:
            maker.feedback = 3
        else:
            maker.feedback = (maker.feedback + 3)/2
            maker.save()
        if taker.feedback == 0:
            taker.feedback = 3
        else:
            taker.feedback = (taker.feedback + 3)/2
            taker.save()

        if offer.trade_type == 'sell':

            seller = UserProfile.objects.get(username=offer.maker).username
            buyer = UserProfile.objects.get(username=offer.taker).username

            try:
                Notification.objects.get(username=offer.taker,
                    offer_id=offer_id, event="received")
            except Exception:
                Notification.objects.create(username=offer.taker,
                    offer_id=offer_id, event="received")
                mail_notifications(buyer, offer_id,
                    "otc received", country, {'token': token}
                )

            try:
                Notification.objects.get(username=offer.maker,
                    offer_id=offer_id, event="release_otc")
            except Exception:
                Notification.objects.create(username=offer.maker,
                    offer_id=offer_id, event="release_otc")
                mail_notifications(seller, offer_id,
                    "otc release", country, {'token': token}
                )


        if offer.trade_type == 'buy':

            seller = UserProfile.objects.get(username=offer.taker).username
            buyer = UserProfile.objects.get(username=offer.maker).username

            try:
                Notification.objects.get(username=offer.taker,
                    offer_id=offer_id, event="release_otc")
            except Exception:
                Notification.objects.create(username=offer.taker,
                    offer_id=offer_id, event="release_otc")
                mail_notifications(seller, offer_id,
                    "otc release", country, {'token': token}

                )


            try:
                Notification.objects.get(username=offer.maker,
                    offer_id=offer_id, event="received")
            except Exception:
                Notification.objects.create(username=offer.maker,
                    offer_id=offer_id, event="received") 
                mail_notifications(buyer, offer_id,
                    "otc received", country, {'token': token}

                )


        return HttpResponseRedirect(reverse('wallet', kwargs={
            'country': country,
            'token': token,
            'security_code': security_code,
            'crypto': crypto,
        }))

    
            
    if "cancel" in request.POST:
        try_cancel = None
        # to prevent double cancelling and screwing up the balance
        if offer.cancelled:
            try_cancel = True
        else:
            try:
                try_cancel = cancel(offer_id)
            except Exception:
                data['message'] = _(u"Cancel failed")

            if try_cancel:
                offer.cancelled = True
                offer.save()
                if offer.trade_type == 'sell':
                    buyer = UserProfile.objects.get(username=offer.taker)
                else:
                    buyer = UserProfile.objects.get(username=offer.maker)
                buyer.feedback = ( buyer.feedback + 1 ) / 2
                buyer.save()
                mail_notifications(
                    username, offer_id, "cancel trade", country,
                    {'token': token})

                try:
                    Notification.objects.get(username=subject,
                        offer_id=offer_id, event="cancel")
                except Exception:
                    Notification.objects.create(username=subject, 
                        offer_id=offer_id, event="cancel")

                return HttpResponseRedirect(reverse('wallet', kwargs={
                    'country': country,
                    'token': token,
                    'security_code': security_code,
                    'crypto': crypto,
                }))
            else:
                data['message'] = _(u"Cancel failed")
                

    return render(request, 'otc_confirm.html', data)    


def payment_confirm(request, country, token, security_code, offer_id, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    data['notifications'] = notification(username=username, token=token)
    

    token_info = Tokens.objects.get(token=token)
    subject = None
    data['offer_id'] = offer_id
    offer = Offers.objects.get(offer_id=offer_id)
    data['offer'] = offer
    #check who's the first person to trigger the timer
    if not offer.start:
        offer.start = datetime.utcnow()
        offer.end = offer.start + timedelta(
            minutes=offer.paymentwindow, seconds=15)
        offer.save() 
        
    data['deadline'] = offer.end.strftime("%-m/%-d/%Y %-I:%M %p")

    dispute_msg = _(u"The timer has expired. Please press the Dispute button.")

    now = timezone.now()

    if now > offer.end:
        data['expired'] = True

    #buyers first.
    if (offer.trade_type == 'sell' and username == offer.taker) or (
        offer.trade_type == 'buy' and username == offer.maker):
        
        if username == offer.taker:
            subject_name = offer.maker
        else:
            subject_name = offer.taker

        if token == 'ETH':
            wallet = Wallet.objects.get(username=subject_name)
        else:
            wallet = Erc20Wallet.objects.get(username=subject_name, token=token)

        trade_info = trade_data_call(offer_id)
      
        data['fiat'] = trade_info['fiat'] 
        
        subject = UserProfile.objects.get(username=subject_name)
        data['subject'] = subject
        if offer.released:    
            return HttpResponseRedirect(reverse('complete', kwargs={
                'country': country,
                'token': token,
                'security_code': security_code,
                'crypto': crypto,
                'address': 'nil',
                'offer_id': offer_id,
                'activity': 'complete_trade',
            }))
        elif offer.paid and now <= offer.end:
            return render(request, 'wait_contract.html', data)
        if token == 'ETH':
            data['amount'] = w3.fromWei(trade_info['amount'],'ether')
        else:
            data['amount'] = trade_info['amount'] /10 ** token_info.decimal_places
        
        if username == offer.taker:
            if token == 'ETH':
                data['nett'] = data['amount'] - w3.fromWei(offer.fees, 'ether')
            else:
                data['nett'] = data['amount'] - Decimal(offer.fees) /10 ** token_info.decimal_places 
        else:
            data['nett'] = data['amount']
    #execute here
        if "paid" in request.POST:
            if now <= offer.end:               
                offer.paid = True
                offer.save()
                data['paid'] = True
                mail_notifications(username, offer_id, "made payment", country)
                
                try:
                    Notification.objects.get(username=subject,
                        offer_id=offer_id, event="paid")
                except Exception:
                    Notification.objects.create(username=subject, 
                        offer_id=offer_id, event="paid")
                return render(request, 'wait_contract.html', data)
            else:
                data['message'] = dispute_msg 

        if "cancel" in request.POST:
            if now <= offer.end:               
                try_cancel = None
                # to prevent double cancelling and screwing up the balance
                if offer.cancelled:
                    try_cancel = True
                else:
                    try:
                        try_cancel = cancel(offer_id)
                    except Exception:
                        data['message'] = _(u"Cancel failed")

                if try_cancel:
                    offer.cancelled = True
                    offer.save()
                    mail_notifications(
                        username, offer_id, "cancel trade", country,
                        {'token': token})

                    try:
                        Notification.objects.get(username=subject,
                            offer_id=offer_id, event="cancel")
                    except Exception:
                        Notification.objects.create(username=subject, 
                            offer_id=offer_id, event="cancel")
 
                    return HttpResponseRedirect(reverse('complete', kwargs={
                        'country': country,
                        'token': token,
                        'security_code': security_code,
                        'crypto': crypto,
                        'activity': 'cancel',
                        'address': 'nil',
                        'offer_id': offer_id,
                    }))
                else:
                    data['message'] = _(u"Cancel failed")
            else:
                data['message'] = dispute_msg

        if "dispute" in request.POST:
            if now > offer.end:
                try:
                    get_dispute = DisputeSession.objects.get(offer_id=offer_id)
                except Exception:
                    DisputeSession.objects.create(
                        offer_id=offer_id,country=country)
                offer.dispute = True
                offer.save()
                mail_notifications(username, offer_id, 'dispute', country)
                mail_notifications(username, offer_id, 'user dispute', country)
                
                try:
                    Notification.objects.get(username=subject,
                        offer_id=offer_id, event="dispute")
                except Exception: 
                    Notification.objects.create(username=subject, 
                        offer_id=offer_id, event="dispute")

                DisputeChat.objects.create(
                    offer_id = offer_id,
                    talker = 'System',
                    message = '%s has entered the chat' % username,  
                )

                return HttpResponseRedirect(reverse('chat', kwargs={
                    'country': country,
                    'token': token,
                    'security_code': security_code,
                    'crypto': crypto,
                    'offer_id': offer_id,
                }))
    

        return render(request, 'buyer_payment.html', data)
        

    #sellers
    else:
        if offer.paid:
            data['paid'] = True
         
        if offer.released:
            return HttpResponseRedirect(reverse('complete', kwargs={
                'country': country,
                'token': token,
                'security_code': security_code,
                'crypto': crypto,
                'address': 'nil',
                'offer_id': offer_id,
                'activity': 'complete_trade',
            }))

        if username == offer.taker:
            subject_name = offer.maker
        else:
            subject_name = offer.taker
        
        if token == 'ETH':
            wallet = Wallet.objects.get(username=subject_name)
        else:
            wallet = Erc20Wallet.objects.get(username=subject_name,token=token)

        trade_info = trade_data_call(offer_id)
        data['fiat'] = trade_info['fiat'] 
        
        subject = UserProfile.objects.get(username=subject_name)

        data['subject'] = subject
        if token == 'ETH':
            data['amount'] = w3.fromWei(trade_info['amount'],'ether')
        else:
            data['amount'] = trade_info['amount'] /10 ** token_info.decimal_places

        if username == offer.taker:
            if token == 'ETH':
                data['nett'] = data['amount'] + w3.fromWei(offer.fees,'ether')
            else:
                data['nett'] = data['amount'] + Decimal(offer.fees) /10 ** token_info.decimal_places
        else:
            data['nett'] = data['amount']

    #execute here        
        if "received" in request.POST:
            if now <= offer.end:
                try:
                    receivedhash = release(offer_id)

                    non_pay_list = ['1CT', 'GO']                     

                    if token not in non_pay_list:
                        give_bonus(offer.taker, offer.fees, token)
                    offer.released = True
                    offer.save()
                    try:
                        Notification.objects.get(username=subject,
                            offer_id=offer_id, event="received")
                    except Exception:
                        Notification.objects.create(username=subject, 
                            offer_id=offer_id, event="received")
                    mail_notifications(username, offer_id, 
                        "released token", country, {'token': token})
                except Exception:
                    data['message'] = _(u"Failed to resolve %s release") % token

                return HttpResponseRedirect(reverse('complete', kwargs={
                    'country': country,
                    'token': token,
                    'security_code': security_code,
                    'crypto': crypto,
                    'address': 'nil',
                    'offer_id': offer_id,
                    'activity': 'complete_trade',
                }))
            else:
                data['message'] = dispute_msg

        if "dispute" in request.POST:
            if now > offer.end:
                try:
                    get_dispute = DisputeSession.objects.get(offer_id=offer_id)
                except Exception:
                    DisputeSession.objects.create(
                        offer_id=offer_id,country=country)
                offer.dispute = True
                offer.save()
                mail_notifications(username, offer_id, 'dispute', country)
                mail_notifications(username, offer_id, 'user dispute', country)
 
                try:
                    Notification.objects.get(username=subject,
                        offer_id=offer_id, event="dispute")
                except Exception:
                    Notification.objects.create(username=subject, 
                        offer_id=offer_id, event="dispute")

                DisputeChat.objects.create(
                    offer_id = offer_id,
                    talker = 'System',
                    message = '%s has entered the chat' % username,  
                )

                return HttpResponseRedirect(reverse('chat', kwargs={
                    'country': country,
                    'token': token,
                    'security_code': security_code,
                    'crypto': crypto,
                    'offer_id': offer_id,
                }))


    return render(request, 'seller_payment.html', data)         


def dispute(request, country, token, security_code, offer_id, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:
        return render(request, 'relog.html')
    data = check
    username = data['username']
    user = data['user']
    trade = Offers.objects.get(offer_id=offer_id)
    data['trade'] = trade
    dispute_obj = DisputeSession.objects.get(offer_id=offer_id)

    maker = UserProfile.objects.get(username=trade.maker)
    taker = UserProfile.objects.get(username=trade.taker)

    if trade.trade_type == 'buy':
        buyer = maker
        seller = taker
    elif trade.trade_type == 'sell':
        buyer = taker
        seller = maker   

    form = DisputeForm()

    if username == maker.username:
        if 'upload' in request.POST:
            form = DisputeForm(request.POST, request.FILES)
            dispute_obj.maker_doc = form['maker_doc'].value()
            dispute_obj.save()

            DisputeChat.objects.create(
                offer_id = offer_id,
                talker = "System",
                message = "%s has just uploaded a file" % username,
            )

            return HttpResponseRedirect(reverse('chat', kwargs={
                'country': country,
                'token': token,
                'security_code': security_code,
                'crypto': crypto,
                'offer_id': offer_id,
            }))
           
 
    elif username == taker.username:
        if 'upload' in request.POST:
            form = DisputeForm(request.POST, request.FILES)            
            dispute_obj.taker_doc = form['taker_doc'].value()
            dispute_obj.save()
            
            DisputeChat.objects.create(
                offer_id = offer_id,
                talker = "System",
                message = "%s has just uploaded a file" % username,
            )

            return HttpResponseRedirect(reverse('chat', kwargs={
                'country': country,
                'token': token,
                'security_code': security_code,
                'crypto': crypto,
                'offer_id': offer_id,
            }))
        
    data['form'] = form

    if username == seller.username:
        return render(request, 'dispute_seller.html', data)
    elif username == buyer.username:
        return render(request, 'dispute_buyer.html', data)


def chat(request, country, token, security_code, offer_id, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']

    data['chat'] = True
    data['offer_id'] = offer_id
    offer = None

    helplist = ['helpmy', 'helpcn', 'helpwb', 'helpid', 'helpau', 'helpvn', 'helpng', 'helpgh', 'helpza', 'helptz', 'helpbw', 'helpotc' , 'helpph']
    if offer_id not in helplist:
        try:
            offer = Offers.objects.get(offer_id=offer_id, dispute=True)
        except Exception:
            data['process_message'] = _(u"This trade is not in dispute!")
            data['chat'] = False
            return render(request, 'process_error.html', data)

        if username != offer.maker:
            if username != offer.taker:
                data['process_message'] = _(u"You do not belong in this chat.")
                data['chat'] = False
                return render(request, 'process_error.html', data)

    if 'send' in request.POST:
        form = ChatForm(request.POST)
        DisputeChat.objects.create(
            offer_id = offer_id,
            talker = username,
            message = form['message'].value()
        )
    chats = DisputeChat.objects.filter(offer_id=offer_id).order_by('timestamp')
    if len(chats) == 0 and offer_id not in helplist:
        DisputeChat.objects.create(
            offer_id = offer_id,
            talker = 'System',
            message = _(u'Hello. Please state the nature of your disputes. Admin shall attend to this dispute as soon as possible.'),
        )    

    list_chats = []
    for chat in chats:
        if chat != chats.last():
            list_chats.append(chat)
    data['chats'] = list_chats

    form = ChatForm()
    data['form'] = form
    
    return render(request, "chat.html", data)


def chat_message(request, offer_id, country=None, token=None, security_code=None, crypto=None):
    last_chat = DisputeChat.objects.filter(offer_id=offer_id).latest('timestamp')
    talker = ''
    try:
        username = UserProfile.objects.get(security_code=security_code).username
    except Exception:
        # getting the admin name... long story
        username = security_code
        
    if username == last_chat.talker:
        talker = '<strong class="text-warning">%s</strong>' % last_chat.talker
    elif last_chat.talker == 'System':
        talker = '%s' % last_chat.talker
    else:
        talker = '<strong class="text-secondary">%s</strong>' % last_chat.talker

    if last_chat.talker == 'System':
        last_msg = "<em>%s: %s</em>" % (talker, last_chat.message)
    else:
        last_msg = "%s: %s" % (talker, last_chat.message)
    return HttpResponse("data: %s\n\n" % last_msg, content_type="text/event-stream")


def create_buy_offer(request, country, token, security_code, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    data['notifications'] = notification(username=username,  token=token)
    currency = None
   
    try:
        if token == 'ETH':
            wallet_address = Wallet.objects.get(username=username).address
        else:
            erc20wallet_address = Erc20Wallet.objects.get(username=username, token=token).address
    except Exception:
        if token == 'ETH':
            data['process_message'] = _(u"It seems that you have not made your wallet yet. Click the Wallet icon to create one.")
            data['no_wallet'] = True
            return render(request, 'process_error.html', data)
        else:
            return HttpResponseRedirect(reverse('wallet', kwargs={
                'country': country,
                'token': token,
                'security_code': security_code,
                'crypto': crypto,
            }))  

    tokendata = Tokens.objects.get(token=token)
    bid = tokendata.bid_usd
    bid_offer = round(bid, 5)
    price = 0
    spread = 0
    rate = 0

    if crypto == 'FIAT':
        rate = Currency.objects.get(country=country).rate
    else:
        otc = Tokens.objects.get(token=crypto)
        rate = 1 / otc.bid_usd
    
    if token == 'SCC' or token == 'TEL':
        price = round(bid_offer * rate, 8)
    else:
        price = round(bid_offer * rate, 5)
    
    tokendata = Tokens.objects.get(token=token)

    eth = Tokens.objects.get(token='ETH')
    mid_eth = (eth.bid_usd + eth.ask_usd)/2
    mid_token = (tokendata.bid_usd + tokendata.ask_usd)/2 
    min_token = round(mid_eth/mid_token) * 0.05
   
    if 'create' in request.POST:
        if not user.verified and crypto == 'FIAT':
            data['process_message'] = _(u"You must be a verified user to make a fiat order.")
            data['no_wallet'] = True
            return render(request, 'process_error.html', data)

        if token == 'PLS':
            data['process_message'] = _(u"You may not create a buy offer with IEO tokens.")
            return render(request, 'process_error.html', data)
            
        if country == 'au':
            form = OfferBuyAU(request.POST)
        else:
            form = OfferBuy(request.POST)

        offer_id = ''.join(random.choice(string.digits) for x in range(6))
        if token == 'ETH':
            if float(form['minimum'].value()) < 0.05:
                data['message'] = _(u"The minimum amount to buy is 0.05 %s") % token
                data['form'] = form  
                data['bid_offer'] = bid_offer
                data['price'] = price
                data['rate'] = rate 
                return render(request, 'buy_offer.html', data)

            elif float(form['minimum'].value()) > float(form['maximum'].value()):
                data['message'] = _(u"This value must be smaller than the maximum")
                data['form'] = form
                data['bid_offer'] = bid_offer
                data['price'] = price
                data['rate'] = rate
                return render(request, 'buy_offer.html', data)
            else:
                pass
             
        else:
            if float(form['minimum'].value()) < min_token:
                data['message'] = _(u"The minimum amount to buy is {min_token} {token}").format(min_token=min_token, token=token)
                data['form'] = form
                data['bid_offer'] = bid_offer
                data['price'] = price
                data['rate'] = rate
                return render(request, 'buy_offer.html', data) 
        
            elif float(form['minimum'].value()) > float(form['maximum'].value()):
                data['message'] = _(u"This value must be smaller than the maximum")
                data['form'] = form  
                data['bid_offer'] = bid_offer
                data['price'] = price
                data['rate'] = rate 
                return render(request, 'buy_offer.html', data)
            else:
                pass

        if crypto == 'GO':
            tokenotc = Tokens.objects.get(token='GO')
            otc_wallet = Erc20Wallet.objects.get(username=username, token='GO')
            mid_otc = (tokenotc.bid_usd + tokenotc.ask_usd)/2

        elif crypto == 'TUSD':
            tokenotc = Tokens.objects.get(token='TUSD')
            otc_wallet = Erc20Wallet.objects.get(username=username, token='TUSD')
            mid_otc = (tokenotc.bid_usd + tokenotc.ask_usd)/2

        elif crypto == 'ETH':
            tokenotc = Tokens.objects.get(token='ETH')
            otc_wallet = Wallet.objects.get(username=username)
            mid_otc = (tokenotc.bid_usd + tokenotc.ask_usd)/2
        
        if crypto != 'FIAT':
            otc_max = mid_token/mid_otc * Decimal(float(form['maximum'].value()))
            otc_balance = Decimal(otc_wallet.balance) / 10 ** 18
        
            if otc_max > otc_balance:
                data['message'] = _(u"Your %s balance is not enough to create this offer") % crypto
                data['form'] = form
                data['bid_offer'] = bid_offer
                data['price'] = price
                data['rate'] = rate
                return render(request, 'buy_offer.html', data)
            else:
                pass
           
        ceiling = form['ceiling'].value()
        if ceiling == '':
            ceiling = Decimal(0)
    
        maximum = Decimal(form['maximum'].value()) * 10 ** tokendata.decimal_places
        minimum = Decimal(form['minimum'].value()) * 10 ** tokendata.decimal_places
        if country == 'ng':
            spread = int(request.POST['rangebuy']) * 20 /10000
        elif country == 'id':
            spread = int(request.POST['rangebuy']) * 10 /10000
        else:
            spread = int(request.POST['rangebuy']) * 5 /10000
     
        if crypto != 'FIAT':
            trade_data = {
                'offer_id': offer_id,
                'country': country,
                'maker': username,
                'maximum': maximum,
                'minimum': minimum,
                'spread': spread,
                'threshold': ceiling,
                'verified_offer': form['verified'].value(),
                'crypto': crypto,
                'trade_type': 'buy',
                'token' : token,
            }
        else:
            trade_data = {
                'offer_id': offer_id,
                'country': country,
                'maker': username,
                'maximum': maximum,
                'minimum': minimum,
                'spread': spread,
                'threshold': ceiling,
                'paymentwindow': form['payment_window'].value(),
                'verified_offer': form['verified'].value(),
                'trade_type': 'buy',
                'token' : token,
            }
         
        Offers.objects.create(**trade_data)

        return HttpResponseRedirect(reverse('buy_list', kwargs={
            'country': country, 
            'token': token,
            'security_code': security_code,
            'crypto': crypto}))
    else:
        if country == 'au':
            form = OfferBuyAU()
        else:
            form = OfferBuy()

    data['form'] = form  
    data['bid_offer'] = bid_offer
    data['price'] = price
    data['rate'] = rate

    return render(request, 'buy_offer.html', data)

def create_sell_offer(request, country, token, security_code, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    fiat = Currency.objects.get(country=country)
    currency = fiat.currency
    data['notifications'] = notification(username=username,  token=token) 
    currency = None

    try:
        if token == 'ETH':
            wallet_address = Wallet.objects.get(username=username).address
        else:
            erc20wallet_address = Erc20Wallet.objects.get(username=username, token=token).address
    except Exception:
        if token == 'ETH':
            data['process_message'] = _(u"It seems that you have not made your wallet yet. Click the Wallet icon to create one.")
            data['no_wallet'] = True
            return render(request, 'process_error.html', data)
        else:
            return HttpResponseRedirect(reverse('wallet', kwargs={
                'country': country,
                'token': token,
                'security_code': security_code,
                'currency': currency,
            }))
    
    tokendata = Tokens.objects.get(token=token)
    ask = tokendata.ask_usd
    ask_offer = round(ask, 5)
    price = 0
    spread = 0
    rate = 0
    
    if crypto == 'FIAT':
        rate = Currency.objects.get(country=country).rate
    else:
        otc = Tokens.objects.get(token=crypto)
        rate = 1 / otc.ask_usd
    
    eth = Tokens.objects.get(token='ETH')
    mid_eth = (eth.bid_usd + eth.ask_usd)/2

    non_pay_list = ['1CT']    

    if token in non_pay_list:
        min_token = round(mid_eth/tokendata.ask_usd) * 0.05
    else:
        mid_token = (tokendata.bid_usd + tokendata.ask_usd)/2
        min_token = round(mid_eth/mid_token, 2) * Decimal(0.05)
   
    if token == 'SCC' or token == 'TEL': 
        price = round(ask_offer * rate, 8)
    else:
        price = round(ask_offer * rate, 5)
    
    tokendata = Tokens.objects.get(token=token)
    mid_token = (tokendata.bid_usd + tokendata.ask_usd)/2

    if 'create' in request.POST:
        if not user.verified and crypto == 'FIAT':
            data['process_message'] = _(u"You must be a verified user to make a fiat order.")
            data['no_wallet'] = True
            return render(request, 'process_error.html', data)

        if token == 'PLS' and username not in ieo.IEO['PLS']['users']:
            data['process_message'] = _(u"You must be a valid issuer to be able to make a sell offer.")
            return render(request, 'process_error.html', data)

        if country == 'au':
            form = OfferSellAU(request.POST)
        else:
            form = OfferSell(request.POST, initial={'country': country,})

        offer_id = ''.join(random.choice(string.digits) for x in range(6))
        
        locked_tokens = 0
        sell_offers = Offers.objects.filter(maker=username, token=token, trade_type='sell').exclude(completed=True).exclude(cancelled=True)
        for sell_offer in sell_offers:
            locked_tokens += sell_offer.maximum 
        if token == 'ETH':
            wallet = Wallet.objects.get(username=username)
            balance = wallet.balance - Decimal(locked_tokens)
        else:
            wallet = Erc20Wallet.objects.get(username=username, token=token)
            balance = wallet.balance - Decimal(locked_tokens)
            
        if Decimal(form['maximum'].value()) * 10 ** tokendata.decimal_places > balance:
            data['message'] = _(u"You do not have enough %s in your iP2PGO Wallet to perform this trade. Choose a lower maximum amount") % token
            data['form'] = form
            data['ask_offer'] = ask_offer
            data['price'] = price
            data['rate'] = rate
            return render(request, 'sell_offer.html', data)
  
        if token == 'ETH':    
            if float(form['minimum'].value()) < 0.05:
                data['message'] = _(u"The minimum amount to sell is 0.05 %s") % token
                data['form'] = form  
                data['ask_offer'] = ask_offer
                data['price'] = price
                data['rate'] = rate 
                return render(request, 'sell_offer.html', data)
        else:
            
            if float(form['minimum'].value()) < min_token:
                data['message'] = _(u"The minimum amount to sell is {min_token} {token}").format(min_token=min_token, token=token)
                data['form'] = form
                data['ask_offer'] = ask_offer
                data['price'] = price
                data['rate'] = rate
                return render(request, 'sell_offer.html', data)


        if float(form['minimum'].value()) > float(form['maximum'].value()):
            data['message'] = _(u"This amount must be smaller than the maximum")
            data['form'] = form  
            data['ask_offer'] = ask_offer
            data['price'] = price
            data['rate'] = rate 
            return render(request, 'sell_offer.html', data)

        floor = form['floor'].value()
        if floor == '':
            floor = Decimal(0)
    
        maximum = Decimal(form['maximum'].value()) * 10 ** tokendata.decimal_places
        minimum = Decimal(form['minimum'].value()) * 10 ** tokendata.decimal_places

        if country == 'ng':
            spread = int(request.POST['rangesell']) * 20 /10000
        elif country == 'id':
            spread = int(request.POST['rangesell']) * 10 /10000
        else:
            spread = int(request.POST['rangesell']) * 5 /10000

        if crypto != 'FIAT':
            trade_data = {
                'offer_id': offer_id,
                'country': country,
                'maker': username,
                'maximum': maximum,
                'minimum': minimum,
                'spread': spread,
                'threshold': floor,
                'verified_offer': form['verified'].value(),
                'crypto': crypto,
                'trade_type': 'sell',
                'token' : token,
            }
        else:
            trade_data = {
                'offer_id': offer_id,
                'country': country,
                'maker': username,
                'maximum': maximum,
                'minimum': minimum,
                'spread': spread,
                'threshold': floor,
                'paymentwindow': form['payment_window'].value(),
                'verified_offer': form['verified'].value(),
                'trade_type': 'sell',
                'token' : token,
            }    
         
        
        
        Offers.objects.create(**trade_data)

        return HttpResponseRedirect(reverse('sell_list', kwargs={
            'country': country, 
            'token': token,
            'security_code': security_code,
            'crypto': crypto }))
    else:
        if country == 'au':
            form = OfferSellAU()
        else:
            form = OfferSell(request.POST, initial={'country': country,})

    data['form'] = form  
    data['ask_offer'] = ask_offer
    data['price'] = price
    data['rate'] = rate

    return render(request, 'sell_offer.html', data)


def order_list(request, country, token, security_code, currency=None):

    check = shared_data(country, token, security_code, currency=None)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    data['notifications'] = notification(username=username,  token=token)
    
    eth = Tokens.objects.get(token=token)
    bid = eth.bid_usd
    ask = eth.ask_usd
    currency = data['currency']
    rate = Currency.objects.get(country=country).rate
    if token == 'SCC' or token == 'TEL':
        price_bid = round(bid * (rate * 1000), 2)
        price_ask = round(ask * (rate * 1000), 2)
    else:
        price_bid = round(bid * rate, 2)
        price_ask = round(ask * rate, 2)
    data['taken'] = []
    taken_offerid = []

    taken = Offers.objects.filter(taker=username, token=token).exclude(
        completed=True, released=True).exclude(cancelled=True)
    for offer in taken:
        info = None
        data['taken'].append(offer)
        taken_offerid.append(offer.offer_id)
        offer.amount = w3.fromWei(offer.amount, 'ether')       

    made = Offers.objects.filter(maker=username).exclude(
        completed=True, released=True).exclude(cancelled=True)
    for offer in made:
        if offer.taker:
            info = None
            data['taken'].append(offer)
            taken_offerid.append(offer.offer_id)
            offer.amount = w3.fromWei(offer.amount, 'ether')
  
    data['buy_offers'] = Offers.objects.filter(maker=username, 
        trade_type='buy', token=token).exclude(completed=True).exclude(
        offer_id__in = taken_offerid).exclude(cancelled=True)
    for offer in data['buy_offers']:
        if offer.taker:
            data['taken'].append(offer)

        setattr(offer, 'price', round(price_bid + price_bid * offer.spread,2))
        offer.minimum = w3.fromWei(offer.minimum,'ether') 
        offer.maximum = w3.fromWei(offer.maximum,'ether') 
        if round(price_bid + price_bid * offer.spread,2) > offer.threshold:
            if offer.threshold != 0:
                setattr(offer, 'status', 'LIMIT UP')
            else:
                setattr(offer, 'status', 'ACTIVE')  
        else:
            setattr(offer, 'status', 'ACTIVE')
 

    data['sell_offers'] = Offers.objects.filter(maker=username,
        trade_type='sell', token=token).exclude(completed=True).exclude(
        offer_id__in = taken_offerid).exclude(cancelled=True)    
    for offer in data['sell_offers']:
        if offer.taker:
            data['taken'].append(offer)
        setattr(offer, 'price', round(price_ask + price_ask * offer.spread,2))
        offer.minimum = w3.fromWei(offer.minimum,'ether') 
        offer.maximum = w3.fromWei(offer.maximum,'ether') 
        if round(price_ask + price_ask * offer.spread,2) < offer.threshold:
            if offer.threshold != 0:
                setattr(offer, 'status', 'LIMIT UP')
            else:
                setattr(offer, 'status', 'ACTIVE')
        else:
            setattr(offer, 'status', 'ACTIVE')  

    data['price_bid'] = price_bid
    data['price_ask'] = price_ask

    if token == '1CT':
        data['price_spot'] = round(price_ask, 2)
    else:
        data['price_spot'] = round((price_bid + price_ask)/2,2)


    
    ico_member = Ico.objects.all()
    member_id = user.member_id 
    
    for ico in ico_member:
        if member_id == ico.issuer:
            data['ico'] = True 


                  
    return render(request, 'order_list.html', data)


def history(request, country, token, security_code, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    data['notifications'] = notification(username=username, token=token)

    history = History.objects.filter(username=username)
    
    for his in history:
        tokendata = Tokens.objects.get(token=his.token)
        setattr(his, 'norm_amount', his.amount / 10 ** tokendata.decimal_places)
    
    data['history'] = history
    return render(request, 'history.html', data)


def wallet(request, country, token, security_code, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    data['notifications'] = notification(username=username, token=token)
    tx_receipt = ''
    token_data = Tokens.objects.get(token=token)
    erc20tokens = Tokens.objects.all().exclude(token='ETH')
    data['erc20tokens'] = erc20tokens
    name = Tokens.objects.get(token=token).name
    data['name'] = name
    eth = Tokens.objects.get(token=token)
    bid = eth.bid_usd
    ask = eth.ask_usd
    currency = data['currency']
    rate = Currency.objects.get(country=country).rate

    if country == 'my' or country == 'otc':
        country_support = 'malaysia'
    elif country == 'au':
        country_support = 'australia'
    elif country == 'ng':
        country_support = 'nigeria'
    elif country == 'cn':
        country_support = 'china'
    elif country == 'cn-wb':
        country_support = 'onecity'
    elif country == 'vn':
        country_support = 'vietnam'
    elif country == 'id':
        country_support = 'indonesia'
    elif country == 'gh':
        country_support = 'ghana'
    elif country == 'za':
        country_support = 'southafrica'
    elif country == 'tz':
        country_support = 'tanzania'
    elif country == 'bw':
        country_support = 'botswana'
    elif country == 'ph':
        country_support = 'philippines'
    
    wait_message = _(u'Please wait for verification by our admin. You will be notified via e-mail once your wallet is ready.')
    wait_erc20 = _(u'Your ERC20 Wallet is still being created in the blockchain. Please check again after 30 minutes if you have just pressed the Create button.')    

    if 'create_wallet' in request.POST:
        return HttpResponseRedirect(reverse('create_wallet', kwargs={
            'country': country,
            'token': token,
            'security_code': security_code,
            'crypto': crypto,
        }))
   

    if 'create_wallet_eth' in request.POST:
        username=user.username
        try:
            wallet = Wallet.objects.get(username=username)
        except Exception:
            Wallet.objects.create(username=username)
            wallet = Wallet.objects.get(username=username)
        
        if not wallet.tx_hash:
            create_user_wallet(username)

            english_speakers = ['my', 'au', 'ng', 'gh', 'za', 'tz', 'bw', 'otc', 'ph'] 
            if country in english_speakers:
                country = 'en'
            elif country == 'cn-wb':
                country = 'cn'

            recipient = user.email
            user.save()
            username = user.username

            subject = _(u"Wallet Created")
            to = [recipient]
            from_email = settings.EMAIL_HOST_USER

            ctx = {
                'username' : username,
                'country' :  country_support
            }

            message = get_template('email/wallet_created-%s.html' % country).render(ctx)
            msg = EmailMessage(subject, message, to=to, from_email=from_email)
            msg.content_subtype = 'html'
            msg.send()
       
            return HttpResponseRedirect(reverse('wallet', kwargs={
                'country': country,
                'token': token,
                'security_code': security_code,
                'crypto': crypto,
            }))
        else:
            data['message'] = _(u'Your Eth Wallet is still being created in the blockchain. Please check again after 30 minutes if you have just pressed the Create button.')    

    try:
        wallet = Wallet.objects.get(username=username)
    except Exception as e:
        data['message'] = _(u'You have not made a wallet yet. Please click the button below to make one.')
        data['no_wallet'] = True
        return render(request, 'wallet.html', data)
    
         
    if not wallet.address:
        if not wallet.tx_hash:
            data['no_wallet'] = True
        try:
            tx_receipt = w3.eth.getTransactionReceipt(wallet.tx_hash)
        except Exception:
            data['message'] = wait_message
        if tx_receipt:
            data['message'] = wait_message
            wallet.address = tx_receipt.contractAddress
            wallet.save()
    else:
        balance = wallet.balance

        if balance >= 0:
            data['eth_balance'] = w3.fromWei(balance, 'ether')
        else:
            data['eth_outstanding'] = w3.fromWei((balance * -1),'ether')

    erc20_check_wallet = None
    try:
        erc20_check_wallet = Erc20Wallet.objects.get(username=username, token='USDT')
    except Exception as e:
        data['message'] = _(u'You have not created your ERC20 Wallet yet. Please tap the button to create one.')
        data['no_erc20wallet'] = True

    
    if wallet.address and erc20_check_wallet:
        if not erc20_check_wallet.tx_hash:
            data['no_erc20wallet'] = True
        else:
            if erc20_check_wallet.tx_hash:
                try:
                    tx_receipt = w3.eth.getTransactionReceipt(erc20_check_wallet.tx_hash)
                except Exception:
                    data['message'] = wait_erc20

            if not erc20_check_wallet.address:
                data['message'] = wait_erc20
                if tx_receipt:
                    data['message'] = wait_erc20
                    erc20_wallet = Erc20Wallet.objects.filter(username=username)
                    for each_token in erc20_wallet:
                        each_token.address = tx_receipt.contractAddress
                        each_token.save()

            if token != 'ETH':
                       
                erc20_wallet = Erc20Wallet.objects.get(username=username, token=token)
                data['erc20_balance'] = erc20_wallet.balance/ (10 ** token_data.decimal_places)

    if 'create_erc20wallet' in request.POST:
        all_tokens = Tokens.objects.all().exclude(token='ETH')
        erc20_wallet = Erc20Wallet.objects.filter(username=username)
        if len(erc20_wallet) == 0:
            for ind_token in all_tokens:
                Erc20Wallet.objects.create(username=username, token=ind_token.token)
                     
        create_erc20_wallet(user.username)

        return HttpResponseRedirect(reverse('wallet', kwargs={
        'country': country,
        'token': token,
        'security_code': security_code,
        'crypto': crypto
        }))


    
    tokendata = Tokens.objects.get(token=token)
    ask_offer = tokendata.ask_usd
    bid_offer = tokendata.bid_usd
    ask_offer = round(ask_offer, 5)

    bid_offer = round(bid_offer, 5)
    price = 0
    rate = 0
   
    if crypto == 'FIAT':
        ask_rate = Currency.objects.get(country=country).rate
        bid_rate = Currency.objects.get(country=country).rate
    else:
        otc = Tokens.objects.get(token=crypto)
        mid_otc = (otc.bid_usd + otc.ask_usd)/2
        ask_rate = 1 / otc.ask_usd
        bid_rate = 1 / otc.ask_usd
    
    eth = Tokens.objects.get(token='ETH')
    mid_eth = (eth.bid_usd + eth.ask_usd)/2

    non_pay_list = ['1CT']    

    if token in non_pay_list:
        min_token = round(mid_eth/tokendata.ask_usd) * 0.05
    else:
        mid_token = (tokendata.bid_usd + tokendata.ask_usd)/2
        min_token = round(mid_eth/mid_token, 2) * Decimal(0.05)

    if crypto == 'FIAT':
        if token == 'SCC' or token == 'TEL':
            price_ask = round(ask_offer * ask_rate, 5)
            price_bid = round(bid_offer * bid_rate, 5)
        else:
            price_ask = round(ask_offer * ask_rate, 2)
            price_bid = round(bid_offer * bid_rate, 2)
            
    else:
        price_ask = round(ask_offer * ask_rate, 5)
        price_bid = round(bid_offer * bid_rate, 5)
            

    if crypto == 'FIAT':
        data['price_bid'] = price_bid
        data['price_ask'] = price_ask
        if token == 'ETH':
            try:
                wallet_balance = w3.fromWei(wallet.balance, 'ether') 
                data['price_spot'] = round((price_bid + price_ask)/2 * wallet_balance,2)
            except Exception:
                wallet_balance = wallet.balance / 10 ** 18
                data['price_spot'] = round((price_bid + price_ask)/2 * wallet_balance,2)
            
        else:
            erc20_wallet = Erc20Wallet.objects.get(username=username, token=token)
            wallet_balance = erc20_wallet.balance / 10 ** token_data.decimal_places
            data['price_spot'] = round((price_bid + price_ask)/2 * wallet_balance,2)

    else:
        data['price_bid'] = price_bid
        data['price_ask'] = price_ask
        if erc20_check_wallet: 
            if token != 'ETH':
                erc20_wallet =  Erc20Wallet.objects.get(username=username, token=token) 
                token_balance = erc20_wallet.balance / 10 ** token_data.decimal_places
            else:
                eth_wallet = Wallet.objects.get(username=username)
                eth_balance = w3.fromWei(eth_wallet.balance, 'ether')
            if token == 'ETH':        
                data['price_spot'] = round(mid_token/mid_otc, 2) * eth_balance
            elif token == 'SCC' or token == 'TEL':
                data['price_spot'] = round(mid_token/mid_otc, 8) * token_balance
            else:
                data['price_spot'] = round(mid_token/mid_otc, 5) * token_balance


    return render(request, 'wallet.html', data)

def sync(request, country, token, security_code, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:
        return render(request, 'relog.html')
    data = check
    username = data['username']
    user = data['user']

    try: 
        wallet = Erc20Wallet.objects.get(username=username, token=token)
    except Exception:
        data['process_message'] = _(u"It seems that you have not made your wallet yet. Click the Wallet icon to create one.")
        return render(request, 'process_error.html', data) 

    balance = get_erc20_balance(wallet.address, token)

    return HttpResponseRedirect(reverse('wallet', kwargs={
        'country': country,
        'token': token,
        'security_code': security_code,
        'crypto': crypto
    }))     
    

def support(request, country, token, security_code, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']

    helplist = {
        'my': 'helpmy',
        'id': 'helpid',
        'cn': 'helpcn',
        'cn-wb': 'helpwb',
        'au': 'helpau',
        'vn': 'helpvn',
        'ng': 'helpng',
        'gh': 'helpgh',
        'za': 'helpza',
        'tz': 'helptz',
        'bw': 'helpbw',
        'otc': 'helpotc', 
        'ph': 'helpph',
    }

    return HttpResponseRedirect(reverse('chat', kwargs={
        'country': country,
        'token': token,
        'security_code': security_code,
        'crypto': crypto,
        'offer_id': helplist[country],
    }))

def complete(request, security_code, token, country, activity, crypto, address=None, offer_id=None, ):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    data['offer_id'] = offer_id
    data['notifications'] = notification(username=username, token=token)

    if activity == 'failed_prep':
        data['process_message'] = _(u"The trade %s is not ready yet. Please wait while the proper transactions are being processed by the blockchain. If you have been seeing this page for more than 30 minutes, either contact us or try again.") % offer_id
        return render(request, 'process_error.html', data)

    if activity == 'cancel':
        data['process_message'] = _(u'You have cancelled the trade with the Offer ID: %s. The Ether has been returned to the owner. You will be charged a penalty by paying all gas costs for cancelling the trade.')% offer_id    
        offer = Offers.objects.get(offer_id=offer_id)
        offer.completed = True
        offer.save()        
        user.feedback = (user.feedback+1)/2 
        user.save()
        return render(request, 'process_error.html', data)
    
    if activity == 'paid_debt':
        data['complete_message'] = _(u'Congratulations! You have cleared your outstanding balance! Now you may perform trades again as usual.')

        return render(request, 'complete.html', data)

    if activity == 'sent_dispute':
        data['complete_message'] = _(u'Your dispute request for trade #%s has been sent. Please be patient while our support team contacts you for further action.') % offer_id
        return render(request, 'complete.html', data)
 
    if activity == 'complete_trade':
        trade = Offers.objects.get(offer_id=offer_id)
        amount = trade.amount

        data['trade'] = trade

        if trade.trade_type=='buy':
            buyer = UserProfile.objects.get(username=trade.maker)
            seller = UserProfile.objects.get(username=trade.taker)
        else:
            buyer = UserProfile.objects.get(username=trade.taker)
            seller = UserProfile.objects.get(username=trade.maker)

        trade.completed = True
        trade.save()
        feedback = {}
        if username == buyer.username:
            if request.method == "POST":
                purpose = "trade completed"
                form = RatingForm(request.POST)
                stars = Decimal(3)
                if 'stars' not in request.POST:
                    pass
                else:
                    stars = Decimal(request.POST['stars'])

                if buyer.feedback == 0:
                    seller.feedback = stars
                else:
                    seller.feedback = (seller.feedback + stars)/2
                seller.save()
                feedback['stars'] = stars
                feedback['comment'] = form['comment'].value()                
                data['thankyou'] = True
                mail_notifications(
                    username, offer_id, purpose, country, data=feedback)
                return render(request, 'thank_you.html', data)
            else:
                form = RatingForm()
            data['form'] = form 
            data['seller'] = seller 
            data['amount'] = w3.fromWei(trade.amount, 'ether')
            if username == trade.taker:
                data['nett'] = w3.fromWei(trade.amount - trade.fees, 'ether') 
            else:
                data['nett'] = w3.fromWei(trade.amount, 'ether')
            return render(request, 'complete_buy.html', data)

        elif username == seller.username:
            if request.method == "POST":
                purpose = "trade completed"
                form = RatingForm(request.POST)
                stars = Decimal(3)
                if 'stars' not in request.POST:
                    pass
                else:
                    stars = Decimal(request.POST['stars'])

                if buyer.feedback == 0:
                    buyer.feedback = stars
                else:
                    buyer.feedback = (buyer.feedback + stars)/2
                buyer.save()
                feedback['stars'] = stars
                feedback['comment'] = form['comment'].value()                
                data['thankyou'] = True
                mail_notifications(
                    username, offer_id, purpose, country, data=feedback)
                return render(request, 'thank_you.html', data)                 
            else:
                form = RatingForm()

            data['form'] = form   
            data['buyer'] = buyer 
            data['amount'] = w3.fromWei(trade.amount, 'ether') 
            if username == trade.taker:
                data['nett'] = w3.fromWei(trade.amount + trade.fees, 'ether') 
            else:
                data['nett'] = w3.fromWei(trade.amount, 'ether')
            return render(request, 'complete_sell.html', data)

     

def editing(request, security_code, token, country, listing, offer_id, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:    
        return render(request, 'relog.html')
    data = check
    username = data['username'] 
    user = data['user']
    data['notifications'] = notification(username=username, token=token)

    data['offer_id'] = offer_id
    bank_name = user.bank_name   
    bank_account = user.bank_account
    holder_name = user.bank_holder
    tokendata = Tokens.objects.get(token=token)
    bid_offer = tokendata.bid_usd
    ask_offer = tokendata.ask_usd
    price = 0
    spread = 0
    
    eth = Tokens.objects.get(token='ETH')
    mid_eth = (eth.bid_usd + eth.ask_usd)/2
    if token == '1CT':
        mid_token = round(mid_eth/tokendata.ask_usd) * 0.05
    else:
        mid_token = (tokendata.bid_usd + tokendata.ask_usd)/2
        min_token = round(mid_eth/mid_token) * 0.05

    offer = Offers.objects.get(offer_id=offer_id)
    if offer.maker and offer.taker:
        data['process_message'] = _(u"Someone has taken your offer #%s. You may not edit this listing any longer. Please go back to your Orders page to conclude the trade.") % offer_id 
        return render(request, 'process_error.html', data)
    rate = 0
    
    if crypto == 'FIAT':
        rate = Currency.objects.get(country=country).rate
    else:
        otc = Tokens.objects.get(token=crypto)
        if listing == 'buy':
            rate = 1 / otc.bid_usd
        if listing == 'sell':
            rate = 1 / otc.ask_usd

    if listing == 'buy':
        price = round(bid_offer * rate, 5)
        buy_order = Offers.objects.get(offer_id=offer_id)
        if 'edit' in request.POST:
            form = OfferBuy(request.POST)
            if country == 'au':
                form = OfferBuyAU(request.POST)
            else:
                form = OfferBuy(request.POST, initial={'country': country,})


            if token == 'ETH':
                if float(form['minimum'].value()) < 0.05:
                    data['message'] = _(u"The minimum amount to buy is 0.05 ETH")    
                    data['form'] = form  
                    data['bid_offer'] = bid_offer
                    data['price'] = price
                    data['rate'] = rate 
                    data['edit'] = True
                
                    return render(request, 'buy_offer.html', data)
               

                elif float(form['minimum'].value()) > float(form['maximum'].value()):
                    data['message'] = _(u"This value must be smaller than the maximum")
                    data['form'] = form
                    data['bid_offer'] = bid_offer
                    data['price'] = price
                    data['rate'] = rate
                    data['edit'] = True

                    return render(request, 'buy_offer.html', data)
                else:
                    pass

            else:
                if float(form['minimum'].value()) < min_token:
                    data['message'] = _(u"The minimum amount to buy is {min_token} {token}").format(min_token=min_token, token=token) 
                    data['form'] = form
                    data['bid_offer'] = bid_offer
                    data['price'] = price
                    data['rate'] = rate
                    data['edit'] = True

                    return render(request, 'buy_offer.html', data)
 
                elif float(form['minimum'].value()) > float(form['maximum'].value()):
                    data['message'] = _(u"This value must be smaller than the maximum")
                    data['form'] = form
                    data['bid_offer'] = bid_offer
                    data['price'] = price
                    data['rate'] = rate
                    data['edit'] = True

                    return render(request, 'buy_offer.html', data)
                else:
                    pass

            if crypto == 'GO':
                tokenotc = Tokens.objects.get(token='GO')
                otc_wallet = Erc20Wallet.objects.get(username=username, token='GO')
                mid_otc = (tokenotc.bid_usd + tokenotc.ask_usd)/2

            elif crypto == 'TUSD':
                tokenotc = Tokens.objects.get(token='TUSD')
                otc_wallet = Erc20Wallet.objects.get(username=username, token='TUSD')
                mid_otc = (tokenotc.bid_usd + tokenotc.ask_usd)/2

            elif crypto == 'ETH':
                tokenotc = Tokens.objects.get(token='ETH')
                otc_wallet = Wallet.objects.get(username=username)
                mid_otc = (tokenotc.bid_usd + tokenotc.ask_usd)/2

            if crypto != 'FIAT':
                otc_max = mid_token/mid_otc * Decimal(float(form['maximum'].value()))
                otc_balance = Decimal(otc_wallet.balance) / 10 ** 18

                if otc_max > otc_balance:
                    data['message'] = _(u"Your %s balance is not enough to create this offer") % crypto
                    data['form'] = form
                    data['bid_offer'] = bid_offer
                    data['price'] = price
                    data['rate'] = rate
                    return render(request, 'buy_offer.html', data)
                else:
                    pass

            if country == 'ng':
                spread = int(request.POST['rangebuy']) / 100 * 0.2
            elif country == 'id':
                spread = int(request.POST['rangebuy']) / 100 * 0.1
            else:
                spread = int(request.POST['rangebuy']) / 100 * 0.05
            
            buy_order.spread = spread
            ceiling = form['ceiling'].value()
            if ceiling == '':
                ceiling = 0
            buy_order.threshold = ceiling  
            if token == 'ETH':    
                buy_order.maximum = w3.toWei(form['maximum'].value(), 'ether')
                buy_order.minimum = w3.toWei(form['minimum'].value(), 'ether')
            else:
                buy_order.maximum = Decimal(form['maximum'].value()) * 10 ** tokendata.decimal_places
                buy_order.minimum = Decimal(form['minimum'].value()) * 10 ** tokendata.decimal_places
            buy_order.paymentwindow = form['payment_window'].value()
            buy_order.save() 

            return HttpResponseRedirect(reverse('buy_list', kwargs={
                'country': country, 
                'token': token,
                'security_code': security_code,
                'crypto': crypto}))

        elif 'cancel' in request.POST:
            buy_order.delete() 

            return HttpResponseRedirect(reverse('buy_list', kwargs={
                'country': country, 
                'token': token,
                'security_code': security_code,
                'crypto': crypto}))
        else:
            form = OfferBuy(initial={
                'spread': buy_order.spread,
                'ceiling': buy_order.threshold,      
                'maximum': w3.fromWei(buy_order.maximum, 'ether'),
                'minimum': w3.fromWei(buy_order.minimum, 'ether'),
                'payment_window': buy_order.paymentwindow,
            })
            if country == 'au':
                form = OfferBuyAU(initial={
                    'spread': buy_order.spread,
                    'ceiling': buy_order.threshold,      
                    'maximum': w3.fromWei(buy_order.maximum, 'ether'),
                    'minimum': w3.fromWei(buy_order.minimum, 'ether'),
                    'payment_window': buy_order.paymentwindow,
                })

        data['form'] = form  
        data['bid_offer'] = bid_offer
        data['price'] = price
        data['rate'] = rate 
        data['edit'] = True
        
        return render(request, 'buy_offer.html', data)

    elif listing == 'sell':
        price = round(ask_offer * rate, 5)
        sell_order = Offers.objects.get(offer_id=offer_id)
        if 'edit' in request.POST:
            form = OfferSell(request.POST)
            if country == 'au':
                form = OfferSellAU(request.POST)
          
            locked_tokens = 0
            sell_offers = Offers.objects.filter(maker=username, token=token, trade_type='sell').exclude(completed=True).exclude(cancelled=True)
            for sell_offer in sell_offers:
                locked_tokens += sell_offer.maximum
            if token == 'ETH':
                wallet = Wallet.objects.get(username=username)
                balance = wallet.balance - Decimal(locked_tokens)
            else:
                wallet = Erc20Wallet.objects.get(username=username, token=token)
                balance = wallet.balance - Decimal(locked_tokens) 
            
            if Decimal(form['maximum'].value()) * 10 ** tokendata.decimal_places > balance:
                data['message'] = _(u"You do not have enough %s in your iP2PGO Wallet to perform this trade. Choose a lower maximum amount") % token
                data['form'] = form
                data['ask_offer'] = ask_offer
                data['price'] = price
                data['rate'] = rate
                data['edit'] = True
                return render(request, 'sell_offer.html', data)
             
            if token == 'ETH':
                if float(form['minimum'].value()) < 0.05:
                    data['message'] = _(u"The minimum amount to buy is 0.05 %s") % token
                    data['form'] = form
                    data['bid_offer'] = bid_offer
                    data['price'] = price
                    data['rate'] = rate
                    data['edit'] = True

                    return render(request, 'buy_offer.html', data)
            else:
               if float(form['minimum'].value()) < min_token:
                    data['message'] = _(u"The minimum amount to buy is {min_token} {token}").format(min_token=min_token, token=token)
                    data['form'] = form
                    data['bid_offer'] = bid_offer
                    data['price'] = price
                    data['rate'] = rate
                    data['edit'] = True

                    return render(request, 'buy_offer.html', data)

            if float(form['minimum'].value()) > float(form['maximum'].value()):
                data['message'] = _(u"This amount must be smaller than the maximum")
                data['form'] = form
                data['ask_offer'] = ask_offer
                data['price'] = price
                data['rate'] = rate
                data['edit'] = True
                return render(request, 'sell_offer.html', data)

            if country == 'ng':
                spread = int(request.POST['rangesell']) / 100 * 0.2
            elif country == 'id':
                spread = int(request.POST['rangesell']) / 100 * 0.1
            else:
                spread = int(request.POST['rangesell']) / 100 * 0.05
            
            sell_order.spread = spread
            floor = form['floor'].value()
            if floor == '':
                floor = 0
            sell_order.threshold = floor   
            if token == 'ETH':
                sell_order.maximum = w3.toWei(form['maximum'].value(), 'ether')
                sell_order.minimum = w3.toWei(form['minimum'].value(), 'ether')
            else:
                sell_order.maximum = Decimal(form['maximum'].value()) * 10 ** tokendata.decimal_places
                sell_order.minimum = Decimal(form['minimum'].value()) * 10 ** tokendata.decimal_places 
            sell_order.paymentwindow = form['payment_window'].value()
            sell_order.save() 

            return HttpResponseRedirect(reverse('sell_list', kwargs={
                'country': country, 
                'token': token,
                'security_code': security_code,
                'crypto': crypto }))

        elif 'cancel' in request.POST:
            sell_order.delete()

            return HttpResponseRedirect(reverse('sell_list', kwargs={
                'country': country,
                'token': token,
                'security_code': security_code,
                'crypto': crypto}))

        else:
            form = OfferSell(initial={
                'country': country,
                'spread': sell_order.spread,
                'floor': sell_order.threshold,      
                'maximum': w3.fromWei(sell_order.maximum, 'ether'),
                'minimum': w3.fromWei(sell_order.minimum, 'ether'),
                'payment_window': sell_order.paymentwindow,
            })
            if country == 'au':
                form = OfferSellAU(initial={
                    'country': country,
                    'spread': sell_order.spread,
                    'floor': sell_order.threshold,      
                    'maximum': w3.fromWei(sell_order.maximum, 'ether'),
                    'minimum': w3.fromWei(sell_order.minimum, 'ether'),
                    'payment_window': sell_order.paymentwindow,
                })

        data['form'] = form  
        data['ask_offer'] = ask_offer
        data['price'] = price
        data['rate'] = rate 
        data['edit'] = True
        
        return render(request, 'sell_offer.html', data)


def mail_notifications(username, offer_id, purpose, country, data=None):
    english = ['my', 'au', 'ng', 'gh', 'za', 'tz', 'bw', 'otc', 'ph']
    chinese = ['cn', 'cn-wb']
    vietnam = ['vn']
    indonesia = ['id']

    if country == 'my' or country == 'otc':
        country_support = 'malaysia'
    elif country == 'au':
        country_support = 'australia'
    elif country == 'ng':
        country_support = 'nigeria'
    elif country == 'cn':
        country_support = 'china'
    elif country == 'cn-wb':
        country_support = 'onecity'
    elif country == 'vn':
        country_support = 'vietnam'
    elif country == 'id':
        country_support = 'indonesia'
    elif country == 'gh':
        country_support = 'ghana'
    elif country == 'za':
        country_support = 'southafrica'
    elif country == 'tz':
        country_support = 'tanzania'
    elif country == 'bw':
        country_support = 'botswana'
    elif country == 'ph':
        country_support = 'philippines'

    offer = Offers.objects.get(offer_id=offer_id)
    maker = UserProfile.objects.get(username=offer.maker)
    taker = UserProfile.objects.get(username=offer.taker)
    if offer.trade_type == 'sell':
        buyer = taker
        seller = maker
    else:
        buyer = maker
        seller = taker

    template = ''
    ctx = ''
    subject = ''
    message = ''
    to = ''
    from_email = ''  
 
    if country in english:
        language = 'en'
    elif country in chinese:
        language = 'cn'
    elif country in vietnam:
        language = 'vn'
    elif country in indonesia:
        language = 'id'

    if purpose == "dispute":

        if country == 'my' or country == 'otc':
            country_name = 'malaysia'
        elif country == 'au':
            country_name = 'australia'
        elif country == 'ng':
            country_name = 'nigeria'
        elif country == 'vn':
            country_name = 'vietnam'
        elif country == 'id':
            country_name = 'indonesia'
        elif country == 'cn-wb':
            country_name = 'onecity'
        elif country == 'gh':
            country_name = 'ghana'
        elif country == 'za':
            country_name = 'southafrica'
        elif country == 'tz':
            country_name = 'tanzania'
        elif country == 'bw':
            country_name = 'botswana'
        elif country == 'ph':
            country_name = 'philippines'

        subject = _(u"Dispute case {countryname} {offerid}").format(countryname=country_name, offerid=offer_id)
        template = "email/disputetosupport-%s.html" % language
        recipient = "admin.%s@ip2pmoney.com" % country_name

        to = [recipient]
        from_email = settings.EMAIL_HOST_USER

        ctx = {
            'buyer_email': buyer.email,
            'seller_email': seller.email,
            'country' : country_support
        }

    if purpose == "user dispute":
        if username == maker.username:
            disputor = taker
        else:
            disputor = maker

        subject = _(u"Dispute for offer #%s" % (offer_id))
        template = "email/autodispute-%s.html" % language 
        recipient = disputor.email 

        to = [recipient]
        from_email = settings.EMAIL_HOST_USER

        ctx = {
            'username': username,
            'offer_id': offer_id,
            'disputor': disputor.username,
            'country' : country_support
        }
        

    if purpose == "made payment":
        # please look at this example on how to do things more effectively
        subject = _(u"[iP2PGO] {username} has made payment to you for trade {offer}.").format(username=buyer.username, offer=offer_id)
        template = 'email/payment-%s.html' % language
        recipient = seller.email

        to = [recipient]
        from_email = settings.EMAIL_HOST_USER

        ctx = {
            'username': seller.username,
            'offer_id': offer_id,
            'buyer': buyer.username,
            'trade_type': offer.trade_type,
            'country' : country_support
        }
    if purpose == "click take":
        subject = _(u"[iP2PGO] {offer} is taking your {trade} offer {offerid}.").format(offer=offer.taker, trade=offer.trade_type, offerid=offer_id)
        template = 'email/offer-%s.html' % language

        recipient = maker.email

        to = [recipient]
        from_email = settings.EMAIL_HOST_USER

        ctx = {
            'username': maker.username,
            'offer_id': offer_id,
            'counterpart': taker.username,
            'trade_type': offer.trade_type,
            'country' : country_support
        }


    if purpose == "cancel trade":
        subject = _(u"[iP2PGO] {username} is cancelling offer trade {offer}.").format(username=buyer.username, offer=offer_id)
        template = 'email/cancel-%s.html' % language

        recipient = seller.email

        to = [recipient]
        from_email = settings.EMAIL_HOST_USER

        ctx = {
            'username': seller.username,
            'offer_id': offer_id,
            'buyer': buyer.username,
            'token': data['token'],
            'country': country_support
        }

    if purpose == "admin cancel taker":
        subject = _(u"[iP2PGO] {user} is cancelling offer trade {offer}.").format(user=username, offer=offer_id)
        template = 'email/cancel_admin-%s.html' % language

        recipient = taker.email

        to = [recipient]
        from_email = settings.EMAIL_HOST_USER

        ctx = {
            'username': taker.username,
            'offer_id': offer_id,
            'buyer': username,
            'token': data['token'],
            'country': country_support
        }

    if purpose == "admin cancel maker":
        subject = _(u"[iP2PGO] {user} is cancelling offer trade {offer}.").format(user=username, offer=offer_id)
        template = 'email/cancel_admin-%s.html' % language

        recipient = maker.email

        to = [recipient]
        from_email = settings.EMAIL_HOST_USER

        ctx = {
            'username': maker.username,
            'offer_id': offer_id,
            'buyer': username,
            'token': data['token'],
            'country': country_support
        }

    if purpose == "trade completed":
        if username == taker.username:
            other_user = maker
            user = taker
        else:
            other_user = taker
            user = maker

        subject = _(u"[iP2PGO] Your trade {offer} has been concluded.").format(offer=offer_id)
        template = 'email/rating-%s.html' % language

        recipient = other_user.email 

        to = [recipient]
        from_email = settings.EMAIL_HOST_USER

        ctx = {
            'username': other_user.username,
            'other_user': user.username,
            'offer_id': offer_id,
            'stars': data['stars'],
            'comment': data['comment'],
            'country': country_support
        }

    if purpose == "released token":

        subject = _(u"[iP2PGO] {seller} has received your payment for trade {offer}").format(seller=seller.username, offer=offer_id)
        template = 'email/release-%s.html' % language

        recipient = buyer.email

        to = [recipient]
        from_email = settings.EMAIL_HOST_USER

        ctx = {
            'username': buyer.username,
            'offer_id': offer_id,
            'seller': seller.username,
            'token': data['token'],
            'country': country_support
        }

    if purpose == "admin released":

        subject = _(u"[iP2PGO] {seller} has received your payment for trade {offer}").format(seller=seller.username, offer=offer_id)
        template = 'email/release_dispute-%s.html' % language

        recipient = buyer.email

        to = [recipient]
        from_email = settings.EMAIL_HOST_USER

        ctx = {
            'username': buyer.username,
            'offer_id': offer_id,
            'seller': seller.username,
            'token': data['token'],
            'country': country_support
        }

    if purpose == "otc release":
    
        subject = _(u"[iP2PGO] Your {offer} trade is done.").format(offer=offer_id)
        template = 'email/releaseotc-%s.html' % language

        recipient = seller.email

        to = [recipient]
        from_email = settings.EMAIL_HOST_USER

        ctx = {
            'username': seller.username,
            'offer_id': offer_id,
            'token': data['token'],
            'country': country_support
        }

    if purpose == "otc received":

        subject = _(u"[iP2PGO] Your {offer} trade is done.").format(offer=offer_id)
        template = 'email/receivedotc-%s.html' % language

        recipient = buyer.email

        to = [recipient]
        from_email = settings.EMAIL_HOST_USER

        ctx = {
            'username': buyer.username,
            'offer_id': offer_id,
            'token': data['token'],
            'country': country_support
        }

    message = get_template(template).render(ctx)
    msg = EmailMessage(subject, message, to=to, from_email=from_email)
    msg.content_subtype = 'html'
    msg.send()


    return True


def logout(request, country, security_code, crypto):
    user = UserProfile.objects.get(security_code=security_code)
    user.security_code = ''
    user.save()
    return HttpResponseRedirect(reverse('index', kwargs={'country': country,})) 
     

def notification(username, token):

    messages = []
    data = {}
    trade = None
    data['username'] = username
    data['token'] = token

    user = UserProfile.objects.get(username=username) 
    security_code = user.security_code
    country = user.country
    token = token
    trade_token = None    

    notes = Notification.objects.filter(username=username)

    # you're trying to read the database, consult your models
    for note in notes:
        offer_id = None
        offer = None
        if note.offer_id:
            offer_id = note.offer_id
            offer = Offers.objects.get(offer_id=offer_id)
            trade_token = offer.token
            if offer.trade_type == 'sell':
                seller = offer.maker
                buyer = offer.taker
            else:
                seller = offer.taker
                buyer = offer.maker
        if note.event == "paid":
            # everything must be a string
            messages.append(_("{user} has made payment for trade {offer}. Check your Orders tab.").format(user=buyer, offer=offer_id))
            # the dismiss button doesn't clear the db yet.

        if note.event == "trade":
            messages.append(_("{taker} has taken your trade {offer}. Check your Orders tab.").format(taker=offer.taker, offer=offer_id))

        if note.event == "trade_otc":
            messages.append(_("{taker} has taken your trade {offer}.").format(taker=offer.taker, offer=offer_id))

        if note.event == "cancel take":
            messages.append(_("Your trade {offer} is not taken and is available again. Check your Orders tab.").format(offer=offer_id))

        if note.event == "cancel":
            messages.append(_("{user} has cancelled your trade {offer}. Check your Orders tab.").format(user=buyer, offer=offer_id))

        if note.event == "received":
            messages.append(_("{sell} has released {tkn} for your trade {offer}. Check your Wallet tab.").format(sell=seller,tkn=trade_token, offer=offer_id))
        
        if note.event == "wallet created":
            messages.append(_("Your wallet has been/is being created! Check your Wallet tab."))
       
        if note.event == "wallet denied":
            messages.append(_("Your KYC verification has failed. Please create your wallet again."))
       
        if note.event == "release_otc":
            messages.append(_("Your {offer} trade is done. The {tkn} is now released to the buyer.").format(offer=offer_id, tkn=trade_token)) 
 
        note.delete()

    return messages

def thankyou(request, country, token, security_code, crypto):
    check = shared_data(country, token, security_code, crypto)
    if not check:
        return render(request, 'relog.html')
    data = check
    username = data['username']
    user = data['user']

    return render(request, 'thank_you.html', data)

def handler404(request, exception):
    
    return render(request, '404_error.html', status=404)


def handler500(request):

    return render(request, '500_error.html', status=500)
