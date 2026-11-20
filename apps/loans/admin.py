from django.contrib import admin
from .models import Loan


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("outil", "emprunteur", "date_debut", "date_fin_prevue", "date_retour", "statut", "date_creation")
    list_filter = ("statut", "date_debut", "date_fin_prevue")
    search_fields = ("outil__titre", "emprunteur__username", "outil__proprietaire__username")
