# EmpruntOutils - Cahier des charges et conception UML

Plateforme de prêt d'outils entre étudiants - Django  
IUT - Génie logiciel (2026)

## 1. Contexte et objectif
Les étudiants possèdent des outils qu'ils utilisent rarement et d'autres en ont besoin ponctuellement.
L'application met en relation propriétaires et emprunteurs pour partager ces outils simplement et gratuitement.

## 2. Périmètre
- **Inclus :** gestion des comptes, des outils, des prêts et des avis, tableau de bord administrateur.
- **Exclu :** paiement en ligne, messagerie temps réel, application mobile.

## 3. Acteurs
- **Visiteur :** consulte le catalogue en lecture seule.
- **Étudiant :** propose et emprunte des outils, dépose des avis.
- **Administrateur :** modère et consulte les statistiques du tableau de bord.

## 4. Besoins fonctionnels
- **F1 :** Inscription, connexion, modification du profil (Haute)
- **F2 :** CRUD des outils (photo, catégorie, état) (Haute)
- **F3 :** Recherche et filtres (mot-clé, catégorie, disponibilité) (Haute)
- **F4 :** Demande d'emprunt avec dates (Haute)
- **F5 :** Acceptation ou refus par le propriétaire (Haute)
- **F6 :** Suivi du statut : demandé, accepté, en cours, rendu (ou refusé / en retard) (Haute)
- **F7 :** Historique des prêts (Haute)
- **F8 :** Avis et note (1 à 5) après retour (Haute)
- **F9 :** Notifications email aux changements de statut (Moyenne)
- **F10 :** Tableau de bord admin (outils les plus prêtés, utilisateurs actifs, retards) (Moyenne)
- **F11 :** Liste de favoris (Basse)
- **F12 :** Badges de réputation calculés dynamiquement (Basse)
- **F13 :** Statistiques personnelles (Basse)
- **F14 :** Calendrier de disponibilité d'un outil (Moyenne)
- **F15 :** Tags libres pour affiner la recherche (Basse)
- **F16 :** Signalement d'un outil endommagé au moment du retour (Moyenne)
- **F17 :** Demande de prolongation d'un prêt en cours (Moyenne)
- **F18 :** Checklist état des lieux avec photo avant / après (Moyenne)
- **F19 :** Rappel automatique par email avant date de fin prévue (Basse)

## 5. Règles de gestion
- **R1 :** Un étudiant ne peut pas emprunter son propre outil.
- **R2 :** Deux prêts ne peuvent pas se chevaucher dans le temps sur un même outil.
- **R3 :** Seul le propriétaire de l'outil valide ou refuse une demande.
- **R4 :** Un avis n'est possible qu'après le retour, une seule fois par prêt.
- **R5 :** Un prêt passe automatiquement en statut « en retard » si la date de fin prévue est dépassée.
- **R6 :** Une demande de prolongation ne doit pas créer de chevauchement avec un autre prêt accepté.
- **R7 :** Un outil signalé comme endommagé au retour passe en état « à réparer » et devient indisponible.

## 6. Architecture & Services
Toute la logique métier réside dans les services métier (`apps.loans.services`, `apps.tools.services`) afin de respecter le principe de séparation des responsabilités.
