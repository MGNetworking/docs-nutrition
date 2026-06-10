# Checklist d'implémentation — API Nutrition

> Document vivant — cocher chaque item au fur et à mesure de l'implémentation.
> Généré à l'étape 8 (validation cohérence) — sert de pont entre conception et développement.
> Source de vérité : `docs/pages/backend/design/design-domain.md` + workflows `docs/annexes/`

---

## Légende

| Symbole | Signification |
|---|---|
| 🔲 | À implémenter |
| 🔄 | En cours |
| ✅ | Terminé |
| ⚠️ | Gap identifié — à trancher avant implémentation |

---

## 1. Couche Domain

### Aggregate Roots
- 🔲 `User`
- 🔲 `DietPlan`
- 🔲 `Diet`
- 🔲 `Meal`
- 🔲 `FoodItem`

### Entités enfants
- 🔲 `WeightEntry` (enfant de `User`)
- 🔲 `MealItem` (enfant de `Meal`)
- 🔲 `SavedFoodItem` (enfant de `User`)

### Value Objects
- 🔲 `MacroDistribution` — invariant : somme = 100%
- 🔲 `NutritionInfo` — snapshot calculé (Calories, Proteins, Carbs, Fats)
- 🔲 `NutritionNeeds` — non persisté, calculé à la demande (Bmr, Tdee, TargetCalories)

### Enums
- 🔲 `ActivityLevel` — Sedentary, LightlyActive, ModeratelyActive, VeryActive, ExtremelyActive
- 🔲 `Goal` — WeightLoss, Maintenance, WeightGain
- 🔲 `MealType` — Breakfast, Lunch, Dinner, Snack
- 🔲 `DietType` — Balanced, HighProtein, Keto, Mediterranean, LowCarb, Vegetarian, Vegan, Custom
- 🔲 `DietStatus` — Active, Inactive, Archived
- 🔲 `Gender` — Male, Female, Other
- 🔲 `Allergen` — 14 valeurs EU (Gluten, Crustaceans, Eggs, Fish, Peanuts, Soybeans, Milk, Nuts, Celery, Mustard, SesameSeeds, SulphurDioxide, Lupin, Molluscs)
- 🔲 `SubscriptionTier` — Free, Pro, Business

### Abonnements & Templates (ajout 2026-05-02)
- 🔲 `User.SubscriptionTier` — champ ajouté (Free par défaut)
- 🔲 `DietPlan.IsTemplate` — bool (false par défaut)
- 🔲 `DietPlan.UserId` — passer à `Guid?` (null si template)

### Invariants domaine à implémenter
- 🔲 `MacroDistribution` : CarbsPercent + ProteinsPercent + FatsPercent = 100%
- 🔲 `Meal` : doit contenir au moins un `MealItem`
- 🔲 `Diet` : une seule `Active` par `User` — bloquer à l'activation (409)
- 🔲 `SavedFoodItem` : un même `FoodItemId` ne peut être sauvegardé qu'une fois par `User`
- 🔲 `Diet.StartDate` : imposée par le système (= date du lancement)
- 🔲 `Diet` : non modifiable une fois lancée (sauf `EndDate`)

---

## 2. Couche Application (Services)

### UserService
- 🔲 Créer le profil utilisateur (+ première `WeightEntry`)
- 🔲 Mettre à jour le profil utilisateur
- 🔲 Ajouter une `WeightEntry`

### DietPlanService
- 🔲 Créer un `DietPlan`
- 🔲 Modifier un `DietPlan`
- 🔲 Supprimer un `DietPlan`
- 🔲 Lister les `DietPlan` d'un utilisateur

### DietService
- 🔲 Lancer un `DietPlan` → créer une `Diet` (snapshot + calcul BMR/TDEE/CalorieTarget)
- 🔲 Terminer une `Diet` (passer en `Archived` + renseigner `EndDate`)
- 🔲 Calculer BMR/TDEE/CalorieTarget (interne — appelé au lancement)
- 🔲 Déduire la `Diet` active à la date d'un `Meal` (pour le bilan)

### MealService
- 🔲 Créer un `Meal` (avec calcul `NutritionInfo` pour chaque `MealItem`)
- 🔲 Lister les repas sauvegardés (`IsSaved = true`)
- 🔲 Supprimer un `Meal`

### FoodItemService
- 🔲 Rechercher des aliments par mot-clé (Redis → PostgreSQL)
- 🔲 Sauvegarder un `FoodItem` dans la liste personnelle (`SavedFoodItem`)
- 🔲 Supprimer un `SavedFoodItem`
- 🔲 Lister les `SavedFoodItem` d'un utilisateur

