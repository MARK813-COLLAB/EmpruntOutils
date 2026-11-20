from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "etudiant@iut.fr"}),
        label="Adresse email",
    )
    telephone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "06 12 34 56 78"}),
        label="Numéro de téléphone",
    )
    filiere = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "BUT Informatique, GEII, etc."}),
        label="Filière d'études",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "telephone", "filiere")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"class": "form-control"})
        if "password" in self.fields:
            self.fields["password"].widget.attrs.update({"class": "form-control"})
        if "password1" in self.fields:
            self.fields["password1"].widget.attrs.update({"class": "form-control"})
        if "password2" in self.fields:
            self.fields["password2"].widget.attrs.update({"class": "form-control"})

    def save(self, commit=True):
        user = super().save(commit=commit)
        telephone = self.cleaned_data.get("telephone", "")
        filiere = self.cleaned_data.get("filiere", "")
        
        # Le signal create_or_update_user_profile a déjà créé le profil
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.telephone = telephone
        profile.filiere = filiere
        if commit:
            profile.save()
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("telephone", "filiere")
        widgets = {
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "filiere": forms.TextInput(attrs={"class": "form-control"}),
        }
