# Backlog Jira — Décomposition Epic / Story / Sub-task

> Source de vérité : `docs/backend/livrable/jira_backlog.py` (script unique — MODE="create")
> Méthodologie : `dev-playbook/guides/jira-scrum.md`
> Story Points : estimation en sprint planning avec l'équipe
> **Commande d'import : voir bas de page**

---

## Definition of Done — s'applique à toutes les Stories

Une Story est terminée quand **toutes** ces conditions sont remplies :

- [ ] Le code compile sans erreur ni warning
- [ ] Le test a été écrit **avant** le code de production (TDD — Red → Green → Refactor)
- [ ] Tous les tests de la Story passent (unitaires + intégration selon la couche)
- [ ] Aucun test existant n'est cassé (zéro régression)
- [ ] Les invariants métier de la Story sont couverts par au moins un test
- [ ] Le code respecte l'architecture DDD — aucune logique métier hors de la couche Domain
- [ ] La PR est relue et approuvée avant merge

---

## Epic 1 — [DOMAIN] Couche Domain

> Implémentation des entités, value objects, enums et invariants métier. Zéro dépendance externe.
> Les tests unitaires Domain sont inclus dans cet Epic — écrits en TDD avant chaque implémentation.

### Story : Aggregate Roots `[3 pts]`
- Sub-task : Créer l'entité User
- Sub-task : Créer l'entité DietPlan
- Sub-task : Créer l'entité Diet
- Sub-task : Créer l'entité Meal
- Sub-task : Créer l'entité FoodItem

### Story : Entités enfants `[2 pts]`
- Sub-task : Créer WeightEntry (enfant de User)
- Sub-task : Créer MealItem (enfant de Meal)
- Sub-task : Créer SavedFoodItem (enfant de User)

### Story : Value Objects `[2 pts]`
- Sub-task : Créer MacroDistribution avec invariant somme = 100%
- Sub-task : Créer NutritionInfo (snapshot Calories/Proteins/Carbs/Fats)
- Sub-task : Créer NutritionNeeds (non persisté — Bmr/Tdee/TargetCalories)

### Story : Enums domaine `[1 pt]`
- Sub-task : Créer ActivityLevel
- Sub-task : Créer Goal
- Sub-task : Créer MealType
- Sub-task : Créer DietType
- Sub-task : Créer DietStatus
- Sub-task : Créer Gender
- Sub-task : Créer Allergen (14 valeurs EU)

### Story : Invariants domaine `[3 pts]`
- Sub-task : Bloquer Diet active si une existe déjà (409 Conflict)
- Sub-task : Valider que Meal contient au moins un MealItem
- Sub-task : Interdire doublon SavedFoodItem par User (409 Conflict)
- Sub-task : Imposer Diet.StartDate = date du lancement (système)
- Sub-task : Interdire modification Diet après lancement (sauf EndDate)

### Story : Abonnements & Templates — Domaine `[3 pts]` *(ajout 2026-05-02)*
- Sub-task : Déclarer enum SubscriptionTier (Free, Pro, Business)
- Sub-task : Ajouter User.SubscriptionTier — Free par défaut à la création
- Sub-task : Ajouter DietPlan.IsTemplate — bool, false par défaut
- Sub-task : Passer DietPlan.UserId en Guid? — null si template

### Story : Tests unitaires Domain `[5 pts]` *(déplacé depuis Epic 5 — TDD : écrits avant le code)*
- Sub-task : Tester MacroDistribution — invariant somme = 100%
- Sub-task : Tester NutritionInfo — calcul snapshot correct (grammes depuis FoodItem × quantité)
- Sub-task : Tester Diet — unicité régime actif par User (DomainException si déjà active)
- Sub-task : Tester Meal — lève DomainException si aucun MealItem à la création
- Sub-task : Tester SavedFoodItem — doublon interdit pour même User (DomainException)
- Sub-task : Tester Diet — StartDate imposée par le système (non assignable par le client)
- Sub-task : Tester Diet — immutabilité après lancement (hors EndDate)
- Sub-task : Tester WeightEntry — doublon même date même User → DomainException

---

## Epic 2 — [APPLICATION] Couche Application

> Services métier et DTOs. Orchestre les use cases — dépend uniquement du Domain.
> Les tests unitaires Application sont inclus dans cet Epic — écrits en TDD avant chaque implémentation.

### Story : UserService `[3 pts]`
- Sub-task : Créer le profil utilisateur + première WeightEntry
- Sub-task : Mettre à jour le profil utilisateur
- Sub-task : Ajouter une WeightEntry

### Story : DietPlanService `[3 pts]`
- Sub-task : Créer un DietPlan
- Sub-task : Modifier un DietPlan
- Sub-task : Supprimer un DietPlan
- Sub-task : Lister les DietPlans d'un utilisateur

