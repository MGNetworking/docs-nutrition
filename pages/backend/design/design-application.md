# Design technique — Couche Application

> Document de référence obligatoire avant tout ticket de la couche Application.
> Source de vérité : `docs/pages/backend/livrable/checklist-implementation.md`
> Modèle domaine : `docs/pages/backend/design/design-domain.md`

---

## 1. Pattern architectural retenu

**Services applicatifs** — un service par domaine fonctionnel.

Chaque service orchestre un ensemble de cas d'usage cohérents. Il charge les agrégats via les repositories, appelle les méthodes métier du Domain, persiste les changements, puis retourne un DTO.

```
Controller → XxxService → IXxxRepository (interface)
                        → Domain (entités, invariants)
                        → DTO (réponse)
```

**Ce que le service NE fait PAS :**
- Contenir des règles métier — elles restent dans le Domain
- Accéder directement à la base de données — il passe par les interfaces de repositories
- Retourner des entités Domain — il retourne uniquement des DTOs

---

## 2. Structure des dossiers

```
src/NutritionApi.Application/
├── Services/
│   ├── UserService.cs
│   ├── DietPlanService.cs
│   ├── DietService.cs
│   ├── MealService.cs
│   ├── FoodItemService.cs
│   ├── NutritionService.cs
│   ├── AdminService.cs
│   └── SubscriptionGuard.cs
├── Interfaces/
│   ├── Repositories/
│   │   ├── IUserRepository.cs
│   │   ├── IDietPlanRepository.cs
│   │   ├── IDietRepository.cs
│   │   ├── IMealRepository.cs
│   │   ├── IFoodItemRepository.cs
│   │   ├── IWeightEntryRepository.cs
│   │   └── ISavedFoodItemRepository.cs
│   ├── Services/
│   │   ├── IUserService.cs               ← contrat pour UsersController
│   │   ├── IDietPlanService.cs           ← contrat pour DietPlansController
│   │   ├── IDietService.cs               ← contrat pour DietsController
│   │   ├── IMealService.cs               ← contrat pour MealsController
│   │   ├── IFoodItemService.cs           ← contrat pour FoodItemsController
│   │   ├── INutritionService.cs          ← contrat pour DietsController (bilan)
│   │   └── IAdminService.cs              ← contrat pour AdminController
│   └── ExternalServices/
│       ├── IFoodCacheService.cs          ← contrat cache Redis (implémenté en Infrastructure)
│       ├── IKeycloakAdminService.cs      ← contrat Keycloak Admin (implémenté en Infrastructure)
│       └── IEmailService.cs             ← contrat envoi email (implémenté en Infrastructure)
├── DTOs/
│   ├── Users/
│   │   ├── CreateUserProfileRequest.cs
│   │   ├── UpdateUserProfileRequest.cs
│   │   └── UserProfileResponse.cs
│   ├── DietPlans/
│   │   ├── CreateDietPlanRequest.cs
│   │   ├── UpdateDietPlanRequest.cs
│   │   └── DietPlanResponse.cs
│   ├── Diets/
│   │   ├── LaunchDietPlanRequest.cs
│   │   └── DietResponse.cs
│   ├── Meals/
│   │   ├── CreateMealRequest.cs
│   │   └── MealResponse.cs
│   ├── FoodItems/
│   │   ├── SaveFoodItemRequest.cs
│   │   └── FoodItemSearchResponse.cs
│   ├── Nutrition/
│   │   └── NutritionBilanResponse.cs
│   └── Admin/
│       ├── AdminDashboardResponse.cs
│       └── SystemHealthResponse.cs
├── Exceptions/
│   ├── NotFoundException.cs
│   ├── ConflictException.cs
│   ├── ForbiddenException.cs
│   └── UnprocessableException.cs
└── DependencyInjection.cs               ← enregistrement des services Application
```

---

## 3. Conventions de nommage

| Type | Convention | Exemple |
|---|---|---|
| Service | `XxxService` | `UserService`, `DietPlanService` |
| DTO request création | `CreateXxxRequest` | `CreateUserProfileRequest` |
| DTO request mise à jour | `UpdateXxxRequest` | `UpdateUserProfileRequest` |
| DTO request action | `[Verbe]XxxRequest` | `LaunchDietPlanRequest` |
| DTO response | `XxxResponse` | `UserProfileResponse`, `DietPlanResponse` |
| Interface repository | `IXxxRepository` | `IUserRepository` |
| Interface service applicatif | `IXxxService` | `IUserService`, `IDietPlanService` |
| Interface service externe | `IXxxService` | `IFoodCacheService`, `IKeycloakAdminService` |
| Exception applicative | `XxxException` | `NotFoundException` |

