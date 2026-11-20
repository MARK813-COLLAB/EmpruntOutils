"""
Services métier pour les prêts (loans) et profils utilisateurs.
Centralise toute la logique métier conformément à la spécification.
"""
from django.db.models import Count
from django.utils import timezone


def calculer_badges_utilisateur(user):
    """
    Calcule dynamiquement les badges de réputation de l'utilisateur (F12).
    Non stocké en base de données.
    Badges possibles :
    - 'Emprunteur fiable' : au moins 2 prêts retournés, 0 retard sur les 5 derniers prêts.
    - 'Top prêteur' : au moins 3 outils prêtés avec succès (statut rendu).
    """
    try:
        from apps.loans.models import Loan
    except (ImportError, AttributeError):
        return []

    if not hasattr(Loan, "objects"):
        return []

    badges = []

    # Emprunteur fiable
    past_borrowed = Loan.objects.filter(emprunteur=user, statut__in=["rendu", "en_retard"]).order_by("-date_retour", "-id")[:5]
    if past_borrowed.count() >= 2:
        had_delay = any(l.statut == "en_retard" or (l.date_retour and l.date_retour > l.date_fin_prevue) for l in past_borrowed)
        if not had_delay:
            badges.append({
                "code": "emprunteur_fiable",
                "label": "Emprunteur fiable",
                "icon": "bi-shield-check",
                "color": "success",
                "description": "Aucun retard sur les derniers prêts empruntés."
            })

    # Top prêteur
    tools_lent_count = Loan.objects.filter(outil__proprietaire=user, statut="rendu").count()
    if tools_lent_count >= 3:
        badges.append({
            "code": "top_preteur",
            "label": "Top prêteur",
            "icon": "bi-award",
            "color": "primary",
            "description": "Plus de 3 outils prêtés avec succès."
        })

    return badges


def get_user_statistics(user):
    """
    Statistiques personnelles pour la page de profil (F13).
    - Nombre de prêts (empruntés et prêtés)
    - Taux de ponctualité (% des prêts rendus à temps)
    - Outil le plus emprunté
    """
    default_stats = {
        "total_borrowed": 0,
        "completed_borrowed": 0,
        "total_lent": 0,
        "taux_ponctualite": 100.0,
        "most_borrowed_tool": "Aucun pour le moment",
    }
    try:
        from apps.loans.models import Loan
    except (ImportError, AttributeError):
        return default_stats

    if not hasattr(Loan, "objects"):
        return default_stats

    # Emprunts effectués par l'utilisateur
    borrowed_loans = Loan.objects.filter(emprunteur=user)
    total_borrowed = borrowed_loans.count()
    completed_borrowed = borrowed_loans.filter(statut="rendu")
    
    # Prêts des outils de l'utilisateur
    lent_loans = Loan.objects.filter(outil__proprietaire=user)
    total_lent = lent_loans.count()

    # Ponctualité
    on_time_count = 0
    total_returned = completed_borrowed.count()
    for loan in completed_borrowed:
        if loan.date_retour and loan.date_retour <= loan.date_fin_prevue:
            on_time_count += 1
        elif not loan.date_retour:
            on_time_count += 1

    taux_ponctualite = round((on_time_count / total_returned * 100), 1) if total_returned > 0 else 100.0

    # Outil le plus emprunté par l'utilisateur
    most_borrowed_stat = (
        borrowed_loans.values("outil__titre")
        .annotate(total=Count("id"))
        .order_by("-total")
        .first()
    )
    most_borrowed_tool = most_borrowed_stat["outil__titre"] if most_borrowed_stat else "Aucun pour le moment"

    return {
        "total_borrowed": total_borrowed,
        "completed_borrowed": total_returned,
        "total_lent": total_lent,
        "taux_ponctualite": taux_ponctualite,
        "most_borrowed_tool": most_borrowed_tool,
    }
