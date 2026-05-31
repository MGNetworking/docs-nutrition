# Design technique — Couche Infrastructure

> Document de référence obligatoire avant tout ticket de la couche Infrastructure.
> Source de vérité : `docs/pages/backend/livrable/checklist-implementation.md`
> Modèle domaine : `docs/pages/backend/design/design-domain.md`

---

## 1. Structure des dossiers

```text
src/NutritionApi.Infrastructure/
├── Persistence/
│   ├── AppDbContext.cs                    ← DbContext principal + IUnitOfWork
│   ├── Configurations/                    ← Fluent API, un fichier par entité
│   │   ├── UserConfiguration.cs
│   │   ├── DietPlanConfiguration.cs
│   │   ├── DietConfiguration.cs
│   │   ├── MealConfiguration.cs
│   │   ├── MealItemConfiguration.cs
│   │   ├── WeightEntryConfiguration.cs
│   │   ├── FoodItemConfiguration.cs
│   │   └── SavedFoodItemConfiguration.cs
│   ├── Repositories/
│   │   ├── UserRepository.cs
│   │   ├── DietPlanRepository.cs
│   │   ├── DietRepository.cs
│   │   ├── MealRepository.cs
│   │   ├── FoodItemRepository.cs
│   │   ├── WeightEntryRepository.cs
│   │   └── SavedFoodItemRepository.cs
│   └── Migrations/                        ← générées par EF Core CLI
├── Cache/
│   └── RedisFoodCacheService.cs           ← implémente IFoodCacheService
├── Jobs/
│   ├── IOffImportJob.cs
│   ├── OffImportJob.cs
│   ├── IRgpdPurgeJob.cs
│   └── RgpdPurgeJob.cs
├── ExternalServices/
│   └── KeycloakAdminService.cs            ← implémente IKeycloakAdminService
└── DependencyInjection.cs                 ← enregistrement des services Infrastructure
```

---

## 2. Configuration EF Core

### DbContext

```csharp
// Infrastructure/Persistence/AppDbContext.cs
public class AppDbContext : DbContext, IUnitOfWork
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<User> Users => Set<User>();
    public DbSet<DietPlan> DietPlans => Set<DietPlan>();
    public DbSet<Diet> Diets => Set<Diet>();
    public DbSet<Meal> Meals => Set<Meal>();
    public DbSet<MealItem> MealItems => Set<MealItem>();
    public DbSet<WeightEntry> WeightEntries => Set<WeightEntry>();
    public DbSet<FoodItem> FoodItems => Set<FoodItem>();
    public DbSet<SavedFoodItem> SavedFoodItems => Set<SavedFoodItem>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(AppDbContext).Assembly);
    }

    public async Task<int> SaveChangesAsync(CancellationToken ct = default)
        => await base.SaveChangesAsync(ct);
}
```

### Convention de nommage — snake_case automatique

Le package Npgsql applique automatiquement la conversion PascalCase → snake_case.

```csharp
// Program.cs / DependencyInjection.cs
services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(connectionString)
           .UseSnakeCaseNamingConvention());
```

| Propriété C# | Colonne PostgreSQL |
|---|---|
| `UserId` | `user_id` |
| `CreatedAt` | `created_at` |
| `MacroProteinPercentage` | `macro_protein_percentage` |
| `CaloriesPer100g` | `calories_per_100g` |

### Approche Fluent API

**Règle :** Fluent API uniquement — aucune Data Annotation sur les entités Domain.

Les entités Domain ne doivent pas connaître la persistance. Toute configuration EF Core est dans `Configurations/`.

### Enums — stockage en string

```csharp
// Exemple dans UserConfiguration.cs
builder.Property(u => u.Gender)
       .HasConversion<string>()
       .HasMaxLength(20);
```

Toutes les propriétés enum sont stockées en `VARCHAR` pour la lisibilité en base.

### Value Objects — Owned Entities

`MacroDistribution` et `NutritionInfo` sont des Value Objects mappés via `OwnsOne` — leurs colonnes sont stockées dans la table de l'entité propriétaire.

