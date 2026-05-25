# jira_backlog.py — Backlog complet projet nutrition-manager (backend)
# Généré automatiquement par generate_backlog.py — NE PAS MODIFIER MANUELLEMENT
# Source  : rules.json v2.0
# Date    : 2026-05-25
# Moteur  : python3 playbook/tools/import_jira.py docs/pages/backend/livrable/jira_backlog.py

MODULE = "backend"
MODE   = "create"

EXISTING_EPICS = {}

# ── Epics ──────────────────────────────────────────────────────────────────────

EPICS = [
    ("EPIC-001", "Domain Layer", "Entités métier, value objects, enums et invariants. Zéro dépendance externe.", "domain"),
    ("EPIC-002", "Application Layer", "Services applicatifs et DTOs. Orchestre les use cases depuis le domaine.", "application"),
    ("EPIC-003", "Infrastructure Layer", "EF Core, repositories, cache Redis, jobs Hangfire et migrations.", "infrastructure"),
    ("EPIC-004", "API Layer", "Controllers REST et middleware. Expose les services applicatifs.", "api"),
]

# ── Stories ────────────────────────────────────────────────────────────────────

STORIES = [
    ("STORY-001", "Modèle domaine — entités et value objects",
     """Contexte : Implémenter l'ensemble des Aggregate Roots, entités enfants et Value Objects du modèle domaine. Chaque entité valide ses invariants intra-agrégat dans le constructeur.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "domain", 5, "EPIC-001"),
    ("STORY-002", "Tests unitaires Domain",
     """Contexte : Couvrir tous les invariants et comportements du Domain. Zéro mock, zéro infrastructure — xUnit seul.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "domain", 3, "EPIC-001"),
    ("STORY-003", "UserService",
     """Contexte : Gestion du profil utilisateur et des pesées.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "Medium", "application", 2, "EPIC-002"),
    ("STORY-004", "DietPlanService",
     """Contexte : CRUD sur les plans alimentaires réutilisables.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "Medium", "application", 2, "EPIC-002"),
    ("STORY-005", "DietService",
     """Contexte : Lancement, clôture et déduction des régimes actifs.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "application", 3, "EPIC-002"),
    ("STORY-006", "MealService",
     """Contexte : Création et gestion des repas.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "Medium", "application", 2, "EPIC-002"),
    ("STORY-007", "FoodItemService",
     """Contexte : Recherche et gestion de la liste personnelle d'aliments.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "Medium", "application", 2, "EPIC-002"),
    ("STORY-008", "NutritionService",
     """Contexte : Calcul du bilan nutritionnel d'une Diet.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "application", 2, "EPIC-002"),
    ("STORY-009", "DTOs Application",
     """Contexte : Contrats d'entrée et de sortie des services.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "Medium", "application", 2, "EPIC-002"),
    ("STORY-010", "Tests unitaires Application",
     """Contexte : Tester les use cases et invariants cross-agrégat. Moq des repositories.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "application", 3, "EPIC-002"),
    ("STORY-011", "Setup environnement de développement local",
     """Contexte : Prérequis à tout le reste.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "infrastructure", 2, "EPIC-003"),
    ("STORY-012", "EF Core — Mapping et repositories",
     """Contexte : Persistance complète du modèle domaine.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "infrastructure", 5, "EPIC-003"),
    ("STORY-013", "Cache Redis et job import Open Food Facts",
     """Contexte : Performance de recherche et fraîcheur des données alimentaires.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "Medium", "infrastructure", 3, "EPIC-003"),
    ("STORY-014", "Tests d'intégration Infrastructure",
     """Contexte : Valider la persistance avec une vraie base de données.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "infrastructure", 3, "EPIC-003"),
    ("STORY-015", "Middleware et configuration ASP.NET Core",
     """Contexte : Fondations communes à tous les controllers.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "api", 3, "EPIC-004"),
    ("STORY-016", "UsersController",
     """Contexte : Endpoints profil utilisateur, pesées et aliments personnels.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "api", 3, "EPIC-004"),
    ("STORY-017", "DietPlansController",
     """Contexte : Endpoints plans alimentaires.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "api", 2, "EPIC-004"),
    ("STORY-018", "DietsController",
     """Contexte : Endpoints régimes actifs et bilan nutritionnel.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "api", 2, "EPIC-004"),
    ("STORY-019", "MealsController et FoodItemsController",
     """Contexte : Endpoints repas et recherche alimentaire.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "api", 3, "EPIC-004"),
    ("STORY-020", "Tests API end-to-end",
     """Contexte : Valider les contrats HTTP avec WebApplicationFactory.
Critères d'acceptation :
- [ ] Tous les éléments de la Sub-task sont implémentés et passent en revue
- [ ] Tests unitaires verts
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts""",
     "High", "api", 3, "EPIC-004"),
]

# ── Sub-tasks ──────────────────────────────────────────────────────────────────

SUBTASKS = [
    ("SUB-001", "Implémenter les Aggregate Roots (User, DietPlan, Diet, Meal, FoodItem)",
     """Objectif : Implémenter les Aggregate Roots (User, DietPlan, Diet, Meal, FoodItem)
Règles métier : Constructeur public avec validations + constructeur privé vide pour EF Core. Méthodes de mutation avec préconditions. Invariants intra-agrégat : Diet immuable après lancement, Meal >= 1 MealItem, StartDate imposée système.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "domain", "STORY-001"),
    ("SUB-002", "Implémenter les entités enfants (WeightEntry, MealItem, SavedFoodItem)",
     """Objectif : Implémenter les entités enfants (WeightEntry, MealItem, SavedFoodItem)
Règles métier : Entités sans existence indépendante. Supprimées en cascade avec leur parent. Constructeur public avec validations + constructeur privé vide pour EF Core.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "domain", "STORY-001"),
    ("SUB-003", "Implémenter les Value Objects (MacroDistribution, NutritionInfo, NutritionNeeds)",
     """Objectif : Implémenter les Value Objects (MacroDistribution, NutritionInfo, NutritionNeeds)
Règles métier : Records immuables, égalité par valeur. Invariant MacroDistribution : somme Carbs + Proteins + Fats = 100%. NutritionNeeds non persisté, calculé à la demande.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "domain", "STORY-001"),
    ("SUB-004", "Déclarer les enums métier (ActivityLevel, Goal, MealType, DietType, DietStatus, Gender, Allergen, SubscriptionTier)",
     """Objectif : Déclarer les enums métier (ActivityLevel, Goal, MealType, DietType, DietStatus, Gender, Allergen, SubscriptionTier)
Règles métier : 8 enums dans NutritionApi.Domain/Enums/. Chaque enum expose Unknown = 0 utilisé uniquement par EF Core.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "domain", "STORY-001"),
    ("SUB-005", "Tester les Aggregate Roots et entités enfants",
     """Objectif : Tester les Aggregate Roots et entités enfants
Règles métier : User (allergène dupliqué, préférence dupliquée), Diet (immuable Active/Completed, StartDate système), Meal (aucun MealItem → exception), DietPlan (modifiable à tout moment), FoodItem (mise à jour import), WeightEntry (poids positif), MealItem (quantité positive), SavedFoodItem (validations constructeur).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "domain", "STORY-002"),
    ("SUB-006", "Tester les Value Objects",
     """Objectif : Tester les Value Objects
Règles métier : MacroDistribution : somme != 100% → exception, somme = 100% → valide. NutritionInfo : calcul snapshot correct depuis MealItems. NutritionNeeds : calcul BMR Mifflin-St Jeor et Harris-Benedict correct.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "domain", "STORY-002"),
    ("SUB-007", "Gérer le profil utilisateur et les pesées",
     """Objectif : Gérer le profil utilisateur et les pesées
Règles métier : Créer le profil (+ première WeightEntry), mettre à jour le profil, ajouter une WeightEntry. Invariant cross-agrégat NTR-67 : interdire doublon SavedFoodItem pour un User (GetByUserAndFoodItemAsync → 409 si existant).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "application", "STORY-003"),
    ("SUB-008", "Gérer les plans alimentaires (CRUD)",
     """Objectif : Gérer les plans alimentaires (CRUD)
Règles métier : Créer, modifier, supprimer et lister les DietPlan d'un utilisateur. Le DietPlan reste modifiable même après avoir servi de base à une Diet.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "application", "STORY-004"),
    ("SUB-009", "Lancer un DietPlan et créer une Diet active",
     """Objectif : Lancer un DietPlan et créer une Diet active
Règles métier : Snapshot du DietPlan au lancement. Calcul BMR/TDEE/CalorieTarget depuis le poids réel. Invariant cross-agrégat NTR-65 : GetActiveByUserIdAsync → 409 si Diet active existe déjà. StartDate imposée système.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "application", "STORY-005"),
    ("SUB-010", "Terminer et déduire une Diet",
     """Objectif : Terminer et déduire une Diet
Règles métier : Terminer une Diet (passer en Archived + EndDate système). Déduire la Diet active à la date d'un Meal (pour le bilan nutritionnel).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "application", "STORY-005"),
    ("SUB-011", "Gérer les repas (création, liste, suppression)",
     """Objectif : Gérer les repas (création, liste, suppression)
Règles métier : Créer un Meal avec calcul NutritionInfo pour chaque MealItem. Lister les repas sauvegardés (IsSaved = true). Supprimer un Meal.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "application", "STORY-006"),
    ("SUB-012", "Rechercher et gérer les aliments personnels",
     """Objectif : Rechercher et gérer les aliments personnels
Règles métier : Rechercher par mot-clé (Redis → PostgreSQL fallback). Sauvegarder un FoodItem dans la liste personnelle. Supprimer et lister les SavedFoodItem d'un utilisateur.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "application", "STORY-007"),
    ("SUB-013", "Calculer le bilan nutritionnel",
     """Objectif : Calculer le bilan nutritionnel
Règles métier : Agréger les MealItems par jour sur la période de la Diet. Inclure les WeightEntries. Produire un NutritionBilanResponse (dailyData + weightEntries + summary).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "application", "STORY-008"),
    ("SUB-014", "Implémenter les DTOs Request et Response",
     """Objectif : Implémenter les DTOs Request et Response
Règles métier : Un DTO Request + Response par use case : CreateUserProfileRequest/Response, CreateDietPlanRequest/Response, LaunchDietPlanRequest/DietResponse, CreateMealRequest/Response, FoodItemSearchResponse, SaveFoodItemRequest, NutritionBilanResponse.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "application", "STORY-009"),
    ("SUB-015", "Tester DietService — lancement et invariants cross-agrégat",
     """Objectif : Tester DietService — lancement et invariants cross-agrégat
Règles métier : LaunchAsync : 409 si Diet active existe déjà (NTR-65). Calcul BMR/TDEE/CalorieTarget correct. Snapshot immuable du DietPlan.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "application", "STORY-010"),
    ("SUB-016", "Tester UserService et FoodItemService — invariants cross-agrégat",
     """Objectif : Tester UserService et FoodItemService — invariants cross-agrégat
Règles métier : UserService : 409 si SavedFoodItem dupliqué pour un User (NTR-67). FoodItemService : recherche Redis → PostgreSQL fallback.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "application", "STORY-010"),
    ("SUB-017", "Tester NutritionService — calcul bilan",
     """Objectif : Tester NutritionService — calcul bilan
Règles métier : Agrégation correcte des MealItems par jour. WeightEntries incluses. Résultat conforme au NutritionBilanResponse attendu.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "application", "STORY-010"),
    ("SUB-018", "Configurer Docker Compose local (PostgreSQL, Keycloak, Redis)",
     """Objectif : Configurer Docker Compose local (PostgreSQL, Keycloak, Redis)
Règles métier : docker-compose.yml avec PostgreSQL 16, Keycloak 24, Redis 7. Fichier .env.example. Export realm Keycloak de développement (realm nutrition, 2 clients, 2 utilisateurs de test).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "infrastructure", "STORY-011"),
    ("SUB-019", "Configurer le mapping EF Core des Aggregate Roots",
     """Objectif : Configurer le mapping EF Core des Aggregate Roots
Règles métier : Fluent API uniquement dans NutritionApi.Infrastructure/Configurations/. User, DietPlan, Diet, Meal, FoodItem — clés, relations, index.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "infrastructure", "STORY-012"),
    ("SUB-020", "Configurer les Value Objects et entités enfants EF Core",
     """Objectif : Configurer les Value Objects et entités enfants EF Core
Règles métier : MacroDistribution et NutritionInfo en owned entities. WeightEntry, MealItem, SavedFoodItem. Index unique sur WeightEntry(UserId+MeasuredAt) et SavedFoodItem(UserId+FoodItemId).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "infrastructure", "STORY-012"),
    ("SUB-021", "Implémenter les repositories",
     """Objectif : Implémenter les repositories
Règles métier : Interface + implémentation pour chaque Aggregate Root : IUserRepository, IDietPlanRepository, IDietRepository, IMealRepository, IFoodItemRepository, IWeightEntryRepository, ISavedFoodItemRepository.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "infrastructure", "STORY-012"),
    ("SUB-022", "Générer la migration initiale et l'import OFF initial",
     """Objectif : Générer la migration initiale et l'import OFF initial
Règles métier : Migration EF Core initiale couvrant toutes les tables. Seed initial du dump Open Food Facts pour la première installation.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "infrastructure", "STORY-012"),
    ("SUB-023", "Implémenter le cache Redis des recherches alimentaires",
     """Objectif : Implémenter le cache Redis des recherches alimentaires
Règles métier : IFoodCacheService / FoodCacheService — get/set par mot-clé avec TTL court. IConnectionMultiplexer injecté.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "infrastructure", "STORY-013"),
    ("SUB-024", "Télécharger et traiter le dump Open Food Facts",
     """Objectif : Télécharger et traiter le dump Open Food Facts
Règles métier : Job Hangfire quotidien (cron 0 3 * * *). Téléchargement JSONL/CSV. Traitement par batch INSERT/UPDATE FoodItem. Retry automatique Hangfire en cas d'échec.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "infrastructure", "STORY-013"),
    ("SUB-025", "Tester les repositories avec Testcontainers",
     """Objectif : Tester les repositories avec Testcontainers
Règles métier : PostgreSQL réel via Testcontainers. Couvrir les opérations CRUD et les requêtes métier (GetActiveByUserId, GetByUserAndFoodItemId, etc.).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "infrastructure", "STORY-014"),
    ("SUB-026", "Tester le cache Redis et le job import OFF",
     """Objectif : Tester le cache Redis et le job import OFF
Règles métier : Cache Redis : get miss → fallback PostgreSQL → set cache. Job import OFF : traitement d'un dump de test, vérification INSERT/UPDATE correct.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "infrastructure", "STORY-014"),
    ("SUB-027", "Configurer le middleware (JWT, extraction User, erreurs, logging)",
     """Objectif : Configurer le middleware (JWT, extraction User, erreurs, logging)
Règles métier : Validation JWT Keycloak (signature + audience + expiration). Extraction sub → résolution User.KeycloakId → User.Id. Gestion globale des erreurs (middleware exception → codes HTTP). Logging des requêtes.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "api", "STORY-015"),
    ("SUB-028", "Configurer OpenAPI / Swagger UI",
     """Objectif : Configurer OpenAPI / Swagger UI
Règles métier : AddSwaggerGen avec titre, version, sécurité JWT Bearer. UseSwagger + UseSwaggerUI hors production uniquement. Commentaires XML activés. Dashboard Hangfire exclu de la spec.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "api", "STORY-015"),
    ("SUB-029", "Implémenter les endpoints profil et pesées",
     """Objectif : Implémenter les endpoints profil et pesées
Règles métier : POST /users/me, GET /users/me, PUT /users/me, POST /users/me/weight-entries, GET /users/me/weight-entries, PUT /users/me/weight-entries/{id}.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "api", "STORY-016"),
    ("SUB-030", "Implémenter les endpoints aliments personnels et RGPD",
     """Objectif : Implémenter les endpoints aliments personnels et RGPD
Règles métier : GET /users/me/saved-food-items, POST /users/me/saved-food-items, DELETE /users/me/saved-food-items/{id}. DELETE /users/me (RGPD Art. 17), POST /users/me/reactivate, GET /users/me/export (RGPD Art. 20).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "api", "STORY-016"),
    ("SUB-031", "Implémenter les endpoints DietPlan",
     """Objectif : Implémenter les endpoints DietPlan
Règles métier : POST /diet-plans, GET /diet-plans, PUT /diet-plans/{id}, DELETE /diet-plans/{id}, POST /diet-plans/{id}/launch.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "api", "STORY-017"),
    ("SUB-032", "Implémenter les endpoints Diet et bilan",
     """Objectif : Implémenter les endpoints Diet et bilan
Règles métier : GET /diets/active, GET /diets, GET /diets/{id}, POST /diets/{id}/archive, GET /diets/{id}/bilan (params : period, date, startDate).
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "api", "STORY-018"),
    ("SUB-033", "Implémenter les endpoints Meal",
     """Objectif : Implémenter les endpoints Meal
Règles métier : POST /meals, GET /meals, GET /meals/{id}, DELETE /meals/{id}, POST /meals/{id}/items, DELETE /meals/{id}/items/{itemId}.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "api", "STORY-019"),
    ("SUB-034", "Implémenter les endpoints FoodItem",
     """Objectif : Implémenter les endpoints FoodItem
Règles métier : GET /food-items?search={motclé} — recherche par mot-clé avec fallback Redis → PostgreSQL.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "Medium", "api", "STORY-019"),
    ("SUB-035", "Tester les endpoints utilisateur et régimes",
     """Objectif : Tester les endpoints utilisateur et régimes
Règles métier : UsersController, DietPlansController, DietsController — cas nominaux + cas d'erreur (400, 401, 403, 404, 409). Validation JWT.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "api", "STORY-020"),
    ("SUB-036", "Tester les endpoints repas et aliments",
     """Objectif : Tester les endpoints repas et aliments
Règles métier : MealsController, FoodItemsController — cas nominaux + cas d'erreur. Bilan nutritionnel GET /diets/{id}/bilan.
Critères d'acceptation :
- [ ] L'implémentation respecte les règles métier décrites
- [ ] Les cas d'erreur sont couverts""",
     "High", "api", "STORY-020"),
]
