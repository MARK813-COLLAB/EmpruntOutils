from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from apps.loans.models import Loan
from .models import Review
from .forms import ReviewForm


@login_required
def review_create_view(request, loan_id):
    """
    Dépôt d'un avis après retour du prêt (F8, R4).
    Garde-fous stricts côté serveur :
    - Seul l'emprunteur peut déposer l'avis.
    - Le statut du prêt DOIT être 'rendu' (Garde-fou #8).
    - Un seul avis par prêt (OneToOneField / R4).
    """
    loan = get_object_or_404(Loan.objects.select_related("outil", "emprunteur"), pk=loan_id)

    # Vérification propriétaire/emprunteur
    if loan.emprunteur != request.user:
        return HttpResponseForbidden("Seul l'emprunteur peut déposer un avis pour ce prêt.")

    # Règle R4 & Garde-fou 8 : statut == 'rendu' obligatoire
    if loan.statut != "rendu":
        return HttpResponseForbidden("Un avis n'est possible qu'après la restitution complète de l'outil (R4).")

    # Règle R4 : une seule fois par prêt
    if hasattr(loan, "avis"):
        messages.warning(request, "Un avis a déjà été déposé pour ce prêt (R4).")
        return redirect("tools:tool_detail", pk=loan.outil.pk)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.pret = loan
            review.auteur = request.user
            review.save()
            messages.success(request, f"Votre avis sur « {loan.outil.titre} » a été publié avec succès.")
            return redirect("tools:tool_detail", pk=loan.outil.pk)
    else:
        form = ReviewForm()

    context = {
        "loan": loan,
        "form": form,
    }
    return render(request, "reviews/review_form.html", context)
