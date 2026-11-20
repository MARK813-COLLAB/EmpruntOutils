from django.core.management.base import BaseCommand
from apps.tools.models import Category


class Command(BaseCommand):
    help = "Initialise les catégories d'outils par défaut."

    def handle(self, *args, **options):
        categories_defaut = [
            "Bricolage général",
            "Outillage électroportatif",
            "Jardinage & Extérieur",
            "Électronique & Soudure",
            "Mécanique auto / vélo",
            "Menuiserie & Travail du bois",
            "Peinture & Décoration",
            "Mesure, Niveau & Traçage",
            "Nettoyage & Gros travaux",
        ]

        creees = 0
        for nom in categories_defaut:
            obj, created = Category.objects.get_or_create(nom=nom)
            if created:
                creees += 1

        self.stdout.write(
            self.style.SUCCESS(f"{creees} catégorie(s) créée(s) avec succès (total : {Category.objects.count()}).")
        )
