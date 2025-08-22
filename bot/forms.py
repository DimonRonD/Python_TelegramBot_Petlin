from django import forms


class LoginForm(forms.Form):
    calendar = forms.CharField(label="calendar", max_length=100)