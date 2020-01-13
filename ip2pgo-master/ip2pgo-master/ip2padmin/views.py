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
from directapp.models import UserProfile, Wallet, Offers, Notification, Currency, Erc20Wallet, History, Tokens
from .models import AdminProfile
from .forms import AdminForm
import random, string, requests
from email.mime.image import MIMEImage
from django.contrib.staticfiles import finders
from django.template import Context
from django.template.loader import render_to_string, get_template
from django.core.mail import EmailMessage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import os, smtplib, base64, pytz
import email.encoders
import email.mime.text
import email.mime.base
import email.utils
from datetime import datetime, timedelta
from web3.auto.infura import w3
from infuraeth.interface import (
    create_user_wallet,
)
from promotions.models import Comissions, Redemption
from django.dispatch import Signal, receiver
from time import sleep
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dispute.models import DisputeSession, DisputeChat
from django.db.models.signals import post_init
from directapp.forms import ChatForm
from infuraeth.interface import release, cancel
from directapp.views import mail_notifications
from directapp.models import Notification


def login(request, country):
    data = {'country': country, 'admin_name': None}
    admin = None

    country_pair = {
        'my': 'Malaysia',
        'id': 'Indonesia',
        'cn': _('China'),
        'cn-wb': 'One City',
        'au': 'Australia',
        'ng': 'Nigeria',
        'vn': 'Vietnam',
        'gh': 'Ghana',
        'za': 'South Africa',
        'tz': 'Tanzania',
        'bw': 'Botswana',
        'otc': 'iP2PGo Global',
        'ph': 'Philippines',
    }
    
    ref_country = country
    if country == 'cn-wb':
        ref_country = 'wb'
    chatroom = 'help%s' % ref_country

    data['country_name'] = country_pair[country]
 
    if 'login' in request.POST:
        admin_form = AdminForm(request.POST)
        if admin_form.is_valid():
            try:
                admin = AdminProfile.objects.get(admin_name=admin_form['admin_name'].value())
            except Exception:
                admin_form = AdminForm()
                return render(request, 'login.html',{
                    'admin_form': admin_form,
                    }
            
                )   
            if admin_form['password'].value() == admin.password:
                if admin.clearance == 'support': 
                    return HttpResponseRedirect(reverse('support_chat', kwargs={    
                        'country': country,
                        'admin_name': admin.admin_name,
                        'offer_id': chatroom,
                    }))           
                if admin.clearance == 'KYC':
                    return HttpResponseRedirect(reverse('list', kwargs={
                        'country': country,
                        'admin_name': admin.admin_name,
                    }))     
                return HttpResponseRedirect(reverse('support_chat', kwargs={
                    'country': country,
                    'admin_name': admin.admin_name,
                    'offer_id': chatroom,
                }))           
 
            else:
                return render(request, 'login.html',{
                    'admin_form': admin_form,
                    }
                )
    else:
        admin_form = AdminForm()
        
    data['admin_form'] = admin_form

    return render(request, 'login.html', data)


