"""
Services métier pour les prêts (loans), profils et outils.
Centralise toute la logique métier conformément à la spécification.
"""
from datetime import date
from django.db import transaction
from django.db.models import Count, Q
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone


def notifier_changement_statut(loan, action, destinataire, message_extra=""):
    """
    Envoie une notification par email lors d'un changement de statut (F9).
    """
    sujets = {
        "demande": f"[EmpruntOutils] Nouvelle demande d'emprunt pour votre outil « {loan.outil.titre} »",
        "accepte": f"[EmpruntOutils] Votre demande d'emprunt pour « {loan.outil.titre} » a été acceptée !",
        "refuse": f"[EmpruntOutils] Votre demande d'emprunt pour « {loan.outil.titre} » a été refusée",
        "en_cours": f"[EmpruntOutils] Le prêt de l'outil « {loan.outil.titre} » a démarré",
        "rendu": f"[EmpruntOutils] L'outil « {loan.outil.titre} » a été marqué comme rendu",
        "en_retard": f"[EmpruntOutils] Prêt en retard pour l'outil « {loan.outil.titre} »",
        "prolongation_demandee": f"[EmpruntOutils] Demande de prolongation pour « {loan.outil.titre} »",
        "prolongation_reponse": f"[EmpruntOutils] Réponse pour la prolongation de « {loan.outil.titre} »",
        "rappel_fin": f"[EmpruntOutils] Rappel : fin de prêt proche pour « {loan.outil.titre} »",
    }
    sujet = sujets.get(action, f"[EmpruntOutils] Mise à jour du prêt « {loan.outil.titre} »")
    
    corps = f"Bonjour {destinataire.username},\n\n"
    if action == "demande":
        corps += f"{loan.emprunteur.username} a demandé à emprunter votre outil « {loan.outil.titre} » du {loan.date_debut.strftime('%d/%m/%Y')} au {loan.date_fin_prevue.strftime('%d/%m/%Y')}.\n"
        corps += "Connectez-vous sur EmpruntOutils pour accepter ou refuser cette demande.\n"
    elif action == "accepte":
        corps += f"Bonne nouvelle ! Le propriétaire {loan.outil.proprietaire.username} a accepté votre demande d'emprunt pour « {loan.outil.titre} » du {loan.date_debut.strftime('%d/%m/%Y')} au {loan.date_fin_prevue.strftime('%d/%m/%Y')}.\n"
    elif action == "refuse":
        corps += f"Votre demande d'emprunt pour l'outil « {loan.outil.titre} » a malheureusement été refusée par son propriétaire.\n"
    elif action == "en_cours":
        corps += f"Le prêt de l'outil « {loan.outil.titre} » est désormais en cours jusqu'au {loan.date_fin_prevue.strftime('%d/%m/%Y')}.\n"
    elif action == "rendu":
        corps += f"Le prêt de l'outil « {loan.outil.titre} » est terminé et a été marqué comme rendu le {timezone.now().strftime('%d/%m/%Y')}.\n"
        if loan.emprunteur == destinataire:
            corps += "N'hésitez pas à laisser un avis et une note sur la plateforme !\n"
    elif action == "en_retard":
        corps += f"Attention : la date de fin prévue ({loan.date_fin_prevue.strftime('%d/%m/%Y')}) pour l'outil « {loan.outil.titre} » est dépassée.\n"
        corps += "Merci de convenir du retour au plus vite.\n"
    elif action == "prolongation_demandee":
        corps += f"{loan.emprunteur.username} a demandé une prolongation jusqu'au {loan.nouvelle_date_fin_demandee.strftime('%d/%m/%Y')} pour « {loan.outil.titre} ».\n"
    elif action == "prolongation_reponse":
        corps += f"La réponse pour votre demande de prolongation sur « {loan.outil.titre} » est : {message_extra}.\n"
    elif action == "rappel_fin":
        corps += f"Rappel : la date de fin de votre prêt pour « {loan.outil.titre} » est prévue le {loan.date_fin_prevue.strftime('%d/%m/%Y')}.\n"

    corps += f"\n---\nL'équipe EmpruntOutils\n"

    try:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@empruntoutils.fr")
        if destinataire.email:
            send_mail(sujet, corps, from_email, [destinataire.email], fail_silently=True)
    except Exception:
        pass


