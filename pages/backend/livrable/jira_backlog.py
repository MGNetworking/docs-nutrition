# jira_backlog.py — Backlog complet projet nutrition-manager (backend)
# Dernière mise à jour : 2026-05-24
# Source de vérité : docs/backend/livrable/jira-backlog-decomposition.md
# Moteur d'import   : python3 playbook/tools/import_jira.py docs/backend/livrable/jira_backlog.py
#
# FORMAT DES TUPLES :
#   EPICS    : (ref, summary, description, label)
#   STORIES  : (ref, summary, description, priority, label, story_points, epic_ref)
#   SUBTASKS : (ref, summary, description, priority, label, story_ref)
#
# PLAGE DE REFS BACKEND : EPIC-001→099 | STORY-001→099 | SUB-001→299

MODULE = "backend"
MODE   = "create"

# ── Epics ──────────────────────────────────────────────────────────────────────

EPICS = [
    ("EPIC-001", "Domain Layer",         "Entités métier, value objects, enums et invariants. Zéro dépendance externe.", "domain"),
    ("EPIC-002", "Application Layer",    "Services applicatifs et DTOs. Orchestre les use cases depuis le domaine.",     "application"),
    ("EPIC-003", "Infrastructure Layer", "EF Core, repositories, cache Redis, jobs Hangfire et migrations.",             "infrastructure"),
    ("EPIC-004", "API Layer",            "Controllers REST et middleware. Expose les services applicatifs.",              "api"),
    ("EPIC-005", "Tests",                "Tests d'intégration Infrastructure (Testcontainers) et tests API end-to-end (WebApplicationFactory). Les tests unitaires Domain et Application sont dans leurs Epics respectifs.", "tests"),
]

# ── Stories ────────────────────────────────────────────────────────────────────

STORIES = [
    # ── Domain (EPIC-001) ────────────────────────────────────────────────────────
    ("STORY-001", "Aggregate Roots",
     "Implémenter les 5 Aggregate Roots dans src/NutritionApi.Domain/Entity/. Chaque entité expose un constructeur public avec validation + un constructeur privé vide pour EF Core. Les méthodes de mutation valident leurs préconditions via ArgumentException ou InvalidOperationException.",
     "Medium", "domain", 5, "EPIC-001"),

    ("STORY-002", "Entités Enfants",
     "Implémenter les 3 entités enfants dans src/NutritionApi.Domain/Entity/. Chaque entité enfant possède un constructeur privé vide pour EF Core et est supprimée en cascade avec son Aggregate Root parent.",
     "Medium", "domain", 3, "EPIC-001"),

    ("STORY-003", "Value Objects Domaine",
     "Implémenter les 3 Value Objects immuables dans src/NutritionApi.Domain/ValueObjects/. Pas d'identité propre, égalité par valeur, invariants validés dans le constructeur.",
     "Medium", "domain", 3, "EPIC-001"),

    ("STORY-004", "Enums Domaine",
     "Déclarer les 8 enums du modèle domaine dans src/NutritionApi.Domain/Enums/. Chaque enum expose une valeur Unknown = 0 utilisée uniquement par EF Core via le constructeur privé vide.",
     "Medium", "domain", 2, "EPIC-001"),

    ("STORY-005", "Invariants Domaine",
     "Implémenter les 5 invariants métier du domaine. Les invariants intra-agrégat sont dans les entités Domain. Les invariants cross-agrégat (unicité Diet active, doublon SavedFoodItem) sont dans les Application Services correspondants.",
     "High", "domain", 5, "EPIC-001"),

    ("STORY-028", "Abonnements & Templates — Domaine",
     "Ajouter SubscriptionTier sur User (Free par défaut), IsTemplate sur DietPlan (false par défaut), UserId nullable sur DietPlan (null si template). Enum SubscriptionTier : Free, Pro, Business.",
     "High", "hors-scope", 3, "EPIC-001"),

    # ── Application (EPIC-002) ───────────────────────────────────────────────────
    ("STORY-006", "UserService",
     "Fichier : src/NutritionApi.Application/Services/UserService.cs. Dépendances injectées : IUserRepository, IWeightEntryRepository. Gère la création de profil, la mise à jour et l'ajout de pesées.",
     "Medium", "application", 3, "EPIC-002"),

    ("STORY-007", "DietPlanService",
     "Fichier : src/NutritionApi.Application/Services/DietPlanService.cs. Dépendances : IDietPlanRepository. CRUD complet sur les plans alimentaires réutilisables d'un utilisateur.",
     "Medium", "application", 3, "EPIC-002"),

    ("STORY-008", "DietService",
     "Fichier : src/NutritionApi.Application/Services/DietService.cs. Dépendances : IDietRepository, IDietPlanRepository, IUserRepository, IWeightEntryRepository. Gère le lancement (snapshot + calcul BMR/TDEE), la clôture et la déduction de Diet par date.",
     "High", "application", 8, "EPIC-002"),

    ("STORY-009", "MealService",
     "Fichier : src/NutritionApi.Application/Services/MealService.cs. Dépendances : IMealRepository, IFoodItemRepository. Gère la création de repas avec calcul NutritionInfo, la liste des repas sauvegardés et la suppression.",
     "Medium", "application", 3, "EPIC-002"),

    ("STORY-010", "FoodItemService",
     "Fichier : src/NutritionApi.Application/Services/FoodItemService.cs. Dépendances : IFoodItemRepository, ISavedFoodItemRepository, IFoodCacheService. Recherche Redis → PostgreSQL, sauvegarde et gestion de la liste personnelle.",
     "Medium", "application", 3, "EPIC-002"),

    ("STORY-011", "NutritionService",
     "Fichier : src/NutritionApi.Application/Services/NutritionService.cs. Dépendances : IMealRepository, IWeightEntryRepository, IDietRepository. Agrège les MealItems par jour sur la période de la Diet et inclut les WeightEntries.",
     "High", "application", 5, "EPIC-002"),

    ("STORY-012", "DTOs Application",
     "Fichier : src/NutritionApi.Application/DTOs/. Un DTO Request (input) et un DTO Response (output) par use case. NutritionBilanResponse inclut dailyData, weightEntries et summary.",
     "Medium", "application", 3, "EPIC-002"),

    ("STORY-029", "SubscriptionGuard — Vérifications tier",
     "Fichier : src/NutritionApi.Application/Guards/SubscriptionGuard.cs. Helper centralisé CheckLimit(tier, count, freeLimit, proLimit) — lève ForbiddenException (403) si limite atteinte. Appelé dans DietPlanService, MealService, FoodItemService, NutritionService.",
     "High", "hors-scope", 5, "EPIC-002"),

    ("STORY-033", "AdminService — KPIs & métriques système",
     "Fichier : src/NutritionApi.Application/Services/AdminService.cs. Agrège KPIs utilisateurs (total, par tier, nouveaux 7j), métriques activité (diets actives, repas 7j, grace period) et santé système depuis les tables HangFire.Job et HangFire.State.",
     "Medium", "hors-scope", 3, "EPIC-002"),

    # ── Infrastructure (EPIC-003) ────────────────────────────────────────────────
    ("STORY-039", "Setup environnement de développement local",
     "Prérequis à tout le reste. Créer infra/dev/docker-compose.yml (PostgreSQL 16, Keycloak 24, Redis 7), infra/dev/.env.example et infra/keycloak/realm-export-dev.json (realm nutrition, 2 clients, 2 utilisateurs de test). Voir infrastructure-setup.md.",
     "High", "infrastructure", 3, "EPIC-003"),

    ("STORY-013", "EF Core Configurations",
     "Fichier : src/NutritionApi.Infrastructure/Configurations/. Fluent API uniquement — pas d'annotations sur les entités Domain. MacroDistribution et NutritionInfo en owned entities. Index unique sur WeightEntry(UserId+MeasuredAt) et SavedFoodItem(UserId+FoodItemId).",
     "Medium", "infrastructure", 5, "EPIC-003"),

    ("STORY-014", "Repositories",
     "Interfaces dans src/NutritionApi.Application/Interfaces/. Implémentations dans src/NutritionApi.Infrastructure/Repositories/. Chaque repository expose les méthodes CRUD minimales nécessaires aux services applicatifs.",
     "Medium", "infrastructure", 5, "EPIC-003"),

    ("STORY-015", "Cache Redis",
     "Interface IFoodCacheService dans Application/Interfaces/. Implémentation FoodCacheService dans Infrastructure/Cache/. Sérialisation JSON + TTL configurable via appsettings.",
     "Medium", "hors-scope", 3, "EPIC-003"),

    ("STORY-016", "Job Import Open Food Facts",
     "Fichier : src/NutritionApi.Infrastructure/Jobs/OffImportJob.cs. Téléchargement dump OFF, traitement par batch (INSERT/UPDATE FoodItem), planification Hangfire cron 0 3 * * *, retry automatique.",
     "High", "hors-scope", 13, "EPIC-003"),

    ("STORY-017", "Job Purge RGPD",
     "Fichier : src/NutritionApi.Infrastructure/Jobs/RgpdPurgeJob.cs. Sélection Users (DeletedAt <= aujourd'hui - 30j), cascade DELETE PostgreSQL, suppression Keycloak Admin, retry Polly si Keycloak indisponible.",
     "High", "hors-scope", 8, "EPIC-003"),

    ("STORY-018", "Migrations Base de Données",
     "Commande : dotnet ef migrations add InitialCreate --project src/NutritionApi.Infrastructure --startup-project src/NutritionApi.Api. Vérifier toutes les tables, index et owned entities dans le fichier généré.",
     "Medium", "infrastructure", 2, "EPIC-003"),

    ("STORY-030", "Abonnements & Templates — Infrastructure",
     "Mise à jour DietPlanConfiguration : UserId nullable, IsTemplate mappé, index sur IsTemplate. Seed des 3 templates initiaux : Équilibré (50/30/20), Protéiné (40/30/30), Keto (5/70/25).",
     "Medium", "hors-scope", 3, "EPIC-003"),

    ("STORY-036", "Configuration Hangfire",
     "Enregistrer Hangfire avec PostgreSqlStorage (schéma HangFire, PrepareSchemaIfNecessary=true). Sécuriser /hangfire via IDashboardAuthorizationFilter (claim rôle admin). Enregistrer OffImportJob (03h00) et RgpdPurgeJob (03h30) au démarrage.",
     "High", "hors-scope", 3, "EPIC-003"),

    ("STORY-040", "Dockerfile + config connexion K3s",
     "Dockerfile multi-stage : SDK .NET 10 pour le build, aspnet:10.0 pour le runtime. Manifests K8s dans infra/k8s/ : configmap.yaml (URLs non-sensibles), secret.yaml.example (valeurs vides), deployment.yaml, service.yaml, ingress.yaml (Traefik TLS). PostgreSQL/Keycloak/Redis sont dans le projet infra K3s séparé.",
     "Medium", "infrastructure", 3, "EPIC-003"),

    ("STORY-041", "CI/CD GitHub Actions — déploiement automatique sur K3s",
     "Prérequis : STORY-040 terminé et premier déploiement manuel validé. Service Account K3s github-actions-deployer (RoleBinding edit, namespace nutrition). Secret KUBECONFIG_B64 dans GitHub. Workflow deploy.yml : build → push GHCR → kubectl set image → rollout status.",
     "Medium", "infrastructure", 3, "EPIC-003"),

    # ── API (EPIC-004) ───────────────────────────────────────────────────────────
    ("STORY-019", "UsersController",
     "Fichier : src/NutritionApi.Api/Controllers/UsersController.cs. Route /users/me. 12 endpoints : profil (POST/GET/PUT), pesées (POST/GET/PUT), aliments sauvegardés (GET/POST/DELETE), et endpoints RGPD (DELETE/reactivate/export).",
     "High", "api", 8, "EPIC-004"),

    ("STORY-020", "DietPlansController",
     "Fichier : src/NutritionApi.Api/Controllers/DietPlansController.cs. Route /diet-plans. 5 endpoints : CRUD plans personnels + POST /{id}/launch qui crée une Diet active avec CalorieTarget calculé.",
     "Medium", "api", 5, "EPIC-004"),

    ("STORY-021", "DietsController",
     "Fichier : src/NutritionApi.Api/Controllers/DietsController.cs. Route /diets. 5 endpoints : GET active, GET historique, GET détail, POST archive (clôture la Diet), GET bilan nutritionnel.",
     "Medium", "api", 5, "EPIC-004"),

    ("STORY-022", "MealsController",
     "Fichier : src/NutritionApi.Api/Controllers/MealsController.cs. Route /meals. 6 endpoints : CRUD repas + POST /{id}/items (ajouter MealItem) + DELETE /{id}/items/{itemId} (retirer MealItem, 400 si dernier).",
     "Medium", "api", 5, "EPIC-004"),

    ("STORY-023", "FoodItemsController",
     "Fichier : src/NutritionApi.Api/Controllers/FoodItemsController.cs. Un seul endpoint : GET /food-items?search={keyword}. Retourne List<FoodItemSearchResponse> via Redis → PostgreSQL.",
     "Medium", "api", 1, "EPIC-004"),

    ("STORY-024", "Middleware HTTP",
     "3 middlewares dans src/NutritionApi.Api/Middleware/. JWT : validation signature Keycloak + extraction sub → User.KeycloakId. Exceptions : ArgumentException→400, Unauthorized→401, Forbidden→403, NotFound→404, Conflict→409, autres→500. Logging : méthode + path + status + durée.",
     "High", "api", 3, "EPIC-004"),

    ("STORY-031", "Auth & Templates — Nouveaux endpoints",
     "GET /diet-plans/templates (Pro/Business uniquement), POST et PUT /admin/diet-plans/templates (rôle admin). Extraction claim sub → User.KeycloakId dans le middleware JWT. Réponses 403 avec message explicite sur le tier requis.",
     "High", "hors-scope", 5, "EPIC-004"),

    ("STORY-034", "AdminController — Dashboard & Santé système",
     "Fichier : src/NutritionApi.Api/Controllers/AdminController.cs. GET /admin/dashboard (KPIs consolidés), GET /admin/system/health (statut jobs Hangfire + count FoodItems), DELETE /admin/diet-plans/templates/{id}. Rôle admin Keycloak requis sur tous les endpoints.",
     "Medium", "hors-scope", 3, "EPIC-004"),

    ("STORY-037", "OpenAPI / Swagger UI",
     "Fichier : src/NutritionApi.Api/Program.cs. AddSwaggerGen avec titre, version et sécurité JWT Bearer. UseSwagger + UseSwaggerUI uniquement hors production. GenerateDocumentationFile=true sur les projets API et Application. Exclure /hangfire de la spec.",
     "Medium", "api", 2, "EPIC-004"),

    # ── Tests ────────────────────────────────────────────────────────────────────
    ("STORY-025", "Tests Unitaires Domain",
     "Fichier : tests/NutritionApi.Domain.Tests/. xUnit, TDD — écrits avant le code de production. Couvrir : MacroDistribution (somme 100%), NutritionInfo (calcul snapshot), Diet (immutabilité Active/Completed, StartDate système), Meal (aucun MealItem → ArgumentException), SavedFoodItem et WeightEntry (validations constructeur).",
     "High", "tests", 5, "EPIC-001"),

    ("STORY-038", "Tests Unitaires Application",
     "Fichier : tests/NutritionApi.Application.Tests/. xUnit + Moq, TDD. Couvrir les cas d'erreur métier : WeightEntry doublon (409), lancement Diet sans WeightEntry (422), lancement avec Diet active (409), Meal sans item, SavedFoodItem doublon (409), agrégation bilan journalier correcte.",
     "High", "tests", 5, "EPIC-002"),

    ("STORY-026", "Tests Intégration Infrastructure",
     "Fichier : tests/NutritionApi.Infrastructure.Tests/. Testcontainers PostgreSQL + Redis. Tester les 7 repositories avec vraie base de données, vérifier les contraintes d'unicité en base, tester FoodCacheService et le job import OFF.",
     "Medium", "tests", 8, "EPIC-005"),

    ("STORY-027", "Tests API Endpoints",
     "Fichier : tests/NutritionApi.Api.Tests/. WebApplicationFactory + Testcontainers. Couvrir chaque endpoint : cas nominal (201/200/204) + cas d'erreur (400/401/403/404/409). Tester la validation JWT (absent → 401, expiré → 401, valide → 200).",
     "Medium", "tests", 8, "EPIC-005"),

    ("STORY-032", "Tests — Abonnements & Templates",
     "Couvrir les blocages par tier : création plan Free (403 au 3ème), accès templates Free (403), période bilan clampée selon tier (7j/1an/illimité), ajout SavedFoodItem Free (403 au 11ème).",
     "Medium", "hors-scope", 3, "EPIC-005"),

    ("STORY-035", "Tests — Admin back-office",
     "Couvrir les endpoints admin : données agrégées correctes (GET /admin/dashboard), 403 si rôle admin absent, statuts jobs corrects (GET /admin/system/health).",
     "Medium", "hors-scope", 2, "EPIC-005"),
]

