from django import forms
from .models import AdminProfile
from django.utils.translation import ugettext_lazy as _

class AdminForm(forms.Form):
    admin_name = forms.CharField(
        label = _(u'Name'),
        widget = forms.TextInput(),
        max_length = 255,
    )

    password = forms.CharField(
        label = _(u'Password'),
        widget = forms.PasswordInput(),
        max_length = 255,
    )