---

## 4. Interfaces de repositories

Les interfaces sont définies dans la couche Application. L'Infrastructure les implémente.

### IUserRepository

```csharp
public interface IUserRepository
{
    Task<User?> GetByIdAsync(Guid id);
    Task<User?> GetByKeycloakIdAsync(string keycloakId);
    Task AddAsync(User user);
    Task UpdateAsync(User user);
}
```

### IDietPlanRepository

```csharp
public interface IDietPlanRepository
{
    Task<DietPlan?> GetByIdAsync(Guid id);
    Task<List<DietPlan>> GetByUserIdAsync(Guid userId);
    Task<List<DietPlan>> GetTemplatesAsync();
    Task AddAsync(DietPlan dietPlan);
    Task UpdateAsync(DietPlan dietPlan);
    Task DeleteAsync(Guid id);
    Task<int> CountByUserIdAsync(Guid userId);
}
```

### IDietRepository

```csharp
public interface IDietRepository
{
    Task<Diet?> GetByIdAsync(Guid id);
    Task<Diet?> GetActiveByUserIdAsync(Guid userId);
    Task<List<Diet>> GetByUserIdAsync(Guid userId);
    Task AddAsync(Diet diet);
    Task UpdateAsync(Diet diet);
}
```

### IMealRepository

```csharp
public interface IMealRepository
{
    Task<Meal?> GetByIdAsync(Guid id);
    Task<List<Meal>> GetByUserIdAsync(Guid userId, DateOnly? date = null, bool? saved = null);
    Task AddAsync(Meal meal);
    Task UpdateAsync(Meal meal);
    Task DeleteAsync(Guid id);
    Task<int> CountSavedByUserIdAsync(Guid userId);
}
```

### IFoodItemRepository

```csharp
public interface IFoodItemRepository
{
    Task<FoodItem?> GetByIdAsync(Guid id);
    Task<FoodItem?> GetByOffIdAsync(string offId);
    Task<List<FoodItem>> SearchByKeywordAsync(string keyword, int limit = 20);
    Task AddAsync(FoodItem foodItem);
    Task UpdateAsync(FoodItem foodItem);
    Task<int> CountAsync();
}
```

### IWeightEntryRepository

```csharp
public interface IWeightEntryRepository
{
    Task<WeightEntry?> GetByIdAsync(Guid id);
    Task<WeightEntry?> GetByUserIdAndDateAsync(Guid userId, DateOnly date);
    Task<List<WeightEntry>> GetByUserIdAsync(Guid userId);
    Task AddAsync(WeightEntry entry);
    Task UpdateAsync(WeightEntry entry);
}
```

### ISavedFoodItemRepository

```csharp
public interface ISavedFoodItemRepository
{
    Task<SavedFoodItem?> GetByIdAsync(Guid id);
    Task<SavedFoodItem?> GetByUserIdAndFoodItemIdAsync(Guid userId, Guid foodItemId);
    Task<List<SavedFoodItem>> GetByUserIdAsync(Guid userId);
    Task AddAsync(SavedFoodItem savedFoodItem);
    Task DeleteAsync(Guid id);
    Task<int> CountByUserIdAsync(Guid userId);
}
```

### IUnitOfWork

```csharp
public interface IUnitOfWork
{
    Task SaveChangesAsync();
}
```

> `AppDbContext` (Infrastructure) implémente cette interface. Elle est injectée dans tous les services qui effectuent des opérations d'écriture atomiques.

---

## 4bis. Interfaces de services applicatifs

Ces interfaces définissent le **contrat entre la couche API et la couche Application**. Elles permettent à l'API de dépendre d'abstractions plutôt que de classes concrètes — prérequis pour une implémentation API-first.

**Règle :** chaque controller injecte `IXxxService`, jamais `XxxService` directement.

```
API layer         → dépend de IXxxService      (défini ici)
Application layer → implémente IXxxService     (XxxService.cs)
```

### IUserService

