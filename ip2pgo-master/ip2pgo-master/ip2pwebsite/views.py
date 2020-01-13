from django.shortcuts import render, HttpResponse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import TemplateView
from django.utils.translation import ugettext_lazy as _
from django.template import loader
from django.shortcuts import render_to_response
from django.urls import reverse
from directapp.models import UserProfile, Dividend, Tokens, Offers
from django.contrib import messages
from .forms import RegistrationForm, ContactForm
import random, string, requests
from django.template import Context
from django.template.loader import render_to_string, get_template
from django.core.mail import EmailMessage
from django.conf import settings
from promotions.referral import register_referral
from django.utils import timezone   
from datetime import timedelta     

def rico_main(request):
    return render(request, 'rico_main.html')

def website(request):
    return render(request, 'website.html')

def error(request):
    return render(request, 'error.html')

def terms(request):
    return render(request, 'terms.html')

def termsofuse(request):
    return render(request, 'termofuse.html')

def faq(request):
    return render(request, 'faq.html')

def policy(request):
    return render(request, 'policy.html')

def country(request):
    #return HttpResponseRedirect(reverse('error'))
    return render(request, 'choosecountry.html')

def register_country(request):
    return render(request, 'registercountry.html')

def rewards(request):
    return render(request, 'rewards.html')

def rico_termsheet(request):
    return render(request, 'ico_termsheet.html')

def referralwebsite(request):
    return render(request, 'referralwebsite.html')

def userguide(request):
    return render(request, 'userguide.html')

def ip2pgoterms(request):
    return render(request, 'ip2pgoterms.html')

def otc_userguide(request):
    return render(request, 'otc_userguide.html')

def fiat_userguide(request):
    return render(request, 'fiat_userguide.html')

def categories(request):
    return render(request, 'categories.html')

def login_categories(request):
    return render(request, 'login_categories.html')

def register_otc(request):
    return render(request, 'register_otc.html')

def login_otc(request):
    return render(request, 'login_otc.html')

def dividends(request):
    today = timezone.now() - timedelta(days=1)
    div_today = Dividend.objects.filter(date__gte=today)
    data = {}
    data['today'] = timezone.now().date() 
    offers = Offers.objects.filter(completed=True, cancelled=False, end__gte=today)
    data['offers'] = len(offers)
    if len(div_today) > 0:
        for div in div_today:
            token = Tokens.objects.get(token=div.name)
            setattr(div, 'amt', amount / 10 ** token.decimal_places)
        data['record'] = div_today

    return render(request, 'dividends.html', data)

def download(request, country):
    data = {}
    data['country'] = country
    return render(request, 'download.html', data)

def registration(request, country):
    data = {}
    data['country'] = country

    if 'register' in request.POST:
        registration_form = RegistrationForm(request.POST)
        register_status, country = register(country, registration_form)

        if register_status :
            return HttpResponseRedirect(reverse('download', kwargs={'country': country}))
            
        else:
            messages.warning(request, 'Registration unsuccessful. Please register with another email address/username or contact us.')
    else:
        registration_form = RegistrationForm()

    data['registration_form'] = registration_form

    return render(request, 'registration.html', data)

def registration_refer(request, country, referral_id):
    data = {}
    data['ref_id'] = referral_id

    if 'register' in request.POST:
        registration_form = RegistrationForm(request.POST)
        register_status, country = register_ref(country, registration_form, data)

        if register_status :
            return HttpResponseRedirect(reverse('download', kwargs={'country': country}))
            
        else:
            messages.warning(request, 'Registration unsuccessful. Please register with another email address/username or contact us.')
    else:
        registration_form = RegistrationForm()
        registration_form.fields['referral_id'].initial = referral_id

    data['registration_form'] = registration_form
    data['referral_id'] = referral_id

    return render(request, 'registration.html', data, country)

def register(country, register_data):
    username = register_data['username'].value().lower()
    status = False
    referral_id = None
    member_id = ''  
    check_email = UserProfile.objects.filter(email=register_data['email'].value())
    check_username = UserProfile.objects.filter(username=username)
    user_referral = register_data['referral_id'].value()
    check_referral = None

    try:
        check_referral = UserProfile.objects.get(member_id=user_referral)
    except Exception as e:
        user_referral = None

    english = ['my', 'au', 'ng', 'gh', 'za', 'tz', 'bw', 'otc', 'ph']
         

    if len(check_email) == 0 and len(check_username) == 0:
        status = True

        retry = True
        while retry:
            retry = False
            member_id = ''
            for n in range(4):
                member_id += random.choice(string.ascii_letters + string.digits)
            testget = UserProfile.objects.filter(member_id=member_id)
            if len(testget) > 0:
                retry = True       
 
        UserProfile.objects.create(
            email = register_data['email'].value(),
            passcode = register_data['passcode'].value(),
            username = username,
            member_id = member_id,
            country = country,
            referral_id = user_referral,

        )
        
        try:
            register_referral(username=username, referral=user_referral)
        except Exception as e:
            # skip referral registration
            pass


        user = UserProfile.objects.get(email=register_data['email'].value())

        recipient = user.email
        username = user.username

        subject =_(u"Welcome to iP2PGO, this is your download link")
        to = [recipient]
        from_email = settings.EMAIL_HOST_USER

        lang = {'cn': 'zh-hans', 'cn-wb': 'zh-hans', 'id': 'id' , 'my': 'en-us', 'au': 'en-us', 'vn': 'vi', 'ng': 'en-us', 'gh': 'en-us','za': 'en-us', 'tz': 'en-us', 'bw': 'en-us', 'otc': 'en-us', 'ph': 'en-us'}
        pref = {'cn': 'cn.', 'cn-wb': '', 'id': 'id.', 'my': 'my.', 'au': 'au.', 'vn': 'vn.', 'ng': 'ng.', 'gh': 'gh.', 'za': 'za.', 'tz': 'tz.' , 'bw': 'bw.' , 'otc': 'otc.', 'ph': 'ph.' }
        dlurl = '%sip2pgo.com/%s/download/%s' % (pref[country], lang[country], country)
        
        ctx = {
            'link': dlurl,
            'username' : username, 
        }
  
        if country in english: 
            message = get_template(
                'registeremail-en.html').render(ctx)
        else:
            message = get_template(
                'registeremail-%s.html' % country).render(ctx)
        msg = EmailMessage(subject, message, to=to, from_email=from_email)
        msg.content_subtype = 'html'
        msg.send()

        status = True
        

    return (status, country)


