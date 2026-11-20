import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.tools.models import Tool, Category, Tag, Favori

User = get_user_model()


@pytest.fixture
def users():
    alice = User.objects.create_user(username="alice", password="password123")
    bob = User.objects.create_user(username="bob", password="password123")
    return {"alice": alice, "bob": bob}


@pytest.fixture
def category():
    return Category.objects.create(nom="Bricolage")


@pytest.fixture
def tool(users, category):
    return Tool.objects.create(
        proprietaire=users["alice"],
        categorie=category,
        titre="Perceuse sans fil",
        description="Perceuse 18V avec deux batteries",
        etat="bon",
        disponible=True,
    )


@pytest.mark.django_db
class TestToolsCRUD:
    def test_create_tool_authenticated(self, client, users, category):
        """Vérifie qu'un utilisateur connecté peut créer un outil avec tags (F2, F15)."""
        client.force_login(users["alice"])
        url = reverse("tools:tool_create")
        
        response = client.get(url)
        assert response.status_code == 200

        data = {
            "titre": "Scie sauteuse",
            "categorie": category.pk,
            "description": "Scie sauteuse pendulaire",
            "etat": "bon",
            "disponible": True,
            "tags_text": "bricolage, bois, decoupe",
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        
        created = Tool.objects.get(titre="Scie sauteuse")
        assert created.proprietaire == users["alice"]
        assert created.tags.count() == 3
        assert set(created.tags.values_list("nom", flat=True)) == {"bricolage", "bois", "decoupe"}

    def test_update_tool_owner_allowed(self, client, users, tool):
        """Vérifie que le propriétaire peut modifier son outil (F2)."""
        client.force_login(users["alice"])
        url = reverse("tools:tool_update", kwargs={"pk": tool.pk})

        data = {
            "titre": "Perceuse à percussion",
            "categorie": tool.categorie.pk,
            "description": "Nouvelle description",
            "etat": "neuf",
            "disponible": True,
            "tags_text": "perceuse, beton",
        }
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200
        tool.refresh_from_db()
        assert tool.titre == "Perceuse à percussion"
        assert tool.etat == "neuf"

    def test_update_tool_non_owner_forbidden_403(self, client, users, tool):
        """Règle stricte : un utilisateur qui n'est pas le propriétaire reçoit une 403 (F2)."""
        client.force_login(users["bob"])
        url = reverse("tools:tool_update", kwargs={"pk": tool.pk})

        data = {
            "titre": "Piratage de titre",
            "categorie": tool.categorie.pk,
            "etat": "bon",
            "disponible": True,
        }
        response = client.post(url, data=data)
        assert response.status_code == 403
        tool.refresh_from_db()
        assert tool.titre == "Perceuse sans fil"

    def test_delete_tool_owner_allowed(self, client, users, tool):
        """Vérifie que le propriétaire peut supprimer son outil (F2)."""
        client.force_login(users["alice"])
        url = reverse("tools:tool_delete", kwargs={"pk": tool.pk})
        
        response = client.get(url)
        assert response.status_code == 200

        response = client.post(url, follow=True)
        assert response.status_code == 200
        assert not Tool.objects.filter(pk=tool.pk).exists()

    def test_delete_tool_non_owner_forbidden_403(self, client, users, tool):
        """Règle stricte : la suppression par un tiers retourne 403 (F2)."""
        client.force_login(users["bob"])
        url = reverse("tools:tool_delete", kwargs={"pk": tool.pk})

        response = client.post(url)
        assert response.status_code == 403
        assert Tool.objects.filter(pk=tool.pk).exists()


@pytest.mark.django_db
class TestToolsSearchAndFilters:
    def test_search_and_filters(self, client, users, category):
        """Vérifie la recherche par mot-clé, catégorie et disponibilité (F3, F15)."""
        cat_jardin = Category.objects.create(nom="Jardinage")
        tag_jardin = Tag.objects.create(nom="jardin")
        
        t1 = Tool.objects.create(
            proprietaire=users["alice"],
            categorie=category,
            titre="Marteau perforateur",
            description="Robuste",
            disponible=True,
        )
        t2 = Tool.objects.create(
            proprietaire=users["alice"],
            categorie=cat_jardin,
            titre="Tondeuse gazon",
            description="Essence",
            disponible=True,
        )
        t2.tags.add(tag_jardin)

        t3 = Tool.objects.create(
            proprietaire=users["alice"],
            categorie=cat_jardin,
            titre="Taille haie",
            disponible=False,
        )

        url = reverse("tools:tool_list")

        # Recherche par mot-clé
        res_q = client.get(url, {"q": "perforateur"})
        assert t1 in res_q.context["tools"]
        assert t2 not in res_q.context["tools"]

        # Filtre par catégorie
        res_cat = client.get(url, {"categorie": cat_jardin.pk})
        assert t1 not in res_cat.context["tools"]
        assert t2 in res_cat.context["tools"]
        assert t3 in res_cat.context["tools"]

        # Filtre par tag (F15)
        res_tag = client.get(url, {"tag": tag_jardin.pk})
        assert t2 in res_tag.context["tools"]
        assert t1 not in res_tag.context["tools"]

        # Filtre combiné disponible uniquement
        res_disp = client.get(url, {"categorie": cat_jardin.pk, "disponible_seulement": "on"})
        assert t2 in res_disp.context["tools"]
        assert t3 not in res_disp.context["tools"]


@pytest.mark.django_db
class TestToolsFavoris:
    def test_toggle_and_list_favoris(self, client, users, tool):
        """Vérifie l'ajout, le retrait et l'affichage des favoris (F11)."""
        client.force_login(users["bob"])
        toggle_url = reverse("tools:toggle_favori", kwargs={"pk": tool.pk})

        # Ajouter aux favoris
        res = client.get(toggle_url, follow=True)
        assert res.status_code == 200
        assert Favori.objects.filter(utilisateur=users["bob"], outil=tool).exists()

        # Lister les favoris
        list_url = reverse("tools:favoris_list")
        res_list = client.get(list_url)
        assert res_list.status_code == 200
        assert tool in [f.outil for f in res_list.context["favoris"]]

        # Retirer des favoris (toggle à nouveau)
        res_toggle_off = client.get(toggle_url, follow=True)
        assert res_toggle_off.status_code == 200
        assert not Favori.objects.filter(utilisateur=users["bob"], outil=tool).exists()


@pytest.mark.django_db
class TestToolAvailability:
    def test_est_disponible_basic(self, tool):
        from datetime import date
        today = date.today()
        assert tool.est_disponible(today, today) is True

        tool.disponible = False
        tool.save()
        assert tool.est_disponible(today, today) is False

        tool.disponible = True
        tool.etat = "a_reparer"
        tool.save()
        assert tool.est_disponible(today, today) is False
