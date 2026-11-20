from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("pret", "auteur", "note", "date")
    list_filter = ("note", "date")
    search_fields = ("pret__outil__titre", "auteur__username", "commentaire")