```csharp
public interface IUserService
{
    Task<UserProfileResponse> CreateUserProfileAsync(string keycloakId, CreateUserProfileRequest request);
    Task<UserProfileResponse> GetUserProfileAsync(string keycloakId);
    Task<UserProfileResponse> UpdateUserProfileAsync(string keycloakId, UpdateUserProfileRequest request);
    Task DeleteUserAsync(string keycloakId);
    Task<UserProfileResponse> ReactivateUserAsync(string keycloakId);
    Task<object> ExportUserDataAsync(string keycloakId);
    Task<WeightEntryResponse> AddWeightEntryAsync(Guid userId, AddWeightEntryRequest request);
    Task<List<WeightEntryResponse>> GetWeightHistoryAsync(Guid userId);
    Task<WeightEntryResponse> UpdateWeightEntryAsync(Guid userId, Guid entryId, UpdateWeightEntryRequest request);
}
```

### IDietPlanService

```csharp
public interface IDietPlanService
{
    Task<List<DietPlanResponse>> GetUserPlansAsync(Guid userId);
    Task<DietPlanResponse> CreateAsync(Guid userId, CreateDietPlanRequest request);
    Task<DietPlanResponse> UpdateAsync(Guid userId, Guid planId, UpdateDietPlanRequest request);
    Task DeleteAsync(Guid userId, Guid planId);
    Task<DietResponse> LaunchAsync(Guid userId, Guid planId);
    Task<List<DietPlanResponse>> GetTemplatesAsync(Guid userId);
}
```

### IDietService

```csharp
public interface IDietService
{
    Task<DietResponse> GetActiveAsync(Guid userId);
    Task<List<DietResponse>> GetHistoryAsync(Guid userId);
    Task<DietResponse> GetByIdAsync(Guid userId, Guid dietId);
    Task<DietResponse> ArchiveAsync(Guid userId, Guid dietId);
    Task<NutritionBilanResponse> GetBilanAsync(Guid userId, Guid dietId, string period, DateOnly? date, DateOnly? startDate, DateOnly? endDate);
}
```

### IMealService

```csharp
public interface IMealService
{
    Task<MealResponse> CreateAsync(Guid userId, CreateMealRequest request);
    Task<List<MealResponse>> GetAllAsync(Guid userId, bool? saved, DateOnly? date);
    Task<MealResponse> GetByIdAsync(Guid userId, Guid mealId);
    Task<MealResponse> UpdateAsync(Guid userId, Guid mealId, UpdateMealRequest request);
    Task DeleteAsync(Guid userId, Guid mealId);
    Task<MealResponse> AddItemAsync(Guid userId, Guid mealId, AddMealItemRequest request);
    Task<MealResponse> RemoveItemAsync(Guid userId, Guid mealId, Guid itemId);
}
```

### IFoodItemService

```csharp
public interface IFoodItemService
{
    Task<List<FoodItemSearchResponse>> SearchAsync(string keyword, int limit = 20);
    Task<List<SavedFoodItemResponse>> GetSavedAsync(Guid userId);
    Task<SavedFoodItemResponse> SaveAsync(Guid userId, SaveFoodItemRequest request);
    Task RemoveSavedAsync(Guid userId, Guid savedId);
}
```

### INutritionService

```csharp
public interface INutritionService
{
    Task<NutritionBilanResponse> GetBilanAsync(Guid userId, Guid dietId, string period, DateOnly? date, DateOnly? startDate, DateOnly? endDate);
}
```

### IAdminService

```csharp
public interface IAdminService
{
    Task<AdminDashboardResponse> GetDashboardAsync();
    Task<SystemHealthResponse> GetSystemHealthAsync();
    Task<DietPlanResponse> CreateTemplateAsync(CreateDietPlanRequest request);
    Task<DietPlanResponse> UpdateTemplateAsync(Guid templateId, UpdateDietPlanRequest request);
    Task DeleteTemplateAsync(Guid templateId);
}
```

---

## 4ter. Interfaces de services externes

Ces interfaces définissent le **contrat entre la couche Application et les services externes** (Infrastructure les implémente). L'Application ne connaît jamais les détails d'implémentation (Redis, Keycloak, SMTP...).

### IFoodCacheService

```csharp
public interface IFoodCacheService
{
    Task<List<FoodItemSearchResponse>?> GetAsync(string keyword);
    Task SetAsync(string keyword, List<FoodItemSearchResponse> results);
    Task InvalidateAsync(string keyword);
}
```

