from django import forms
from .models import Loan


class LoanRequestForm(forms.Form):
    date_debut = forms.DateField(
        label="Date de début souhaitée",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    date_fin_prevue = forms.DateField(
        label="Date de fin prévue",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )


class LoanAcceptForm(forms.Form):
    photo_avant = forms.ImageField(
        required=False,
        label="Photo état des lieux avant prêt (F18)",
        help_text="Optionnel : prenez une photo de l'outil pour attester de son bon état au départ.",
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )


class LoanReturnForm(forms.Form):
    photo_apres = forms.ImageField(
        required=False,
        label="Photo état des lieux au retour (F18)",
        help_text="Optionnel : photo de l'outil lors de la restitution.",
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )
    signale_endommage = forms.BooleanField(
        required=False,
        label="Signaler l'outil comme endommagé ou détérioré (F16)",
        help_text="Si coché, l'outil passera automatiquement en état « à réparer » et sera indisponible (R7).",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class LoanProlongationForm(forms.Form):
    nouvelle_date_fin_demandee = forms.DateField(
        label="Nouvelle date de fin souhaitée (F17)",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
