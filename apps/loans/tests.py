from datetime import date, timedelta
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.core.exceptions import ValidationError, PermissionDenied
from apps.tools.models import Tool, Category
from apps.loans.models import Loan
from apps.loans import services

User = get_user_model()


@pytest.fixture
def users():
    alice = User.objects.create_user(username="alice", email="alice@test.fr", password="password123")
    bob = User.objects.create_user(username="bob", email="bob@test.fr", password="password123")
    charlie = User.objects.create_user(username="charlie", email="charlie@test.fr", password="password123")
    return {"alice": alice, "bob": bob, "charlie": charlie}


@pytest.fixture
def category():
    return Category.objects.create(nom="Bricolage")


@pytest.fixture
def tool(users, category):
    return Tool.objects.create(
        proprietaire=users["alice"],
        categorie=category,
        titre="Perceuse sans fil",
        description="Outil de test",
        etat="bon",
        disponible=True,
    )


@pytest.mark.django_db
class TestLoanBusinessRules:
    def test_rule_r1_cannot_borrow_own_tool(self, users, tool):
        """R1 : Un étudiant ne peut pas emprunter son propre outil."""
        today = date.today()
        tomorrow = today + timedelta(days=1)
        with pytest.raises(ValidationError) as exc:
            services.creer_demande_pret(
                outil=tool,
                emprunteur=users["alice"],  # propriétaire
                date_debut=today,
                date_fin_prevue=tomorrow,
            )
        assert "R1" in str(exc.value)

    def test_rule_r2_overlapping_loans_rejected(self, users, tool):
        """R2 : Deux prêts ne peuvent pas se chevaucher sur un même outil."""
        d1 = date.today() + timedelta(days=5)
        d2 = date.today() + timedelta(days=10)

        # Création et acceptation du premier prêt
        loan1 = services.creer_demande_pret(tool, users["bob"], d1, d2)
        services.accepter_pret(loan1, users["alice"])
        assert loan1.statut == "accepte"

        # Demande 2 chevauchant [d1, d2]
        overlap_start = date.today() + timedelta(days=8)
        overlap_end = date.today() + timedelta(days=12)
        with pytest.raises(ValidationError) as exc:
            services.creer_demande_pret(tool, users["charlie"], overlap_start, overlap_end)
        assert "R2" in str(exc.value)

    def test_rule_r3_only_owner_can_accept_or_refuse(self, users, tool):
        """R3 : Seul le propriétaire peut accepter ou refuser une demande."""
        d1 = date.today() + timedelta(days=2)
        d2 = date.today() + timedelta(days=4)
        loan = services.creer_demande_pret(tool, users["bob"], d1, d2)

        # Charlie (tiers) tente d'accepter
        with pytest.raises(PermissionDenied):
            services.accepter_pret(loan, users["charlie"])

        # Charlie (tiers) tente de refuser
        with pytest.raises(PermissionDenied):
            services.refuser_pret(loan, users["charlie"])

        # Alice (propriétaire) accepte avec succès
        services.accepter_pret(loan, users["alice"])
        loan.refresh_from_db()
        assert loan.statut == "accepte"

    def test_rule_r7_and_f16_damaged_tool_becomes_unavailable(self, users, tool):
        """F16 & R7 : Signalement d'outil endommagé au retour."""
        d1 = date.today() + timedelta(days=1)
        d2 = date.today() + timedelta(days=3)
        loan = services.creer_demande_pret(tool, users["bob"], d1, d2)
        services.accepter_pret(loan, users["alice"])
        services.demarrer_pret(loan, users["alice"])

        # Marquer rendu avec dommage signalé
        services.marquer_rendu(loan, users["alice"], signale_endommage=True)
        loan.refresh_from_db()
        tool.refresh_from_db()

        assert loan.statut == "rendu"
        assert tool.signale_endommage is True
        assert tool.etat == "a_reparer"
        assert tool.disponible is False
        assert tool.est_disponible(d1, d2) is False

    def test_rule_r6_and_f17_prolongation_checks_overlap(self, users, tool):
        """F17 & R6 : Demande de prolongation avec vérification de non-chevauchement."""
        d1 = date.today()
        d2 = date.today() + timedelta(days=5)
        loan1 = services.creer_demande_pret(tool, users["bob"], d1, d2)
        services.accepter_pret(loan1, users["alice"])
        services.demarrer_pret(loan1, users["alice"])

        # Un autre prêt accepté plus tard [d+7, d+10]
        d3 = date.today() + timedelta(days=7)
        d4 = date.today() + timedelta(days=10)
        loan2 = services.creer_demande_pret(tool, users["charlie"], d3, d4)
        services.accepter_pret(loan2, users["alice"])

        # Bob demande une prolongation jusqu'à d+8 (qui chevauche d3)
        with pytest.raises(ValidationError) as exc:
            services.demander_prolongation(loan1, users["bob"], date.today() + timedelta(days=8))
        assert "R6" in str(exc.value)

        # Prolongation sans chevauchement jusqu'à d+6
        services.demander_prolongation(loan1, users["bob"], date.today() + timedelta(days=6))
        loan1.refresh_from_db()
        assert loan1.nouvelle_date_fin_demandee == date.today() + timedelta(days=6)

        # Validation par le propriétaire
        services.valider_prolongation(loan1, users["alice"], accepter=True)
        loan1.refresh_from_db()
        assert loan1.date_fin_prevue == date.today() + timedelta(days=6)
        assert loan1.nouvelle_date_fin_demandee is None