### IKeycloakAdminService

```csharp
public interface IKeycloakAdminService
{
    Task DisableUserAsync(string keycloakId);
    Task EnableUserAsync(string keycloakId);
    Task DeleteUserAsync(string keycloakId);
}
```

### IEmailService

```csharp
public interface IEmailService
{
    Task SendReactivationEmailAsync(string toEmail, string reactivationLink, TimeSpan validity);
}
```

> Utilisé par `UserService.DeleteUserAsync()` — envoie le lien signé de réactivation valable 30 jours (workflow RGPD).
> Implémenté dans Infrastructure — le fournisseur SMTP/email est un détail d'infrastructure.

---

## 5. Services applicatifs

### UserService

**Responsabilités :**
- Créer le profil utilisateur + première `WeightEntry`
- Mettre à jour les données biométriques
- Ajouter une `WeightEntry`
- Retourner le profil avec calcul `NutritionNeeds` (BMR/TDEE) — uniquement sur `GetProfileAsync`, pas à la création

**Signatures :**
```csharp
Task<UserProfileResponse> CreateUserProfileAsync(string keycloakId, CreateUserProfileRequest request);
Task<UserProfileResponse> UpdateUserProfileAsync(string keycloakId, UpdateUserProfileRequest request);
```

> `keycloakId` vient du token JWT (claim `sub`) — jamais dans le body de la requête. Le controller l'extrait depuis `HttpContext.User` et le passe en paramètre séparé.

**Dépendances :** `IUserRepository`, `IWeightEntryRepository`, `IUnitOfWork`

---

### DietPlanService

**Responsabilités :**
- CRUD complet des `DietPlan` personnels
- Lister les templates partagés (`IsTemplate = true`)
- Vérifier les limites de tier via `SubscriptionGuard` avant création

**Dépendances :** `IDietPlanRepository`, `SubscriptionGuard`

---

### DietService

**Responsabilités :**
- Lancer un `DietPlan` → créer une `Diet` (snapshot + calcul BMR/TDEE/CalorieTarget)
- Bloquer le lancement si une `Diet` active existe déjà (`ConflictException`)
- Archiver une `Diet` active
- Récupérer la `Diet` active ou l'historique

**Dépendances :** `IDietRepository`, `IDietPlanRepository`, `IUserRepository`

---

### MealService

**Responsabilités :**
- Créer un `Meal` avec calcul `NutritionInfo` pour chaque `MealItem`
- Lister les repas (filtre par date, `IsSaved`)
- Modifier les propriétés d'un repas (name, mealType, notes, consumedAt)
- Supprimer un `Meal`
- Vérifier les limites de tier via `SubscriptionGuard` avant création de repas sauvegardé

**Dépendances :** `IMealRepository`, `IFoodItemRepository`, `SubscriptionGuard`

---

### FoodItemService

**Responsabilités :**
- Rechercher des aliments (Redis → PostgreSQL si cache manquant)
- Sauvegarder / supprimer un `SavedFoodItem`
- Lister les `SavedFoodItem` d'un utilisateur
- Vérifier les limites de tier via `SubscriptionGuard`

**Dépendances :** `IFoodItemRepository`, `ISavedFoodItemRepository`, `IFoodCacheService`, `SubscriptionGuard`

---

### NutritionService

**Responsabilités :**
- Calculer le bilan nutritionnel d'une `Diet` sur une période
- Agréger les `MealItem` + `WeightEntry` par jour
- Restreindre la période selon le tier (`SubscriptionGuard`)

**Dépendances :** `IDietRepository`, `IMealRepository`, `IWeightEntryRepository`, `SubscriptionGuard`

---

### SubscriptionGuard

**Responsabilités :**
- Centraliser toutes les vérifications de limites par tier
- Lever une `ForbiddenException` si la limite est atteinte ou le tier insuffisant

**Limites par tier :**

| Ressource | Free | Pro | Business |
|---|---|---|---|
| DietPlans personnels | 2 | 20 | Illimité |
| Accès templates | ❌ | ✅ | ✅ |
| Repas sauvegardés | 5 | 50 | Illimité |
| SavedFoodItems | 10 | 100 | Illimité |
| Période bilan | 7 jours | 1 an | Illimité |