```csharp
// Dans DietConfiguration.cs (et DietPlanConfiguration.cs)
builder.OwnsOne(d => d.MacroDistribution, macro =>
{
    macro.Property(m => m.ProteinPercentage).HasColumnName("macro_protein_pct");
    macro.Property(m => m.CarbPercentage).HasColumnName("macro_carb_pct");
    macro.Property(m => m.FatPercentage).HasColumnName("macro_fat_pct");
});

// Dans MealItemConfiguration.cs
builder.OwnsOne(mi => mi.Nutrition, n =>
{
    n.Property(x => x.Calories).HasColumnName("nutrition_calories");
    n.Property(x => x.Proteins).HasColumnName("nutrition_proteins");
    n.Property(x => x.Carbs).HasColumnName("nutrition_carbs");
    n.Property(x => x.Fats).HasColumnName("nutrition_fats");
});
```

### Listes primitives — colonnes PostgreSQL array

`User.Allergies` (`List<Allergen>`) et `User.DietaryPreferences` (`List<string>`) ainsi que `FoodItem.AllergensTags` sont mappées sur des colonnes PostgreSQL array via Npgsql.

```csharp
// Dans UserConfiguration.cs
builder.Property(u => u.Allergies)
       .HasColumnType("text[]")
       .HasConversion(
           v => v.Select(a => a.ToString()).ToArray(),
           v => v.Select(s => Enum.Parse<Allergen>(s)).ToList());

builder.Property(u => u.DietaryPreferences)
       .HasColumnType("text[]");
```

---

## 3. Schéma de la base de données

### Table `users`

| Colonne | Type PostgreSQL | Contraintes |
|---|---|---|
| `id` | `UUID` | PK |
| `keycloak_id` | `VARCHAR(255)` | NOT NULL, UNIQUE |
| `birth_date` | `DATE` | NOT NULL |
| `gender` | `VARCHAR(20)` | NOT NULL |
| `height` | `REAL` | NOT NULL |
| `activity_level` | `VARCHAR(30)` | NOT NULL |
| `allergies` | `TEXT[]` | NOT NULL DEFAULT '{}' |
| `dietary_preferences` | `TEXT[]` | NOT NULL DEFAULT '{}' |
| `subscription_tier` | `VARCHAR(20)` | NOT NULL DEFAULT 'Free' |
| `created_at` | `TIMESTAMPTZ` | NOT NULL |
| `deleted_at` | `TIMESTAMPTZ` | NULL |

### Table `diet_plans`

| Colonne | Type PostgreSQL | Contraintes |
|---|---|---|
| `id` | `UUID` | PK |
| `user_id` | `UUID` | NULL, FK → `users(id)` |
| `is_template` | `BOOLEAN` | NOT NULL DEFAULT false |
| `name` | `VARCHAR(200)` | NOT NULL |
| `diet_type` | `VARCHAR(30)` | NOT NULL |
| `goal` | `VARCHAR(30)` | NOT NULL |
| `target_weight` | `REAL` | NOT NULL |
| `macro_protein_pct` | `INTEGER` | NOT NULL |
| `macro_carb_pct` | `INTEGER` | NOT NULL |
| `macro_fat_pct` | `INTEGER` | NOT NULL |

### Table `diets`

| Colonne | Type PostgreSQL | Contraintes |
|---|---|---|
| `id` | `UUID` | PK |
| `user_id` | `UUID` | NOT NULL, FK → `users(id)` |
| `name` | `VARCHAR(200)` | NOT NULL |
| `diet_type` | `VARCHAR(30)` | NOT NULL |
| `goal` | `VARCHAR(30)` | NOT NULL |
| `target_weight` | `REAL` | NOT NULL |
| `calorie_target` | `INTEGER` | NOT NULL |
| `macro_protein_pct` | `INTEGER` | NOT NULL |
| `macro_carb_pct` | `INTEGER` | NOT NULL |
| `macro_fat_pct` | `INTEGER` | NOT NULL |
| `diet_status` | `VARCHAR(20)` | NOT NULL DEFAULT 'Active' |
| `start_date` | `DATE` | NOT NULL |
| `end_date` | `DATE` | NULL |

