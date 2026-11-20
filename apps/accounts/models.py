from django.db import models
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Utilisateur",
    )
    telephone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Numéro de téléphone",
    )
    filiere = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Filière d'études",
    )

    class Meta:
        verbose_name = "Profil étudiant"
        verbose_name_plural = "Profils étudiants"

    def __str__(self):
        return f"Profil de {self.user.username}"

    @property
    def badge(self):
        """
        Calcul dynamique des badges de réputation (F12).
        Non stocké en base de données.
        """
        from apps.loans.services import calculer_badges_utilisateur
        return calculer_badges_utilisateur(self.user)
