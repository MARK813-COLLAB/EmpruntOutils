from django.contrib import admin
from .models import Category, Tag, Tool, Favori


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "nom")
    search_fields = ("nom",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "nom")
    search_fields = ("nom",)


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ("titre", "categorie", "proprietaire", "etat", "disponible", "signale_endommage", "date_creation")
    list_filter = ("categorie", "etat", "disponible", "signale_endommage")
    search_fields = ("titre", "description", "proprietaire__username")


@admin.register(Favori)
class FavoriAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "outil", "date_ajout")
    search_fields = ("utilisateur__username", "outil__titre")