### RgpdService
- 🔲 `ExportUserDataAsync` — agréger les données de l'utilisateur (User, WeightEntry, DietPlan, Diet, Meal, SavedFoodItem, FoodItem)
- 🔲 `DeleteUserAsync` — soft delete + désactivation Keycloak
- 🔲 `ReactivateUserAsync` — réactivation pendant la grace period

### NutritionService
- 🔲 Calculer le bilan nutritionnel d'une `Diet` (agrégation `MealItem` + `WeightEntry` par période)

### SubscriptionGuard — vérifications tier (ajout 2026-05-02)
- 🔲 Helper `SubscriptionGuard` (ou méthode centralisée) — vérifie les limites selon `User.SubscriptionTier`
- 🔲 `DietPlanService` — bloquer création plan personnel si limite tier atteinte (Free: 2, Pro: 20)
- 🔲 `DietPlanService` — bloquer accès templates si tier = Free (403)
- 🔲 `DietPlanService` — lister les templates partagés (`IsTemplate = true`)
- 🔲 `MealService` — bloquer création repas sauvegardé si limite tier atteinte (Free: 5, Pro: 50)
- 🔲 `FoodItemService` — bloquer ajout SavedFoodItem si limite tier atteinte (Free: 10, Pro: 100)
- 🔲 `NutritionService` — restreindre la période du bilan selon tier (Free: 7j, Pro: 1 an)

### DTOs (un DTO Request + Response par use case)
- 🔲 `CreateUserProfileRequest` / `UserProfileResponse`
- 🔲 `CreateDietPlanRequest` / `DietPlanResponse`
- 🔲 `LaunchDietPlanRequest` / `DietResponse`
- 🔲 `CreateMealRequest` / `MealResponse`
- 🔲 `FoodItemSearchResponse`
- 🔲 `SaveFoodItemRequest`
- 🔲 `NutritionBilanResponse` (dailyData + weightEntries + summary)

---

## 3. Couche Infrastructure

### EF Core — Configurations (Fluent API)
- 🔲 `UserConfiguration`
- 🔲 `DietPlanConfiguration`
- 🔲 `DietConfiguration`
- 🔲 `MealConfiguration`
- 🔲 `MealItemConfiguration`
- 🔲 `FoodItemConfiguration`
- 🔲 `WeightEntryConfiguration`
- 🔲 `SavedFoodItemConfiguration`
- 🔲 Value Object `MacroDistribution` (owned entity)
- 🔲 Value Object `NutritionInfo` (owned entity)

### Repositories
- 🔲 `IUserRepository` / `UserRepository`
- 🔲 `IDietPlanRepository` / `DietPlanRepository`
- 🔲 `IDietRepository` / `DietRepository`
- 🔲 `IMealRepository` / `MealRepository`
- 🔲 `IFoodItemRepository` / `FoodItemRepository`
- 🔲 `IWeightEntryRepository` / `WeightEntryRepository`
- 🔲 `ISavedFoodItemRepository` / `SavedFoodItemRepository`

### Cache Redis
- 🔲 Configuration Redis (`IConnectionMultiplexer`)
- 🔲 `IFoodCacheService` / `FoodCacheService` — get/set par mot-clé (TTL court)

### Job d'import Open Food Facts (Hangfire)
- 🔲 Téléchargement du dump OFF (JSONL/CSV)
- 🔲 Traitement par batch (INSERT / UPDATE `FoodItem`)
- 🔲 Planification quotidienne via Hangfire (`RecurringJob.AddOrUpdate`, cron `0 3 * * *`)
- 🔲 Gestion des erreurs et reprise après échec (Hangfire retry automatique)

### Job de purge RGPD (Hangfire — quotidien)
- 🔲 `SELECT User WHERE DeletedAt <= maintenant - 30 jours`
- 🔲 DELETE cascade PostgreSQL : `MealItems → Meals → WeightEntries → SavedFoodItems → DietPlans → Diets → User`
- 🔲 `DELETE /admin/realms/{realm}/users/{KeycloakId}` (Keycloak Admin) pour chaque utilisateur purgé
- 🔲 Planification quotidienne via Hangfire (`RecurringJob.AddOrUpdate`, cron `0 3 30 * *`)
- 🔲 Gestion des erreurs (Keycloak indisponible → retry Hangfire, données déjà supprimées → ignorer)

### Migrations EF Core
- 🔲 Migration initiale (toutes les tables)
- 🔲 Import initial du dump OFF (première installation)

