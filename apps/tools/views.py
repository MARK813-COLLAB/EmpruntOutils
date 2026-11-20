from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Q
from .models import Tool, Category, Tag, Favori
from .forms import ToolForm, ToolFilterForm


def tool_list_view(request):
    """
    Catalogue des outils avec filtres et recherche (F3, F15).
    Accessible à tous les visiteurs.
    """
    form = ToolFilterForm(request.GET)
    tools = Tool.objects.select_related("proprietaire", "categorie").prefetch_related("tags")

    if form.is_valid():
        q = form.cleaned_data.get("q")
        if q:
            tools = tools.filter(
                Q(titre__icontains=q) | Q(description__icontains=q)
            )
        categorie = form.cleaned_data.get("categorie")
        if categorie:
            tools = tools.filter(categorie=categorie)
        tag = form.cleaned_data.get("tag")
        if tag:
            tools = tools.filter(tags=tag)
        disponible_seulement = form.cleaned_data.get("disponible_seulement")
        if disponible_seulement:
            tools = tools.filter(disponible=True).exclude(etat="a_reparer")

    user_favoris_ids = set()
    if request.user.is_authenticated:
        user_favoris_ids = set(
            Favori.objects.filter(utilisateur=request.user).values_list("outil_id", flat=True)
        )

    context = {
        "tools": tools,
        "form": form,
        "user_favoris_ids": user_favoris_ids,
    }
    return render(request, "tools/tool_list.html", context)


def tool_detail_view(request, pk):
    """
    Fiche détaillée d'un outil avec calendrier des réservations (F14) et avis (F8).
    """
    tool = get_object_or_404(
        Tool.objects.select_related("proprietaire", "categorie").prefetch_related("tags"),
        pk=pk,
    )

    is_favori = False
    if request.user.is_authenticated:
        is_favori = Favori.objects.filter(utilisateur=request.user, outil=tool).exists()

    # Créneaux déjà réservés (F14 - Calendrier de disponibilité)
    reserved_loans = []
    try:
        from apps.loans.models import Loan
        reserved_loans = Loan.objects.filter(
            outil=tool,
            statut__in=["accepte", "en_cours", "en_retard"],
        ).order_by("date_debut")
    except (ImportError, AttributeError):
        pass

    # Avis sur cet outil (F8)
    reviews = []
    try:
        from apps.reviews.models import Review
        reviews = Review.objects.filter(pret__outil=tool).select_related("auteur")
    except (ImportError, AttributeError):
        pass

    context = {
        "tool": tool,
        "is_favori": is_favori,
        "reserved_loans": reserved_loans,
        "reviews": reviews,
    }
    return render(request, "tools/tool_detail.html", context)


@login_required
def tool_create_view(request):
    """
    Ajout d'un nouvel outil (F2).
    """
    if request.method == "POST":
        form = ToolForm(request.POST, request.FILES)
        if form.is_valid():
            tool = form.save(commit=False)
            tool.proprietaire = request.user
            tool.save()
            form.save_m2m()
            form._save_tags(tool)
            messages.success(request, f"L'outil « {tool.titre} » a été ajouté avec succès.")
            return redirect("tools:my_tools")
        else:
            messages.error(request, "Erreur lors de l'enregistrement de l'outil.")
    else:
        form = ToolForm()

    return render(request, "tools/tool_form.html", {"form": form, "title": "Ajouter un outil"})


@login_required
def tool_update_view(request, pk):
    """
    Modification d'un outil (F2).
    Contrôle strict des droits côté serveur : seul le propriétaire peut modifier.
    """
    tool = get_object_or_404(Tool, pk=pk)

    if tool.proprietaire != request.user:
        return HttpResponseForbidden("Vous n'êtes pas autorisé à modifier cet outil.")

    if request.method == "POST":
        form = ToolForm(request.POST, request.FILES, instance=tool)
        if form.is_valid():
            tool = form.save()
            messages.success(request, f"L'outil « {tool.titre} » a été mis à jour.")
            return redirect("tools:tool_detail", pk=tool.pk)
        else:
            messages.error(request, "Erreur lors de la modification de l'outil.")
    else:
        form = ToolForm(instance=tool)

    return render(request, "tools/tool_form.html", {"form": form, "tool": tool, "title": "Modifier l'outil"})


@login_required
def tool_delete_view(request, pk):
    """
    Suppression d'un outil (F2).
    Contrôle strict des droits côté serveur : seul le propriétaire peut supprimer.
    """
    tool = get_object_or_404(Tool, pk=pk)

    if tool.proprietaire != request.user:
        return HttpResponseForbidden("Vous n'êtes pas autorisé à supprimer cet outil.")

    if request.method == "POST":
        titre = tool.titre
        tool.delete()
        messages.success(request, f"L'outil « {titre} » a été supprimé.")
        return redirect("tools:my_tools")

    return render(request, "tools/tool_confirm_delete.html", {"tool": tool})


@login_required
def my_tools_view(request):
    """
    Liste des outils de l'utilisateur connecté.
    """
    tools = Tool.objects.filter(proprietaire=request.user).select_related("categorie").prefetch_related("tags")
    return render(request, "tools/my_tools.html", {"tools": tools})


@login_required
def favoris_list_view(request):
    """
    Liste des outils favoris de l'utilisateur (F11).
    """
    favoris = Favori.objects.filter(utilisateur=request.user).select_related("outil", "outil__categorie", "outil__proprietaire")
    return render(request, "tools/favoris_list.html", {"favoris": favoris})


@login_required
def toggle_favori_view(request, pk):
    """
    Ajouter / retirer un outil des favoris (F11).
    """
    tool = get_object_or_404(Tool, pk=pk)
    favori, created = Favori.objects.get_or_create(utilisateur=request.user, outil=tool)

    if not created:
        favori.delete()
        messages.info(request, f"« {tool.titre} » a été retiré de vos favoris.")
    else:
        messages.success(request, f"« {tool.titre} » a été ajouté à vos favoris.")

    # Redirection vers la page précédente si possible
    next_url = request.META.get("HTTP_REFERER")
    if next_url:
        return redirect(next_url)
    return redirect("tools:tool_detail", pk=tool.pk)