### Table `meals`

| Colonne | Type PostgreSQL | Contraintes |
|---|---|---|
| `id` | `UUID` | PK |
| `user_id` | `UUID` | NOT NULL, FK → `users(id)` |
| `name` | `VARCHAR(200)` | NOT NULL |
| `meal_type` | `VARCHAR(20)` | NOT NULL |
| `consumed_at` | `TIMESTAMPTZ` | NOT NULL |
| `notes` | `TEXT` | NULL |
| `is_saved` | `BOOLEAN` | NOT NULL DEFAULT false |

### Table `meal_items`

| Colonne | Type PostgreSQL | Contraintes |
|---|---|---|
| `id` | `UUID` | PK |
| `meal_id` | `UUID` | NOT NULL, FK → `meals(id)` ON DELETE CASCADE |
| `food_item_id` | `UUID` | NOT NULL, FK → `food_items(id)` |
| `quantity` | `REAL` | NOT NULL (grammes) |
| `nutrition_calories` | `REAL` | NOT NULL |
| `nutrition_proteins` | `INTEGER` | NOT NULL |
| `nutrition_carbs` | `INTEGER` | NOT NULL |
| `nutrition_fats` | `INTEGER` | NOT NULL |

### Table `weight_entries`

| Colonne | Type PostgreSQL | Contraintes |
|---|---|---|
| `id` | `UUID` | PK |
| `user_id` | `UUID` | NOT NULL, FK → `users(id)` |
| `weight` | `REAL` | NOT NULL (kg) |
| `measured_at` | `DATE` | NOT NULL |

### Table `food_items`

| Colonne | Type PostgreSQL | Contraintes |
|---|---|---|
| `id` | `UUID` | PK |
| `off_id` | `VARCHAR(100)` | NOT NULL, UNIQUE |
| `name` | `VARCHAR(500)` | NOT NULL |
| `calories_per_100g` | `REAL` | NOT NULL |
| `proteins_per_100g` | `INTEGER` | NOT NULL |
| `carbs_per_100g` | `INTEGER` | NOT NULL |
| `fats_per_100g` | `INTEGER` | NOT NULL |
| `allergens_tags` | `TEXT[]` | NOT NULL DEFAULT '{}' |
| `cached_at` | `TIMESTAMPTZ` | NOT NULL |

### Table `saved_food_items`

| Colonne | Type PostgreSQL | Contraintes |
|---|---|---|
| `id` | `UUID` | PK |
| `user_id` | `UUID` | NOT NULL, FK → `users(id)` |
| `food_item_id` | `UUID` | NOT NULL, FK → `food_items(id)` |
| `saved_at` | `TIMESTAMPTZ` | NOT NULL |

**Contrainte unique :** `(user_id, food_item_id)` — un aliment ne peut être sauvegardé qu'une fois par utilisateur.

---

## 4. Pattern des repositories

### IUnitOfWork

Défini dans la couche **Application** (`Application/Interfaces/IUnitOfWork.cs`). `AppDbContext` l'implémente dans Infrastructure.

```csharp
// Application/Interfaces/IUnitOfWork.cs
public interface IUnitOfWork
{
    Task<int> SaveChangesAsync(CancellationToken ct = default);
}
```

**Règle :** Les méthodes `AddAsync`, `UpdateAsync`, `DeleteAsync` des repositories **ne sauvegardent pas** — elles trackent seulement les changements dans le contexte EF Core. Le service applicatif appelle `IUnitOfWork.SaveChangesAsync()` en fin d'opération pour persister tout en une seule transaction.

```csharp
// Exemple dans UserService.CreateProfileAsync
await _userRepository.AddAsync(user);
await _weightEntryRepository.AddAsync(entry);
await _unitOfWork.SaveChangesAsync();   // ← persistance atomique
```