### Abonnements & Templates — Infrastructure (ajout 2026-05-02)
- 🔲 `DietPlanConfiguration` — `UserId` nullable + `IsTemplate` + index sur `IsTemplate`
- 🔲 Seed des templates initiaux (données de départ — fichier JSON ou migration)

---

## 4. Couche API (Controllers + Endpoints)

### AuthController — géré par Keycloak
- 🔲 Flux OAuth2/OIDC délégué à Keycloak (voir `workflow_Flux_authentification.mermaid`)

### UsersController
- 🔲 `POST /users/me` — créer le profil (auto-déclenché à la première connexion Keycloak)
- 🔲 `GET /users/me` — lire le profil + BMR/TDEE calculés à la demande
- 🔲 `PUT /users/me` — mettre à jour le profil
- 🔲 `POST /users/me/weight-entries` — ajouter une pesée
- 🔲 `GET /users/me/weight-entries` — historique des pesées
- 🔲 `PUT /users/me/weight-entries/{id}` — modifier une pesée existante
- 🔲 `GET /users/me/saved-food-items` — liste personnelle d'aliments
- 🔲 `POST /users/me/saved-food-items` — sauvegarder un aliment dans la liste personnelle
- 🔲 `DELETE /users/me/saved-food-items/{id}` — retirer un aliment de la liste

### RgpdController
- 🔲 `DELETE /rgpd` — suppression du compte (RGPD Art. 17)
- 🔲 `POST /rgpd/reactivate` — réactivation du compte pendant la grace period (RGPD)
- 🔲 `GET /rgpd/export` — export des données (RGPD Art. 20)

### DietPlansController
- 🔲 `POST /diet-plans` — créer un plan
- 🔲 `GET /diet-plans` — lister ses plans
- 🔲 `PUT /diet-plans/{id}` — modifier un plan
- 🔲 `DELETE /diet-plans/{id}` — supprimer un plan
- 🔲 `POST /diet-plans/{id}/launch` — lancer un plan → créer une Diet active

### DietsController
- 🔲 `GET /diets/active` — récupérer le régime actif (utilisé sur dashboard + écran Diet active)
- 🔲 `GET /diets` — lister ses régimes (historique)
- 🔲 `GET /diets/{id}` — détail d'un régime
- 🔲 `POST /diets/{id}/archive` — terminer un régime actif (`workflow_terminer-diet.mermaid`)
- 🔲 `GET /diets/{id}/bilan` — bilan nutritionnel de la période (params : `period`, `date`, `startDate`)

### MealsController
- 🔲 `POST /meals` — créer un repas (ponctuel ou sauvegardé)
- 🔲 `GET /meals` — lister ses repas (filtre : `?saved=true`, `?date=`)
- 🔲 `GET /meals/{id}` — détail d'un repas
- 🔲 `PATCH /meals/{id}` — modifier les propriétés d'un repas (name, mealType, notes, consumedAt)
- 🔲 `DELETE /meals/{id}` — supprimer un repas
- 🔲 `POST /meals/{id}/items` — ajouter un MealItem à un repas
- 🔲 `DELETE /meals/{id}/items/{itemId}` — retirer un MealItem d'un repas

### FoodItemsController
- 🔲 `GET /food-items?search={motclé}` — rechercher un aliment

### Middleware
- 🔲 Validation JWT Keycloak (vérification signature + audience + expiration)
- 🔲 Extraction `sub` → résolution `User.KeycloakId` → `User.Id` (middleware ou extension)
- 🔲 Gestion globale des erreurs (middleware exception → codes HTTP)
- 🔲 Logging des requêtes

### Auth & Abonnements — API (ajout 2026-05-02)
- 🔲 `GET /diet-plans/templates` — lister les templates partagés (Pro + Business uniquement)
- 🔲 `POST /admin/diet-plans/templates` — créer un template (rôle `admin` uniquement)
- 🔲 `PUT /admin/diet-plans/templates/{id}` — modifier un template (rôle `admin` uniquement)
- 🔲 Politique d'autorisation `RequireRole("admin")` — appliquée sur les endpoints `/admin/**`
- 🔲 Réponses 403 — tier insuffisant + message explicite (`"This feature requires a Pro subscription"`)

### AdminController — Back-office (ajout 2026-05-02)
- 🔲 `GET /admin/dashboard` — KPIs consolidés (utilisateurs par tier, activité, grace period)
- 🔲 `GET /admin/system/health` — statut jobs OFF import + purge RGPD + count FoodItems
- 🔲 `DELETE /admin/diet-plans/templates/{id}` — supprimer un template (rôle `admin` uniquement)

