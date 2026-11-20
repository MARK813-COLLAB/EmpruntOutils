from django.core.management.base import BaseCommand
from apps.loans import services


class Command(BaseCommand):
    help = "Envoie des rappels par email aux emprunteurs dont la date de fin de prêt est dans moins de 2 jours (F19)."

    def handle(self, *args, **options):
        nb_rappels = services.envoyer_rappels_fin_pret()
        self.stdout.write(
            self.style.SUCCESS(f"{nb_rappels} rappel(s) de prêt envoyé(s).")
        )