### Repositories spécialisés

Pas de repository générique — chaque repository implémente l'interface définie dans la couche Application.

**Structure type d'un repository :**

```csharp
// Infrastructure/Persistence/Repositories/UserRepository.cs
public sealed class UserRepository : IUserRepository
{
    private readonly AppDbContext _context;

    public UserRepository(AppDbContext context) => _context = context;

    public async Task<User?> GetByIdAsync(Guid id)
        => await _context.Users.FirstOrDefaultAsync(u => u.Id == id);

    public async Task<User?> GetByKeycloakIdAsync(string keycloakId)
        => await _context.Users.FirstOrDefaultAsync(u => u.KeycloakId == keycloakId);

    public async Task AddAsync(User user)
        => await _context.Users.AddAsync(user);

    public Task UpdateAsync(User user)
    {
        _context.Users.Update(user);
        return Task.CompletedTask;
    }
}
```

### Gestion du soft delete

`User.DeletedAt` n'est **pas** un filtre global EF Core (Query Filter) — les services filtrent explicitement selon le besoin (certains endpoints admin doivent voir les comptes supprimés).

---

## 5. Configuration Redis

### Package NuGet

```xml
<PackageReference Include="StackExchange.Redis" Version="2.8.*" />
<PackageReference Include="Microsoft.Extensions.Caching.StackExchangeRedis" Version="10.*" />
```

### Structure des clés

| Cas d'usage | Clé Redis | Type de valeur |
|---|---|---|
| Résultats de recherche par mot-clé | `food:search:{keyword_normalisé}` | JSON (`List<FoodItemSearchResponse>`) |

Le mot-clé est normalisé : minuscules + trim avant d'être utilisé comme clé.

```csharp
var cacheKey = $"food:search:{keyword.ToLowerInvariant().Trim()}";
```

### TTL

| Clé | TTL |
|---|---|
| `food:search:*` | **24 heures** — aligné sur la fréquence du job d'import OFF |

### Stratégie d'invalidation

Le job `OffImportJob` invalide le cache après chaque import réussi en supprimant toutes les clés `food:search:*`.

```csharp
// Dans OffImportJob, après l'import
await _cache.KeyDeleteByPatternAsync("food:search:*");
```

### Implémentation — `RedisFoodCacheService`

`RedisFoodCacheService` implémente `IFoodCacheService` (interface définie dans Application).

```csharp
public sealed class RedisFoodCacheService : IFoodCacheService
{
    private readonly IDistributedCache _cache;
    private static readonly TimeSpan Ttl = TimeSpan.FromHours(24);

    public async Task<List<FoodItemSearchResponse>?> GetSearchResultsAsync(string keyword) { ... }
    public async Task SetSearchResultsAsync(string keyword, List<FoodItemSearchResponse> results) { ... }
    public async Task InvalidateSearchCacheAsync() { ... }
}
```

### Configuration dans `Program.cs`

```csharp
builder.Services.AddStackExchangeRedisCache(options =>
{
    options.Configuration = builder.Configuration.GetConnectionString("Redis");
    options.InstanceName = "nutrition:";
});
```

---

## 6. Configuration Hangfire

Voir `docs/pages/backend/annexes/infrastructure-hangfire.md` pour le détail complet.

### Jobs planifiés

| Job | Classe | Schedule (cron) | Heure UTC |
|---|---|---|---|
| Import Open Food Facts | `OffImportJob` | `0 3 * * *` | 03h00 |
| Purge RGPD | `RgpdPurgeJob` | `30 3 * * *` | 03h30 |

### Interfaces des jobs

```csharp
// Infrastructure/Jobs/IOffImportJob.cs
public interface IOffImportJob
{
    Task RunAsync();
}

// Infrastructure/Jobs/IRgpdPurgeJob.cs
public interface IRgpdPurgeJob
{
    Task RunAsync();
}
```

### Stockage

Schéma PostgreSQL dédié `HangFire` — créé automatiquement au démarrage (`PrepareSchemaIfNecessary = true`).