### AdminService — Application (ajout 2026-05-02)
- 🔲 Agréger KPIs utilisateurs (total, par tier, nouveaux 7 derniers jours)
- 🔲 Agréger métriques activité (diets actives, repas 7j, comptes en grace period)
- 🔲 Agréger santé système depuis tables Hangfire (HangFire.Job + HangFire.State)

### OpenAPI / Swagger UI (ajout 2026-05-02)
- 🔲 Configurer `AddSwaggerGen` — titre, version, sécurité JWT Bearer
- 🔲 Activer `UseSwagger` + `UseSwaggerUI` uniquement hors production
- 🔲 Activer les commentaires XML (`<GenerateDocumentationFile>true</GenerateDocumentationFile>`) sur les projets API et Application
- 🔲 Exclure le dashboard Hangfire (`/hangfire`) de la spec OpenAPI

---

## 5. Gaps identifiés ⚠️

| # | Gap | Impact | Action requise |
|---|---|---|---|
| G1 | **Terminer une Diet** — aucun workflow ni endpoint défini | ✅ Résolu — `workflow_terminer-diet.mermaid` + `POST /diets/{id}/archive`. EndDate imposée système (= aujourd'hui) | — |
| G2 | **Ajouter une WeightEntry** — aucun workflow défini | ✅ Résolu — `workflow_gestion-poids.mermaid`. MeasuredAt = aujourd'hui par défaut, modifiable. Une seule entrée par date (409 si doublon) | — |
| G3 | **Mettre à jour le profil** — aucun workflow défini | ✅ Résolu — `workflow_mise-a-jour-profil.mermaid`. Tous les champs modifiables (PATCH sémantique). `DietaryPreferences` sans impact métier en v1 | — |
| G4 | **Supprimer un SavedFoodItem** — endpoint manquant | ✅ Résolu — dans `workflow_mise-a-jour-profil.mermaid`. `DELETE /users/me/saved-food-items/{id}` → 204 No Content | — |
| G5 | **RGPD** — suppression compte + export données | ✅ Résolu — `workflow_rgpd.mermaid` (4 parties : export, soft delete + Keycloak disable, réactivation, purge job). Connexion Keycloak Admin documentée dans `infrastructure-keycloak-admin.md` | — |

---

## 6. Tests

### Configuration couverture de code
- 🔲 `coverlet.collector` installé dans les 3 projets de test (Domain, Application, Infrastructure)
- 🔲 `tests/coverage.runsettings` créé (format Cobertura, exclusion des projets Tests)
- 🔲 Seuils définis : Domain 90% · Application 80% · Infrastructure 70% · API 70%
- 🔲 Commande de génération du rapport documentée (`reportgenerator`)
- 🔲 Étape couverture ajoutée dans le workflow CI

### Tests unitaires (couche Domain)

#### Aggregate Roots
- 🔲 `User` — UserId non vide, SubscriptionTier valide, UpdateProfile validations
- 🔲 `DietPlan` — template : UserId null obligatoire · personnel : UserId requis · invariants DietType/Goal
- 🔲 `Diet` — constructeur → Active · EnsureEditable bloque Active/Archived/Cancelled · ChangeDietStatus transitions · EndDate posée sur Archived et Cancelled
- 🔲 `Meal` — au moins 1 MealItem · UserId non vide · RemoveMealItem refuse si <= 1 item · ChangeConsumedAt valide
- 🔲 `FoodItem` — UpdateFromImport validations · setters internes uniquement

#### Entités enfants
- 🔲 `WeightEntry` — poids > 0 · measuredAt non default · Update() valide
- 🔲 `MealItem` — mealId/foodItemId non vides · quantité > 0 · NutritionInfo non null
- 🔲 `SavedFoodItem` — userId/foodItemId non vides

#### Value Objects
- 🔲 `MacroDistribution` — invariant somme = 100%
- 🔲 `NutritionInfo` — calcul snapshot (calories/protéines/glucides/lipides × quantité)
- 🔲 `NutritionNeeds` — calcul BMR Mifflin-St Jeor · calcul TDEE

### Tests d'intégration (couche Infrastructure)
- 🔲 Repositories avec Testcontainers (PostgreSQL réel)
- 🔲 Cache Redis
- 🔲 Job import OFF (dump test)

### Tests API (couche API)
- 🔲 Tous les endpoints — cas nominaux + cas d'erreur
- 🔲 Validation JWT

---

*Dernière mise à jour : 2026-04-28 — Étape 8 (validation cohérence)*
