from datetime import date, timedelta
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.models import Profile
from apps.tools.models import Tool, Category
from apps.loans.models import Loan
from apps.loans.services import calculer_badges_utilisateur, get_user_statistics

User = get_user_model()


@pytest.mark.django_db
class TestAccounts:
    def test_profile_created_automatically_on_user_creation(self):
        """Vérifie que le signal post_save crée automatiquement le profil utilisateur."""
        user = User.objects.create_user(username="alice", password="password123")
        assert hasattr(user, "profile")
        assert isinstance(user.profile, Profile)
        assert str(user.profile) == f"Profil de {user.username}"

    def test_user_registration_view(self, client):
        """Vérifie le formulaire d'inscription et la redirection."""
        url = reverse("accounts:register")
        response = client.get(url)
        assert response.status_code == 200

        data = {
            "username": "bob",
            "email": "bob@etu.univ.fr",
            "telephone": "0601020304",
            "filiere": "BUT Informatique",
            "password": "ComplexPassword123!",
            "password1": "ComplexPassword123!",
            "password2": "ComplexPassword123!",
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        assert User.objects.filter(username="bob").exists()
        bob = User.objects.get(username="bob")
        assert bob.profile.telephone == "0601020304"
        assert bob.profile.filiere == "BUT Informatique"

    def test_user_login_and_logout(self, client):
        """Vérifie la connexion et la déconnexion."""
        user = User.objects.create_user(username="charlie", password="password123")
        login_url = reverse("accounts:login")
        
        # Test login
        response = client.post(login_url, {"username": "charlie", "password": "password123"}, follow=True)
        assert response.status_code == 200
        assert "_auth_user_id" in client.session

        # Test logout (Django 5 requiert POST pour la déconnexion par défaut)
        logout_url = reverse("accounts:logout")
        response = client.post(logout_url, follow=True)
        assert response.status_code == 200
        assert "_auth_user_id" not in client.session

    def test_profile_update_view_authenticated(self, client):
        """Vérifie la modification des informations de profil."""
        user = User.objects.create_user(username="david", email="david@old.com", password="password123")
        client.force_login(user)

        profile_url = reverse("accounts:profile")
        response = client.get(profile_url)
        assert response.status_code == 200

        # Update profile
        data = {
            "username": "david",
            "email": "david@new.com",
            "first_name": "David",
            "last_name": "Dupont",
            "telephone": "0799887766",
            "filiere": "GEII",
        }
        response = client.post(profile_url, data=data, follow=True)
        assert response.status_code == 200

        user.refresh_from_db()
        assert user.email == "david@new.com"
        assert user.profile.telephone == "0799887766"
        assert user.profile.filiere == "GEII"

    def test_profile_view_unauthenticated_redirects(self, client):
        """Vérifie que l'accès au profil sans être connecté redirige vers la page de login."""
        profile_url = reverse("accounts:profile")
        response = client.get(profile_url)
        assert response.status_code == 302
        assert reverse("accounts:login") in response.url

    def test_reputation_badges_and_personal_statistics(self, client):
        """Vérifie le calcul dynamique des badges (F12) et statistiques personnelles (F13)."""
        emma = User.objects.create_user(username="emma", password="password123")
        lucas = User.objects.create_user(username="lucas", password="password123")
        cat = Category.objects.create(nom="Outillage")
        tool1 = Tool.objects.create(proprietaire=lucas, categorie=cat, titre="Perceuse")
        tool2 = Tool.objects.create(proprietaire=lucas, categorie=cat, titre="Ponceuse")
        tool3 = Tool.objects.create(proprietaire=lucas, categorie=cat, titre="Scie")

        # Emma emprunte 2 fois sans retard
        Loan.objects.create(
            outil=tool1,
            emprunteur=emma,
            date_debut=date.today() - timedelta(days=10),
            date_fin_prevue=date.today() - timedelta(days=5),
            date_retour=date.today() - timedelta(days=5),
            statut="rendu",
        )
        Loan.objects.create(
            outil=tool1,
            emprunteur=emma,
            date_debut=date.today() - timedelta(days=4),
            date_fin_prevue=date.today() - timedelta(days=2),
            date_retour=date.today() - timedelta(days=2),
            statut="rendu",
        )

        # Lucas prête 3 outils avec succès
        Loan.objects.create(
            outil=tool2,
            emprunteur=emma,
            date_debut=date.today() - timedelta(days=3),
            date_fin_prevue=date.today() - timedelta(days=1),
            date_retour=date.today() - timedelta(days=1),
            statut="rendu",
        )

        # Badges d'Emma : Emprunteur fiable
        badges_emma = calculer_badges_utilisateur(emma)
        codes_emma = [b["code"] for b in badges_emma]
        assert "emprunteur_fiable" in codes_emma

        # Badges de Lucas : Top prêteur
        badges_lucas = calculer_badges_utilisateur(lucas)
        codes_lucas = [b["code"] for b in badges_lucas]
        assert "top_preteur" in codes_lucas

        # Statistiques d'Emma
        stats = get_user_statistics(emma)
        assert stats["total_borrowed"] == 3
        assert stats["completed_borrowed"] == 3
        assert stats["taux_ponctualite"] == 100.0
        assert stats["most_borrowed_tool"] == "Perceuse"
