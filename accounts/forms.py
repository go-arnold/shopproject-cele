from django import forms
from allauth.account.forms import SignupForm
from django.utils.translation import gettext_lazy as _
from .models import Profile
import re


class PhoneSignupForm(SignupForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["phone_number"] = forms.CharField(
            max_length=20,
            label=_("Numero de telephone"),
            widget=forms.TextInput(attrs={
                'placeholder': 'Entrez le numero ici',

            }),
            help_text=_("Enter your phone number in international format"),
        )

    def clean_phone_number(self):
        phone = self.cleaned_data["phone_number"].strip()
        phone = re.sub(r"[^\d+]", "", phone)

        if not re.match(r"^\+\d{8,15}$", phone):
            raise forms.ValidationError(
                _("Le numéro de téléphone doit être au format international (par exemple : +243970000000).")
            )

        if Profile.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError(
                _("Ce numéro de téléphone est déjà enregistré.")
            )
        if phone.startswith("+243") and len(phone) != 13:
            raise forms.ValidationError(
                _("Les numéros de téléphone de la RDC doivent comporter 9 chiffres après le +243.")
            )

        return phone

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()

        phone = re.sub(r"[^\d+]", "", phone)

        if not re.match(r"^\+\d{8,15}$", phone):
            raise forms.ValidationError(
                _("Le numéro de téléphone doit être au format international (par exemple : +243970000000).")
            )

        if phone.startswith("+243") and len(phone) != 13:
            raise forms.ValidationError(
                _("Les numéros de téléphone de la RDC doivent comporter 9 chiffres après le +243.")
            )

        if Profile.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError(
                _("Ce numéro de téléphone est déjà enregistré.")
            )

        return phone

    def save(self, request):
        user = super().save(request)
        user.profile.phone_number = self.cleaned_data["phone_number"]
        user.profile.save(update_fields=["phone_number"])
        return user

    """def save(self, request):
        user = super().save(request)

        phone = self.cleaned_data.get("phone")
        if phone:
            user.profile.phone_number = phone
            user.profile.save(update_fields=["phone_number"])

        return user"""
