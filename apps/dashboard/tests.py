from datetime import date, timedelta
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.tools.models import Tool, Category
from apps.loans.models import Loan

User = get_user_model()


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(username="admin", email="admin@iut.fr", password="password123")


@pytest.fixture
def student_user():
    return User.objects.create_user(username="student", email="student@iut.fr", password="password123")


@pytest.fixture
def sample_data(student_user):
    cat = Category.objects.create(nom="Bricolage")
    tool = Tool.objects.create(
        proprietaire=student_user,
        categorie=cat,
        titre="Perceuse visseuse",
        disponible=True,
    )
    # Prêt en retard
    Loan.objects.create(
        outil=tool,
        emprunteur=student_user,
        date_debut=date.today() - timedelta(days=5),
        date_fin_prevue=date.today() - timedelta(days=2),
        statut="en_retard",
    )
    return tool


@pytest.mark.django_db
class TestDashboard:
    def test_non_staff_cannot_access_dashboard(self, client, student_user):
        """Un utilisateur non-staff ne peut pas accéder au tableau de bord (F10)."""
        client.force_login(student_user)
        url = reverse("dashboard:index")
        response = client.get(url)
        # staff_member_required redirige vers le login admin
        assert response.status_code == 302
        assert "login" in response.url

    def test_staff_can_access_dashboard_with_statistics(self, client, admin_user, sample_data):
        """L'administrateur accède au tableau de bord avec les statistiques (F10)."""
        client.force_login(admin_user)
        url = reverse("dashboard:index")
        response = client.get(url)
        assert response.status_code == 200
        assert "total_users" in response.context
        assert "total_tools" in response.context
        assert "overdue_loans_count" in response.context
        assert response.context["overdue_loans_count"] >= 1
        assert len(response.context["most_lent_tools"]) >= 1