def list(request, country, admin_name):
    data = {'admin_name': admin_name, 'country': country}
    data['admin'] = AdminProfile.objects.get(admin_name=admin_name)
    username = None
    users = UserProfile.objects.filter(country=country, verified = False)
    wallets = Wallet.objects.all() 
    data['users'] = users
    data['wallets'] = wallets
    template = ''
    ctx = ''
    subject = ''
    message = ''
    to = ''
    from_email = ''
    recipient = ''
    raw_name = ''
    english = ['my', 'au', 'ng', 'gh', 'za', 'tz', 'bw', 'otc', 'ph']
    chinese = ['cn', 'cn-wb']

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

    if 'create' in request.POST:
        username =  request.POST['create']
        try:
            wallet = Wallet.objects.get(username=username)
        except Exception:
            pass
          
        
        if not wallet.tx_hash:
            create_user_wallet(username) 
        
            user = UserProfile.objects.get(username=username)
            user.verified = True
            user.save()

            Notification.objects.create(
               username=username, event="wallet created")

            if country in english:
                country = 'en'
            elif country in chinese:
                country = 'cn'

            recipient = user.email
            subject = _(u"Wallet Created")
            template = ('wallet_created-%s.html' % country)
            to = [recipient]
            from_email = settings.EMAIL_HOST_USER

            ctx = { 
                'username' : username,
                'country' :  country_support
            }

            message = get_template(template).render(ctx)
            msg = EmailMessage(subject, message, to=to, from_email=from_email)
            msg.content_subtype = 'html'
            msg.send()
        
        else:

            user = UserProfile.objects.get(username=username)
            user.verified = True
            user.save()

            if country in english:
                country = 'en'
            elif country in chinese:
                country = 'cn'

            recipient = user.email
            subject = _(u"Verified User")
            template = ('verified_user-%s.html' % country)
            to = [recipient]
            from_email = settings.EMAIL_HOST_USER

            ctx = {
                'username' : username,
                'country' :  country_support
            }

            message = get_template(template).render(ctx)
            msg = EmailMessage(subject, message, to=to, from_email=from_email)
            msg.content_subtype = 'html'
            msg.send()

    elif 'deny' in request.POST:
        username = request.POST['deny']

        wallet = Wallet.objects.get(username=username)
        wallet.delete()
        user = UserProfile.objects.get(username=username)

        Notification.objects.create(
            username=username, event="wallet denied")

        if country in english:
            country = 'en'
        elif country in chinese:
            country = 'cn'

        recipient = user.email
        subject = _(u"Uploading KYC again")
        template = ('upload_again-%s.html' % country)
        to = [recipient]
        from_email = settings.EMAIL_HOST_USER

        ctx = { 
            'username': username,
            'country': country_support
        }
        
        message = get_template(template).render(ctx)
        msg = EmailMessage(subject, message, to=to, from_email=from_email)
        msg.content_subtype = 'html'
        msg.send()

        data['message'] = "Re-try email sent to %s" % user.username
    return render(request, 'list.html', data)


def dispute(request, country, admin_name): 
    data = {}
    data['country'] = country
    data['admin_name'] = admin_name
    dispute_list = DisputeSession.objects.filter(country=country)
    for dispute in dispute_list:
        offer = Offers.objects.get(offer_id=dispute.offer_id)
        setattr(dispute, 'taker', offer.taker)
        setattr(dispute, 'maker', offer.maker)        
    data['dispute_list'] = dispute_list

    return render(request, 'dispute_list.html', data)


def chat(request, country, admin_name, offer_id):
    data = {}
    data['offer_id'] = offer_id
    data['admin_name'] = admin_name
    data['country'] = country
    data['admin'] = AdminProfile.objects.get(admin_name=admin_name) 
    if 'help' not in offer_id:
        case = DisputeSession.objects.get(offer_id=offer_id)
        offer = Offers.objects.get(offer_id=offer_id)
        currency = Currency.objects.get(country=country).currency
        data['currency'] = currency
        data['taker'] = offer.taker
        data['maker'] = offer.maker
        data['fiat'] = offer.fiat
        data['amount'] = offer.amount / 10**18  
        data['token'] = offer.token
        if case.status == 'Done':
            data['done'] = True
 
        if offer.trade_type == 'buy':
            buyer = offer.maker
            seller = offer.taker
        else:
            buyer = offer.taker
            seller = offer.maker
    
        data['buyer'] = buyer
        data['seller'] = seller

        data['maker_doc'] = case.maker_doc
        data['taker_doc'] = case.taker_doc
        if not case.admin:
            case.admin = admin_name
            case.status = _(u'Pending')
            case.save()

    if 'send' in request.POST:
        form = ChatForm(request.POST)
        DisputeChat.objects.create(
            offer_id = offer_id,
            talker = admin_name,
            message = form['message'].value()
        )

    if 'release' in request.POST:
        offer.dispute = False
        release(offer_id)
        offer.released = True
        offer.save()
        mail_notifications(admin_name, offer_id,
            "admin released", country, {'token': offer.token})

        DisputeChat.objects.create(
            offer_id = offer_id,
            talker = admin_name,
            message = _("Offer {offer} {token} has been released to the buyer. Please check your iP2PGO wallet. This trade has been concluded, thank you.".format(offer=offer_id, token=offer.token)),
        )
        case.status = _(u"Done")
        case.save()

    if 'cancel' in request.POST:
        offer.dispute = False
        if not offer.cancelled:
            cancel(offer_id)
            offer.cancelled = True
        offer.save()
        mail_notifications(
            admin_name, offer_id, "admin cancel taker", country, 
            {'token': offer.token})
        mail_notifications(
            admin_name, offer_id, "admin cancel maker", country, 
            {'token': offer.token})

        DisputeChat.objects.create(
            offer_id = offer_id,
            talker = admin_name,
            message = _("Offer {offer} has been cancelled. The {token} has been returned to the seller. Please check your iP2PGO wallet. This trade has been concluded, thank you.".format(offer=offer_id, token=offer.token)),
        )
        case.status = _(u'Done')
        case.save()

    form = ChatForm()
    data['form'] = form
    chats = DisputeChat.objects.filter(offer_id=offer_id).order_by('timestamp')
    list_chats = []
    for chat in chats:
        if chat != chats.last():
            list_chats.append(chat)
    data['chats'] = list_chats
  
    if 'help' not in offer_id:
        data['maker_doc_approve'] = case.maker_doc_approve
        data['taker_doc_approve'] = case.taker_doc_approve
        data['token'] = offer.token

    return render(request, 'chat_admin.html', data)