def creer_demande_pret(outil, emprunteur, date_debut, date_fin_prevue):
    """
    Crée une nouvelle demande de prêt (F4).
    Règles de gestion vérifiées :
    - R1 : Un étudiant ne peut pas emprunter son propre outil.
    - Dates : date_debut <= date_fin_prevue et date_debut >= aujourd'hui.
    - R2 : Pas de chevauchement sur cet outil avec un prêt actif.
    Verrouillage strict avec select_for_update() dans une transaction atomique.
    """
    from apps.tools.models import Tool
    from apps.loans.models import Loan

    # Règle R1
    if emprunteur == outil.proprietaire:
        raise ValidationError("Vous ne pouvez pas emprunter votre propre outil (R1).")

    # Validation chronologique
    today = timezone.now().date()
    if date_debut < today:
        raise ValidationError("La date de début ne peut pas être dans le passé.")
    if date_fin_prevue < date_debut:
        raise ValidationError("La date de fin prévue doit être postérieure ou égale à la date de début.")

    # Règle R2 avec verrouillage transactionnel
    with transaction.atomic():
        # Verrouillage pessimiste sur la ligne de l'outil pour éviter toute race condition
        outil_locked = Tool.objects.select_for_update().get(pk=outil.pk)

        if not outil_locked.disponible or outil_locked.etat == "a_reparer":
            raise ValidationError("Cet outil n'est pas disponible actuellement au prêt.")

        # Vérification chevauchement avec prêts actifs
        chevauchement = Loan.objects.filter(
            outil=outil_locked,
            statut__in=["accepte", "en_cours", "en_retard"],
            date_debut__lte=date_fin_prevue,
            date_fin_prevue__gte=date_debut,
        ).exists()

        if chevauchement:
            raise ValidationError("Cet outil est déjà réservé sur cette période (R2).")

        loan = Loan.objects.create(
            outil=outil_locked,
            emprunteur=emprunteur,
            date_debut=date_debut,
            date_fin_prevue=date_fin_prevue,
            statut="demande",
        )

    # Notification F9
    notifier_changement_statut(loan, "demande", outil.proprietaire)
    return loan


def accepter_pret(loan, user, photo_avant=None):
    """
    Accepte une demande de prêt (F5, R3).
    Seul le propriétaire de l'outil peut accepter.
    Possibilité d'enregistrer la photo de l'état des lieux avant prêt (F18).
    """
    from apps.tools.models import Tool
    from apps.loans.models import Loan

    if user != loan.outil.proprietaire:
        raise PermissionDenied("Seul le propriétaire de l'outil peut accepter la demande (R3).")

    if loan.statut != "demande":
        raise ValidationError("Cette demande ne peut plus être acceptée.")

    with transaction.atomic():
        # Verrouillage pour s'assurer qu'aucun autre prêt n'a été accepté entre-temps
        Tool.objects.select_for_update().get(pk=loan.outil.pk)

        conflit = Loan.objects.filter(
            outil=loan.outil,
            statut__in=["accepte", "en_cours", "en_retard"],
            date_debut__lte=loan.date_fin_prevue,
            date_fin_prevue__gte=loan.date_debut,
        ).exclude(pk=loan.pk).exists()

        if conflit:
            raise ValidationError("Un autre prêt chevauche désormais cette période.")

        loan.statut = "accepte"
        if photo_avant:
            loan.photo_avant = photo_avant
        loan.save()

    notifier_changement_statut(loan, "accepte", loan.emprunteur)
    return loan


def refuser_pret(loan, user):
    """
    Refuse une demande de prêt (F5, R3).
    Seul le propriétaire de l'outil peut refuser.
    """
    if user != loan.outil.proprietaire:
        raise PermissionDenied("Seul le propriétaire de l'outil peut refuser la demande (R3).")

    if loan.statut != "demande":
        raise ValidationError("Cette demande ne peut plus être refusée.")

    loan.statut = "refuse"
    loan.save()

    notifier_changement_statut(loan, "refuse", loan.emprunteur)
    return loan


def demarrer_pret(loan, user):
    """
    Fait passer le prêt au statut 'en_cours' (F6).
    """
    if user not in (loan.outil.proprietaire, loan.emprunteur):
        raise PermissionDenied("Vous n'êtes pas autorisé à modifier ce prêt.")

    if loan.statut != "accepte":
        raise ValidationError("Le prêt doit être au statut 'accepté' pour démarrer.")

    loan.statut = "en_cours"
    loan.save()

    notifier_changement_statut(loan, "en_cours", loan.emprunteur if user == loan.outil.proprietaire else loan.outil.proprietaire)
    return loan


def marquer_rendu(loan, user, photo_apres=None, signale_endommage=False):
    """
    Marque le prêt comme rendu (F6, F16, R7, F18).
    Si un dommage est signalé :
    - loan.outil.signale_endommage = True
    - loan.outil.etat = 'a_reparer'
    - loan.outil.disponible = False
    """
    if user not in (loan.outil.proprietaire, loan.emprunteur):
        raise PermissionDenied("Vous n'êtes pas autorisé à marquer ce prêt comme rendu.")

    if loan.statut not in ["en_cours", "en_retard", "accepte"]:
        raise ValidationError("Ce prêt ne peut pas être marqué comme rendu dans son état actuel.")

    with transaction.atomic():
        loan.statut = "rendu"
        loan.date_retour = timezone.now().date()
        if photo_apres:
            loan.photo_apres = photo_apres
        loan.save()

        # Règle R7 & F16 : outil endommagé au retour
        if signale_endommage:
            outil = loan.outil
            outil.signale_endommage = True
            outil.etat = "a_reparer"
            outil.disponible = False
            outil.save()

    destinataire = loan.emprunteur if user == loan.outil.proprietaire else loan.outil.proprietaire
    notifier_changement_statut(loan, "rendu", destinataire)
    return loan


