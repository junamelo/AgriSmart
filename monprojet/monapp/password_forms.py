from django import forms
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-green-300 rounded-md',
            'placeholder': 'Votre adresse email'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("Aucun compte n'est associé à cette adresse email.")
        return email

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-green-300 rounded-md',
            'placeholder': 'Nouveau mot de passe'
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-green-300 rounded-md',
            'placeholder': 'Confirmer le nouveau mot de passe'
        })
    )
