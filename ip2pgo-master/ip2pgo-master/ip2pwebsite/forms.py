
from django import forms
from django.utils.translation import ugettext_lazy as _

class RegistrationForm(forms.Form):
    email = forms.EmailField(
        label = _(u'Email'),
        widget = forms.TextInput(),
        max_length = 255,
    )

    username = forms.CharField(
        label = _(u'Username'),
        widget = forms.TextInput(),
        max_length = 255,
    )

    passcode = forms.CharField(
        label = _(u'Passcode'),
        widget = forms.PasswordInput(),
        max_length = 6,
    )

    repasscode = forms.CharField(
        label = _(u'Re-enter Passcode'),
        widget = forms.PasswordInput(),
        max_length = 6,
    ) 
       
    referral_id = forms.CharField(
        label = _(u'Referral ID'),
        widget = forms.TextInput(),
        max_length = 4,
        required = False,
    )
    
class UpdateProfile(forms.Form):
    
     username = forms.CharField(
        label = 'Username',
        widget = forms.TextInput(),
        max_length = 50,
    )   

     sex = forms.CharField(
         label = "Gender",
         widget = forms.TextInput(),
         max_length = 1,
     )

class ContactForm(forms.Form):
    name = forms.CharField(
        label = _(u'Name'),
        widget = forms.TextInput(),
        max_length = 20,
        required=True,
    )

    from_email = forms.EmailField(
        label = _(u'Email'),        
        widget = forms.TextInput(),
        max_length = 50,
        required=True,
    )

    message = forms.CharField(
        label = _(u'Message'),
        widget= forms.Textarea(),
        required=True,
    )