@pytest.mark.django_db
class TestLoanViewsAndWorkflow:
    def test_create_loan_view(self, client, users, tool):
        """Vue de demande d'emprunt (F4)."""
        client.force_login(users["bob"])
        url = reverse("loans:loan_create", kwargs={"tool_id": tool.pk})

        response = client.get(url)
        assert response.status_code == 200

        d1 = date.today() + timedelta(days=2)
        d2 = date.today() + timedelta(days=5)
        data = {
            "date_debut": d1.strftime("%Y-%m-%d"),
            "date_fin_prevue": d2.strftime("%Y-%m-%d"),
        }
        res_post = client.post(url, data=data, follow=True)
        assert res_post.status_code == 200
        assert Loan.objects.filter(emprunteur=users["bob"], outil=tool).exists()

    def test_accept_and_refuse_views_security_403(self, client, users, tool):
        """Vérifie le contrôle des droits serveur (403) pour acceptation/refus (F5, R3)."""
        d1 = date.today() + timedelta(days=2)
        d2 = date.today() + timedelta(days=5)
        loan = services.creer_demande_pret(tool, users["bob"], d1, d2)

        client.force_login(users["charlie"])
        accept_url = reverse("loans:loan_accept", kwargs={"pk": loan.pk})
        res = client.post(accept_url, {})
        assert res.status_code == 403

        refuse_url = reverse("loans:loan_refuse", kwargs={"pk": loan.pk})
        res = client.post(refuse_url, {})
        assert res.status_code == 403

    def test_loan_list_view_shows_loans(self, client, users, tool):
        """Historique des prêts affiché (F7)."""
        client.force_login(users["bob"])
        d1 = date.today() + timedelta(days=1)
        d2 = date.today() + timedelta(days=3)
        services.creer_demande_pret(tool, users["bob"], d1, d2)

        url = reverse("loans:loan_list")
        response = client.get(url)
        assert response.status_code == 200
        assert len(response.context["my_borrowed_loans"]) == 1


@pytest.mark.django_db
class TestLoanNotificationsAndCommands:
    def test_email_notifications_sent(self, users, tool):
        """Notifications email envoyées à chaque statut (F9)."""
        mail.outbox.clear()
        d1 = date.today() + timedelta(days=1)
        d2 = date.today() + timedelta(days=3)
        loan = services.creer_demande_pret(tool, users["bob"], d1, d2)

        # 1 email envoyé à Alice
        assert len(mail.outbox) == 1
        assert "Nouvelle demande" in mail.outbox[0].subject

        services.accepter_pret(loan, users["alice"])
        # 1 nouvel email envoyé à Bob
        assert len(mail.outbox) == 2
        assert "acceptée" in mail.outbox[1].subject

    def test_check_overdue_loans_command(self, users, tool):
        """Commande manage.py check_overdue_loans (R5)."""
        yesterday = date.today() - timedelta(days=1)
        past_start = yesterday - timedelta(days=3)

        loan = Loan.objects.create(
            outil=tool,
            emprunteur=users["bob"],
            date_debut=past_start,
            date_fin_prevue=yesterday,
            statut="en_cours",
        )
        assert loan.est_en_retard() is True

        call_command("check_overdue_loans")
        loan.refresh_from_db()
        assert loan.statut == "en_retard"

    def test_send_loan_reminders_command(self, users, tool):
        """Commande manage.py send_loan_reminders (F19)."""
        mail.outbox.clear()
        tomorrow = date.today() + timedelta(days=1)
        Loan.objects.create(
            outil=tool,
            emprunteur=users["bob"],
            date_debut=date.today(),
            date_fin_prevue=tomorrow,
            statut="en_cours",
        )
        call_command("send_loan_reminders")
        assert len(mail.outbox) >= 1
        assert "Rappel" in mail.outbox[0].subject
