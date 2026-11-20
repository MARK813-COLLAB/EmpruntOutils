from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.loans.models import Loan


class Review(models.Model):
    pret = models.OneToOneField(
        Loan,
        on_delete=models.CASCADE,
        related_name="avis",
        verbose_name="Prêt concerné",
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="avis_laisses",
        verbose_name="Auteur de l'avis",
    )
    note = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Note sur 5",
        help_text="Attribuez une note de 1 (très décevant) à 5 (excellent)",
    )
    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire d'évaluation",
    )
    date = models.DateTimeField(auto_now_add=True, verbose_name="Date de publication")

    class Meta:
        verbose_name = "Avis sur le prêt"
        verbose_name_plural = "Avis sur les prêts"
        ordering = ["-date"]

    def __str__(self):
        return f"Avis {self.note}/5 par {self.auteur.username} sur {self.pret.outil.titre}"