**Aucune migration EF Core** pour les tables Hangfire — elles sont gérées par le package lui-même.

### File d'attente (queue)

File par défaut (`default`) pour les deux jobs. Pas de file dédiée par job — le volume est trop faible pour justifier une ségrégation.

---

## 7. Structure des migrations

### Convention de nommage

```
{Description}
```

Exemples :
- `InitialSchema`
- `AddIndexOnFoodItemOffId`
- `AddDeletedAtToUser`

Le timestamp est géré automatiquement par EF Core dans le nom de fichier généré.

### Commandes EF Core CLI

```bash
# Créer une migration
dotnet ef migrations add InitialSchema \
  --project src/NutritionApi.Infrastructure \
  --startup-project src/NutritionApi.Api \
  --output-dir Persistence/Migrations

# Appliquer les migrations
dotnet ef database update \
  --project src/NutritionApi.Infrastructure \
  --startup-project src/NutritionApi.Api

# Rollback vers une migration précédente
dotnet ef database update NomDeLaMigrationCible \
  --project src/NutritionApi.Infrastructure \
  --startup-project src/NutritionApi.Api
```

### Règles

- **Une migration = un changement logique.** Ne pas regrouper des modifications sans rapport dans une seule migration.
- **Jamais de migration manuelle** — toujours générée par `dotnet ef migrations add`.
- Les migrations sont **committées dans git** avec le code qui les nécessite.

---

## 8. Injection de dépendances

```csharp
// Infrastructure/DependencyInjection.cs
public static class InfrastructureExtensions
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        // EF Core + PostgreSQL
        services.AddDbContext<AppDbContext>(options =>
            options.UseNpgsql(configuration.GetConnectionString("Default"))
                   .UseSnakeCaseNamingConvention());

        services.AddScoped<IUnitOfWork>(sp => sp.GetRequiredService<AppDbContext>());

        // Repositories
        services.AddScoped<IUserRepository, UserRepository>();
        services.AddScoped<IDietPlanRepository, DietPlanRepository>();
        services.AddScoped<IDietRepository, DietRepository>();
        services.AddScoped<IMealRepository, MealRepository>();
        services.AddScoped<IFoodItemRepository, FoodItemRepository>();
        services.AddScoped<IWeightEntryRepository, WeightEntryRepository>();
        services.AddScoped<ISavedFoodItemRepository, SavedFoodItemRepository>();

        // Cache Redis
        services.AddScoped<IFoodCacheService, RedisFoodCacheService>();

        // Services externes
        services.AddScoped<IKeycloakAdminService, KeycloakAdminService>();

        // Hangfire
        services.AddHangfire(config => config
            .UsePostgreSqlStorage(configuration.GetConnectionString("Default"),
                new PostgreSqlStorageOptions
                {
                    SchemaName = "HangFire",
                    PrepareSchemaIfNecessary = true
                }));
        services.AddHangfireServer();

        // Jobs Hangfire
        services.AddScoped<IOffImportJob, OffImportJob>();
        services.AddScoped<IRgpdPurgeJob, RgpdPurgeJob>();

        return services;
    }
}
```

```csharp
// Api/Program.cs
builder.Services.AddInfrastructure(builder.Configuration);
```

---

## 9. Règles transverses

- **Aucune logique métier dans les repositories.** Un repository lit et écrit — c'est tout. Les invariants restent dans le Domain, les orchestrations dans l'Application.
- **`SaveChangesAsync()` est appelé exclusivement par les services via `IUnitOfWork`.** Les repositories ne sauvegardent jamais eux-mêmes.
- **Les requêtes sont filtrées par `userId` dans les repositories**, pas dans les services — c'est la responsabilité du repository de retourner uniquement les données appartenant à l'utilisateur demandé.
- **`FoodItem` est la seule table sans filtre `userId`** — c'est une table de référence partagée.
- **Pas de lazy loading** — toutes les relations sont chargées explicitement avec `Include()` quand nécessaire.
