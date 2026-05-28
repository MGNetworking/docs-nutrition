# Design technique — Couche Application

> Document de référence obligatoire avant tout ticket de la couche Application.
> Source de vérité : `docs/pages/backend/livrable/checklist-implementation.md`
> Modèle domaine : `docs/pages/backend/domaine/Modele-domaine.md`

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
│   └── Services/
│       ├── IFoodCacheService.cs          ← contrat du cache Redis (implémenté en Infrastructure)
│       └── IKeycloakAdminService.cs      ← contrat Keycloak Admin (implémenté en Infrastructure)
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
| Interface service externe | `IXxxService` | `IFoodCacheService` |
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

---

## 5. Services applicatifs

### UserService

**Responsabilités :**
- Créer le profil utilisateur + première `WeightEntry`
- Mettre à jour les données biométriques
- Ajouter une `WeightEntry`
- Calculer `NutritionNeeds` (BMR/TDEE) à la demande — via le Domain, sans persistance

**Dépendances :** `IUserRepository`, `IWeightEntryRepository`

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

**`UserProfileResponse`** doit inclure : données biométriques + `Bmr` + `Tdee` calculés à la demande (non persistés).

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
