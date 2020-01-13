from django import forms

class UploadForm(forms.Form):
    screenshot = forms.FileField()