def demander_prolongation(loan, user, nouvelle_date_fin):
    """
    Demande de prolongation d'un prêt en cours (F17, R6).
    Soumise à validation du propriétaire.
    """
    from apps.loans.models import Loan
    from apps.tools.models import Tool

    if user != loan.emprunteur:
        raise PermissionDenied("Seul l'emprunteur peut demander une prolongation.")

    if loan.statut not in ["en_cours", "en_retard"]:
        raise ValidationError("Seul un prêt en cours peut être prolongé.")

    if nouvelle_date_fin <= loan.date_fin_prevue:
        raise ValidationError("La nouvelle date de fin doit être postérieure à la date de fin prévue actuelle.")

    with transaction.atomic():
        Tool.objects.select_for_update().get(pk=loan.outil.pk)

        # R6 : vérification qu'aucun autre prêt actif ne chevauche l'extension
        chevauchement = Loan.objects.filter(
            outil=loan.outil,
            statut__in=["accepte", "en_cours", "en_retard"],
            date_debut__lte=nouvelle_date_fin,
            date_fin_prevue__gt=loan.date_fin_prevue,
        ).exclude(pk=loan.pk).exists()

        if chevauchement:
            raise ValidationError("L'outil est déjà réservé par un autre étudiant sur cette période de prolongation (R6).")

        loan.nouvelle_date_fin_demandee = nouvelle_date_fin
        loan.save()

    notifier_changement_statut(loan, "prolongation_demandee", loan.outil.proprietaire)
    return loan


def valider_prolongation(loan, user, accepter=True):
    """
    Validation ou refus d'une prolongation par le propriétaire (F17).
    """
    from apps.loans.models import Loan
    from apps.tools.models import Tool

    if user != loan.outil.proprietaire:
        raise PermissionDenied("Seul le propriétaire peut valider une prolongation.")

    if not loan.nouvelle_date_fin_demandee:
        raise ValidationError("Aucune prolongation n'est en attente pour ce prêt.")

    with transaction.atomic():
        if accepter:
            Tool.objects.select_for_update().get(pk=loan.outil.pk)
            # Vérifier à nouveau la règle R6
            conflit = Loan.objects.filter(
                outil=loan.outil,
                statut__in=["accepte", "en_cours", "en_retard"],
                date_debut__lte=loan.nouvelle_date_fin_demandee,
                date_fin_prevue__gt=loan.date_fin_prevue,
            ).exclude(pk=loan.pk).exists()

            if conflit:
                raise ValidationError("Impossible d'accepter : un autre prêt chevauche désormais cette période.")

            loan.date_fin_prevue = loan.nouvelle_date_fin_demandee
            if loan.statut == "en_retard" and loan.date_fin_prevue >= timezone.now().date():
                loan.statut = "en_cours"
            loan.nouvelle_date_fin_demandee = None
            loan.save()
            msg = "Acceptée"
        else:
            loan.nouvelle_date_fin_demandee = None
            loan.save()
            msg = "Refusée"

    notifier_changement_statut(loan, "prolongation_reponse", loan.emprunteur, message_extra=msg)
    return loan


def verifier_prets_en_retard():
    """
    Passe automatiquement les prêts en statut 'en_retard' si date_fin_prevue < aujourd'hui (R5).
    Appelée par la commande manage.py check_overdue_loans.
    """
    from apps.loans.models import Loan

    today = timezone.now().date()
    overdue_loans = Loan.objects.filter(
        statut="en_cours",
        date_fin_prevue__lt=today,
    )

    count = 0
    for loan in overdue_loans:
        loan.statut = "en_retard"
        loan.save()
        notifier_changement_statut(loan, "en_retard", loan.emprunteur)
        notifier_changement_statut(loan, "en_retard", loan.outil.proprietaire)
        count += 1

    return count


def envoyer_rappels_fin_pret():
    """
    Envoie un email de rappel aux emprunteurs dont le prêt se termine dans moins de 2 jours (F19).
    Appelée par la commande manage.py send_loan_reminders.
    """
    from apps.loans.models import Loan

    today = timezone.now().date()
    in_two_days = today + timezone.timedelta(days=2)

    loans = Loan.objects.filter(
        statut="en_cours",
        date_fin_prevue__gte=today,
        date_fin_prevue__lte=in_two_days,
    )

    count = 0
    for loan in loans:
        notifier_changement_statut(loan, "rappel_fin", loan.emprunteur)
        count += 1

    return count


def calculer_badges_utilisateur(user):
    """
    Calcule dynamiquement les badges de réputation de l'utilisateur (F12).
    Non stocké en base de données.
    Badges possibles :
    - 'Emprunteur fiable' : au moins 2 prêts retournés, 0 retard sur les 5 derniers prêts.
    - 'Top prêteur' : au moins 3 outils prêtés avec succès (statut rendu).
    """
    from apps.loans.models import Loan

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
    from apps.loans.models import Loan

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
