# jira_backlog.py — Backlog complet projet nutrition-manager (backend)
# Généré automatiquement par generate_backlog.py — NE PAS MODIFIER MANUELLEMENT
# Source  : rules.json v1.0
# Date    : 2026-05-25
# Moteur  : python3 playbook/tools/import_jira.py docs/pages/backend/livrable/jira_backlog.py

MODULE = "backend"
MODE   = "create"

EXISTING_EPICS = {}

# ── Epics ──────────────────────────────────────────────────────────────────────

EPICS = [
    ("EPIC-001", "Domain Layer", "Modélisation complète du domaine métier : Aggregate Roots, entités enfants, Value Objects et invariants.", "domain"),
    ("EPIC-002", "Application Layer", "Services applicatifs, orchestration des use cases, DTOs et contrôle des règles d'abonnement.", "application"),
    ("EPIC-003", "Infrastructure Layer", "Persistance EF Core, repositories, cache Redis, jobs Hangfire et migrations.", "infrastructure"),
    ("EPIC-004", "API Layer", "Controllers, middleware, sécurité JWT, autorisation par rôle et documentation OpenAPI.", "api"),
    ("EPIC-005", "Tests", "Tests unitaires du domaine, tests d'intégration de l'infrastructure et tests end-to-end de l'API.", "tests"),
]

# ── Stories ────────────────────────────────────────────────────────────────────