# proof is only either maker or taker
def verify(request, country, admin_name, offer_id, user):
    data = {'country': country, 'admin_name': admin_name, 'offer_id': offer_id,
        'user': user}
    offer = Offers.objects.get(offer_id=offer_id)
    case = DisputeSession.objects.get(offer_id=offer_id)
  
    if 'approve' in request.POST:
        if user == offer.taker:
            case.taker_doc_approve = True
        elif user == offer.maker:
            case.maker_doc_approve = True
        case.save()

        DisputeChat.objects.create(
            offer_id = offer_id,
            talker = admin_name,
            message = _("Okay %s, I have verified your screenshot." % user),
        )

        return HttpResponseRedirect(reverse('chat_admin', kwargs={
            'country': country, 'admin_name': admin_name, 'offer_id': offer_id
        }))
    
    if 'deny' in request.POST:
        DisputeChat.objects.create(
            offer_id = offer_id,
            talker = admin_name,
            message = _("{use}, can you upload a new screenshot? I couldn't verify your last one.".format(use=user)),
        )
        
        return HttpResponseRedirect(reverse('chat_admin', kwargs={
            'country': country, 'admin_name': admin_name, 'offer_id': offer_id
        }))
    
    data['user'] = UserProfile.objects.get(username=user)
    if user == offer.taker:
        data['screenshot'] = case.taker_doc
        data['approved'] = case.taker_doc_approve
    else:
        data['screenshot'] = case.maker_doc
        data['approved'] = case.maker_doc_approve

    return render(request, 'dispute_verification.html', data)  

def list_allusers(request, country, admin_name):
    data = {'country': country, 'admin_name': admin_name}
    users = UserProfile.objects.filter(country=country, verified='1').order_by('-created')

    data['users'] = users

    num = len(users)
    for user in users:
        setattr(user,'num',num)
        num -= 1


    for user in users:
        referer = ''
        wallet = None
        try:
            referer = UserProfile.objects.get(member_id=user.referral_id).username
        except Exception:
            pass

        setattr(user, "referer", referer)

        taker_trades = Offers.objects.filter(taker=user.username)
        volume = 0
        for trade in taker_trades:
            volume += trade.amount

        setattr(user, "tradevol", w3.fromWei(volume,'ether'))

        maker_trades = Offers.objects.filter(maker=user.username)
        volume = 0
        for trade in maker_trades:
            volume += trade.amount

        setattr(user, "makervol", w3.fromWei(volume,'ether'))

        try:
            wallet = Wallet.objects.get(username=user.username)
        except Exception:
            pass

        if wallet:
            if wallet.tx_hash:
                setattr(user, "approved", True)

        timezones = {
            'my': 8,
            'cn': 8,
            'cn-wb': 8,
            'id': 7,
            'au': 6,
            'ng': 1,
            'vn': 7,
            'gh': 0,
            'za': 2,
            'tz': 3,
            'bw': 2,
            'otc': 8,
            'ph': 8,
        }
        user.created = user.created + timedelta(hours=timezones[country])

    return render(request, 'userlist.html', data)

