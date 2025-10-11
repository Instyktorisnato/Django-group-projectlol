
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Свою почту дай которая рабочая типа.')
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date'}))

    class Meta:
        model = User
        fields = ('username','email','date_of_birth','password1','password2')

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Свое придумай чето")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Зделайте на другую Почту пж")
        return email
