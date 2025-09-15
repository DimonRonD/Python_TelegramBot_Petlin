from django import forms


class LoginForm(forms.Form):
    calendar = forms.CharField(label="calendar", max_length=100)


class ExportForm(forms.Form):
    export = forms.CharField(label="export", max_length=100)