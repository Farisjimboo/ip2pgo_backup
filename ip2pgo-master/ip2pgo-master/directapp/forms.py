from django import forms
from .models import BankReference, UserProfile, Currency, Tokens
from .models import Passcode
from dispute.models import DisputeSession, DisputeChat
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import RadioSelect


class LoginForm(forms.Form):
    email = forms.EmailField(
        label = _(u'Email'),
        widget = forms.TextInput(),
        max_length = 255,
    )
    
    code = forms.CharField(
        label = _(u'Passcode'),
        widget = forms.PasswordInput(),
        max_length = 6,
    )

class SecurityForm(forms.Form):
    code = forms.CharField(
        label = _(u'Security Code'),
        widget = forms.PasswordInput(),
        max_length = 6,
    )

class UpdateForm(forms.Form):
    def __init__(self,*args,**kwargs):
       country = kwargs['initial']['country'].upper()
       if country == 'CN-WB':
           country = 'CN'
       choices = BankReference.objects.filter(country=country).values_list('name', flat=True)
       super(UpdateForm, self).__init__(*args, **kwargs)
       self.fields['bank_name'] = forms.ModelChoiceField(choices)
       self.fields['bank_name'].label = _(u'Payment Method')
       self.fields['bank_name'].initial = choices
    
    class Meta:
        model = UserProfile 
        fields = ('upload_ic', 'upload_selfie', )
    
  
    phone_number = forms.IntegerField(
        label = _(u'Phone Number'),
        widget = forms.TextInput(),
    )
    
    display_name = forms.CharField(
        label = _(u'Display Name'),
        widget = forms.TextInput(),
        max_length = 50,
        required = False,
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


    holder_name = forms.CharField(
        label = _(u'Account Holder Name'),
        widget = forms.TextInput(),
        max_length = 50,
    )

    bank_account = forms.CharField(
        label = _(u'Account No.(for Bank) / Mobile No.(for Mobile Money)'),
        widget = forms.TextInput(),
        max_length = 50,
    )

    upload_ic = forms.FileField(
        label = _(u'Please upload your national identification card. '),
    )

    upload_selfie = forms.FileField(
        label = _(u'Please upload a selfie holding your national identification card. Make sure that the photos are clear '),
    )

    bsb = forms.CharField(
        label = 'BSB',
        widget = forms.TextInput(),
        max_length = 50, 
    )

    payid = forms.CharField(
        label = 'Pay ID / Osko (if available)',
        widget = forms.TextInput(),
        max_length = 50,
        required = False,
    )

class DisputeForm(forms.Form):
    class Meta:
        model = DisputeSession
        fields = ('maker_doc', 'taker_doc', )

    maker_doc = forms.FileField()
    taker_doc = forms.FileField()

    
class PasscodeForm(forms.Form):

    passcode = forms.CharField(
        label =_(u'Passcode'),
        widget = forms.PasswordInput(),
        max_length = 6,
    ) 

class resetPasscodeForm(forms.Form):
    passcode = forms.CharField(
        label = _(u'New Passcode'),
        widget = forms.TextInput(),
        max_length = 6,
    )

class Gender(forms.Form):
    field1 = forms.ChoiceField(required=True,
        widget=forms.RadioSelect(
           attrs={'class': 'Radio'}),
           choices=(('male','Male'),('female','Female'),
        )
    ) 

class OfferSell(forms.Form):


    TIMER_CHOICES = (
        (15, '15 minutes'),
        (30, '30 minutes'),
    )


    floor = forms.CharField(
        label = _(u'Floor Price'),
        widget = forms.TextInput(),
        max_length = 20,
        required = False,
    )
     
   
    maximum = forms.DecimalField(
        label = _(u'Maximum amount to sell'),
        widget = forms.TextInput(),
        max_digits = 20,
    )	

    minimum = forms.DecimalField(
        label = _(u'Minimum amount to sell'),
        widget = forms.TextInput(),
        max_digits = 20,
    )
    
    
    verified = forms.BooleanField(
        label=_(u'For Verified User Only:'),
        required = False,
    )
 
    payment_window = forms.ChoiceField(
        label=_(u'Payment Window'),
        choices=TIMER_CHOICES,
    )
  

class OfferBuy(forms.Form):
    TIMER_CHOICES = (
        (15, '15 minutes'),
        (30, '30 minutes'),
    )   


    ceiling = forms.CharField(
        label = _(u'Ceiling Price'),
        widget = forms.TextInput(),
        max_length = 20,
        required = False,
    )

    maximum = forms.DecimalField(
        label = _(u'Maximum amount to buy'),
        widget = forms.TextInput(),
        max_digits = 20,
    )

    minimum = forms.DecimalField(
        label = _(u'Minimum amount to buy'),
        widget = forms.TextInput(),
        max_digits = 20,
    )
   

    payment_window = forms.ChoiceField(
        label=_(u'Payment Window'),
        choices=TIMER_CHOICES,
    )
   
    verified = forms.BooleanField(
        label=_(u'For Verified User Only:'),
        required = False,
    )

    
    


class OfferBuyAU(forms.Form):
    TIMER_CHOICES = (
        (30, '30 minutes'),
        (1440, '24 hours'),
    )   

    ceiling = forms.CharField(
        label = _(u'Ceiling Price'),
        widget = forms.TextInput(),
        max_length = 20,
        required = False,
    )

    maximum = forms.DecimalField(
        label = _(u'Maximum amount to buy'),
        widget = forms.TextInput(),
        max_digits = 20,
    )

    minimum = forms.DecimalField(
        label = _(u'Minimum amount to buy'),
        widget = forms.TextInput(),
        max_digits = 20,
    )

    
    verified = forms.BooleanField(
        label=_(u'For Verified User Only:'),
        required = False,
    )
   

    payment_window = forms.ChoiceField(
        label=_(u'Payment Window'),
        choices=TIMER_CHOICES,
    )


class OfferSellAU(forms.Form):
    TIMER_CHOICES = (
        (30, '30 minutes'),
        (1440, '24 hours'),
    )   

    floor = forms.CharField(
        label = _(u'Floor Price'),
        widget = forms.TextInput(),
        max_length = 20,
        required = False,
    )
     
   
    maximum = forms.DecimalField(
        label = _(u'Maximum amount to sell'),
        widget = forms.TextInput(),
        max_digits = 20,
    )	

    minimum = forms.DecimalField(
        label = _(u'Minimum amount to sell'),
        widget = forms.TextInput(),
        max_digits = 20,
    )

   
    verified = forms.BooleanField(
        label=_(u'For Verified User Only:'),
        required = False,
    )
   
    payment_window = forms.ChoiceField(
        label=_(u'Payment Window'),
        choices=TIMER_CHOICES,
    )


class Selling(forms.Form):
    amount = forms.DecimalField(
        label=_(u'Amount to Sell'),
        max_digits = 20,
        localize = True,
    )

    verified = forms.BooleanField(
        label=_(u'Transaction fees with GO Token:'),
        required = False,
    )

class Buying(forms.Form):
    amount = forms.DecimalField(
        label=_(u'Amount to Buy'),
        #widget=forms.TextInput(attrs={'placeholder': 'Amount to Buy'}),
        max_digits = 20,
        localize = True,
    )

    
    verified = forms.BooleanField(
        label=_(u'Transaction fees with GO Token:'),
        required = False,
    )

class WithdrawalForm(forms.Form):
     
    amount = forms.DecimalField(
        label = _(u'Amount'),
        decimal_places = 18,
        max_digits = 50,
    )

    address = forms.CharField(
        label = _(u'Withdraw to'),
        max_length = 100,
    )

class RatingForm(forms.Form):
    
    comment = forms.CharField(
        label = _(u'Comment (optional)'),
        max_length = 255,
        required = False,
    )

class ChatForm(forms.Form):
    message = forms.CharField(max_length=255, required=False)

class DepositForm(forms.Form):
    txhash = forms.CharField(
        label = _(u'Confirm your deposit by providing a verified tx hash below'),
        max_length=255,
    )