def register_ref(country, register_data, data):
    username = register_data['username'].value().lower()
    status = False
    member_id = ''  
    check_email = UserProfile.objects.filter(email=register_data['email'].value())
    check_username = UserProfile.objects.filter(username=username)

    english = ['my', 'au', 'ng', 'gh', 'za', 'tz', 'bw', 'otc', 'ph']
    
    if len(check_email) == 0 and len(check_username) == 0:
        status = True
     
    referral_id = data['ref_id']

    specialized = ['A-', 'D-', 'C-']
    if status:
        retry = True
        while retry:
            retry = False
            member_id = ''
            for special in specialized:
                if special in referral_id:
                    member_id = special 
            for n in range(4):
                member_id += random.choice(string.ascii_letters + string.digits)
            testget = UserProfile.objects.filter(member_id=member_id)
            if len(testget) > 0:
                retry = True 
         
        UserProfile.objects.create(
            email = register_data['email'].value(),
            passcode = register_data['passcode'].value(),
            username = username,
            referral_id = referral_id,
            member_id = member_id,
            country = country,
        )

        try:
            register_referral(username=username, referral=referral_id)
        except Exception as e:
            # skip referral registration
            pass
        
        user = UserProfile.objects.get(email=register_data['email'].value())

        recipient = user.email
        username = user.username

        subject =_(u"This is your download link")
        to = [recipient]
        from_email = settings.EMAIL_HOST_USER

        lang = {'cn': 'zh-hans', 'cn-wb': 'zh-hans', 'id': 'id' , 'my': 'en-us', 'au': 'en-us', 'vn': 'vi', 'ng': 'en-us', 'gh': 'en-us', 'za': 'en-us', 'tz': 'en-us', 'bw': 'en-us', 'otc': 'en-us', 'ph': 'en-us'}
        pref = {'cn': 'cn.', 'cn-wb': '', 'id': 'id.', 'my': 'my.', 'au': 'au.', 'vn': 'vn.', 'ng': 'ng.', 'gh': 'gh.', 'za': 'za.', 'tz': 'tz.' , 'bw': 'bw.', 'otc': 'otc.', 'ph': 'ph.'}
        dlurl = '%sip2pgo.com/%s/download/%s' % (pref[country], lang[country], country)
        
        ctx = {
            'link': dlurl,
            'username' : username, 
        }
  
        if country in english: 
            message = get_template(
                'registeremail-en.html').render(ctx)
        else:
            message = get_template(
                'registeremail-%s.html' % country).render(ctx)
        msg = EmailMessage(subject, message, to=to, from_email=from_email)
        msg.content_subtype = 'html'
        msg.send()

        status = True

    return (status, country)




def loading(request, country):
    data = {}
    lang = {'cn': 'zh-hans', 'cn-wb': 'zh-hans', 'id': 'id' , 'my': 'en-us', 'au': 'en-us', 'vn': 'vi', 'ng': 'en-us', 'gh': 'en-us', 'za': 'en-us', 'tz': 'en-us' , 'bw': 'en-us', 'otc': 'en-us', 'ph': 'en-us'}
    pref = {'cn': 'cn.', 'cn-wb': '', 'id': 'id.', 'my': 'my.', 'au': 'au.', 'vn': 'vn.', 'ng': 'ng.', 'gh': 'gh.', 'za': 'za.', 'tz': 'tz.' , 'bw': 'bw.', 'otc': 'en-us', 'ph': 'ph.'}
    data['dlurl'] = '%sip2pgo.com/%s/download/%s' % (pref[country], lang[country], country)
 
    return render(request, 'download.html', data)


def contact(request):
    form_class = ContactForm

    # new logic!
    if request.method == 'POST':
        form = form_class(data=request.POST)

        if form.is_valid():
            name = request.POST.get(
                'name'
            , '')
            from_email = request.POST.get(
                'from_email'
            , '')
            form_message = request.POST.get('message', '')

            # Email the profile with the
            # contact information
            template = get_template('contact_template.txt')
            context = {
                'name': name,
                'from_email': from_email,
                'form_message': form_message,
               
            }
            content = template.render(context)

            email = EmailMessage(
                "New contact form submission",
                content,
                "Contact Form" +'',
                ['ip2pglobal@gmail.com'],
                headers = {'Reply-To': from_email }
            )
            email.send()
            messages.success(request, 'Your message have successfull send. Please wait our admin to reply your message.')

    return render(request, 'contactus.html', {
        'form': form_class,
    })
