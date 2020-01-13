from django import forms
from django.utils.translation import ugettext_lazy as _

class loginform(forms.Form):
    email = forms.EmailField(label=_(u'Email'), max_length=255,
        widget=forms.TextInput())
    password = forms.CharField(label=_(u'Password'), max_length=255,
        widget=forms.PasswordInput())

class registerform(forms.Form):
    email = forms.EmailField(label=_(u'Email'), max_length=255,
        widget=forms.TextInput())
    password = forms.CharField(label=_(u'Password'), max_length=255,
        widget=forms.TextInput())
    address = forms.CharField(label=_(u'ETH Wallet Address'), max_length=255,
        widget=forms.TextInput())
    referral = forms.CharField(label=_(u'Referral Code (Optional)'), max_length=255,
        widget=forms.TextInput(), required=False)
    referer = forms.BooleanField(label=_(u'Join Referer Program'), required=False)
    verify = forms.BooleanField(label=_(u'I hereby verify that everything I have included in these forms are correct.'))  