**Dépendances :** aucune (logique pure, pas de repository)

---

### AdminService

**Responsabilités :**
- Agréger les KPIs utilisateurs (total, par tier, nouveaux 7 derniers jours)
- Agréger les métriques d'activité (diets actives, repas 7j, comptes en grace period)
- Agréger la santé système depuis les tables Hangfire

**Dépendances :** `IUserRepository`, `IDietRepository`, `IMealRepository`

---

## 6. DTOs

Les DTOs sont des `record` C# — immuables, égalité par valeur.

**Règle :** un DTO ne contient jamais d'entité Domain. Il ne contient que des types primitifs, d'autres records, ou des enums.

| DTO Request | DTO Response | Service |
|---|---|---|
| `CreateUserProfileRequest` | `UserProfileResponse` | `UserService` |
| `UpdateUserProfileRequest` | `UserProfileResponse` | `UserService` |
| — | `WeightEntryResponse` | `UserService` |
| `CreateDietPlanRequest` | `DietPlanResponse` | `DietPlanService` |
| `UpdateDietPlanRequest` | `DietPlanResponse` | `DietPlanService` |
| `LaunchDietPlanRequest` | `DietResponse` | `DietService` |
| `CreateMealRequest` | `MealResponse` | `MealService` |
| `SaveFoodItemRequest` | — | `FoodItemService` |
| — | `FoodItemSearchResponse` | `FoodItemService` |
| — | `NutritionBilanResponse` | `NutritionService` |
| — | `AdminDashboardResponse` | `AdminService` |
| — | `SystemHealthResponse` | `AdminService` |

**Champs des DTOs Users :**

