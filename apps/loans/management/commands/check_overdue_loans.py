from django.core.management.base import BaseCommand
from apps.loans import services


class Command(BaseCommand):
    help = "Vérifie les prêts en cours dont la date de fin est dépassée et les marque comme 'en_retard' (R5)."

    def handle(self, *args, **options):
        nb_marques = services.verifier_prets_en_retard()
        self.stdout.write(
            self.style.SUCCESS(f"{nb_marques} prêt(s) marqué(s) comme en retard.")
        )
