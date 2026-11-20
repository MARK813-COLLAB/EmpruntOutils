from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    NOTE_CHOICES = [(i, f"{i} étoile{'s' if i > 1 else ''}") for i in range(5, 0, -1)]

    note = forms.ChoiceField(
        choices=NOTE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Note d'évaluation",
    )

    class Meta:
        model = Review
        fields = ("note", "commentaire")
        widgets = {
            "commentaire": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Partagez votre expérience avec cet outil et ce prêt...",
                }
            ),
        }