### Story : DietService `[5 pts]`
- Sub-task : Lancer un DietPlan → créer une Diet (snapshot complet)
- Sub-task : Calculer BMR/TDEE/CalorieTarget au lancement
- Sub-task : Terminer une Diet (Archived + EndDate = aujourd'hui)
- Sub-task : Déduire la Diet active à la date d'un Meal

### Story : MealService `[3 pts]`
- Sub-task : Créer un Meal avec calcul NutritionInfo par MealItem
- Sub-task : Lister les repas sauvegardés (IsSaved = true)
- Sub-task : Supprimer un Meal

### Story : FoodItemService `[3 pts]`
- Sub-task : Rechercher des aliments par mot-clé (Redis → PostgreSQL)
- Sub-task : Sauvegarder un FoodItem dans la liste personnelle
- Sub-task : Supprimer un SavedFoodItem
- Sub-task : Lister les SavedFoodItems d'un utilisateur

### Story : NutritionService `[5 pts]`
- Sub-task : Calculer le bilan nutritionnel d'une Diet (agrégation MealItems + WeightEntries)

### Story : DTOs `[2 pts]`
- Sub-task : CreateUserProfileRequest / UserProfileResponse
- Sub-task : CreateDietPlanRequest / DietPlanResponse
- Sub-task : LaunchDietPlanRequest / DietResponse
- Sub-task : CreateMealRequest / MealResponse
- Sub-task : FoodItemSearchResponse
- Sub-task : SaveFoodItemRequest
- Sub-task : NutritionBilanResponse (dailyData + weightEntries + summary)

### Story : SubscriptionGuard — Vérifications tier `[5 pts]` *(ajout 2026-05-02)*
- Sub-task : Implémenter helper SubscriptionGuard (méthode centralisée CheckLimit)
- Sub-task : DietPlanService — bloquer création plan si limite tier atteinte (Free: 2, Pro: 20)
- Sub-task : DietPlanService — bloquer accès templates si tier Free (403)
- Sub-task : DietPlanService — lister les templates partagés (IsTemplate = true)
- Sub-task : MealService — bloquer sauvegarde repas si limite tier atteinte (Free: 5, Pro: 50)
- Sub-task : FoodItemService — bloquer ajout SavedFoodItem si limite tier atteinte (Free: 10, Pro: 100)
- Sub-task : NutritionService — clamper période bilan selon tier (Free: 7j, Pro: 1 an, Business: illimité)

### Story : AdminService — KPIs & métriques système `[3 pts]` *(ajout 2026-05-02)*
- Sub-task : Agréger KPIs utilisateurs (total, par tier, nouveaux 7j)
- Sub-task : Agréger métriques activité (diets actives, repas 7j, grace period)
- Sub-task : Agréger santé système depuis tables Hangfire (HangFire.Job + HangFire.State)

### Story : Tests unitaires Application `[5 pts]` *(ajout 2026-05-04 — TDD : écrits avant le code)*
- Sub-task : Tester UserService — ajout WeightEntry doublon même date → 409
- Sub-task : Tester DietService — lancement sans WeightEntry → 422
- Sub-task : Tester DietService — lancement avec Diet active existante → 409
- Sub-task : Tester MealService — création Meal sans MealItem → rejeté (DomainException)
- Sub-task : Tester FoodItemService — SavedFoodItem doublon → 409
- Sub-task : Tester NutritionService — bilan agrégation journalière correcte (Moq repositories)
- Sub-task : Tester SubscriptionGuard — blocage limite plans Free (403)
- Sub-task : Tester SubscriptionGuard — blocage ajout repas sauvegardé Free (403)
- Sub-task : Tester SubscriptionGuard — restriction période bilan Free 7j

---

## Epic 3 — [INFRASTRUCTURE] Couche Infrastructure

> Accès aux données : EF Core, repositories, cache Redis, jobs planifiés.

### Story : EF Core Configurations `[3 pts]`
- Sub-task : UserConfiguration (Fluent API)
- Sub-task : DietPlanConfiguration (Fluent API)
- Sub-task : DietConfiguration (Fluent API)
- Sub-task : MealConfiguration (Fluent API)
- Sub-task : MealItemConfiguration (Fluent API)
- Sub-task : FoodItemConfiguration (Fluent API)
- Sub-task : WeightEntryConfiguration (Fluent API)
- Sub-task : SavedFoodItemConfiguration (Fluent API)
- Sub-task : MacroDistribution en owned entity EF Core
- Sub-task : NutritionInfo en owned entity EF Core

### Story : Repositories `[5 pts]`
- Sub-task : IUserRepository / UserRepository
- Sub-task : IDietPlanRepository / DietPlanRepository
- Sub-task : IDietRepository / DietRepository
- Sub-task : IMealRepository / MealRepository
- Sub-task : IFoodItemRepository / FoodItemRepository
- Sub-task : IWeightEntryRepository / WeightEntryRepository
- Sub-task : ISavedFoodItemRepository / SavedFoodItemRepository

### Story : Cache Redis `[2 pts]`
- Sub-task : Configurer IConnectionMultiplexer
- Sub-task : Implémenter IFoodCacheService / FoodCacheService (get/set par mot-clé)

### Story : Job import Open Food Facts (Hangfire) `[13 pts]`
- Sub-task : Télécharger le dump OFF (JSONL/CSV)
- Sub-task : Traiter le dump par batch (INSERT/UPDATE FoodItem)
- Sub-task : Implémenter IOffImportJob et OffImportJob (classe Hangfire — résolution DI)
- Sub-task : Gérer les erreurs et la reprise après échec (retry Hangfire)

### Story : Job purge RGPD (Hangfire) `[8 pts]`
- Sub-task : Sélectionner les utilisateurs à purger (DeletedAt <= 30 jours)
- Sub-task : Supprimer les données en cascade dans PostgreSQL
- Sub-task : Supprimer l'utilisateur dans Keycloak Admin (par KeycloakId)
- Sub-task : Implémenter IRgpdPurgeJob et RgpdPurgeJob (classe Hangfire — résolution DI)
- Sub-task : Gérer les erreurs (Keycloak indisponible → retry Polly)

### Story : Migrations EF Core `[2 pts]`
- Sub-task : Créer la migration initiale (toutes les tables)
- Sub-task : Préparer l'import initial du dump OFF (première installation)

### Story : Abonnements & Templates — Infrastructure `[3 pts]` *(ajout 2026-05-02)*
- Sub-task : DietPlanConfiguration — UserId nullable, IsTemplate mappé, index sur IsTemplate
- Sub-task : Seed des templates initiaux (migration ou fichier JSON)

### Story : Configuration Hangfire `[3 pts]` *(ajout 2026-05-02)*
- Sub-task : Configurer Hangfire avec stockage PostgreSQL (schéma HangFire, PrepareSchemaIfNecessary=true)
- Sub-task : Sécuriser le dashboard /hangfire — filtre rôle admin Keycloak
- Sub-task : Enregistrer les jobs récurrents au démarrage (OffImportJob à 03h00, RgpdPurgeJob à 03h30)

---

## Epic 4 — [API] Couche API

> Controllers REST + middleware. Expose les fonctionnalités — dépend de Application.

### Story : UsersController `[5 pts]`
- Sub-task : POST /users/me — créer le profil
- Sub-task : GET /users/me — lire profil + BMR/TDEE calculés
- Sub-task : PUT /users/me — mettre à jour le profil
- Sub-task : POST /users/me/weight-entries — ajouter une pesée
- Sub-task : GET /users/me/weight-entries — historique des pesées
- Sub-task : PUT /users/me/weight-entries/{id} — modifier une pesée
- Sub-task : GET /users/me/saved-food-items — liste personnelle aliments
- Sub-task : POST /users/me/saved-food-items — sauvegarder un aliment
- Sub-task : DELETE /users/me/saved-food-items/{id} — retirer un aliment
- Sub-task : DELETE /users/me — suppression compte (RGPD Art. 17)
- Sub-task : POST /users/me/reactivate — réactivation compte (RGPD)
- Sub-task : GET /users/me/export — export données (RGPD Art. 20)

### Story : DietPlansController `[3 pts]`
- Sub-task : POST /diet-plans — créer un plan
- Sub-task : GET /diet-plans — lister ses plans
- Sub-task : PUT /diet-plans/{id} — modifier un plan
- Sub-task : DELETE /diet-plans/{id} — supprimer un plan
- Sub-task : POST /diet-plans/{id}/launch — lancer un plan → créer une Diet

### Story : DietsController `[3 pts]`
- Sub-task : GET /diets/active — récupérer le régime actif
- Sub-task : GET /diets — lister ses régimes (historique)
- Sub-task : GET /diets/{id} — détail d'un régime
- Sub-task : POST /diets/{id}/archive — terminer un régime actif
- Sub-task : GET /diets/{id}/bilan — bilan nutritionnel de la période

### Story : MealsController `[3 pts]`
- Sub-task : POST /meals — créer un repas
- Sub-task : GET /meals — lister ses repas (filtres : saved / date)
- Sub-task : GET /meals/{id} — détail d'un repas
- Sub-task : DELETE /meals/{id} — supprimer un repas
- Sub-task : POST /meals/{id}/items — ajouter un MealItem
- Sub-task : DELETE /meals/{id}/items/{itemId} — retirer un MealItem

### Story : FoodItemsController `[1 pt]`
- Sub-task : GET /food-items?search={motclé} — rechercher un aliment

### Story : Middleware `[3 pts]`
- Sub-task : Valider le JWT Keycloak (middleware auth)
- Sub-task : Gérer les erreurs globalement (exception → code HTTP)
- Sub-task : Logger les requêtes entrantes

### Story : Auth & Templates — Nouveaux endpoints `[5 pts]` *(ajout 2026-05-02)*
- Sub-task : GET /diet-plans/templates — liste templates partagés (Pro/Business uniquement)
- Sub-task : POST /admin/diet-plans/templates — créer un template (rôle admin)
- Sub-task : PUT /admin/diet-plans/templates/{id} — modifier un template (rôle admin)
- Sub-task : Middleware JWT — extraction claim sub → User.KeycloakId
- Sub-task : Réponses 403 tier insuffisant avec message explicite

### Story : AdminController — Dashboard & Santé système `[3 pts]` *(ajout 2026-05-02)*
- Sub-task : GET /admin/dashboard — KPIs consolidés (utilisateurs par tier, activité, grace period)
- Sub-task : GET /admin/system/health — statut jobs OFF import + purge RGPD + count FoodItems
- Sub-task : DELETE /admin/diet-plans/templates/{id} — supprimer un template (rôle admin)

### Story : OpenAPI / Swagger UI `[2 pts]` *(ajout 2026-05-02)*
- Sub-task : Configurer AddSwaggerGen — titre, version, sécurité JWT Bearer
- Sub-task : Activer UseSwagger + UseSwaggerUI hors production uniquement
- Sub-task : Activer commentaires XML sur les projets API et Application
- Sub-task : Exclure le dashboard /hangfire de la spec OpenAPI

---

## Epic 5 — [TESTS] Tests d'intégration et API

> Tests qui nécessitent le stack complet monté : base de données réelle (Testcontainers), serveur HTTP (WebApplicationFactory).
> Les tests unitaires Domain et Application sont dans leurs Epics respectifs (1 et 2) — écrits en TDD avant le code.

### Story : Tests intégration Infrastructure `[5 pts]`
- Sub-task : Tester repositories avec Testcontainers (PostgreSQL réel)
- Sub-task : Tester le cache Redis
- Sub-task : Tester le job import OFF (dump de test)

### Story : Tests API `[5 pts]`
- Sub-task : Tester tous les endpoints (cas nominaux + cas d'erreur)
- Sub-task : Tester la validation JWT

### Story : Tests — Abonnements & Templates `[3 pts]` *(ajout 2026-05-02)*
- Sub-task : Tester blocage création plan si limite Free atteinte (403)
- Sub-task : Tester blocage accès templates pour tier Free (403)
- Sub-task : Tester restriction période bilan selon tier (Free: 7j, Pro: 1 an)
- Sub-task : Tester blocage SavedFoodItem limite Free (403)

### Story : Tests — Admin back-office `[2 pts]` *(ajout 2026-05-02)*
- Sub-task : Tester GET /admin/dashboard — données agrégées correctes
- Sub-task : Tester GET /admin/dashboard — 403 si rôle admin absent
- Sub-task : Tester GET /admin/system/health — statuts jobs corrects

---

---

## Commande d'import Jira

**Prérequis — configurer les credentials :**

```bash
cp playbook/tools/.env.example docs/backend/livrable/.env
# Remplir JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY=NTRTN
```

**Lancer l'import :**

```bash
python3 playbook/tools/import_jira.py docs/backend/livrable/jira_backlog.py
```

> ⚠️ Le fichier `.env` ne doit jamais être commité — il est dans `.gitignore`.

---

*Généré le 2026-04-29 — Source : checklist-implementation.md (étape 8)*
*Mis à jour le 2026-05-02 — Ajout : Auth, SubscriptionTier, DietPlan templates, Admin back-office — Source : 7.nutrition-abonnements.md + 8.nutrition-admin.md*
*Mis à jour le 2026-05-02 — Ajout : Configuration Hangfire (STORY-036 / SUB-151→153). Script fusionné en un seul fichier jira_backlog.py.*
*Mis à jour le 2026-05-04 — TDD : tests Domain (STORY-025) déplacés dans Epic 1 + invariants manquants ajoutés (SUB-158→162). Tests Application ajoutés (STORY-038 / SUB-163→171) dans Epic 2. Epic 5 recentré sur intégration + API uniquement. Definition of Done ajoutée en en-tête.*
*Mis à jour le 2026-05-04 — Commande d'import ajoutée en fin de fichier.*