| DTO | Champs |
|---|---|
| `CreateUserProfileRequest` | `BirthDate`, `Gender`, `ActivityLevel`, `Height`, `Weight`, `Allergies`, `DietaryPreferences` |
| `UpdateUserProfileRequest` | `BirthDate`, `Gender`, `ActivityLevel`, `Height`, `Allergies`, `DietaryPreferences` |
| `UserProfileResponse` | `Id`, `KeycloakId`, `BirthDate`, `Gender`, `ActivityLevel`, `Height`, `Allergies`, `DietaryPreferences`, `SubscriptionTier`, `CreatedAt`, `Bmr?`, `Tdee?`, `TargetCalories?`, `LatestWeight?` |
| `AddWeightEntryRequest` | `Weight`, `MeasuredAt?` (défaut aujourd'hui) |
| `UpdateWeightEntryRequest` | `Weight`, `MeasuredAt` |
| `WeightEntryResponse` | `Id`, `Weight`, `MeasuredAt` |
| `SaveFoodItemRequest` | `FoodItemId` |
| `SavedFoodItemResponse` | `Id`, `FoodItemId`, `Name`, `CaloriesPer100g`, `SavedAt` |

> `UserProfileResponse` — `Bmr`, `Tdee`, `TargetCalories`, `LatestWeight` sont `null` à la création (POST) et calculés uniquement sur `GetProfileAsync` (GET /users/me).

**Champs des DTOs DietPlans :**

| DTO | Champs |
|---|---|
| `CreateDietPlanRequest` | `Name`, `DietType`, `Goal`, `TargetWeight`, `MacroDistribution` (ProteinPct, CarbPct, FatPct) |
| `UpdateDietPlanRequest` | `Name`, `DietType`, `Goal`, `TargetWeight`, `MacroDistribution` |
| `DietPlanResponse` | `Id`, `Name`, `DietType`, `Goal`, `TargetWeight`, `MacroDistribution`, `IsTemplate` |

**Champs des DTOs Diets :**

| DTO | Champs |
|---|---|
| `LaunchDietPlanRequest` | *(aucun champ — StartDate imposée système)* |
| `DietResponse` | `Id`, `Name`, `DietType`, `Goal`, `TargetWeight`, `CalorieTarget`, `MacroDistribution`, `Status`, `StartDate`, `EndDate?` |
| `NutritionBilanResponse` | `DietId`, `StartDate`, `EndDate`, `TotalCalories`, `TotalProteins`, `TotalCarbs`, `TotalFats`, `DailyBreakdown[]`, `WeightProgression[]` |

**Champs des DTOs Meals :**

| DTO | Champs |
|---|---|
| `CreateMealRequest` | `Name`, `MealType`, `ConsumedAt`, `Notes?`, `IsSaved`, `Items[]` (FoodItemId, Quantity) |
| `UpdateMealRequest` | `Name?`, `MealType?`, `Notes?`, `ConsumedAt?`, `IsSaved?` |
| `AddMealItemRequest` | `FoodItemId`, `Quantity` (grammes) |
| `MealResponse` | `Id`, `Name`, `MealType`, `ConsumedAt`, `Notes?`, `IsSaved`, `Items[]` |
| `MealItemResponse` | `Id`, `FoodItemId`, `FoodName`, `Quantity`, `Calories`, `Proteins`, `Carbs`, `Fats` |

**Champs des DTOs FoodItems :**

| DTO | Champs |
|---|---|
| `FoodItemSearchResponse` | `Id`, `Name`, `CaloriesPer100g`, `ProteinsPer100g`, `CarbsPer100g`, `FatsPer100g`, `AllergensTags[]` |

**Champs des DTOs Admin :**

| DTO | Champs |
|---|---|
| `AdminDashboardResponse` | `TotalUsers`, `UsersByTier` (Free/Pro/Business), `NewUsersLast7Days`, `ActiveDiets`, `MealsLast7Days`, `UsersInGracePeriod` |
| `SystemHealthResponse` | `FoodItemsCount`, `LastImportAt?`, `HangfireJobs[]` (JobName, LastRun, NextRun, Status) |

---

## 7. Gestion des erreurs

Les exceptions applicatives vivent dans `Application/Exceptions/`. La couche API les intercepte via un middleware et les traduit en codes HTTP.

| Exception | Signification | Code HTTP |
|---|---|---|
| `NotFoundException` | Ressource introuvable | 404 |
| `ConflictException` | Conflit d'état (ex : Diet active déjà existante) | 409 |
| `ForbiddenException` | Tier insuffisant ou rôle manquant | 403 |
| `UnprocessableException` | Données valides mais règle métier violée | 422 |

**Règle :** les services lèvent ces exceptions. Ils ne retournent jamais `null` pour signaler une erreur — ils lèvent toujours une exception explicite.

---

## 8. Injection de dépendances

Chaque couche expose une extension `AddXxx()` appelée dans `Program.cs`.

**Prérequis — package NuGet à ajouter dans `NutritionApi.Application` :**

```bash
dotnet add package Microsoft.Extensions.DependencyInjection.Abstractions
```

> Ce package fournit `IServiceCollection`. Il est nécessaire dans les projets class library — il n'est pas inclus automatiquement contrairement aux projets ASP.NET Core.
> `NutritionApi.Infrastructure` aura besoin du même package pour son propre `DependencyInjection.cs`.

```csharp
// Application/DependencyInjection.cs
public static class ApplicationExtensions
{
    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        services.AddScoped<UserService>();
        services.AddScoped<DietPlanService>();
        services.AddScoped<DietService>();
        services.AddScoped<MealService>();
        services.AddScoped<FoodItemService>();
        services.AddScoped<NutritionService>();
        services.AddScoped<AdminService>();
        services.AddScoped<SubscriptionGuard>();
        return services;
    }
}
```

```csharp
// Api/Program.cs
using NutritionApi.Application; // ← using obligatoire pour résoudre AddApplication()

builder.Services.AddApplication();
// Les repositories (IXxxRepository → XxxRepository) sont enregistrés dans AddInfrastructure()
```

**Durée de vie :** tous les services Application sont `Scoped` — une instance par requête HTTP.

---

## 9. Règles transverses

- **Un service = un domaine fonctionnel.** Ne pas créer de service générique `AppService` ou `BaseService`.
- **Les repositories sont injectés par interface.** Jamais par implémentation concrète.
- **`SubscriptionGuard` est appelé en début de méthode**, avant toute opération de lecture ou d'écriture.
- **Les DTOs Request ne sont jamais passés au Domain.** Le service extrait les valeurs primitives et les passe aux constructeurs/méthodes des entités.
- **Les entités Domain ne traversent jamais la frontière Application → API.** Seuls les DTOs Response sortent du service.
- **Workflow API-first.** Avant de coder les DTOs et services d'un ticket, définir les champs exacts des endpoints dans `design-api.md`. Les DTOs découlent des contrats d'endpoint, pas l'inverse.