STORIES = [
    ("STORY-001", "Aggregate Roots du domaine",
     """Contexte : Implémenter les cinq Aggregate Roots avec leurs constructeurs, encapsulation et invariants intra-agrégat.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "domain", 3, "EPIC-001"),
    ("STORY-002", "Entités enfants et Value Objects",
     """Contexte : Implémenter les entités enfants et les Value Objects du domaine avec leurs invariants.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "domain", 3, "EPIC-001"),
    ("STORY-003", "Gestion du profil utilisateur",
     """Contexte : Orchestration des use cases de création, mise à jour du profil et suivi du poids.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "application", 3, "EPIC-002"),
    ("STORY-004", "Gestion des plans diététiques",
     """Contexte : CRUD des plans personnels et gestion des templates partagés avec contrôle des limites d'abonnement.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "application", 3, "EPIC-002"),
    ("STORY-005", "Cycle de vie d'un régime (Diet)",
     """Contexte : Orchestration du lancement d'un plan, du calcul nutritionnel et de la clôture d'un régime.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "application", 3, "EPIC-002"),
    ("STORY-006", "Gestion des repas",
     """Contexte : Création de repas avec calcul nutritionnel en temps réel et contrôle des limites d'abonnement.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "application", 3, "EPIC-002"),
    ("STORY-007", "Gestion des aliments",
     """Contexte : Recherche d'aliments et gestion des favoris personnels avec contrôle des limites d'abonnement.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "application", 3, "EPIC-002"),
    ("STORY-008", "Bilan nutritionnel",
     """Contexte : Calcul et agrégation du bilan nutritionnel d'une période de régime.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "application", 2, "EPIC-002"),
    ("STORY-009", "Contrôle des limites d'abonnement (SubscriptionGuard)",
     """Contexte : Mécanisme centralisé de vérification des limites selon le tier d'abonnement de l'utilisateur.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "Medium", "application", 2, "EPIC-002"),
    ("STORY-010", "Administration et supervision",
     """Contexte : Services applicatifs pour l'agrégation des KPIs utilisateurs et la supervision du système.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "Medium", "application", 3, "EPIC-002"),
    ("STORY-011", "Persistance EF Core et migrations",
     """Contexte : Configurations Fluent API, migration initiale et seed des données de départ.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "infrastructure", 3, "EPIC-003"),
    ("STORY-012", "Repositories",
     """Contexte : Implémentation de l'accès aux données pour toutes les entités via le pattern Repository.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "infrastructure", 2, "EPIC-003"),
    ("STORY-013", "Cache Redis pour les aliments",
     """Contexte : Mise en cache des résultats de recherche d'aliments pour réduire la charge sur PostgreSQL.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "infrastructure", 2, "EPIC-003"),
    ("STORY-014", "Job d'import Open Food Facts (Hangfire)",
     """Contexte : Import quotidien automatisé du dump OFF pour maintenir la base d'aliments à jour.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "infrastructure", 2, "EPIC-003"),
    ("STORY-015", "Job de purge RGPD (Hangfire)",
     """Contexte : Suppression automatisée des comptes marqués pour suppression après la grace period de 30 jours.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "infrastructure", 2, "EPIC-003"),
    ("STORY-016", "Infrastructure API (middleware et OpenAPI)",
     """Contexte : Mise en place des couches transversales : authentification JWT, gestion des erreurs, logging et documentation API.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "api", 3, "EPIC-004"),
    ("STORY-017", "UsersController — profil, pesées et RGPD",
     """Contexte : Endpoints de gestion du profil utilisateur, historique de poids, aliments favoris et droits RGPD.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "api", 3, "EPIC-004"),
    ("STORY-018", "DietPlansController — plans et templates",
     """Contexte : Endpoints de gestion des plans diététiques personnels et des templates partagés.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "api", 3, "EPIC-004"),
    ("STORY-019", "DietsController — régimes et bilan",
     """Contexte : Endpoints de consultation des régimes et du bilan nutritionnel.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "api", 3, "EPIC-004"),
    ("STORY-020", "MealsController et FoodItemsController",
     """Contexte : Endpoints de gestion des repas et de recherche d'aliments.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "api", 3, "EPIC-004"),
    ("STORY-021", "AdminController — back-office",
     """Contexte : Endpoints d'administration réservés au rôle admin pour la supervision et la gestion des templates.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "Medium", "api", 3, "EPIC-004"),
    ("STORY-022", "Tests unitaires — Domain Layer",
     """Contexte : Vérifier les invariants et règles métier du domaine en isolation totale.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "tests", 2, "EPIC-005"),
    ("STORY-023", "Tests d'intégration — Infrastructure Layer",
     """Contexte : Vérifier la persistance, le cache et les jobs sur des services réels via Testcontainers.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "tests", 3, "EPIC-005"),
    ("STORY-024", "Tests API — couverture end-to-end",
     """Contexte : Vérifier le comportement de tous les endpoints sur des cas nominaux et des cas d'erreur.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "tests", 2, "EPIC-005"),
]

# ── Sub-tasks ──────────────────────────────────────────────────────────────────

SUBTASKS = [
    ("SUB-001", "Implémenter User et DietPlan",
     """Objectif : Implémenter User et DietPlan
Règles métier : User : profil biométrique complet (âge, poids, taille, genre, niveau d'activité, objectif), tier d'abonnement (SubscriptionTier, Free par défaut). DietPlan : moule réutilisable sans dates ni CalorieTarget, IsTemplate (false par défaut), UserId nullable (null si template partagé).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "domain", "STORY-001"),
    ("SUB-002", "Implémenter Diet",
     """Objectif : Implémenter Diet
Règles métier : Diet représente un régime actif. StartDate imposée par le système au lancement (= date du jour). Non modifiable une fois lancée (sauf EndDate). Invariant : une seule Diet en statut Active par User — toute tentative de lancement quand une Diet est déjà active lève une erreur métier (409).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "domain", "STORY-001"),
    ("SUB-003", "Implémenter Meal et FoodItem",
     """Objectif : Implémenter Meal et FoodItem
Règles métier : Meal : repas d'un utilisateur, peut être sauvegardé (IsSaved). Invariant intra-agrégat : doit contenir au moins un MealItem. FoodItem : aliment issu du dump Open Food Facts, source des données nutritionnelles.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "domain", "STORY-001"),
    ("SUB-004", "Implémenter WeightEntry, MealItem et SavedFoodItem",
     """Objectif : Implémenter WeightEntry, MealItem et SavedFoodItem
Règles métier : WeightEntry : pesée d'un User (poids, date mesurée). MealItem : item d'un Meal avec quantité, porte la NutritionInfo calculée au moment de la création. SavedFoodItem : lien entre un User et un FoodItem. Invariant : un même FoodItemId ne peut être sauvegardé qu'une fois par User.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "domain", "STORY-002"),
    ("SUB-005", "Implémenter MacroDistribution et NutritionInfo",
     """Objectif : Implémenter MacroDistribution et NutritionInfo
Règles métier : MacroDistribution : répartition des macronutriments en pourcentages. Invariant : CarbsPercent + ProteinsPercent + FatsPercent = 100%. NutritionInfo : snapshot immuable des valeurs nutritionnelles (Calories, Proteins, Carbs, Fats) capturé au moment de la création d'un MealItem.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "domain", "STORY-002"),
    ("SUB-006", "Implémenter NutritionNeeds",
     """Objectif : Implémenter NutritionNeeds
Règles métier : Value Object calculé à la demande, non persisté. Contient BMR (Mifflin-St Jeor), TDEE et CalorieTarget selon l'objectif de l'utilisateur. Produit par le DietService au lancement d'un plan — résultat intermédiaire du calcul nutritionnel.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "domain", "STORY-002"),
    ("SUB-007", "Créer et mettre à jour le profil utilisateur",
     """Objectif : Créer et mettre à jour le profil utilisateur
Règles métier : À la création : initialiser le profil avec une première WeightEntry (poids actuel). À la mise à jour : tous les champs biométriques sont modifiables. Retourner un UserProfileResponse complet incluant BMR et TDEE calculés à la demande.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "application", "STORY-003"),
    ("SUB-008", "Gestion des pesées (WeightEntry)",
     """Objectif : Gestion des pesées (WeightEntry)
Règles métier : Ajouter une pesée avec date mesurée (par défaut aujourd'hui). Contrainte : une seule entrée par date par User (conflit → erreur métier 409). Retourner l'historique des pesées.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "application", "STORY-003"),
    ("SUB-009", "CRUD des plans personnels avec contrôle tier",
     """Objectif : CRUD des plans personnels avec contrôle tier
Règles métier : Créer, modifier, supprimer et lister les DietPlan personnels d'un utilisateur. Contrôle tier à la création : Free max 2 plans, Pro max 20 plans — erreur métier 403 si dépassement.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "application", "STORY-004"),
    ("SUB-010", "Plans templates partagés",
     """Objectif : Plans templates partagés
Règles métier : Lister les DietPlan templates (IsTemplate = true). Accès restreint aux tiers Pro et Business — erreur 403 si tier Free. Création et modification des templates réservées au rôle admin.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "application", "STORY-004"),
    ("SUB-011", "Lancer un DietPlan (création d'une Diet active)",
     """Objectif : Lancer un DietPlan (création d'une Diet active)
Règles métier : Vérifier qu'aucune Diet n'est déjà active pour l'utilisateur (sinon 409). Calculer BMR (Mifflin-St Jeor), TDEE et CalorieTarget depuis le profil utilisateur. Créer le snapshot de la Diet avec StartDate = aujourd'hui. Les données nutritionnelles sont gelées à la date de lancement.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "application", "STORY-005"),
    ("SUB-012", "Archiver une Diet et déduire la Diet active par date",
     """Objectif : Archiver une Diet et déduire la Diet active par date
Règles métier : Terminer une Diet active : passer en statut Archived, EndDate = date du jour (imposée par le système). Déduire la Diet active à la date d'un Meal (pour alimenter le bilan nutritionnel).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "application", "STORY-005"),
    ("SUB-013", "Créer un repas",
     """Objectif : Créer un repas
Règles métier : Créer un Meal avec ses MealItems. Calculer NutritionInfo pour chaque MealItem à partir des données du FoodItem. Un repas peut être sauvegardé (IsSaved = true). Contrôle tier : Free max 5 repas sauvegardés, Pro max 50 — erreur 403 si dépassement.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "application", "STORY-006"),
    ("SUB-014", "Lister et supprimer des repas",
     """Objectif : Lister et supprimer des repas
Règles métier : Lister les repas avec filtres (par date, sauvegardés uniquement). Supprimer un repas existant.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "application", "STORY-006"),
    ("SUB-015", "Rechercher des aliments",
     """Objectif : Rechercher des aliments
Règles métier : Recherche par mot-clé avec stratégie cache-first : chercher d'abord dans Redis (TTL court), fallback sur PostgreSQL si cache miss. Retourner une liste de FoodItemSearchResponse.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "application", "STORY-007"),
    ("SUB-016", "Gérer les aliments favoris (SavedFoodItem)",
     """Objectif : Gérer les aliments favoris (SavedFoodItem)
Règles métier : Sauvegarder un FoodItem dans la liste personnelle. Invariant : unicité par FoodItemId et UserId. Contrôle tier : Free max 10 favoris, Pro max 100 — erreur 403 si dépassement. Supprimer un favori. Lister les favoris de l'utilisateur.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "application", "STORY-007"),
    ("SUB-017", "Calculer le bilan nutritionnel d'une Diet",
     """Objectif : Calculer le bilan nutritionnel d'une Diet
Règles métier : Agréger les MealItems et WeightEntries par période (jour, semaine, mois). Restriction par tier : Free max 7 jours d'historique, Pro max 1 an. Retourner un NutritionBilanResponse avec dailyData, weightEntries et summary.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "application", "STORY-008"),
    ("SUB-018", "Implémenter SubscriptionGuard",
     """Objectif : Implémenter SubscriptionGuard
Règles métier : Helper centralisé appelé par les services applicatifs pour vérifier les limites selon le tier (Free, Pro, Business). Lève une erreur métier 403 avec message explicite ('This feature requires a Pro subscription') si la limite est atteinte. Centralisé pour éviter la duplication des vérifications dans chaque service.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "application", "STORY-009"),
    ("SUB-019", "KPIs utilisateurs (AdminService)",
     """Objectif : KPIs utilisateurs (AdminService)
Règles métier : Agréger : total utilisateurs par tier, nouveaux utilisateurs sur les 7 derniers jours, diets actives, repas créés sur 7 jours, comptes en grace period (suppression en cours).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "application", "STORY-010"),
    ("SUB-020", "Santé système (AdminService)",
     """Objectif : Santé système (AdminService)
Règles métier : Agréger depuis les tables Hangfire (HangFire.Job, HangFire.State) : statut des jobs d'import OFF et de purge RGPD, nombre de FoodItems en base.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "application", "STORY-010"),
    ("SUB-021", "Configurations Fluent API de toutes les entités",
     """Objectif : Configurations Fluent API de toutes les entités
Règles métier : Configurer le mapping EF Core pour toutes les entités : User, DietPlan (UserId nullable, IsTemplate, index sur IsTemplate), Diet, Meal, MealItem, FoodItem, WeightEntry, SavedFoodItem. Configurer MacroDistribution et NutritionInfo comme owned entities.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "infrastructure", "STORY-011"),
    ("SUB-022", "Migration initiale et import initial OFF",
     """Objectif : Migration initiale et import initial OFF
Règles métier : Générer la migration initiale créant toutes les tables. Prévoir l'import initial du dump Open Food Facts à la première installation (avant mise en production).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "infrastructure", "STORY-011"),
    ("SUB-023", "Seed des templates initiaux",
     """Objectif : Seed des templates initiaux
Règles métier : Charger les DietPlan templates partagés à partir d'un fichier JSON ou d'une migration de données (IsTemplate = true, UserId = null).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Low", "infrastructure", "STORY-011"),
    ("SUB-024", "Implémenter les repositories EF Core",
     """Objectif : Implémenter les repositories EF Core
Règles métier : Repositories pour : User, DietPlan, Diet, Meal, FoodItem, WeightEntry, SavedFoodItem. Chaque repository expose les opérations nécessaires aux services applicatifs (pas de CRUD générique exposé — uniquement les requêtes réellement utilisées).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "infrastructure", "STORY-012"),
    ("SUB-025", "Configurer Redis et implémenter FoodCacheService",
     """Objectif : Configurer Redis et implémenter FoodCacheService
Règles métier : Configurer IConnectionMultiplexer. Implémenter FoodCacheService : get/set des résultats de recherche par mot-clé avec TTL court. Invalidation automatique à l'expiration (pas d'invalidation manuelle).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "infrastructure", "STORY-013"),
    ("SUB-026", "Implémenter le job d'import OFF",
     """Objectif : Implémenter le job d'import OFF
Règles métier : Télécharger le dump OFF (JSONL/CSV). Traiter par batch (INSERT / UPDATE FoodItem). Planifier quotidiennement via Hangfire (cron '0 3 * * *'). Gérer les erreurs et la reprise après échec via le mécanisme de retry automatique Hangfire.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "infrastructure", "STORY-014"),
    ("SUB-027", "Implémenter le job de purge RGPD",
     """Objectif : Implémenter le job de purge RGPD
Règles métier : Sélectionner les utilisateurs avec DeletedAt <= aujourd'hui - 30 jours. Supprimer en cascade via PostgreSQL : MealItems → Meals → WeightEntries → SavedFoodItems → DietPlans → Diets → User. Appeler DELETE /admin/realms/{realm}/users/{KeycloakId} pour chaque utilisateur purgé. Gestion des erreurs : Keycloak indisponible → retry Hangfire, données déjà supprimées → ignorer. Planification quotidienne (cron '0 3 30 * *').
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "infrastructure", "STORY-015"),
    ("SUB-028", "Middleware JWT Keycloak",
     """Objectif : Middleware JWT Keycloak
Règles métier : Valider les tokens JWT : vérification signature, audience et expiration. Extraire le claim 'sub' (KeycloakId) et résoudre l'identité en User.Id interne. Bloquer les requêtes sans token valide avec 401.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "api", "STORY-016"),
    ("SUB-029", "Gestion globale des erreurs et logging",
     """Objectif : Gestion globale des erreurs et logging
Règles métier : Middleware d'exception global : mapper les erreurs domaine vers les codes HTTP appropriés (409 conflit, 403 tier insuffisant, 404 non trouvé, 400 validation). Logging des requêtes entrantes et sortantes.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "api", "STORY-016"),
    ("SUB-030", "Configuration OpenAPI/Swagger",
     """Objectif : Configuration OpenAPI/Swagger
Règles métier : Configurer AddSwaggerGen avec titre, version et sécurité JWT Bearer. Activer UseSwagger + UseSwaggerUI uniquement hors production. Activer les commentaires XML sur les projets API et Application. Exclure le dashboard Hangfire (/hangfire) de la spec OpenAPI.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "api", "STORY-016"),
    ("SUB-031", "Endpoints profil et pesées",
     """Objectif : Endpoints profil et pesées
Règles métier : POST /users/me (création profil, déclenché à la première connexion Keycloak), GET /users/me (profil + BMR/TDEE calculés à la demande), PUT /users/me, POST /users/me/weight-entries, GET /users/me/weight-entries, PUT /users/me/weight-entries/{id}.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "api", "STORY-017"),
    ("SUB-032", "Endpoints aliments favoris",
     """Objectif : Endpoints aliments favoris
Règles métier : GET /users/me/saved-food-items, POST /users/me/saved-food-items (sauvegarder un aliment), DELETE /users/me/saved-food-items/{id}.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "api", "STORY-017"),
    ("SUB-033", "Endpoints RGPD",
     """Objectif : Endpoints RGPD
Règles métier : DELETE /users/me (soft delete, désactivation Keycloak, grace period 30j). POST /users/me/reactivate (réactivation pendant grace period). GET /users/me/export (export RGPD Art. 20 — toutes les données de l'utilisateur).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "api", "STORY-017"),
    ("SUB-034", "Endpoints CRUD et lancement de plans",
     """Objectif : Endpoints CRUD et lancement de plans
Règles métier : POST /diet-plans, GET /diet-plans, PUT /diet-plans/{id}, DELETE /diet-plans/{id}, POST /diet-plans/{id}/launch (lancer un plan → créer une Diet active).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "api", "STORY-018"),
    ("SUB-035", "Endpoints templates partagés",
     """Objectif : Endpoints templates partagés
Règles métier : GET /diet-plans/templates (liste des templates, Pro + Business uniquement). POST /admin/diet-plans/templates, PUT /admin/diet-plans/templates/{id} (rôle admin uniquement). Politique RequireRole('admin') sur les endpoints /admin/**.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "api", "STORY-018"),
    ("SUB-036", "Endpoints consultation et archivage",
     """Objectif : Endpoints consultation et archivage
Règles métier : GET /diets/active, GET /diets (historique), GET /diets/{id} (détail), POST /diets/{id}/archive (terminer un régime actif).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "api", "STORY-019"),
    ("SUB-037", "Endpoint bilan nutritionnel",
     """Objectif : Endpoint bilan nutritionnel
Règles métier : GET /diets/{id}/bilan — calculer et retourner le bilan de la période. Paramètres acceptés : period (day/week/month), date, startDate. Déléguer au NutritionService avec contrôle de la période autorisée selon le tier.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "api", "STORY-019"),
    ("SUB-038", "Endpoints repas (MealsController)",
     """Objectif : Endpoints repas (MealsController)
Règles métier : POST /meals, GET /meals (filtres : ?saved=true, ?date=), GET /meals/{id}, DELETE /meals/{id}, POST /meals/{id}/items (ajouter un MealItem), DELETE /meals/{id}/items/{itemId}.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "api", "STORY-020"),
    ("SUB-039", "Endpoint recherche aliments (FoodItemsController)",
     """Objectif : Endpoint recherche aliments (FoodItemsController)
Règles métier : GET /food-items?search={motclé} — déléguer au FoodItemService (cache Redis en priorité, fallback PostgreSQL).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "api", "STORY-020"),
    ("SUB-040", "Endpoints supervision système",
     """Objectif : Endpoints supervision système
Règles métier : GET /admin/dashboard (KPIs consolidés : utilisateurs par tier, activité, comptes en grace period). GET /admin/system/health (statut jobs OFF import + purge RGPD + count FoodItems).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "api", "STORY-021"),
    ("SUB-041", "Endpoint suppression de templates",
     """Objectif : Endpoint suppression de templates
Règles métier : DELETE /admin/diet-plans/templates/{id} (rôle admin uniquement). Réponses 403 avec message explicite pour tier insuffisant sur tous les endpoints protégés.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Low", "api", "STORY-021"),
    ("SUB-042", "Tests des invariants et règles domaine",
     """Objectif : Tests des invariants et règles domaine
Règles métier : MacroDistribution : rejet si somme des pourcentages ≠ 100%. NutritionInfo : calcul correct du snapshot. Diet : règles d'activation — rejet si une Diet est déjà active, StartDate imposée système, non-modifiabilité après lancement.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "tests", "STORY-022"),
    ("SUB-043", "Tests repositories avec Testcontainers",
     """Objectif : Tests repositories avec Testcontainers
Règles métier : Tests d'intégration des repositories sur une instance PostgreSQL réelle via Testcontainers. Vérifier les opérations de lecture/écriture et les contraintes d'unicité (SavedFoodItem par FoodItemId+UserId, WeightEntry par date+UserId).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "tests", "STORY-023"),
    ("SUB-044", "Tests Redis et job import OFF",
     """Objectif : Tests Redis et job import OFF
Règles métier : Tests du FoodCacheService (get/set/expiration TTL). Tests du job d'import OFF sur un dump de test (couverture insert/update, gestion des erreurs de téléchargement).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "tests", "STORY-023"),
    ("SUB-045", "Tests de tous les endpoints API",
     """Objectif : Tests de tous les endpoints API
Règles métier : Cas nominaux et cas d'erreur pour chaque endpoint (400, 401, 403, 404, 409). Validation JWT : rejet des tokens invalides/expirés. Tests des limites tier (Free vs Pro vs Business).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "tests", "STORY-024"),
]
