import random, string, requests
from datetime import datetime
from decimal import Decimal
from django.shortcuts import render
from django.http import HttpResponseRedirect as re
from django.urls import reverse
from . import forms
from directapp.models import UserProfile, Wallet, RICOGO as ricoers
from . import crowdfund
from infuraeth import infura_settings
from django.core import exceptions as e

def login(request):
    data = {}
    message = None
    verified = False
    if request.method == 'POST':
        form = forms.loginform(request.POST)
        email = str(form['email'].value())
        try:
            user = ricoers.objects.get(email=email)
        except Exception:
            user = None
        if user:
            user.security_code = None
            user.save()
            password = str(form['password'].value())
            if password == user.password:
                security_code = ''
                for n in range(10):
                    security_code += random.choice(
                        string.digits+string.ascii_letters)
                user.security_code = security_code
                user.save()
                verified = True
            else:
                form = forms.loginform()
                message = "The password is incorrect. Please enter the correct password"
        else:
            form = forms.loginform()
            message = "That email is not registered yet. Please register or enter a registered email"
    else:
        form = forms.loginform()
    data['form'] = form    
    if message:
        data['message'] = message

    if verified:
        return re(reverse('ricomain', kwargs={'security_code': security_code})) 
    else:
        return render(request, 'ricologin.html', data) 

def main(request, security_code):
    data = {}
    message = None
    okay = False
    ref_bonus = Decimal(0.1)
    divtoeth = 10 ** 18    

    try:
        user = ricoers.objects.get(security_code=security_code)
    except Exception:
        user = None
        message = "This session has expired. Please login again."

    if user:
        latest_data = check_crowdfund(user.address)
        if latest_data:
            okay = True
    else:
        message = "This user does not participate in our programme."

    if message:
        data['message'] = message

    if okay:
        if user.referer:
            data['username'] = user.username
            find_referee = ricoers.objects.filter(referral=user.username)
            if len(find_referee) > 0:
                data['referee'] = []
                referee_bonus = 0
                for referee in find_referee:
                    if referee.amount > 0:
                        data['referee'].append(referee.email)
                        referee_bonus += Decimal(referee.amount) * ref_bonus
                if referee_bonus > user.ref_bonus:
                    user.ref_bonus = referee_bonus
                    user.save()
        data['email'] = user.email    
        data['amount'] = round(((user.amount + user.ref_bonus) / divtoeth), 2)
        data['referral'] = user.referral       
        data['crowdfund'] = crowdfund.address

        return render(request, 'ricomain.html', data)
    else:
        return re(reverse('ricologin'))

def register(request):
    data = {}
    message = None
    okay = False

    if request.method == 'POST':
        form = forms.registerform(request.POST)
        email = str(form['email'].value())
        address = str(form['address'].value())
        password = str(form['password'].value())
        referral = str(form['referral'].value())

        try:
            get_email = ricoers.objects.get(email=email)
            data['message'] = "Your Email already exist. Try different one."
            form = forms.registerform(request.POST)
            data['form'] = form
            return render(request, 'ricoregister.html', data)            
        except e.DoesNotExist:
            pass

        try:
            get_wallet = ricoers.objects.get(address=address)
            data['message']= "Your  ETH Wallet Address already exist. Use different address."        
            form = forms.registerform(request.POST)
            data['form'] = form
            return render(request, 'ricoregister.html', data)            
        except e.DoesNotExist:
            pass

        if form['referer'].value() == 1: 
            username = ''
            for n in range(6):
                username += random.choice(string.digits+string.ascii_letters)
        else:
            username = None
        ricoers.objects.create(
            email = email,
            password = password,
            address = address,
            referral = referral,
            referer = form['referer'].value(),
            username = username,
        )
        if form['verify'].value():
            okay = True
        else:
            form = forms.registerform(request.POST)
            message = "You must verify that your registration is correct first." 
    else:
        form = forms.registerform()
    
    data['form'] = form
    if message:
        data['message'] = message

    if okay:
        return re(reverse('ricologin'))
    else:
        return render(request, 'ricoregister.html', data)

def check_crowdfund(address):
    
    try:
        user = ricoers.objects.get(address=address)
    except Exception:
        return False

    okay = False
    ethtogo = 15000
    stage_one = {'timestamp':datetime(2019,6,1,0,0,0).timestamp(), 'bonus':Decimal(1.5)}
    stage_two = {'timestamp':datetime(2019,7,1,0,0,0).timestamp(), 'bonus':Decimal(1.2)}
    stage_three = {'timestamp':datetime(2019,8,1,0,0,0).timestamp(),'bonus':Decimal(1.1)}
    endpoint = "http://api.etherscan.io/api?module=account&action=txlist&address=%s&startblock=0&endblock=99999999&sort=asc&apikey=%s" % (crowdfund.address, infura_settings.ETHERSCAN_KEY)

    response = requests.get(endpoint)
    
    if response.status_code == 200:
        okay = True
        data = response.json()
        result = data['result']
        current_eth_amount = 0
        for transaction in result:
            if transaction['from'] == address.lower():
                if int(transaction['timeStamp']) < int(stage_one['timestamp']):
                    current_eth_amount += Decimal(transaction['value'])
                    if current_eth_amount > user.eth:
                        eth = Decimal(transaction['value'])
                        go = eth * ethtogo * stage_one['bonus']
                        user.eth = eth
                        user.amount = go
                        user.save()        
                elif int(transaction['timeStamp']) < int(stage_two['timestamp']):
                    current_eth_amount += Decimal(transaction['value'])
                    if current_eth_amount > user.eth:
                        eth = Decimal(transaction['value'])
                        go = eth * ethtogo * stage_two['bonus']
                        user.eth = eth
                        user.amount = go
                        user.save()        
                elif int(transaction['timeStamp']) < int(stage_three['timestamp']):
                    current_eth_amount += Decimal(transaction['value'])
                    if current_eth_amount > user.eth:
                        eth = Decimal(transaction['value'])
                        go = eth * ethtogo * stage_three['bonus']
                        user.eth = eth
                        user.amount = go
                        user.save()       
                else:
                    current_eth_amount += Decimal(transaction['value'])
                    if current_eth_amount > user.eth:
                        eth = Decimal(transaction['value'])
                        go = eth * ethtogo
                        user.eth = eth
                        user.amount = go
                        user.save()       
                 
    if okay:
        return True
    else:
        return False
