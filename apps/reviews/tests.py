from datetime import date, timedelta
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.tools.models import Tool, Category
from apps.loans.models import Loan
from apps.reviews.models import Review

User = get_user_model()


@pytest.fixture
def users():
    alice = User.objects.create_user(username="alice", password="password123")
    bob = User.objects.create_user(username="bob", password="password123")
    charlie = User.objects.create_user(username="charlie", password="password123")
    return {"alice": alice, "bob": bob, "charlie": charlie}


@pytest.fixture
def category():
    return Category.objects.create(nom="Bricolage")


@pytest.fixture
def tool(users, category):
    return Tool.objects.create(
        proprietaire=users["alice"],
        categorie=category,
        titre="Ponceuse excentrique",
        disponible=True,
    )


@pytest.fixture
def returned_loan(users, tool):
    return Loan.objects.create(
        outil=tool,
        emprunteur=users["bob"],
        date_debut=date.today() - timedelta(days=5),
        date_fin_prevue=date.today() - timedelta(days=2),
        date_retour=date.today() - timedelta(days=2),
        statut="rendu",
    )


@pytest.mark.django_db
class TestReviews:
    def test_create_review_on_returned_loan_success(self, client, users, returned_loan):
        """Vérifie le dépôt d'un avis après retour (F8, R4)."""
        client.force_login(users["bob"])
        url = reverse("reviews:review_create", kwargs={"loan_id": returned_loan.pk})

        response = client.get(url)
        assert response.status_code == 200

        data = {
            "note": 5,
            "commentaire": "Super ponceuse, très propre et puissante !",
        }
        post_res = client.post(url, data=data, follow=True)
        assert post_res.status_code == 200
        assert Review.objects.filter(pret=returned_loan, auteur=users["bob"]).exists()
        rev = Review.objects.get(pret=returned_loan)
        assert rev.note == 5
        assert "Super" in rev.commentaire

    def test_cannot_review_non_returned_loan_security_403(self, client, users, tool):
        """Garde-fou #8 & R4 : Impossible de déposer un avis si statut != 'rendu' (403)."""
        active_loan = Loan.objects.create(
            outil=tool,
            emprunteur=users["bob"],
            date_debut=date.today(),
            date_fin_prevue=date.today() + timedelta(days=2),
            statut="en_cours",
        )
        client.force_login(users["bob"])
        url = reverse("reviews:review_create", kwargs={"loan_id": active_loan.pk})

        # Même par un GET ou POST direct vers l'URL
        res_get = client.get(url)
        assert res_get.status_code == 403

        res_post = client.post(url, {"note": 4, "commentaire": "test"})
        assert res_post.status_code == 403
        assert not Review.objects.filter(pret=active_loan).exists()

    def test_only_borrower_can_leave_review_security_403(self, client, users, returned_loan):
        """Un utilisateur tiers (Charlie) ne peut pas laisser d'avis (403)."""
        client.force_login(users["charlie"])
        url = reverse("reviews:review_create", kwargs={"loan_id": returned_loan.pk})

        res = client.post(url, {"note": 5, "commentaire": "Fake review"})
        assert res.status_code == 403
        assert not Review.objects.filter(pret=returned_loan).exists()

    def test_cannot_leave_duplicate_review(self, client, users, returned_loan):
        """R4 : Un seul avis possible par prêt (OneToOneField)."""
        Review.objects.create(
            pret=returned_loan,
            auteur=users["bob"],
            note=4,
            commentaire="Premier avis",
        )
        client.force_login(users["bob"])
        url = reverse("reviews:review_create", kwargs={"loan_id": returned_loan.pk})

        res = client.post(url, {"note": 5, "commentaire": "Deuxième avis"}, follow=True)
        assert res.status_code == 200
        assert Review.objects.filter(pret=returned_loan).count() == 1
