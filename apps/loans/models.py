from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.tools.models import Tool


class Loan(models.Model):
    STATUT_CHOICES = [
        ("demande", "Demandé"),
        ("accepte", "Accepté"),
        ("en_cours", "En cours"),
        ("rendu", "Rendu"),
        ("refuse", "Refusé"),
        ("en_retard", "En retard"),
    ]

    outil = models.ForeignKey(
        Tool,
        on_delete=models.CASCADE,
        related_name="prets",
        verbose_name="Outil prêté",
    )
    emprunteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emprunts",
        verbose_name="Emprunteur",
    )
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin_prevue = models.DateField(verbose_name="Date de fin prévue")
    date_retour = models.DateField(null=True, blank=True, verbose_name="Date effective de retour")
    nouvelle_date_fin_demandee = models.DateField(
        null=True,
        blank=True,
        verbose_name="Nouvelle date de fin demandée (prolongation)",
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="demande",
        verbose_name="Statut du prêt",
    )
    photo_avant = models.ImageField(
        upload_to="etat_des_lieux/",
        blank=True,
        null=True,
        verbose_name="Photo état des lieux avant prêt",
    )
    photo_apres = models.ImageField(
        upload_to="etat_des_lieux/",
        blank=True,
        null=True,
        verbose_name="Photo état des lieux au retour",
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de la demande")

    class Meta:
        verbose_name = "Prêt d'outil"
        verbose_name_plural = "Prêts d'outils"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Prêt de {self.outil.titre} à {self.emprunteur.username} ({self.get_statut_display()})"

    def est_en_retard(self) -> bool:
        """True si statut en_cours et date_fin_prevue < aujourd'hui."""
        if self.statut == "en_retard":
            return True
        if self.statut == "en_cours" and self.date_fin_prevue < timezone.now().date():
            return True
        return False
