from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from apps.tools.models import Tool
from apps.loans.models import Loan

User = get_user_model()


@staff_member_required
def dashboard_index(request):
    """
    Tableau de bord administrateur (F10).
    Réservé au personnel (is_staff).
    Indicateurs :
    - Outils les plus prêtés
    - Utilisateurs les plus actifs
    - Prêts en retard
    - Statistiques globales
    """
    # 1. Statistiques globales
    total_users = User.objects.count()
    total_tools = Tool.objects.count()
    total_loans = Loan.objects.count()
    active_loans_count = Loan.objects.filter(statut__in=["accepte", "en_cours"]).count()
    overdue_loans_count = Loan.objects.filter(statut="en_retard").count()
    damaged_tools_count = Tool.objects.filter(Q(etat="a_reparer") | Q(signale_endommage=True)).count()

    # 2. Outils les plus prêtés (top 5)
    most_lent_tools = (
        Tool.objects.annotate(
            nb_prets=Count("prets", filter=Q(prets__statut__in=["accepte", "en_cours", "rendu", "en_retard"]))
        )
        .order_by("-nb_prets")[:5]
    )

    # 3. Utilisateurs les plus actifs (emprunts + prêts proposés)
    most_active_borrowers = (
        User.objects.annotate(
            nb_emprunts=Count("emprunts"),
            nb_outils=Count("outils"),
        )
        .order_by("-nb_emprunts")[:5]
    )

    # 4. Liste des prêts en retard actuels
    overdue_loans = Loan.objects.filter(statut="en_retard").select_related("outil", "emprunteur", "outil__proprietaire")

    context = {
        "total_users": total_users,
        "total_tools": total_tools,
        "total_loans": total_loans,
        "active_loans_count": active_loans_count,
        "overdue_loans_count": overdue_loans_count,
        "damaged_tools_count": damaged_tools_count,
        "most_lent_tools": most_lent_tools,
        "most_active_borrowers": most_active_borrowers,
        "overdue_loans": overdue_loans,
    }
    return render(request, "dashboard/index.html", context)
