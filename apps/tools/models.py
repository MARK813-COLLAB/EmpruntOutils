from django.db import models
from django.conf import settings
from django.urls import reverse


class Category(models.Model):
    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom de la catégorie")

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Tag(models.Model):
    nom = models.CharField(max_length=50, unique=True, verbose_name="Nom du tag")

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Tool(models.Model):
    ETAT_CHOICES = [
        ("neuf", "Neuf"),
        ("bon", "Bon état"),
        ("use", "Usagé"),
        ("a_reparer", "À réparer"),
    ]

    proprietaire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="outils",
        verbose_name="Propriétaire",
    )
    categorie = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="outils",
        verbose_name="Catégorie",
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="outils",
        verbose_name="Tags",
    )
    titre = models.CharField(max_length=150, verbose_name="Titre de l'outil")
    description = models.TextField(blank=True, verbose_name="Description détaillée")
    photo = models.ImageField(
        upload_to="outils/",
        blank=True,
        null=True,
        verbose_name="Photo de l'outil",
    )
    etat = models.CharField(
        max_length=20,
        choices=ETAT_CHOICES,
        default="bon",
        verbose_name="État de l'outil",
    )
    disponible = models.BooleanField(
        default=True,
        verbose_name="Disponible au prêt",
    )
    signale_endommage = models.BooleanField(
        default=False,
        verbose_name="Signalé endommagé",
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")

    class Meta:
        verbose_name = "Outil"
        verbose_name_plural = "Outils"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.titre} ({self.categorie.nom})"

    def get_absolute_url(self):
        return reverse("tools:tool_detail", kwargs={"pk": self.pk})

    def est_disponible(self, debut, fin) -> bool:
        """
        Vérifie si l'outil est disponible sur l'intervalle [debut, fin].
        Retourne False si disponible=False, si état=='a_reparer',
        ou si un prêt actif chevauche la période demandée.
        """
        if not self.disponible or self.etat == "a_reparer":
            return False

        try:
            from apps.loans.models import Loan
        except (ImportError, AttributeError):
            return True

        if not hasattr(Loan, "objects"):
            return True

        # Chevauchement avec un prêt actif (accepte, en_cours, en_retard)
        # R2 & R6
        chevauchement = Loan.objects.filter(
            outil=self,
            statut__in=["accepte", "en_cours", "en_retard"],
            date_debut__lte=fin,
            date_fin_prevue__gte=debut,
        ).exists()

        return not chevauchement


class Favori(models.Model):
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favoris",
        verbose_name="Utilisateur",
    )
    outil = models.ForeignKey(
        Tool,
        on_delete=models.CASCADE,
        related_name="favoris",
        verbose_name="Outil favori",
    )
    date_ajout = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")

    class Meta:
        verbose_name = "Favori"
        verbose_name_plural = "Favoris"
        unique_together = ("utilisateur", "outil")
        ordering = ["-date_ajout"]

    def __str__(self):
        return f"Favori: {self.utilisateur.username} - {self.outil.titre}"