def list_newusers(request, country, admin_name):
    data = {'country': country, 'admin_name': admin_name}

    users = UserProfile.objects.filter(country=country, verified='0').order_by('-created')

    try:
        users = UserProfile.objects.filter(country=country, verified='0').order_by('-created')
    except Exception:
        pass

    data['users'] = users

    wallet_users = 0

    num = len(users)
    for user in users:
        setattr(user,'num',num)
        num -= 1


    for user in users:
        referer = ''
        wallet = None
        try:
            referer = UserProfile.objects.get(member_id=user.referral_id).username
        except Exception:
            pass

        setattr(user, "referer", referer)

        taker_trades = Offers.objects.filter(taker=user.username)
        volume = 0
        for trade in taker_trades:
            volume += trade.amount

        setattr(user, "tradevol", w3.fromWei(volume,'ether'))

        try:
            wallet = Wallet.objects.get(username=user.username)
        except Exception:
            pass

        if wallet:
            if wallet.tx_hash:
                setattr(user, "approved", True)
                wallet_users += 1

        timezones = {
            'my': 8,
            'cn': 8,
            'cn-wb': 8,
            'id': 7,
            'au': 6,
            'ng': 1,
            'vn': 7,
            'gh': 0,
            'za': 2,
            'tz': 3,
            'bw': 2,
            'otc': 8,
            'ph': 8,
        }
        user.created = user.created + timedelta(hours=timezones[country])

    data['wallet_users'] = wallet_users
    data['no_wallet_users'] = len(users) - wallet_users

    num = len(users)
    for user in users:
        setattr(user, 'num', num)
        num -= 1
    data['num'] = num

    return render(request, 'new_userlist.html', data)     

def list_unverifiedusers(request, country, admin_name):
    data = {'country': country, 'admin_name': admin_name}

    username = None

    users = UserProfile.objects.filter(country=country, verified='0').order_by('-created')

    data['users'] = users

    wallet_users = 0

    for user in users:
        referer = ''
        wallet = None
        try:
            referer = UserProfile.objects.get(member_id=user.referral_id).username
        except Exception:
            pass

        setattr(user, "referer", referer)

        taker_trades = Offers.objects.filter(taker=user.username)
        volume = 0
        for trade in taker_trades:
            volume += trade.amount

        setattr(user, "tradevol", w3.fromWei(volume,'ether'))

        maker_trades = Offers.objects.filter(maker=user.username)
        volume = 0
        for trade in maker_trades:
            volume += trade.amount

        setattr(user, "makervol", w3.fromWei(volume,'ether'))

        try:
            wallet = Wallet.objects.get(username=user.username)
        except Exception:
            pass

        if wallet:
            if wallet.tx_hash:
                setattr(user, "approved", True)
                wallet_users += 1

        timezones = {
            'my': 8,
            'cn': 8,
            'cn-wb': 8,
            'id': 7,
            'au': 6,
            'ng': 1,
            'vn': 7,
            'gh': 0,
            'za': 2,
            'tz': 3,
            'bw': 2,
            'otc': 8,
            'ph': 8,
        }
        user.created = user.created + timedelta(hours=timezones[country])

    data['wallet_users'] = wallet_users
    data['no_wallet_users'] = len(users) - wallet_users

    num = len(users)
    for user in users:
        setattr(user, 'num', num)
        num -= 1
    data['num'] = num

    return render(request, 'unverified_user.html', data)    
    
def histories(request, country, admin_name, username):
    data = {}

    data['username'] = username
    data['admin_name'] = admin_name
    data['country'] = country
    
    user = UserProfile.objects.get(username=username)
    email = user.email
    history = History.objects.filter(username=username)

    for his in history:
        tokendata = Tokens.objects.get(token=his.token)
        setattr(his, 'norm_amount', his.amount / 10 ** tokendata.decimal_places)

    data['history'] = history
    data['email'] = email

    return render(request, 'history_user.html', data)

def support_chat(request, country, admin_name, offer_id):
    ref_country = country
    if country == 'cn-wb':
        ref_country = 'wb'
    chatroom = 'help%s' % ref_country
    

    return HttpResponseRedirect(reverse('chat_admin', kwargs={
        'country': country,
        'admin_name': admin_name,
        'offer_id': chatroom,
    })) 
