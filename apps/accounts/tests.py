import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.accounts.models import Profile

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
