from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import HttpResponseForbidden
from apps.tools.models import Tool
from .models import Loan
from .forms import LoanRequestForm, LoanAcceptForm, LoanReturnForm, LoanProlongationForm
from . import services


@login_required
def loan_list_view(request):
    """
    Historique et suivi des prêts (F6, F7).
    Affiche séparément :
    - Les outils empruntés par l'utilisateur
    - Les demandes et prêts sur les outils de l'utilisateur
    """
    my_borrowed_loans = (
        Loan.objects.filter(emprunteur=request.user)
        .select_related("outil", "outil__proprietaire")
        .order_by("-date_creation")
    )
    my_tools_loans = (
        Loan.objects.filter(outil__proprietaire=request.user)
        .select_related("outil", "emprunteur")
        .order_by("-date_creation")
    )

    context = {
        "my_borrowed_loans": my_borrowed_loans,
        "my_tools_loans": my_tools_loans,
    }
    return render(request, "loans/loan_list.html", context)


@login_required
def loan_create_view(request, tool_id):
    """
    Formulaire de demande d'emprunt (F4).
    Vérifie R1 (auto-emprunt interdit) et R2 (pas de chevauchement).
    """
    tool = get_object_or_404(Tool, pk=tool_id)

    # Règle R1
    if tool.proprietaire == request.user:
        messages.error(request, "Vous ne pouvez pas emprunter votre propre outil (R1).")
        return redirect("tools:tool_detail", pk=tool.pk)

    if not tool.disponible or tool.etat == "a_reparer":
        messages.error(request, "Cet outil est indisponible au prêt.")
        return redirect("tools:tool_detail", pk=tool.pk)

    if request.method == "POST":
        form = LoanRequestForm(request.POST)
        if form.is_valid():
            date_debut = form.cleaned_data["date_debut"]
            date_fin_prevue = form.cleaned_data["date_fin_prevue"]
            try:
                loan = services.creer_demande_pret(
                    outil=tool,
                    emprunteur=request.user,
                    date_debut=date_debut,
                    date_fin_prevue=date_fin_prevue,
                )
                messages.success(request, f"Votre demande d'emprunt pour « {tool.titre} » a été envoyée au propriétaire.")
                return redirect("loans:loan_list")
            except ValidationError as e:
                messages.error(request, e.message if hasattr(e, "message") else str(e))
    else:
        form = LoanRequestForm()

    context = {
        "tool": tool,
        "form": form,
    }
    return render(request, "loans/loan_create.html", context)


@login_required
def loan_accept_view(request, pk):
    """
    Acceptation d'une demande par le propriétaire (F5, R3, F18).
    """
    loan = get_object_or_404(Loan, pk=pk)

    if loan.outil.proprietaire != request.user:
        return HttpResponseForbidden("Seul le propriétaire de l'outil peut accepter cette demande (R3).")

    if request.method == "POST":
        form = LoanAcceptForm(request.POST, request.FILES)
        if form.is_valid():
            photo_avant = form.cleaned_data.get("photo_avant")
            try:
                services.accepter_pret(loan, request.user, photo_avant=photo_avant)
                messages.success(request, f"La demande de {loan.emprunteur.username} a été acceptée.")
                return redirect("loans:loan_list")
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = LoanAcceptForm()

    return render(request, "loans/loan_accept.html", {"loan": loan, "form": form})


@login_required
def loan_refuse_view(request, pk):
    """
    Refus d'une demande par le propriétaire (F5, R3).
    """
    loan = get_object_or_404(Loan, pk=pk)

    if loan.outil.proprietaire != request.user:
        return HttpResponseForbidden("Seul le propriétaire de l'outil peut refuser cette demande (R3).")

    if request.method == "POST":
        try:
            services.refuser_pret(loan, request.user)
            messages.info(request, f"La demande de {loan.emprunteur.username} a été refusée.")
            return redirect("loans:loan_list")
        except ValidationError as e:
            messages.error(request, str(e))

    return render(request, "loans/loan_confirm_refuse.html", {"loan": loan})


@login_required
def loan_start_view(request, pk):
    """
    Démarrage d'un prêt accepté -> 'en_cours' (F6).
    """
    loan = get_object_or_404(Loan, pk=pk)

    if request.user not in (loan.outil.proprietaire, loan.emprunteur):
        return HttpResponseForbidden("Action non autorisée.")

    if request.method == "POST":
        try:
            services.demarrer_pret(loan, request.user)
            messages.success(request, f"Le prêt de « {loan.outil.titre} » est désormais en cours.")
        except ValidationError as e:
            messages.error(request, str(e))

    return redirect("loans:loan_list")


@login_required
def loan_return_view(request, pk):
    """
    Restitution d'un outil : passage à 'rendu' (F6, F16, R7, F18).
    Permet l'upload photo après et le signalement dommage.
    """
    loan = get_object_or_404(Loan, pk=pk)

    if request.user not in (loan.outil.proprietaire, loan.emprunteur):
        return HttpResponseForbidden("Action non autorisée.")

    if request.method == "POST":
        form = LoanReturnForm(request.POST, request.FILES)
        if form.is_valid():
            photo_apres = form.cleaned_data.get("photo_apres")
            signale_endommage = form.cleaned_data.get("signale_endommage", False)
            try:
                services.marquer_rendu(
                    loan=loan,
                    user=request.user,
                    photo_apres=photo_apres,
                    signale_endommage=signale_endommage,
                )
                if signale_endommage:
                    messages.warning(request, "L'outil a été marqué comme rendu et signalé endommagé (passé à réparer).")
                else:
                    messages.success(request, "L'outil a bien été marqué comme rendu.")
                return redirect("loans:loan_list")
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = LoanReturnForm()

    return render(request, "loans/loan_return.html", {"loan": loan, "form": form})


@login_required
def loan_prolongation_view(request, pk):
    """
    Demande de prolongation de prêt par l'emprunteur (F17, R6).
    """
    loan = get_object_or_404(Loan, pk=pk)

    if request.user != loan.emprunteur:
        return HttpResponseForbidden("Seul l'emprunteur peut demander une prolongation.")

    if request.method == "POST":
        form = LoanProlongationForm(request.POST)
        if form.is_valid():
            nouvelle_date = form.cleaned_data["nouvelle_date_fin_demandee"]
            try:
                services.demander_prolongation(loan, request.user, nouvelle_date)
                messages.success(request, f"Votre demande de prolongation jusqu'au {nouvelle_date.strftime('%d/%m/%Y')} a été transmise.")
                return redirect("loans:loan_list")
            except ValidationError as e:
                messages.error(request, e.message if hasattr(e, "message") else str(e))
    else:
        form = LoanProlongationForm()

    return render(request, "loans/loan_prolongation.html", {"loan": loan, "form": form})


@login_required
def loan_prolongation_validate_view(request, pk, action):
    """
    Validation ou refus d'une prolongation par le propriétaire (F17).
    action: 'accept' ou 'refuse'
    """
    loan = get_object_or_404(Loan, pk=pk)

    if request.user != loan.outil.proprietaire:
        return HttpResponseForbidden("Seul le propriétaire peut valider cette prolongation.")

    if request.method == "POST":
        accepter = (action == "accept")
        try:
            services.valider_prolongation(loan, request.user, accepter=accepter)
            if accepter:
                messages.success(request, "La prolongation a été acceptée.")
            else:
                messages.info(request, "La prolongation a été refusée.")
        except ValidationError as e:
            messages.error(request, str(e))

    return redirect("loans:loan_list")