# ── Sub-tasks ──────────────────────────────────────────────────────────────────

SUBTASKS = [
    # ── STORY-001 : Aggregate Roots ─────────────────────────────────────────────
    ("SUB-001", "Implémenter entité User",
     "Fichier : src/NutritionApi.Domain/Entity/User.cs. Propriétés : Id (Guid init), KeycloakId (string), BirthDate (DateOnly), Gender, Height (float cm), ActivityLevel, Allergies (List<Allergen>), DietaryPreferences (List<string>), CreatedAt (DateTime.UtcNow imposé système), DeletedAt (DateTime? nullable). Comportements : ChangeBirthDate, ChangeGender, ChangeActivityLevel, ChangeHeight, AddAllergen (doublon interdit), RemoveAllergen, AddDietaryPreference (doublon interdit), RemoveDietaryPreference, MarkAsDeleted (fixe DeletedAt = DateTime.UtcNow).",
     "Medium", "domain", "STORY-001"),

    ("SUB-002", "Implémenter entité DietPlan",
     "Fichier : src/NutritionApi.Domain/Entity/DietPlan.cs. Propriétés : Id, UserId (Guid?), IsTemplate (bool, false par défaut), Name, DietType, Goal, TargetWeight (float kg), MacroDistribution (VO). Comportements : Rename, ChangeDietType, ChangeGoal, SetTargetWeight, AdjustMacros. Pas de CalorieTarget — ce calcul dépend du poids réel au lancement (appartient à DietService). Toujours modifiable — aucun lien avec les Diet déjà lancées.",
     "Medium", "domain", "STORY-001"),

    ("SUB-003", "Implémenter entité Diet",
     "Fichier : src/NutritionApi.Domain/Entity/Diet.cs. Propriétés : Id, UserId, Name, DietType, Goal, TargetWeight, CalorieTarget (int), MacroDistribution, DietStatus, StartDate (DateOnly), EndDate (DateOnly?). StartDate = DateOnly.FromDateTime(DateTime.UtcNow) imposé dans le constructeur. EnsureEditable() privé : lève InvalidOperationException si Active ou Completed — appelé dans Rename, ChangeDietType, ChangeGoal, SetTargetWeight, SetCalorieTarget, AdjustMacros. ChangeDietStatus : bloque si Completed, fixe EndDate automatiquement si Completed.",
     "Medium", "domain", "STORY-001"),

    ("SUB-004", "Implémenter entité Meal",
     "Fichier : src/NutritionApi.Domain/Entity/Meal.cs. Propriétés : Id, UserId, Name, MealType, Notes (string?), MealItems (List<MealItem>), ConsumedAt (DateTime fourni utilisateur), IsSaved (bool). Constructeur : lève ArgumentException si mealItems null ou vide. Comportements : Rename, ChangeNote (null = suppression), ChangeMealType, AddMealItem, RemoveMealItem (lève InvalidOperationException si Count <= 1).",
     "Medium", "domain", "STORY-001"),

    ("SUB-005", "Implémenter entité FoodItem",
     "Fichier : src/NutritionApi.Domain/Entity/FoodItem.cs. Propriétés : Id, OffId (string, code-barres OFF), Name, CaloriesPer100g (float), ProteinsPer100g, CarbsPer100g, FatsPer100g, AllergensTags (List<Allergen>), CachedAt (DateTime). Comportement : UpdateFromImport(name, calories, proteins, carbs, fats, allergens) — appelé par le job quotidien, met à jour toutes les valeurs et CachedAt. Table partagée entre tous les utilisateurs.",
     "Medium", "domain", "STORY-001"),

    # ── STORY-002 : Entités Enfants ─────────────────────────────────────────────
    ("SUB-006", "Implémenter entité WeightEntry",
     "Fichier : src/NutritionApi.Domain/Entity/WeightEntry.cs. Propriétés : Id, UserId, Weight (float kg, > 0), MeasuredAt (DateOnly fourni par l'utilisateur — peut être antérieur). Immuable après création — aucun comportement de modification exposé. Supprimé en cascade à la suppression du User.",
     "Medium", "domain", "STORY-002"),

    ("SUB-007", "Implémenter entité MealItem",
     "Fichier : src/NutritionApi.Domain/Entity/MealItem.cs. Propriétés : Id, MealId, FoodItemId, Quantity (float grammes, > 0), Nutrition (NutritionInfo VO). Nutrition est un snapshot calculé à la création : FoodItem.XxxPer100g * (Quantity / 100). Comportements : SetQuantity, SetNutrition. Supprimé en cascade à la suppression du Meal.",
     "Medium", "domain", "STORY-002"),

    ("SUB-008", "Implémenter entité SavedFoodItem",
     "Fichier : src/NutritionApi.Domain/Entity/SavedFoodItem.cs. Propriétés : Id, UserId, FoodItemId, SavedAt (DateTime.UtcNow imposé système). Immuable après création. Invariant cross-agrégat : un même FoodItemId ne peut être sauvegardé qu'une fois par User — vérifié dans FoodItemService via ISavedFoodItemRepository.ExistsAsync(userId, foodItemId). Supprimé en cascade à la suppression du User.",
     "Medium", "domain", "STORY-002"),

    # ── STORY-003 : Value Objects ───────────────────────────────────────────────
    ("SUB-009", "Implémenter MacroDistribution",
     "Fichier : src/NutritionApi.Domain/ValueObjects/MacroDistribution.cs. Propriétés : ProteinPercentage (int), CarbPercentage (int), FatPercentage (int). Invariant : ProteinPercentage + CarbPercentage + FatPercentage == 100 — lève ArgumentException sinon. Toutes les valeurs >= 0. Appartient à Diet et DietPlan — représente un objectif de répartition en %, pas des grammes.",
     "Medium", "domain", "STORY-003"),

    ("SUB-010", "Implémenter NutritionInfo",
     "Fichier : src/NutritionApi.Domain/ValueObjects/NutritionInfo.cs. Propriétés : Calories (float kcal), Proteins (int g), Carbs (int g), Fats (int g). Toutes les valeurs >= 0. Calcul snapshot : FoodItem.XxxPer100g * (Quantity / 100). Appartient à MealItem — représente ce qui a réellement été consommé, différent de MacroDistribution (objectif %).",
     "Medium", "domain", "STORY-003"),

    ("SUB-011", "Implémenter NutritionNeeds",
     "Fichier : src/NutritionApi.Domain/ValueObjects/NutritionNeeds.cs. Propriétés : Bmr (float kcal), Tdee (float kcal), TargetCalories (float kcal), MacroDistribution (VO). Toutes les valeurs > 0. Non persisté — calculé à la demande par DietService.CalculateNutritionNeeds(user, currentWeight).",
     "Medium", "domain", "STORY-003"),

    # ── STORY-004 : Enums ───────────────────────────────────────────────────────
    ("SUB-012", "Déclarer enum ActivityLevel",
     "Fichier : src/NutritionApi.Domain/Enums/ActivityLevel.cs. Valeurs : Unknown = 0, Sedentary, LightlyActive, ModeratelyActive, VeryActive, ExtremelyActive. Coefficient NAP associé pour DietService : 1.2 / 1.375 / 1.55 / 1.725 / 1.9.",
     "Medium", "domain", "STORY-004"),

    ("SUB-013", "Déclarer enum Goal",
     "Fichier : src/NutritionApi.Domain/Enums/Goal.cs. Valeurs : Unknown = 0, WeightLoss, Maintenance, WeightGain. Ajustement CalorieTarget dans DietService : WeightLoss → TDEE * 0.82, Maintenance → TDEE, WeightGain → TDEE * 1.18.",
     "Medium", "domain", "STORY-004"),

    ("SUB-014", "Déclarer enum MealType",
     "Fichier : src/NutritionApi.Domain/Enums/MealType.cs. Valeurs : Unknown = 0, Breakfast, Lunch, Dinner, Snack.",
     "Medium", "domain", "STORY-004"),

    ("SUB-015", "Déclarer enum DietType",
     "Fichier : src/NutritionApi.Domain/Enums/DietType.cs. Valeurs : Unknown = 0, Balanced, HighProtein, Keto, Mediterranean, LowCarb, Vegetarian, Vegan, Custom.",
     "Medium", "domain", "STORY-004"),

    ("SUB-016", "Déclarer enum DietStatus",
     "Fichier : src/NutritionApi.Domain/Enums/DietStatus.cs. Valeurs : Unknown = 0, Active, Inactive, Archived. Active = Diet en cours. Archived = Diet clôturée (EndDate renseignée).",
     "Medium", "domain", "STORY-004"),

    ("SUB-017", "Déclarer enum Gender",
     "Fichier : src/NutritionApi.Domain/Enums/Gender.cs. Valeurs : Male, Female, Other. Utilisé dans le calcul BMR (Mifflin-St Jeor) : +5 pour Male, -161 pour Female.",
     "Medium", "domain", "STORY-004"),

    ("SUB-018", "Déclarer enum Allergen",
     "Fichier : src/NutritionApi.Domain/Enums/Allergen.cs. 14 valeurs EU : Gluten, Crustaceans, Eggs, Fish, Peanuts, Soybeans, Milk, Nuts, Celery, Mustard, SesameSeeds, SulphurDioxide, Lupin, Molluscs. Calqué sur les allergènes normalisés Open Food Facts.",
     "Medium", "domain", "STORY-004"),

    # ── STORY-005 : Invariants ──────────────────────────────────────────────────
    ("SUB-019", "Bloquer lancement si Diet active existe déjà",
     "Cross-agrégat — implémenter dans DietService.LaunchAsync (src/NutritionApi.Application/Services/DietService.cs). Avant création : IDietRepository.GetActiveByUserIdAsync(userId). Si résultat non null → lève ConflictException (409). Message : User already has an active diet. Archive it before launching a new one.",
     "High", "domain", "STORY-005"),

    ("SUB-020", "Valider présence d'au moins un MealItem",
     "Intra-agrégat — dans src/NutritionApi.Domain/Entity/Meal.cs. Constructeur : lève ArgumentException si mealItems == null ou Count == 0. RemoveMealItem : lève InvalidOperationException(Meal must contain at least one MealItem.) si MealItems.Count <= 1.",
     "Medium", "domain", "STORY-005"),

    ("SUB-021", "Interdire doublon SavedFoodItem pour un User",
     "Cross-agrégat — implémenter dans FoodItemService.SaveFoodItemAsync (src/NutritionApi.Application/Services/FoodItemService.cs). Avant création : ISavedFoodItemRepository.ExistsAsync(userId, foodItemId). Si true → lève ConflictException (409). Message : This food item is already saved.",
     "Medium", "domain", "STORY-005"),

    ("SUB-022", "Imposer Diet.StartDate à la date du lancement",
     "Intra-agrégat — dans src/NutritionApi.Domain/Entity/Diet.cs. Dans le constructeur : StartDate = DateOnly.FromDateTime(DateTime.UtcNow). Pas de setter public — non modifiable après création.",
     "High", "domain", "STORY-005"),

    ("SUB-023", "Interdire modification Diet après lancement",
     "Intra-agrégat — dans src/NutritionApi.Domain/Entity/Diet.cs. Méthode privée EnsureEditable() : lève InvalidOperationException($Diet cannot be modified when status is {StatusDiet}.) si StatusDiet == Active ou Completed. Appelée dans : Rename, ChangeDietType, ChangeGoal, SetTargetWeight, SetCalorieTarget, AdjustMacros. ChangeDietStatus ne l'appelle pas (transitions de statut restent possibles).",
     "High", "domain", "STORY-005"),

    # ── STORY-006 : UserService ─────────────────────────────────────────────────
    ("SUB-024", "Créer profil utilisateur avec première WeightEntry",
     "Méthode : UserService.CreateProfileAsync(CreateUserProfileRequest dto). Vérifier que KeycloakId n'existe pas déjà (409 si doublon). Créer User (SubscriptionTier = Free) + WeightEntry initiale en une transaction. Retourner UserProfileResponse.",
     "Medium", "application", "STORY-006"),

    ("SUB-025", "Mettre à jour profil utilisateur",
     "Méthode : UserService.UpdateProfileAsync(Guid userId, UpdateUserProfileRequest dto). Appeler les méthodes domaine : ChangeBirthDate, ChangeGender, ChangeHeight, ChangeActivityLevel, AddAllergen/RemoveAllergen, AddDietaryPreference/RemoveDietaryPreference selon les champs fournis. IUserRepository.UpdateAsync.",
     "Medium", "application", "STORY-006"),

    ("SUB-026", "Ajouter WeightEntry utilisateur",
     "Méthode : UserService.AddWeightEntryAsync(Guid userId, AddWeightEntryRequest dto). Vérifier IWeightEntryRepository.ExistsAsync(userId, dto.MeasuredAt) — lève ConflictException (409) si doublon. Créer et persister la WeightEntry.",
     "Medium", "application", "STORY-006"),

    # ── STORY-007 : DietPlanService ─────────────────────────────────────────────
    ("SUB-027", "Créer un DietPlan",
     "Méthode : DietPlanService.CreateAsync(Guid userId, CreateDietPlanRequest dto). Créer DietPlan avec UserId = userId, IsTemplate = false. IDietPlanRepository.AddAsync. Retourner DietPlanResponse.",
     "Medium", "application", "STORY-007"),

    ("SUB-028", "Modifier un DietPlan",
     "Méthode : DietPlanService.UpdateAsync(Guid userId, Guid dietPlanId, UpdateDietPlanRequest dto). Vérifier appartenance (dietPlan.UserId == userId) — 403 sinon. Appeler Rename, ChangeDietType, ChangeGoal, SetTargetWeight, AdjustMacros selon les champs fournis. IDietPlanRepository.UpdateAsync.",
     "Medium", "application", "STORY-007"),

    ("SUB-029", "Supprimer un DietPlan",
     "Méthode : DietPlanService.DeleteAsync(Guid userId, Guid dietPlanId). Vérifier appartenance — 403 sinon. IDietPlanRepository.DeleteAsync.",
     "Medium", "application", "STORY-007"),

    ("SUB-030", "Lister les DietPlans d'un utilisateur",
     "Méthode : DietPlanService.GetAllForUserAsync(Guid userId). IDietPlanRepository.GetAllByUserIdAsync(userId). Retourner List<DietPlanResponse>.",
     "Medium", "application", "STORY-007"),

    # ── STORY-008 : DietService ─────────────────────────────────────────────────
    ("SUB-031", "Lancer DietPlan et créer Diet active",
     "Méthode : DietService.LaunchAsync(Guid userId, Guid dietPlanId). 1) IDietRepository.GetActiveByUserIdAsync → 409 si Diet active existante. 2) IWeightEntryRepository.GetLatestByUserIdAsync → 422 si aucune WeightEntry. 3) Calculer NutritionNeeds. 4) Créer Diet snapshot depuis DietPlan + CalorieTarget calculé. IDietRepository.AddAsync.",
     "High", "application", "STORY-008"),

    ("SUB-032", "Calculer BMR TDEE CalorieTarget au lancement",
     "Méthode interne : DietService.CalculateNutritionNeeds(User user, float currentWeight). BMR Mifflin-St Jeor : Homme = (10*P) + (6.25*T) - (5*A) + 5, Femme = -161. TDEE = BMR * NAP (ActivityLevel). CalorieTarget : WeightLoss = TDEE*0.82, Maintenance = TDEE, WeightGain = TDEE*1.18. Retourner NutritionNeeds (VO non persisté).",
     "High", "application", "STORY-008"),

    ("SUB-033", "Terminer une Diet active",
     "Méthode : DietService.ArchiveAsync(Guid userId, Guid dietId). Vérifier appartenance + StatusDiet == Active (404 / 400 sinon). diet.ChangeDietStatus(DietStatus.Archived) → EndDate fixée automatiquement. IDietRepository.UpdateAsync.",
     "Medium", "application", "STORY-008"),

    ("SUB-034", "Déduire Diet active à la date d'un Meal",
     "Méthode : DietService.GetDietAtDateAsync(Guid userId, DateTime date). Récupérer les Diets du User et filtrer : StartDate <= date && (EndDate == null || EndDate >= date). Retourner la Diet correspondante ou null. Utilisé par NutritionService pour le bilan.",
     "Medium", "application", "STORY-008"),

    # ── STORY-009 : MealService ─────────────────────────────────────────────────
    ("SUB-035", "Créer Meal avec calcul NutritionInfo",
     "Méthode : MealService.CreateAsync(Guid userId, CreateMealRequest dto). Pour chaque item : IFoodItemRepository.GetByIdAsync + calculer NutritionInfo snapshot (FoodItem.XxxPer100g * quantity / 100). Créer Meal avec la liste MealItem calculés (400 si aucun item). IMealRepository.AddAsync.",
     "Medium", "application", "STORY-009"),

    ("SUB-036", "Lister repas sauvegardés",
     "Méthode : MealService.GetSavedMealsAsync(Guid userId). IMealRepository.GetSavedByUserIdAsync(userId). Retourner List<MealResponse>.",
     "Medium", "application", "STORY-009"),

    ("SUB-037", "Supprimer un Meal",
     "Méthode : MealService.DeleteAsync(Guid userId, Guid mealId). Vérifier appartenance (meal.UserId == userId) — 403 sinon. IMealRepository.DeleteAsync (cascade sur MealItems).",
     "Medium", "application", "STORY-009"),

    # ── STORY-010 : FoodItemService ─────────────────────────────────────────────
    ("SUB-038", "Rechercher aliment par mot-clé",
     "Méthode : FoodItemService.SearchAsync(string keyword). 1) IFoodCacheService.GetAsync(keyword) — si hit : retourner directement. 2) IFoodItemRepository.SearchByKeywordAsync(keyword) + IFoodCacheService.SetAsync. Retourner List<FoodItemSearchResponse>.",
     "Medium", "application", "STORY-010"),

    ("SUB-039", "Sauvegarder FoodItem dans liste personnelle",
     "Méthode : FoodItemService.SaveFoodItemAsync(Guid userId, Guid foodItemId). Vérifier FoodItem existe (404 sinon). ISavedFoodItemRepository.ExistsAsync(userId, foodItemId) → 409 si doublon. Créer SavedFoodItem (SavedAt = DateTime.UtcNow). ISavedFoodItemRepository.AddAsync.",
     "Medium", "application", "STORY-010"),

    ("SUB-040", "Supprimer SavedFoodItem de la liste personnelle",
     "Méthode : FoodItemService.DeleteSavedFoodItemAsync(Guid userId, Guid savedFoodItemId). Vérifier appartenance — 403 sinon. ISavedFoodItemRepository.DeleteAsync.",
     "Medium", "application", "STORY-010"),

    ("SUB-041", "Lister SavedFoodItems d'un utilisateur",
     "Méthode : FoodItemService.GetSavedFoodItemsAsync(Guid userId). ISavedFoodItemRepository.GetAllByUserIdAsync(userId). Retourner List<FoodItemSearchResponse> avec le détail FoodItem.",
     "Medium", "application", "STORY-010"),

    # ── STORY-011 : NutritionService ────────────────────────────────────────────
    ("SUB-042", "Calculer bilan nutritionnel d'une Diet",
     "Méthode : NutritionService.GetBilanAsync(Guid userId, Guid dietId, BilanPeriod period, ...). Récupérer les Meals du User sur la période (StartDate/EndDate de la Diet). Agréger MealItem.Nutrition par jour → dailyData. Récupérer WeightEntries sur la même période. Retourner NutritionBilanResponse (dailyData + weightEntries + summary avec moyennes).",
     "High", "application", "STORY-011"),

    # ── STORY-012 : DTOs Application ────────────────────────────────────────────
    ("SUB-043", "Créer CreateUserProfileRequest et UserProfileResponse",
     "Fichier : src/NutritionApi.Application/DTOs/. CreateUserProfileRequest : KeycloakId, BirthDate, Gender, Height, ActivityLevel, Allergies, DietaryPreferences, Weight (float, pour la première WeightEntry). UserProfileResponse : tous les champs profil + Bmr/Tdee calculés à la demande.",
     "Medium", "application", "STORY-012"),

    ("SUB-044", "Créer CreateDietPlanRequest et DietPlanResponse",
     "CreateDietPlanRequest : Name, DietType, Goal, TargetWeight, MacroDistribution (ProteinPct, CarbPct, FatPct). DietPlanResponse : Id, UserId, Name, DietType, Goal, TargetWeight, MacroDistribution.",
     "Medium", "application", "STORY-012"),

    ("SUB-045", "Créer LaunchDietPlanRequest et DietResponse",
     "LaunchDietPlanRequest : DietPlanId (seul champ — tout le reste est calculé ou copié). DietResponse : Id, Name, DietType, Goal, TargetWeight, CalorieTarget, MacroDistribution, Status, StartDate, EndDate.",
     "Medium", "application", "STORY-012"),

    ("SUB-046", "Créer CreateMealRequest et MealResponse",
     "CreateMealRequest : Name, MealType, ConsumedAt, Notes?, IsSaved, Items (List avec FoodItemId + Quantity). MealResponse : Id, Name, MealType, ConsumedAt, Notes, IsSaved, Items (avec NutritionInfo par item) + total nutritionnel agrégé.",
     "Medium", "application", "STORY-012"),

    ("SUB-047", "Créer FoodItemSearchResponse",
     "Champs : Id, Name, CaloriesPer100g, ProteinsPer100g, CarbsPer100g, FatsPer100g, AllergensTags.",
     "Medium", "application", "STORY-012"),

    ("SUB-048", "Créer SaveFoodItemRequest",
     "Champs : FoodItemId (Guid).",
     "Medium", "application", "STORY-012"),

    ("SUB-049", "Créer NutritionBilanResponse",
     "dailyData : List<DailyNutrition> — Date + Calories/Proteins/Carbs/Fats agrégés par jour. weightEntries : List<WeightEntryResponse> — MeasuredAt + Weight. summary : CalorieTarget, AverageCalories, AverageProteins, AverageCarbs, AverageFats, StartWeight, CurrentWeight.",
     "Medium", "application", "STORY-012"),

    # ── STORY-013 : EF Core Configurations ─────────────────────────────────────
    ("SUB-050", "Configurer UserConfiguration Fluent API",
     "Fichier : src/NutritionApi.Infrastructure/Configurations/UserConfiguration.cs. HasKey(u => u.Id). HasIndex(u => u.KeycloakId).IsUnique(). Allergies et DietaryPreferences : stocker en colonnes JSON via HasConversion ou table de liaison.",
     "Medium", "infrastructure", "STORY-013"),

    ("SUB-051", "Configurer DietPlanConfiguration Fluent API",
     "Fichier : src/NutritionApi.Infrastructure/Configurations/DietPlanConfiguration.cs. HasKey. HasOne<User>().WithMany().HasForeignKey(d => d.UserId).IsRequired(false) (nullable). OwnsOne(d => d.MacroDistribution) — colonnes MacroDistribution_ProteinPercentage/CarbPercentage/FatPercentage.",
     "Medium", "infrastructure", "STORY-013"),

    ("SUB-052", "Configurer DietConfiguration Fluent API",
     "Fichier : src/NutritionApi.Infrastructure/Configurations/DietConfiguration.cs. HasKey. HasOne<User>().WithMany().HasForeignKey(d => d.UserId). OwnsOne(d => d.MacroDistribution). Colonnes StartDate (DateOnly), EndDate (DateOnly?).",
     "Medium", "infrastructure", "STORY-013"),

    ("SUB-053", "Configurer MealConfiguration Fluent API",
     "Fichier : src/NutritionApi.Infrastructure/Configurations/MealConfiguration.cs. HasKey. HasOne<User>().WithMany().HasForeignKey(m => m.UserId). HasMany(m => m.MealItems).WithOne().HasForeignKey(mi => mi.MealId).OnDelete(DeleteBehavior.Cascade).",
     "Medium", "infrastructure", "STORY-013"),

    ("SUB-054", "Configurer MealItemConfiguration Fluent API",
     "Fichier : src/NutritionApi.Infrastructure/Configurations/MealItemConfiguration.cs. HasKey. OwnsOne(mi => mi.Nutrition) — colonnes Nutrition_Calories/Proteins/Carbs/Fats.",
     "Medium", "infrastructure", "STORY-013"),

    ("SUB-055", "Configurer FoodItemConfiguration Fluent API",
     "Fichier : src/NutritionApi.Infrastructure/Configurations/FoodItemConfiguration.cs. HasKey. HasIndex(f => f.OffId).IsUnique(). HasIndex(f => f.Name) pour la recherche fulltext. AllergensTags : stocker en JSON via HasConversion.",
     "Medium", "infrastructure", "STORY-013"),

    ("SUB-056", "Configurer WeightEntryConfiguration Fluent API",
     "Fichier : src/NutritionApi.Infrastructure/Configurations/WeightEntryConfiguration.cs. HasKey. HasOne<User>().WithMany().HasForeignKey(w => w.UserId).OnDelete(DeleteBehavior.Cascade). HasIndex(w => new { w.UserId, w.MeasuredAt }).IsUnique() — garantit l'unicité en base.",
     "Medium", "infrastructure", "STORY-013"),

    ("SUB-057", "Configurer SavedFoodItemConfiguration Fluent API",
     "Fichier : src/NutritionApi.Infrastructure/Configurations/SavedFoodItemConfiguration.cs. HasKey. HasIndex(s => new { s.UserId, s.FoodItemId }).IsUnique() — doublon interdit. HasOne<User>().WithMany().HasForeignKey(s => s.UserId).OnDelete(DeleteBehavior.Cascade).",
     "Medium", "infrastructure", "STORY-013"),

    ("SUB-058", "Configurer MacroDistribution en owned entity EF Core",
     "Configuré via OwnsOne dans DietConfiguration et DietPlanConfiguration. Colonnes générées : MacroDistribution_ProteinPercentage, MacroDistribution_CarbPercentage, MacroDistribution_FatPercentage.",
     "Medium", "infrastructure", "STORY-013"),

    ("SUB-059", "Configurer NutritionInfo en owned entity EF Core",
     "Configuré via OwnsOne dans MealItemConfiguration. Colonnes générées : Nutrition_Calories, Nutrition_Proteins, Nutrition_Carbs, Nutrition_Fats.",
     "Medium", "infrastructure", "STORY-013"),

    # ── STORY-014 : Repositories ────────────────────────────────────────────────
    ("SUB-060", "Implémenter IUserRepository et UserRepository",
     "Interface src/NutritionApi.Application/Interfaces/IUserRepository.cs : GetByIdAsync, GetByKeycloakIdAsync, AddAsync, UpdateAsync, DeleteAsync. Implémentation src/NutritionApi.Infrastructure/Repositories/UserRepository.cs avec DbContext.",
     "Medium", "infrastructure", "STORY-014"),

    ("SUB-061", "Implémenter IDietPlanRepository et DietPlanRepository",
     "Interface : GetByIdAsync, GetAllByUserIdAsync(Guid userId), GetTemplatesAsync(), AddAsync, UpdateAsync, DeleteAsync. Implémentation EF Core avec DbContext.",
     "Medium", "infrastructure", "STORY-014"),

    ("SUB-062", "Implémenter IDietRepository et DietRepository",
     "Interface : GetByIdAsync, GetActiveByUserIdAsync(Guid userId), GetAllByUserIdAsync, GetByUserIdAndDateAsync, AddAsync, UpdateAsync. Implémentation EF Core.",
     "Medium", "infrastructure", "STORY-014"),

    ("SUB-063", "Implémenter IMealRepository et MealRepository",
     "Interface : GetByIdAsync, GetAllByUserIdAsync(Guid userId, DateTime? date), GetSavedByUserIdAsync(Guid userId), AddAsync, DeleteAsync. Implémentation EF Core avec Include(MealItems).",
     "Medium", "infrastructure", "STORY-014"),

    ("SUB-064", "Implémenter IFoodItemRepository et FoodItemRepository",
     "Interface : GetByIdAsync, GetByOffIdAsync(string offId), SearchByKeywordAsync(string keyword), AddAsync, UpdateAsync. SearchByKeywordAsync : recherche ILIKE sur Name pour PostgreSQL.",
     "Medium", "infrastructure", "STORY-014"),

    ("SUB-065", "Implémenter IWeightEntryRepository et WeightEntryRepository",
     "Interface : GetLatestByUserIdAsync(Guid userId), GetAllByUserIdAsync(Guid userId), ExistsAsync(Guid userId, DateOnly date), AddAsync. GetLatestByUserIdAsync : ORDER BY MeasuredAt DESC, LIMIT 1.",
     "Medium", "infrastructure", "STORY-014"),

    ("SUB-066", "Implémenter ISavedFoodItemRepository et SavedFoodItemRepository",
     "Interface : GetAllByUserIdAsync(Guid userId), ExistsAsync(Guid userId, Guid foodItemId), AddAsync, DeleteAsync. Implémentation EF Core.",
     "Medium", "infrastructure", "STORY-014"),

    # ── STORY-015 : Cache Redis ──────────────────────────────────────────────────
    ("SUB-067", "Configurer IConnectionMultiplexer Redis",
     "Dans src/NutritionApi.Infrastructure/DependencyInjection.cs : services.AddSingleton<IConnectionMultiplexer>(ConnectionMultiplexer.Connect(config[Redis:ConnectionString])). Gérer les erreurs de connexion au démarrage.",
     "Medium", "infrastructure", "STORY-015"),

    ("SUB-068", "Implémenter IFoodCacheService et FoodCacheService",
     "Interface src/NutritionApi.Application/Interfaces/IFoodCacheService.cs : GetAsync(string keyword), SetAsync(string keyword, List<FoodItem> items, TimeSpan ttl). Implémentation src/NutritionApi.Infrastructure/Cache/FoodCacheService.cs : sérialisation JSON + TTL configurable via appsettings.",
     "Medium", "infrastructure", "STORY-015"),

    # ── STORY-016 : Job Import OFF (Hangfire) ───────────────────────────────────
    ("SUB-069", "Télécharger le dump Open Food Facts",
     "HttpClient vers https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz. Télécharger dans un fichier temporaire, décompresser, retourner le flux de lignes.",
     "High", "infrastructure", "STORY-016"),

    ("SUB-070", "Traiter le dump par batch INSERT UPDATE FoodItem",
     "Parcourir ligne par ligne. Si OffId existant : appeler FoodItem.UpdateFromImport(). Sinon : créer nouveau FoodItem. Traiter par batch de 1000 lignes (configurable). Logger les erreurs par lot.",
     "High", "infrastructure", "STORY-016"),

    ("SUB-071", "Implémenter IOffImportJob et OffImportJob",
     "Interface src/NutritionApi.Application/Interfaces/IOffImportJob.cs : RunAsync(). Implémentation src/NutritionApi.Infrastructure/Jobs/OffImportJob.cs. Attribut [AutomaticRetry(Attempts = 3)]. Enregistrement : RecurringJob.AddOrUpdate<IOffImportJob>(off-import, j => j.RunAsync(), 0 3 * * *).",
     "Medium", "infrastructure", "STORY-016"),

    ("SUB-072", "Gérer erreurs import et reprise après échec",
     "Logger les erreurs par lot sans interrompre le traitement global. Hangfire gère le retry automatique selon AutomaticRetry(Attempts = 3). Ignorer les lignes malformées.",
     "Medium", "infrastructure", "STORY-016"),

    # ── STORY-017 : Job Purge RGPD (Hangfire) ──────────────────────────────────
    ("SUB-073", "Sélectionner comptes à purger après 30 jours",
     "Requête : SELECT Users WHERE DeletedAt <= DateTime.UtcNow - 30 jours. Traiter par lots pour éviter les timeouts sur grande volumétrie.",
     "High", "infrastructure", "STORY-017"),

    ("SUB-074", "Supprimer données utilisateur en cascade PostgreSQL",
     "Cascade DELETE dans l'ordre : MealItems → Meals → WeightEntries → SavedFoodItems → DietPlans → Diets → User. Utiliser une transaction par utilisateur.",
     "High", "infrastructure", "STORY-017"),

    ("SUB-075", "Supprimer utilisateur dans Keycloak Admin",
     "DELETE /admin/realms/{realm}/users/{KeycloakId} via HttpClient Keycloak Admin. Ignorer 404 (utilisateur déjà absent). Gérer 401/403 (token admin expiré).",
     "High", "infrastructure", "STORY-017"),

    ("SUB-076", "Implémenter IRgpdPurgeJob et RgpdPurgeJob",
     "Interface src/NutritionApi.Application/Interfaces/IRgpdPurgeJob.cs. Implémentation src/NutritionApi.Infrastructure/Jobs/RgpdPurgeJob.cs. Enregistrement : RecurringJob.AddOrUpdate<IRgpdPurgeJob>(rgpd-purge, j => j.RunAsync(), 30 3 * * *).",
     "High", "infrastructure", "STORY-017"),

    ("SUB-077", "Gérer erreurs Keycloak indisponible avec retry Polly",
     "Policy Polly sur l'appel Keycloak Admin : 3 retries avec backoff exponentiel. Si Keycloak indisponible après retries : logger l'erreur et passer à l'utilisateur suivant (pas d'interruption du job).",
     "High", "infrastructure", "STORY-017"),

    # ── STORY-018 : Migrations ───────────────────────────────────────────────────
    ("SUB-078", "Créer migration initiale EF Core",
     "Commande : dotnet ef migrations add InitialCreate --project src/NutritionApi.Infrastructure --startup-project src/NutritionApi.Api. Vérifier le fichier généré : toutes les tables présentes, index uniques créés (WeightEntry, SavedFoodItem, FoodItem.OffId), owned entities en colonnes.",
     "Medium", "infrastructure", "STORY-018"),

    ("SUB-079", "Préparer import initial dump Open Food Facts",
     "Script SQL ou migration EF Core seed pour déclencher le premier import OFF au déploiement initial. Vérifier que la table FoodItem est peuplée avant la mise en production.",
     "Medium", "infrastructure", "STORY-018"),

    # ── STORY-019 : UsersController ─────────────────────────────────────────────
    ("SUB-080", "Implémenter POST /users/me",
     "Fichier : src/NutritionApi.Api/Controllers/UsersController.cs. Body : CreateUserProfileRequest. Response : 201 Created + UserProfileResponse. Déclenché automatiquement à la première connexion Keycloak. UserId extrait du claim sub via le middleware JWT.",
     "Medium", "api", "STORY-019"),

    ("SUB-081", "Implémenter GET /users/me",
     "Response : 200 OK + UserProfileResponse incluant Bmr et Tdee calculés à la demande via DietService.CalculateNutritionNeeds. 404 si profil non encore créé.",
     "Medium", "api", "STORY-019"),

    ("SUB-082", "Implémenter PUT /users/me",
     "Body : champs modifiables (BirthDate, Gender, Height, ActivityLevel, Allergies, DietaryPreferences). Response : 200 OK + UserProfileResponse mis à jour.",
     "Medium", "api", "STORY-019"),

    ("SUB-083", "Implémenter POST /users/me/weight-entries",
     "Body : { weight: float, measuredAt: DateOnly }. Response : 201 Created. 409 si doublon même date.",
     "Medium", "api", "STORY-019"),

    ("SUB-084", "Implémenter GET /users/me/weight-entries",
     "Response : 200 OK + List<WeightEntryResponse> triée par MeasuredAt DESC.",
     "Medium", "api", "STORY-019"),

    ("SUB-085", "Implémenter PUT /users/me/weight-entries/{id}",
     "WeightEntry est immuable en Domain — à trancher : supprimer + recréer (DELETE + POST) ou autoriser un update applicatif. Response : 200 OK. 404 si introuvable. 403 si n'appartient pas à l'utilisateur.",
     "Medium", "api", "STORY-019"),

    ("SUB-086", "Implémenter GET /users/me/saved-food-items",
     "Response : 200 OK + List<FoodItemSearchResponse> avec le détail de chaque FoodItem sauvegardé.",
     "Medium", "api", "STORY-019"),

    ("SUB-087", "Implémenter POST /users/me/saved-food-items",
     "Body : SaveFoodItemRequest { FoodItemId }. Response : 201 Created. 404 si FoodItem inconnu. 409 si déjà sauvegardé.",
     "Medium", "api", "STORY-019"),

    ("SUB-088", "Implémenter DELETE /users/me/saved-food-items/{id}",
     "Response : 204 No Content. 404 si introuvable. 403 si n'appartient pas à l'utilisateur.",
     "Medium", "api", "STORY-019"),

    ("SUB-089", "Implémenter DELETE /users/me (suppression RGPD)",
     "Appelle user.MarkAsDeleted() (soft delete) + désactivation du compte Keycloak. RGPD Art. 17. Response : 204 No Content.",
     "High", "hors-scope", "STORY-019"),

    ("SUB-090", "Implémenter POST /users/me/reactivate",
     "Réinitialise DeletedAt = null si dans la grace period (30 jours depuis DeletedAt). Response : 200 OK. 400 si grace period expirée.",
     "High", "hors-scope", "STORY-019"),

    ("SUB-091", "Implémenter GET /users/me/export (RGPD Art. 20)",
     "Retourner un JSON contenant toutes les données personnelles : profil, Diets, Meals, WeightEntries, SavedFoodItems. RGPD Art. 20.",
     "High", "hors-scope", "STORY-019"),

    # ── STORY-020 : DietPlansController ─────────────────────────────────────────
    ("SUB-092", "Implémenter POST /diet-plans",
     "Body : CreateDietPlanRequest. Response : 201 Created + DietPlanResponse.",
     "Medium", "api", "STORY-020"),

    ("SUB-093", "Implémenter GET /diet-plans",
     "Response : 200 OK + List<DietPlanResponse> filtrée par userId du token.",
     "Medium", "api", "STORY-020"),

    ("SUB-094", "Implémenter PUT /diet-plans/{id}",
     "Body : champs modifiables du DietPlan. Response : 200 OK + DietPlanResponse. 403 si n'appartient pas à l'utilisateur.",
     "Medium", "api", "STORY-020"),

    ("SUB-095", "Implémenter DELETE /diet-plans/{id}",
     "Response : 204 No Content. 403 si n'appartient pas à l'utilisateur. 404 si introuvable.",
     "Medium", "api", "STORY-020"),

    ("SUB-096", "Implémenter POST /diet-plans/{id}/launch",
     "Lance le plan et crée une Diet active avec CalorieTarget calculé. Response : 201 Created + DietResponse. 409 si Diet active existante. 422 si aucune WeightEntry pour le calcul BMR.",
     "High", "api", "STORY-020"),

    # ── STORY-021 : DietsController ─────────────────────────────────────────────
    ("SUB-097", "Implémenter GET /diets/active",
     "Response : 200 OK + DietResponse. 404 si aucune Diet active pour l'utilisateur.",
     "Medium", "api", "STORY-021"),

    ("SUB-098", "Implémenter GET /diets (historique)",
     "Response : 200 OK + List<DietResponse> triée par StartDate DESC.",
     "Medium", "api", "STORY-021"),

    ("SUB-099", "Implémenter GET /diets/{id}",
     "Response : 200 OK + DietResponse. 403 si n'appartient pas à l'utilisateur. 404 si introuvable.",
     "Medium", "api", "STORY-021"),

    ("SUB-100", "Implémenter POST /diets/{id}/archive",
     "Clôture la Diet active. Response : 200 OK + DietResponse avec EndDate renseignée. 400 si Diet déjà archivée.",
     "Medium", "api", "STORY-021"),

    ("SUB-101", "Implémenter GET /diets/{id}/bilan",
     "Query params : period (day/week/month/full), date, startDate. Response : 200 OK + NutritionBilanResponse (dailyData + weightEntries + summary).",
     "High", "api", "STORY-021"),

    # ── STORY-022 : MealsController ─────────────────────────────────────────────
    ("SUB-102", "Implémenter POST /meals",
     "Body : CreateMealRequest. Response : 201 Created + MealResponse avec NutritionInfo calculée par item.",
     "Medium", "api", "STORY-022"),

    ("SUB-103", "Implémenter GET /meals",
     "Query params : ?saved=true, ?date=YYYY-MM-DD. Response : 200 OK + List<MealResponse>.",
     "Medium", "api", "STORY-022"),

    ("SUB-104", "Implémenter GET /meals/{id}",
     "Response : 200 OK + MealResponse avec items et NutritionInfo. 403 si n'appartient pas à l'utilisateur.",
     "Medium", "api", "STORY-022"),

    ("SUB-105", "Implémenter DELETE /meals/{id}",
     "Response : 204 No Content. Cascade sur MealItems. 403 si n'appartient pas à l'utilisateur.",
     "Medium", "api", "STORY-022"),

    ("SUB-106", "Implémenter POST /meals/{id}/items",
     "Body : { foodItemId: Guid, quantity: float }. Response : 201 Created + MealResponse mis à jour.",
     "Medium", "api", "STORY-022"),

    ("SUB-107", "Implémenter DELETE /meals/{id}/items/{itemId}",
     "Response : 204 No Content. 400 si dernier MealItem (invariant domaine : Meal doit avoir au moins 1 item). 403 si n'appartient pas à l'utilisateur.",
     "Medium", "api", "STORY-022"),

    # ── STORY-023 : FoodItemsController ─────────────────────────────────────────
    ("SUB-108", "Implémenter GET /food-items (recherche par mot-clé)",
     "Query param : ?search={keyword}. Response : 200 OK + List<FoodItemSearchResponse>. Stratégie : Redis d'abord, PostgreSQL si absent du cache.",
     "Medium", "api", "STORY-023"),

    # ── STORY-024 : Middleware HTTP ──────────────────────────────────────────────
    ("SUB-109", "Implémenter validation JWT Keycloak",
     "Fichier : src/NutritionApi.Api/Program.cs ou Extensions/AuthExtensions.cs. AddAuthentication(JwtBearerDefaults).AddJwtBearer avec Authority = keycloakUrl et ValidAudience. Extraire claim sub → résoudre User.KeycloakId.",
     "High", "api", "STORY-024"),

    ("SUB-110", "Implémenter gestion globale des erreurs HTTP",
     "Fichier : src/NutritionApi.Api/Middleware/ExceptionMiddleware.cs. Mapper : ArgumentException → 400, UnauthorizedException → 401, ForbiddenException → 403, NotFoundException → 404, ConflictException → 409, InvalidOperationException → 400, toute autre exception → 500.",
     "High", "api", "STORY-024"),

    ("SUB-111", "Implémenter logging des requêtes entrantes",
     "Fichier : src/NutritionApi.Api/Middleware/RequestLoggingMiddleware.cs. Logguer : méthode HTTP, path, status code, durée en ms. Utiliser ILogger<RequestLoggingMiddleware>.",
     "Medium", "api", "STORY-024"),

    # ── STORY-025 : Tests Unitaires Domain ───────────────────────────────────────
    ("SUB-112", "Tester MacroDistribution invariant somme 100%",
     "Fichier : tests/NutritionApi.Domain.Tests/ValueObjects/MacroDistributionTests.cs. Nominal : 40/30/30 → instanciation réussie. Erreur : 50/30/30 → ArgumentException (somme = 110%). Erreur : valeur négative → ArgumentException.",
     "High", "tests", "STORY-025"),

    ("SUB-113", "Tester NutritionInfo calcul snapshot correct",
     "Fichier : tests/NutritionApi.Domain.Tests/ValueObjects/NutritionInfoTests.cs. Nominal : 150g de poulet (20g protéines/100g) → Proteins = 30. Erreur : valeur négative → ArgumentOutOfRangeException.",
     "Medium", "tests", "STORY-025"),

    ("SUB-114", "Tester Diet règle unicité régime actif",
     "Fichier : tests/NutritionApi.Domain.Tests/Entity/DietTests.cs. EnsureEditable() lève InvalidOperationException quand StatusDiet == Active. EnsureEditable() lève InvalidOperationException quand StatusDiet == Completed. StartDate == DateOnly.FromDateTime(DateTime.UtcNow) à la création.",
     "High", "tests", "STORY-025"),

    ("SUB-158", "Tester Meal — DomainException si aucun MealItem à la création",
     "Fichier : tests/NutritionApi.Domain.Tests/Entity/MealTests.cs. Liste vide → ArgumentException. Liste null → ArgumentException. RemoveMealItem sur Meal à 1 item → InvalidOperationException.",
     "High", "tests", "STORY-025"),

    ("SUB-159", "Tester SavedFoodItem — doublon interdit par User",
     "Fichier : tests/NutritionApi.Domain.Tests/Entity/SavedFoodItemTests.cs. Vérifier immuabilité de l'entité. Vérifier validations constructeur (UserId non vide, FoodItemId non vide, SavedAt imposé système).",
     "Medium", "tests", "STORY-025"),

    ("SUB-160", "Tester Diet — StartDate imposée système non modifiable",
     "Fichier : tests/NutritionApi.Domain.Tests/Entity/DietTests.cs. Vérifier que diet.StartDate == DateOnly.FromDateTime(DateTime.UtcNow). Vérifier absence de setter public sur StartDate.",
     "High", "tests", "STORY-025"),

    ("SUB-161", "Tester Diet — immutabilité après lancement sauf EndDate",
     "Fichier : tests/NutritionApi.Domain.Tests/Entity/DietTests.cs. Rename() sur Diet Active → InvalidOperationException. ChangeDietStatus(Active → Archived) reste possible. ChangeDietStatus sur Diet Completed → InvalidOperationException.",
     "High", "tests", "STORY-025"),

    ("SUB-162", "Tester WeightEntry — doublon même date même User",
     "Fichier : tests/NutritionApi.Domain.Tests/Entity/WeightEntryTests.cs. Vérifier validations constructeur : Weight > 0, UserId non vide, MeasuredAt non default.",
     "Medium", "tests", "STORY-025"),

    # ── STORY-038 : Tests Unitaires Application ──────────────────────────────────
    ("SUB-163", "Tester UserService — WeightEntry doublon même date → 409",
     "Fichier : tests/NutritionApi.Application.Tests/Services/UserServiceTests.cs. Mock IWeightEntryRepository.ExistsAsync(userId, date) → true. Vérifier que le service lève ConflictException (409).",
     "Medium", "tests", "STORY-038"),

    ("SUB-164", "Tester DietService — lancement sans WeightEntry → 422",
     "Fichier : tests/NutritionApi.Application.Tests/Services/DietServiceTests.cs. Mock IWeightEntryRepository.GetLatestByUserIdAsync(userId) → null. Vérifier que le service lève une exception 422.",
     "High", "tests", "STORY-038"),

    ("SUB-165", "Tester DietService — lancement avec Diet active existante → 409",
     "Mock IDietRepository.GetActiveByUserIdAsync(userId) → renvoie une Diet. Vérifier que le service lève ConflictException (409).",
     "High", "tests", "STORY-038"),

    ("SUB-166", "Tester MealService — création Meal sans MealItem → rejeté",
     "Fichier : tests/NutritionApi.Application.Tests/Services/MealServiceTests.cs. DTO avec Items = [] → vérifier que ArgumentException du domaine remonte correctement.",
     "High", "tests", "STORY-038"),

    ("SUB-167", "Tester FoodItemService — SavedFoodItem doublon → 409",
     "Fichier : tests/NutritionApi.Application.Tests/Services/FoodItemServiceTests.cs. Mock ISavedFoodItemRepository.ExistsAsync(userId, foodItemId) → true. Vérifier que le service lève ConflictException (409).",
     "Medium", "tests", "STORY-038"),

    ("SUB-168", "Tester NutritionService — bilan agrégation journalière correcte",
     "Fichier : tests/NutritionApi.Application.Tests/Services/NutritionServiceTests.cs. Mock repas sur 3 jours différents. Vérifier que dailyData contient 3 entrées avec les bonnes sommes de Calories/Proteins/Carbs/Fats.",
     "High", "tests", "STORY-038"),

    ("SUB-169", "Tester SubscriptionGuard — blocage limite plans Free",
     "Mock IDietPlanRepository retournant 2 plans existants. Vérifier retour 403 à la tentative de création d'un 3ème pour un utilisateur Free.",
     "High", "hors-scope", "STORY-038"),

    ("SUB-170", "Tester SubscriptionGuard — blocage repas sauvegardé Free",
     "Mock IMealRepository retournant 5 repas sauvegardés. Vérifier retour 403 pour un utilisateur Free.",
     "High", "hors-scope", "STORY-038"),

    ("SUB-171", "Tester SubscriptionGuard — restriction période bilan Free 7j",
     "Vérifier que la période effective retournée pour un utilisateur Free est clampée à 7 jours quelle que soit la période demandée.",
     "High", "hors-scope", "STORY-038"),

    # ── STORY-026 : Tests Intégration ────────────────────────────────────────────
    ("SUB-115", "Tester repositories avec Testcontainers PostgreSQL",
     "Fichier : tests/NutritionApi.Infrastructure.Tests/. Démarrer un conteneur PostgreSQL avec Testcontainers, appliquer les migrations. Tester les 7 repositories. Vérifier les contraintes d'unicité en base (WeightEntry, SavedFoodItem).",
     "Medium", "tests", "STORY-026"),

    ("SUB-116", "Tester cache Redis avec Testcontainers",
     "Démarrer un conteneur Redis avec Testcontainers. Tester FoodCacheService.GetAsync (cache miss → null) et SetAsync + GetAsync (cache hit avec données correctes).",
     "Medium", "tests", "STORY-026"),

    ("SUB-117", "Tester job import Open Food Facts avec dump test",
     "Fichier dump de test (50 lignes). Vérifier que les FoodItem sont créés au premier passage et mis à jour (UpdateFromImport) au second passage.",
     "Medium", "tests", "STORY-026"),

    # ── STORY-027 : Tests API ────────────────────────────────────────────────────
    ("SUB-118", "Tester tous les endpoints cas nominaux et cas erreur",
     "Fichier : tests/NutritionApi.Api.Tests/. WebApplicationFactory<Program> + Testcontainers PostgreSQL. Couvrir 201, 200, 204, 400, 401, 403, 404, 409 selon les endpoints.",
     "Medium", "tests", "STORY-027"),

    ("SUB-119", "Tester rejet JWT invalide sur endpoints protégés",
     "Requête sans token → 401. Token expiré → 401. Token valide avec sub inconnu → 404 (profil non créé). Token valide avec profil créé → 200.",
     "High", "tests", "STORY-027"),

    # ── STORY-028 : Domaine Abonnements & Templates ──────────────────────────────
    ("SUB-120", "Déclarer enum SubscriptionTier",
     "Fichier : src/NutritionApi.Domain/Enums/SubscriptionTier.cs. Valeurs : Free = 0, Pro, Business.",
     "Medium", "domain", "STORY-028"),

    ("SUB-121", "Ajouter User.SubscriptionTier",
     "Fichier : src/NutritionApi.Domain/Entity/User.cs. Ajouter SubscriptionTier SubscriptionTier { get; private set; } — Free par défaut à la création. Pas dans le JWT — source de vérité en base uniquement.",
     "Medium", "domain", "STORY-028"),

    ("SUB-122", "Ajouter DietPlan.IsTemplate",
     "Fichier : src/NutritionApi.Domain/Entity/DietPlan.cs. Ajouter bool IsTemplate { get; private set; } — false par défaut. True = template partagé, accessible en lecture seule aux tiers Pro/Business uniquement.",
     "Medium", "domain", "STORY-028"),

    ("SUB-123", "Passer DietPlan.UserId en Guid nullable",
     "Fichier : src/NutritionApi.Domain/Entity/DietPlan.cs. Passer UserId de Guid à Guid? — null si IsTemplate = true. Un template n'appartient à aucun utilisateur.",
     "Medium", "domain", "STORY-028"),

    # ── STORY-029 : SubscriptionGuard ───────────────────────────────────────────
    ("SUB-124", "Implémenter helper SubscriptionGuard",
     "Fichier : src/NutritionApi.Application/Guards/SubscriptionGuard.cs. Méthode statique CheckLimit(SubscriptionTier tier, int currentCount, int freeLimit, int proLimit) — lève ForbiddenException (403) si currentCount >= limite selon le tier.",
     "High", "application", "STORY-029"),

    ("SUB-125", "Vérifier limite plans personnels dans DietPlanService",
     "Dans DietPlanService.CreateAsync : compter les DietPlans IsTemplate=false de l'utilisateur. Appeler SubscriptionGuard.CheckLimit(tier, count, freeLimit: 2, proLimit: 20).",
     "High", "application", "STORY-029"),

    ("SUB-126", "Bloquer accès templates si tier Free dans DietPlanService",
     "Dans DietPlanService.GetTemplatesAsync : vérifier user.SubscriptionTier != Free — lève ForbiddenException (403) sinon.",
     "High", "application", "STORY-029"),

    ("SUB-127", "Lister les DietPlan templates partagés",
     "Nouvelle méthode DietPlanService.GetTemplatesAsync() : IDietPlanRepository.GetTemplatesAsync() → retourner uniquement IsTemplate = true.",
     "Medium", "application", "STORY-029"),

    ("SUB-128", "Vérifier limite repas sauvegardés dans MealService",
     "Dans MealService.CreateAsync si IsSaved = true : compter les Meals sauvegardés. SubscriptionGuard.CheckLimit(tier, count, freeLimit: 5, proLimit: 50).",
     "High", "application", "STORY-029"),

    ("SUB-129", "Vérifier limite SavedFoodItems dans FoodItemService",
     "Dans FoodItemService.SaveFoodItemAsync : compter les SavedFoodItems existants. SubscriptionGuard.CheckLimit(tier, count, freeLimit: 10, proLimit: 100).",
     "High", "application", "STORY-029"),

    ("SUB-130", "Restreindre période bilan selon tier dans NutritionService",
     "Dans NutritionService.GetBilanAsync : calculer maxDays selon tier (Free = 7, Pro = 365, Business = int.MaxValue) et clamper la période effective.",
     "High", "application", "STORY-029"),

    # ── STORY-030 : Infrastructure Abonnements & Templates ──────────────────────
    ("SUB-131", "Mettre à jour DietPlanConfiguration EF Core",
     "Dans DietPlanConfiguration : ajouter HasIndex(d => d.IsTemplate) pour filtrage rapide. UserId nullable déjà configuré via IsRequired(false).",
     "Medium", "infrastructure", "STORY-030"),

    ("SUB-132", "Seed des templates initiaux",
     "Insérer 3 DietPlan templates initiaux (IsTemplate=true, UserId=null) via migration ou fichier JSON de seed : Équilibré (50/30/20), Protéiné (40/30/30), Keto (5/70/25).",
     "Medium", "infrastructure", "STORY-030"),

    # ── STORY-031 : Auth & Templates — Nouveaux endpoints ───────────────────────
    ("SUB-133", "Implémenter GET /diet-plans/templates",
     "Retourner tous les DietPlan templates (IsTemplate = true). Accessible Pro et Business uniquement — 403 si tier Free.",
     "High", "api", "STORY-031"),

    ("SUB-134", "Implémenter POST /admin/diet-plans/templates",
     "Créer un template partagé (IsTemplate=true, UserId=null). Protégé par le rôle admin Keycloak (claim realm_access.roles contient admin).",
     "Medium", "api", "STORY-031"),

    ("SUB-135", "Implémenter PUT /admin/diet-plans/templates/{id}",
     "Modifier un template existant. Protégé par le rôle admin Keycloak. Response : 200 OK + DietPlanResponse.",
     "Medium", "api", "STORY-031"),

    ("SUB-136", "Extraction KeycloakId depuis claim sub dans le middleware JWT",
     "Après validation du token : extraire claim sub → User.KeycloakId. Résoudre User.Id via IUserRepository.GetByKeycloakIdAsync. Stocker dans HttpContext.Items pour les controllers.",
     "High", "api", "STORY-031"),

    ("SUB-137", "Réponses 403 tier insuffisant avec message explicite",
     "ExceptionMiddleware : mapper ForbiddenException → 403 avec body { message: This feature requires a Pro subscription }.",
     "Medium", "api", "STORY-031"),

    # ── STORY-032 : Tests Abonnements & Templates ────────────────────────────────
    ("SUB-138", "Tester blocage création plan si limite Free atteinte",
     "Utilisateur Free avec 2 plans existants. Tentative de création d'un 3ème → vérifier retour 403.",
     "Medium", "tests", "STORY-032"),

    ("SUB-139", "Tester blocage accès templates pour tier Free",
     "GET /diet-plans/templates avec token utilisateur Free → vérifier 403.",
     "Medium", "tests", "STORY-032"),

    ("SUB-140", "Tester restriction période bilan selon tier",
     "Free : période demandée 30j → période effective 7j. Pro : période demandée 2 ans → période effective 1 an. Business : illimité.",
     "Medium", "tests", "STORY-032"),

    ("SUB-141", "Tester blocage SavedFoodItem limite Free",
     "Utilisateur Free avec 10 SavedFoodItems. Tentative d'ajout d'un 11ème → vérifier retour 403.",
     "Medium", "tests", "STORY-032"),

    # ── STORY-033 : AdminService ─────────────────────────────────────────────────
    ("SUB-142", "Agréger KPIs utilisateurs",
     "Méthode AdminService.GetUserKpisAsync(). COUNT total Users. GROUP BY SubscriptionTier. COUNT Users créés dans les 7 derniers jours (CreatedAt >= Now - 7j).",
     "Medium", "application", "STORY-033"),

    ("SUB-143", "Agréger métriques activité",
     "Méthode AdminService.GetActivityMetricsAsync(). COUNT Diets WHERE Status = Active. COUNT Meals WHERE CreatedAt >= Now - 7j. COUNT Users WHERE DeletedAt IS NOT NULL (grace period).",
     "Medium", "application", "STORY-033"),

    ("SUB-144", "Agréger santé système depuis tables Hangfire",
     "Méthode AdminService.GetSystemHealthAsync(). Requêtes directes sur HangFire.Job et HangFire.State. Statuts : success / failed / never_run. Retourner date + statut du dernier import OFF et du dernier job purge.",
     "Medium", "application", "STORY-033"),

    # ── STORY-034 : AdminController ──────────────────────────────────────────────
    ("SUB-145", "Implémenter GET /admin/dashboard",
     "Retourner KPIs consolidés : users (total, par tier, nouveaux 7j) + activity (diets actives, repas 7j, comptes grace period). Rôle admin Keycloak requis. Response : 200 OK.",
     "Medium", "api", "STORY-034"),

    ("SUB-146", "Implémenter GET /admin/system/health",
     "Retourner le statut des jobs Hangfire (offImport + rgpdPurge : success/failed/never_run + date) et le count FoodItems en base. Rôle admin requis.",
     "Medium", "api", "STORY-034"),

    ("SUB-147", "Implémenter DELETE /admin/diet-plans/templates/{id}",
     "Supprimer un DietPlan IsTemplate = true. Rôle admin requis. Response : 204 No Content. 404 si introuvable.",
     "Medium", "api", "STORY-034"),

    # ── STORY-035 : Tests Admin ──────────────────────────────────────────────────
    ("SUB-148", "Tester GET /admin/dashboard — données agrégées correctes",
     "Seed : 3 users (2 Free, 1 Pro), 1 Diet active, 5 Meals cette semaine. Vérifier que les compteurs retournés correspondent.",
     "Medium", "tests", "STORY-035"),

    ("SUB-149", "Tester GET /admin/dashboard — 403 si rôle admin absent",
     "Token valide sans rôle admin → vérifier retour 403.",
     "Medium", "tests", "STORY-035"),

    ("SUB-150", "Tester GET /admin/system/health — statuts jobs corrects",
     "Vérifier les statuts success/failed/never_run selon l'état simulé des tables HangFire.Job et HangFire.State.",
     "Medium", "tests", "STORY-035"),

    # ── STORY-037 : OpenAPI / Swagger UI ────────────────────────────────────────
    ("SUB-154", "Configurer AddSwaggerGen avec sécurité JWT Bearer",
     "Dans Program.cs : services.AddSwaggerGen avec SwaggerDoc v1, OpenApiSecurityDefinition Bearer (scheme Bearer, in header), AddSecurityRequirement sur tous les endpoints [Authorize].",
     "Medium", "api", "STORY-037"),

    ("SUB-155", "Activer Swagger UI hors production",
     "Dans Program.cs : if (!app.Environment.IsProduction()) { app.UseSwagger(); app.UseSwaggerUI(); }. Accessible sur /swagger.",
     "Medium", "api", "STORY-037"),

    ("SUB-156", "Activer commentaires XML sur les projets API et Application",
     "Dans les .csproj NutritionApi.Api et NutritionApi.Application : <GenerateDocumentationFile>true</GenerateDocumentationFile>. Référencer le fichier XML dans IncludeXmlComments dans AddSwaggerGen.",
     "Medium", "api", "STORY-037"),

    ("SUB-157", "Exclure le dashboard Hangfire de la spec OpenAPI",
     "Configurer un IDocumentFilter ou une convention Swashbuckle pour que les routes /hangfire n'apparaissent pas dans swagger.json.",
     "Low", "api", "STORY-037"),

    # ── STORY-036 : Configuration Hangfire ──────────────────────────────────────
    ("SUB-151", "Configurer Hangfire avec stockage PostgreSQL",
     "Dans DependencyInjection.cs : services.AddHangfire(c => c.UsePostgreSqlStorage(connectionString, new PostgreSqlStorageOptions { SchemaName = HangFire, PrepareSchemaIfNecessary = true })). Voir infrastructure-hangfire.md.",
     "High", "infrastructure", "STORY-036"),

    ("SUB-152", "Sécuriser le dashboard /hangfire — rôle admin Keycloak",
     "Implémenter HangfireAdminAuthorizationFilter : IsDashboardAuthorizationFilter. Vérifier token JWT valide + claim realm_access.roles contient admin.",
     "High", "infrastructure", "STORY-036"),

    ("SUB-153", "Enregistrer les jobs récurrents au démarrage",
     "Dans Program.cs après app.UseHangfireDashboard() : RecurringJob.AddOrUpdate<IOffImportJob>(off-import, j => j.RunAsync(), 0 3 * * *) et RecurringJob.AddOrUpdate<IRgpdPurgeJob>(rgpd-purge, j => j.RunAsync(), 30 3 * * *).",
     "High", "infrastructure", "STORY-036"),

    # ── STORY-039 : Setup environnement de développement local ──────────────────
    ("SUB-172", "Créer infra/dev/docker-compose.yml",
     "Services : app-db (PostgreSQL 16, port 5432), keycloak-db (PostgreSQL 16, port 5433), keycloak (Keycloak 24, port 8080, --import-realm, volume vers realm-export-dev.json), redis (Redis 7, port 6379). Variables lues depuis infra/dev/.env.",
     "High", "infrastructure", "STORY-039"),

    ("SUB-173", "Créer infra/dev/.env.example",
     "Variables : POSTGRES_USER/PASSWORD, KC_DB_USER/PASSWORD, KC_ADMIN_USER/PASSWORD, ConnectionStrings__NutritionDb, Keycloak__Authority, Keycloak__Realm, Keycloak__ClientId, Redis__ConnectionString. Ajouter infra/dev/.env au .gitignore.",
     "High", "infrastructure", "STORY-039"),

    ("SUB-174", "Générer et versionner infra/keycloak/realm-export-dev.json",
     "Configurer le realm nutrition manuellement : client nutrition-api (public, PKCE), client nutrition-api-service (confidential, service account, rôle manage-users), rôles realm user + admin, 2 utilisateurs de test (user@test.com + admin@test.com). Exporter via Admin Console → Partial export. Commiter.",
     "High", "infrastructure", "STORY-039"),

    ("SUB-175", "Vérifier le démarrage complet et l'import automatique du realm",
     "docker compose down && docker compose up -d. Vérifier : Keycloak importe le realm au démarrage, 4 services healthy, dotnet ef database update s'applique sans erreur. Tester un login sur /realms/nutrition.",
     "Medium", "infrastructure", "STORY-039"),

    # ── STORY-040 : Dockerfile + config connexion K3s ───────────────────────────
    ("SUB-176", "Créer le Dockerfile multi-stage de l'API",
     "Stage build : FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build — COPY, dotnet restore, dotnet publish -c Release. Stage runtime : FROM mcr.microsoft.com/dotnet/aspnet:10.0 — COPY --from=build. ENTRYPOINT [dotnet, NutritionApi.Api.dll].",
     "High", "infrastructure", "STORY-040"),

    ("SUB-177", "Créer infra/k8s/configmap.yaml",
     "Variables non-sensibles : ASPNETCORE_ENVIRONMENT=Production, Keycloak__Authority, Keycloak__Realm, Keycloak__ClientId, Keycloak__AdminBaseUrl, ConnectionStrings__Redis. Les URLs pointent vers les services K3s du projet infra séparé.",
     "Medium", "infrastructure", "STORY-040"),

    ("SUB-178", "Créer infra/k8s/secret.yaml.example + documenter kubectl create secret",
     "Fichier .example commité (valeurs vides) : ConnectionStrings__NutritionDb et Keycloak__ServiceClientSecret. Commande kubectl create secret generic nutrition-secrets documentée dans infrastructure-setup.md. Jamais de valeurs réelles committées.",
     "High", "infrastructure", "STORY-040"),

    ("SUB-179", "Créer infra/k8s/deployment.yaml et service.yaml",
     "Deployment nutrition-api : 1 replica, image GHCR, envFrom configmap + secret, readinessProbe GET /health sur port 8080. Service ClusterIP port 80 → 8080.",
     "Medium", "infrastructure", "STORY-040"),

    ("SUB-180", "Créer infra/k8s/ingress.yaml (Traefik K3s)",
     "Annotations : kubernetes.io/ingress.class: traefik, traefik.ingress.kubernetes.io/router.tls: true. TLS sur api.nutrition.example.com. Route / → nutrition-api-service:80.",
     "Medium", "infrastructure", "STORY-040"),

    # ── STORY-041 : CI/CD GitHub Actions ────────────────────────────────────────
    ("SUB-181", "Créer Service Account K3s dédié au déploiement GitHub Actions",
     "kubectl create serviceaccount github-actions-deployer -n nutrition. RoleBinding clusterrole=edit limité au namespace nutrition. Extraire token, construire kubeconfig minimal, encoder en base64. Voir infrastructure-setup.md Section 3.",
     "High", "infrastructure", "STORY-041"),

    ("SUB-182", "Ajouter le secret KUBECONFIG_B64 dans GitHub",
     "GitHub → Settings → Secrets and variables → Actions → New repository secret. Valeur = sortie base64 du kubeconfig Service Account. Supprimer le fichier kubeconfig local immédiatement après.",
     "High", "infrastructure", "STORY-041"),

    ("SUB-183", "Créer .github/workflows/deploy.yml",
     "Trigger : push sur main. Steps : checkout → login GHCR (GITHUB_TOKEN) → docker build+push (tag SHA + latest) → setup kubectl → decode KUBECONFIG_B64 → kubectl set image → rollout status --timeout=120s → kubectl get pods.",
     "High", "infrastructure", "STORY-041"),

    ("SUB-184", "Vérifier le premier déploiement automatique",
     "Push un commit sur main. Vérifier pipeline : build OK, push GHCR OK, rollout OK. Vérifier pods (kubectl get pods -n nutrition) et endpoint via Ingress. Corriger si rollout timeout.",
     "Medium", "infrastructure", "STORY-041"),
]
