from django import forms
from .models import LoanApplication,UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth.forms import PasswordChangeForm


class LoanApplicationForm(forms.ModelForm):
    class Meta:
        model = LoanApplication
        exclude = ['user']
        widgets = {
            'Gender': forms.TextInput(attrs={'placeholder': 'e.g. Male / Female', 'class': 'form-control'}),
            'Married': forms.TextInput(attrs={'placeholder': 'e.g. Yes / No', 'class': 'form-control'}),
            'Dependents': forms.TextInput(attrs={'placeholder': 'e.g. 0, 1, 2, 3+', 'class': 'form-control'}),
            'Education': forms.TextInput(attrs={'placeholder': 'e.g. Graduate / Not Graduate', 'class': 'form-control'}),
            'Self_Employed': forms.TextInput(attrs={'placeholder': 'e.g. Yes / No', 'class': 'form-control'}),
            'ApplicantIncome': forms.NumberInput(attrs={'placeholder': 'e.g. 5000', 'class': 'form-control'}),
            'CoapplicantIncome': forms.NumberInput(attrs={'placeholder': 'e.g. 2000', 'class': 'form-control'}),
            'LoanAmount': forms.NumberInput(attrs={'placeholder': 'e.g. 120', 'class': 'form-control'}),
            'Loan_Amount_Term': forms.NumberInput(attrs={'placeholder': 'e.g. 360', 'class': 'form-control'}),
            'Credit_History': forms.TextInput(attrs={'placeholder': 'e.g. 1 = Good, 0 = Bad', 'class': 'form-control'}),
            'Property_Area': forms.TextInput(attrs={'placeholder': 'e.g. Urban / Rural / Semiurban', 'class': 'form-control'}),
        }



class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    mobile_number = forms.CharField(max_length=15)
    address = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'mobile_number', 'address', 'password1', 'password2']

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['mobile_number', 'address']

# Change Password Form (already provided by Django, we just use it)
class CustomPasswordChangeForm(PasswordChangeForm):
    pass