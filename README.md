# EmpruntOutils

Plateforme web de prêt d'outils entre étudiants, développée avec Django 5 et Bootstrap 5.

## Fonctionnalités principales
- **Comptes étudiants :** Inscription, connexion, gestion du profil (téléphone, filière)
- **Catalogue & Outils :** CRUD des outils, catégories, tags, photos, favoris, recherche multicritère
- **Gestion des prêts :** Demandes de réservation avec calendrier, validation propriétaire, suivi des statuts (`demande`, `accepte`, `en_cours`, `rendu`, `refuse`, `en_retard`)
- **Règles métier :** Contrôle des chevauchements de dates avec transactions atomiques et verrouillage (`select_for_update`), interdiction d'emprunter ses propres outils
- **Avis & Notes :** Évaluation après retour d'un prêt (note de 1 à 5 et commentaire)
- **Fonctionnalités avancées :** Prolongation de prêt avec validation, état des lieux (photos avant / après), signalement d'outils endommagés, rappels automatiques et détection des retards
- **Statistiques & Badges :** Badges de réputation dynamiques, statistiques personnelles, tableau de bord administrateur

## Prérequis
- Python 3.11 ou 3.12
- Git

## Installation

1. **Cloner le dépôt :**
   ```bash
   git clone <url-du-repo>
   cd EmpruntOutils
   ```

2. **Créer et activer l'environnement virtuel :**
   ```bash
   python -m venv .venv
   # Sous Windows PowerShell :
   .\.venv\Scripts\Activate.ps1
   # Sous Linux / macOS :
   source .venv/bin/activate
   ```

3. **Installer les dépendances :**
   ```bash
   pip install -r requirements.txt
   ```

4. **Variables d'environnement :**
   Copiez `.env.example` en `.env` et adaptez les valeurs si nécessaire :
   ```bash
   cp .env.example .env
   ```

5. **Appliquer les migrations :**
   ```bash
   python manage.py migrate
   ```

6. **Créer un superutilisateur (administrateur) :**
   ```bash
   python manage.py createsuperuser
   ```

7. **Lancer le serveur de développement :**
   ```bash
   python manage.py runserver
   ```
   L'application est accessible à l'adresse [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

## Lancement des tests

Pour exécuter la suite complète de tests avec calcul de couverture :
```bash
pytest
```
ou via Django test runner :
```bash
python manage.py test
```

## Commandes personnalisées
- Marquer les prêts en retard :
  ```bash
  python manage.py check_overdue_loans
  ```
- Envoyer les rappels automatiques avant fin de prêt :
  ```bash
  python manage.py send_loan_reminders
  ```
