from django import forms
from .models import Tool, Category, Tag


class ToolForm(forms.ModelForm):
    tags_text = forms.CharField(
        required=False,
        label="Tags (séparés par des virgules)",
        help_text="Ex: bricolage, jardinage, électrique",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "perceuse, sans fil, batterie"}),
    )

    class Meta:
        model = Tool
        fields = ("titre", "categorie", "description", "photo", "etat", "disponible")
        widgets = {
            "titre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom de l'outil"}),
            "categorie": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Description détaillée, état d'usage, accessoires fournis..."}),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "etat": forms.Select(attrs={"class": "form-select"}),
            "disponible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["tags_text"].initial = ", ".join(t.nom for t in self.instance.tags.all())

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            self._save_tags(instance)
        return instance

    def _save_tags(self, instance):
        tags_raw = self.cleaned_data.get("tags_text", "")
        instance.tags.clear()
        if tags_raw:
            for tag_name in [t.strip().lower() for t in tags_raw.split(",") if t.strip()]:
                tag_obj, _ = Tag.objects.get_or_create(nom=tag_name)
                instance.tags.add(tag_obj)


class ToolFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Recherche par mot-clé",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Rechercher un outil..."}),
    )
    categorie = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="Toutes les catégories",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    tag = forms.ModelChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        empty_label="Tous les tags",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    disponible_seulement = forms.BooleanField(
        required=False,
        label="Disponibles uniquement",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
