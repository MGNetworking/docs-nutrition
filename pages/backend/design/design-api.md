# Design technique — Couche API

> Document de référence obligatoire avant tout ticket de la couche API.
> Source de vérité : `docs/pages/backend/livrable/checklist-implementation.md`
> Contrats API par écran : `docs/pages/backend/livrable/specs-frontend.md`
> Configuration technique (middleware, JWT, Swagger) : `design-api-infrastructure.md`

---

## 1. Structure des dossiers

```
src/NutritionApi.Api/
├── Controllers/
│   ├── UsersController.cs
│   ├── RgpdController.cs
│   ├── DietPlansController.cs
│   ├── DietsController.cs
│   ├── NutritionController.cs
│   ├── MealsController.cs
│   ├── FoodItemsController.cs
│   └── AdminController.cs
├── Middleware/
│   ├── ExceptionMiddleware.cs
│   └── UserResolutionMiddleware.cs
├── Extensions/
│   ├── ClaimsPrincipalExtensions.cs
│   └── ServiceCollectionExtensions.cs
├── Filters/
│   └── HangfireAdminAuthorizationFilter.cs
├── Properties/
│   └── launchSettings.json
├── appsettings.json
├── appsettings.Development.json
└── Program.cs
```

---

## 2. Routing

**Préfixe global :** `/api/v1/`

Appliqué via attribut sur chaque controller — pas de préfixe global dans `Program.cs` pour garder la flexibilité des routes `/admin` et `/hangfire`.

```csharp
[ApiController]
[Route("api/v1/[controller]")]
[Authorize]
public class UsersController : ControllerBase { ... }
```

### Table des routes par controller

| Controller | Route de base | Rôle requis |
|---|---|---|
| `UsersController` | `/api/v1/users` | `user` |
| `RgpdController` | `/api/v1/rgpd` | `user` |
| `DietPlansController` | `/api/v1/diet-plans` | `user` |
| `DietsController` | `/api/v1/diets` | `user` |
| `NutritionController` | `/api/v1/nutrition` | `user` |
| `MealsController` | `/api/v1/meals` | `user` |
| `FoodItemsController` | `/api/v1/food-items` | `user` |
| `AdminController` | `/api/v1/admin` | `admin` |

### Endpoints complets

#### UsersController — `/api/v1/users`

| Méthode | Route | Description | Code succès |
|---|---|---|---|
| `POST` | `/users/me` | Créer le profil (1ère connexion) | 201 |
| `GET` | `/users/me` | Lire le profil + BMR/TDEE | 200 |
| `PUT` | `/users/me` | Mettre à jour le profil | 200 |
| `POST` | `/users/me/weight-entries` | Ajouter une pesée | 201 |
| `GET` | `/users/me/weight-entries` | Historique des pesées | 200 |
| `PUT` | `/users/me/weight-entries/{id}` | Modifier une pesée | 200 |
| `GET` | `/users/me/saved-food-items` | Liste des favoris | 200 |
| `POST` | `/users/me/saved-food-items` | Sauvegarder un aliment | 201 |
| `DELETE` | `/users/me/saved-food-items/{id}` | Retirer un aliment des favoris | 204 |

#### RgpdController — `/api/v1/rgpd`

| Méthode | Route | Description | Code succès |
|---|---|---|---|
| `DELETE` | `/rgpd` | Demande suppression RGPD | 204 |
| `POST` | `/rgpd/reactivate` | Réactivation pendant grace period | 200 |
| `GET` | `/rgpd/export` | Export données RGPD | 200 |

#### DietPlansController — `/api/v1/diet-plans`

| Méthode | Route | Description | Code succès |
|---|---|---|---|
| `GET` | `/diet-plans` | Lister ses plans personnels | 200 |
| `POST` | `/diet-plans` | Créer un plan | 201 |
| `PUT` | `/diet-plans/{id}` | Modifier un plan | 200 |
| `DELETE` | `/diet-plans/{id}` | Supprimer un plan | 204 |
| `GET` | `/diet-plans/templates` | Lister les templates (Pro/Business) | 200 |

#### DietsController — `/api/v1/diets`

| Méthode | Route | Description | Code succès |
|---|---|---|---|
| `POST` | `/diets/{id}/launch` | Lancer un plan → Diet active | 201 |
| `GET` | `/diets/active` | Récupérer le régime actif | 200 |
| `GET` | `/diets` | Historique des régimes | 200 |
| `GET` | `/diets/{id}` | Détail d'un régime | 200 |
| `POST` | `/diets/{id}/archive` | Terminer le régime actif | 200 |

#### NutritionController — `/api/v1/nutrition`

| Méthode | Route | Description | Code succès |
|---|---|---|---|
| `GET` | `/nutrition/{id}/bilan` | Bilan nutritionnel d'un régime | 200 |

#### MealsController — `/api/v1/meals`

| Méthode | Route | Description | Code succès |
|---|---|---|---|
| `POST` | `/meals` | Créer un repas | 201 |
| `GET` | `/meals` | Lister ses repas (`?saved=true`, `?date=`) | 200 |
| `GET` | `/meals/{id}` | Détail d'un repas | 200 |
| `PATCH` | `/meals/{id}` | Modifier un repas (name, mealType, notes, consumedAt) | 200 |
| `DELETE` | `/meals/{id}` | Supprimer un repas | 204 |
| `POST` | `/meals/{id}/items` | Ajouter un MealItem | 201 |
| `DELETE` | `/meals/{id}/items/{itemId}` | Retirer un MealItem | 204 |

#### FoodItemsController — `/api/v1/food-items`

| Méthode | Route | Description | Code succès |
|---|---|---|---|
| `GET` | `/food-items?search={motclé}` | Rechercher un aliment | 200 |

#### AdminController — `/api/v1/admin`

| Méthode | Route | Description | Code succès |
|---|---|---|---|
| `GET` | `/admin/dashboard` | KPIs consolidés | 200 |
| `GET` | `/admin/system/health` | Statut jobs Hangfire + count FoodItems | 200 |
| `POST` | `/admin/diet-plans/templates` | Créer un template | 201 |
| `PUT` | `/admin/diet-plans/templates/{id}` | Modifier un template | 200 |
| `DELETE` | `/admin/diet-plans/templates/{id}` | Supprimer un template | 204 |

---

## 3. Pattern de réponse

### Réponses de succès — format raw (sans enveloppe)

Les réponses de succès retournent directement l'objet ou la liste — pas d'enveloppe `{ data: ... }`.

```
GET /users/me          → UserProfileResponse          (200)
GET /diet-plans        → List<DietPlanResponse>        (200)
POST /diet-plans       → DietPlanResponse              (201 + Location header)
POST /diets/{id}/archive → DietResponse               (200)
DELETE /meals/{id}     → (aucun corps)                 (204)
```

**Header `Location` sur les 201 :**

```csharp
return CreatedAtAction(nameof(GetById), new { id = result.Id }, result);
```

### Réponses d'erreur — RFC 7807 ProblemDetails

Toutes les erreurs utilisent le format `ProblemDetails` standard ASP.NET Core.

```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.4",
  "title": "Not Found",
  "status": 404,
  "detail": "DietPlan introuvable.",
  "traceId": "00-abc123..."
}
```

### Codes HTTP par cas

| Situation | Code | Déclenché par |
|---|---|---|
| Succès lecture | 200 OK | — |
| Ressource créée | 201 Created | — |
| Succès sans corps | 204 No Content | suppressions |
| Corps invalide / validation | 400 Bad Request | `[ApiController]` automatique |
| Token absent ou invalide | 401 Unauthorized | Middleware JWT |
| Rôle insuffisant | 403 Forbidden | `[Authorize(Roles = "admin")]` |
| Tier insuffisant | 403 Forbidden | `ForbiddenException` → ExceptionMiddleware |
| Ressource introuvable | 404 Not Found | `NotFoundException` → ExceptionMiddleware |
| Conflit d'état | 409 Conflict | `ConflictException` → ExceptionMiddleware |
| Règle métier violée | 422 Unprocessable Entity | `UnprocessableException` → ExceptionMiddleware |
| Erreur inattendue | 500 Internal Server Error | ExceptionMiddleware (sans détail en prod) |

---

## 4. Structure type d'un controller

```csharp
[ApiController]
[Route("api/v1/[controller]")]
[Authorize]
public class DietPlansController : ControllerBase
{
    private readonly DietPlanService _service;

    public DietPlansController(DietPlanService service) => _service = service;

    /// <summary>Lister les plans personnels de l'utilisateur.</summary>
    [HttpGet]
    [ProducesResponseType(typeof(List<DietPlanResponse>), StatusCodes.Status200OK)]
    public async Task<IActionResult> GetAll()
    {
        var userId = HttpContext.GetUserId();
        var result = await _service.GetUserPlansAsync(userId);
        return Ok(result);
    }

    /// <summary>Créer un plan diététique personnel.</summary>
    [HttpPost]
    [ProducesResponseType(typeof(DietPlanResponse), StatusCodes.Status201Created)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status403Forbidden)]
    public async Task<IActionResult> Create([FromBody] CreateDietPlanRequest request)
    {
        var userId = HttpContext.GetUserId();
        var result = await _service.CreateAsync(userId, request);
        return CreatedAtAction(nameof(GetById), new { id = result.Id }, result);
    }
}
```

**Règles :**

- Le controller extrait `userId` depuis `HttpContext` — il ne le passe jamais via `[FromBody]` ou `[FromQuery]`.
- Le controller ne contient aucune logique métier — il délègue au service applicatif.
- Le controller ne mappe jamais manuellement des entités Domain — il reçoit et retourne des DTOs.
- `[FromBody]` pour les requêtes POST/PUT/PATCH, `[FromRoute]` pour les ids, `[FromQuery]` pour les filtres.

---

## 5. Contrats par endpoint

> Pour chaque endpoint : Request body (champs + types), Response body, codes d'erreur métier.
> Le 400 (validation automatique `[ApiController]`) et le 401 (JWT) sont implicites sur toutes les routes — non répétés.

---

### UsersController — `/api/v1/users`

#### `POST /users/me` — Créer le profil

**Request** `CreateUserProfileRequest`

| Champ | Type | Obligatoire |
|---|---|---|
| `birthDate` | `DateOnly` | ✅ |
| `gender` | `Gender` | ✅ |
| `activityLevel` | `ActivityLevel` | ✅ |
| `height` | `float` (cm) | ✅ |
| `weight` | `float` (kg) | ✅ — crée la première `WeightEntry` |
| `allergies` | `List<Allergen>` | ✅ — liste vide = aucune allergie confirmée |
| `dietaryPreferences` | `List<string>` | ✅ — liste vide = aucune préférence confirmée |

**Response 201** `UserProfileResponse`

| Champ | Type |
|---|---|
| `id` | `Guid` |
| `keycloakId` | `string` |
| `birthDate` | `DateOnly` |
| `gender` | `Gender` |
| `activityLevel` | `ActivityLevel` |
| `height` | `float` |
| `allergies` | `List<Allergen>` |
| `dietaryPreferences` | `List<string>` |
| `subscriptionTier` | `SubscriptionTier` |
| `createdAt` | `DateTime` |

**Erreurs :** 409 profil déjà existant pour ce `keycloakId`

---

#### `GET /users/me` — Lire le profil + BMR/TDEE

**Response 200** `UserProfileResponse` + champs nutritionnels calculés

| Champ supplémentaire | Type |
|---|---|
| `bmr` | `float` (kcal) |
| `tdee` | `float` (kcal) |
| `targetCalories` | `float` (kcal) |
| `latestWeight` | `float?` (kg) — dernière `WeightEntry`, null si aucune |

**Erreurs :** 404 profil inexistant

---

#### `PUT /users/me` — Mettre à jour le profil

**Request** `UpdateUserProfileRequest`

| Champ | Type | Obligatoire |
|---|---|---|
| `birthDate` | `DateOnly` | ✅ |
| `gender` | `Gender` | ✅ |
| `activityLevel` | `ActivityLevel` | ✅ |
| `height` | `float` (cm) | ✅ |
| `allergies` | `List<Allergen>` | ✅ |
| `dietaryPreferences` | `List<string>` | ✅ |

**Response 200** `UserProfileResponse`

**Erreurs :** 404 profil inexistant

---

#### `POST /users/me/weight-entries` — Ajouter une pesée

**Request** `AddWeightEntryRequest`

| Champ | Type | Obligatoire |
|---|---|---|
| `weight` | `float` (kg) | ✅ |
| `measuredAt` | `DateOnly` | ❌ — défaut : aujourd'hui |

**Response 201** `WeightEntryResponse`

| Champ | Type |
|---|---|
| `id` | `Guid` |
| `weight` | `float` |
| `measuredAt` | `DateOnly` |

**Erreurs :** 409 entrée déjà existante pour cette date

---

#### `GET /users/me/weight-entries` — Historique des pesées

Aucun body. **Response 200** `List<WeightEntryResponse>` — trié par `measuredAt` décroissant.

---

#### `PUT /users/me/weight-entries/{id}` — Modifier une pesée

**Request** `UpdateWeightEntryRequest`

| Champ | Type | Obligatoire |
|---|---|---|
| `weight` | `float` (kg) | ✅ |
| `measuredAt` | `DateOnly` | ✅ |

**Response 200** `WeightEntryResponse`

**Erreurs :** 404, 409 (doublon date)

---

#### `GET /users/me/saved-food-items` — Liste des favoris

Aucun body. **Response 200** `List<SavedFoodItemResponse>`

`SavedFoodItemResponse`

| Champ | Type |
|---|---|
| `id` | `Guid` |
| `foodItemId` | `Guid` |
| `name` | `string` |
| `caloriesPer100g` | `float` |
| `savedAt` | `DateTime` |

---

#### `POST /users/me/saved-food-items` — Sauvegarder un aliment

**Request** `SaveFoodItemRequest`

| Champ | Type | Obligatoire |
|---|---|---|
| `foodItemId` | `Guid` | ✅ |

**Response 201** `SavedFoodItemResponse`

**Erreurs :** 404 aliment introuvable, 403 limite tier atteinte, 409 aliment déjà sauvegardé

---

#### `DELETE /users/me/saved-food-items/{id}` — Retirer un favori

Aucun body. **Response 204.** **Erreurs :** 404

---

### RgpdController — `/api/v1/rgpd`

#### `DELETE /rgpd` — Demande suppression RGPD

Aucun body. **Response 204.** Déclenche soft delete + désactivation Keycloak.

---

#### `POST /rgpd/reactivate` — Réactivation pendant grace period

Aucun body. **Response 200** `UserProfileResponse`. **Erreurs :** 404, 409 (compte non en grace period)

---

#### `GET /rgpd/export` — Export données RGPD

Aucun body.

**Response 200** — fichier ZIP téléchargeable contenant `mon-export.json` (toutes les données de l'utilisateur : profil, pesées, diet plans, diets, repas, aliments favoris).

| Header | Valeur |
|---|---|
| `Content-Type` | `application/zip` |
| `Content-Disposition` | `attachment; filename="export-yyyy-MM-dd.zip"` |

DTO retourné par le service : `UserExportResponse` — voir `docs/pages/backend/features/rgpd.md` pour l'implémentation complète (principe en mémoire, ZipArchive, responsabilités par couche).

---

### DietPlansController — `/api/v1/diet-plans`

`DietPlanResponse`

| Champ | Type |
|---|---|
| `id` | `Guid` |
| `name` | `string` |
| `dietType` | `DietType` |
| `goal` | `Goal` |
| `targetWeight` | `float` |
| `macroDistribution` | `MacroDistributionDto` (proteinPct, carbPct, fatPct) |
| `isTemplate` | `bool` |

---

#### `GET /diet-plans` — Lister ses plans personnels

Aucun body. **Response 200** `List<DietPlanResponse>` — plans personnels uniquement (`IsTemplate = false`).

---

#### `POST /diet-plans` — Créer un plan

**Request** `CreateDietPlanRequest`

| Champ | Type | Obligatoire |
|---|---|---|
| `name` | `string` | ✅ |
| `dietType` | `DietType` | ✅ |
| `goal` | `Goal` | ✅ |
| `targetWeight` | `float` (kg) | ✅ |
| `macroDistribution` | `MacroDistributionDto` | ✅ — somme des % doit = 100 |

**Response 201** `DietPlanResponse`

**Erreurs :** 403 limite tier atteinte (Free max 2, Pro max 20), 422 macros ≠ 100%

---

#### `PUT /diet-plans/{id}` — Modifier un plan

**Request** `UpdateDietPlanRequest` — mêmes champs que `CreateDietPlanRequest`

**Response 200** `DietPlanResponse`

**Erreurs :** 404, 403 (template non modifiable par un user)

---

#### `DELETE /diet-plans/{id}` — Supprimer un plan

Aucun body. **Response 204.** **Erreurs :** 404

---

#### `GET /diet-plans/templates` — Lister les templates

Aucun body. **Response 200** `List<DietPlanResponse>` — `IsTemplate = true` uniquement.

**Erreurs :** 403 tier Free

---

### DietsController — `/api/v1/diets`

`DietResponse`

| Champ | Type |
|---|---|
| `id` | `Guid` |
| `name` | `string` |
| `dietType` | `DietType` |
| `goal` | `Goal` |
| `targetWeight` | `float` |
| `calorieTarget` | `int` |
| `macroDistribution` | `MacroDistributionDto` |
| `status` | `DietStatus` |
| `startDate` | `DateOnly` |
| `endDate` | `DateOnly?` |

---

#### `POST /diets/{id}/launch` — Lancer un plan → crée une Diet

Aucun body — `StartDate` imposée par le système (aujourd'hui).

**Response 201** `DietResponse`

**Erreurs :** 404, 409 diet déjà active, 422 aucune `WeightEntry` disponible (CalorieTarget incalculable)

---

#### `GET /diets/active` — Régime actif

Aucun body. **Response 200** `DietResponse`. **Erreurs :** 404 aucun régime actif

---

#### `GET /diets` — Historique des régimes

Aucun body. **Response 200** `List<DietResponse>` — trié par `startDate` décroissant.

---

#### `GET /diets/{id}` — Détail d'un régime

Aucun body. **Response 200** `DietResponse`. **Erreurs :** 404

---

#### `POST /diets/{id}/archive` — Terminer le régime

Aucun body — `EndDate` imposée par le système (aujourd'hui).

**Response 200** `DietResponse`. **Erreurs :** 404, 422 régime non actif

---

### NutritionController — `/api/v1/nutrition`

`NutritionBilanResponse`

| Champ | Type |
|---|---|
| `dietId` | `Guid` |
| `startDate` | `DateOnly` |
| `endDate` | `DateOnly` |
| `totalCalories` | `float` |
| `totalProteins` | `float` |
| `totalCarbs` | `float` |
| `totalFats` | `float` |
| `dailyBreakdown` | `List<DailyNutritionDto>` |
| `weightProgression` | `List<WeightEntryResponse>` |

---

#### `GET /nutrition/{id}/bilan` — Bilan nutritionnel d'un régime

**Query params :** `period` (ex: `week`, `month`, `custom`), `date?`, `startDate?`, `endDate?`

**Response 200** `NutritionBilanResponse`. **Erreurs :** 404, 403

---

### MealsController — `/api/v1/meals`

`MealResponse`

| Champ | Type |
|---|---|
| `id` | `Guid` |
| `name` | `string` |
| `mealType` | `MealType` |
| `consumedAt` | `DateTime` |
| `notes` | `string?` |
| `isSaved` | `bool` |
| `items` | `List<MealItemResponse>` |

`MealItemResponse`

| Champ | Type |
|---|---|
| `id` | `Guid` |
| `foodItemId` | `Guid` |
| `foodName` | `string` |
| `quantity` | `float` (g) |
| `calories` | `float` |
| `proteins` | `float` |
| `carbs` | `float` |
| `fats` | `float` |

---

#### `POST /meals` — Créer un repas

**Request** `CreateMealRequest`

| Champ | Type | Obligatoire |
|---|---|---|
| `name` | `string` | ✅ |
| `mealType` | `MealType` | ✅ |
| `consumedAt` | `DateTime` | ✅ |
| `notes` | `string?` | ❌ |
| `isSaved` | `bool` | ✅ — `false` = ponctuel |
| `items` | `List<MealItemInputDto>` (foodItemId, quantity) | ✅ — au moins 1 |

**Response 201** `MealResponse`

**Erreurs :** 403 limite repas sauvegardés atteinte, 404 FoodItem introuvable

---

#### `GET /meals` — Lister les repas

**Query** `?saved=true|false`, `?date=2026-05-31`

**Response 200** `List<MealResponse>`

---

#### `GET /meals/{id}` — Détail d'un repas

**Response 200** `MealResponse`. **Erreurs :** 404

---

#### `PATCH /meals/{id}` — Modifier un repas

**Request** `UpdateMealRequest` — tous les champs optionnels

| Champ | Type |
|---|---|
| `name` | `string?` |
| `mealType` | `MealType?` |
| `notes` | `string?` |
| `consumedAt` | `DateTime?` |
| `isSaved` | `bool?` |

**Response 200** `MealResponse`. **Erreurs :** 404

---

#### `DELETE /meals/{id}` — Supprimer un repas

Aucun body. **Response 204.** **Erreurs :** 404

---

#### `POST /meals/{id}/items` — Ajouter un aliment au repas

**Request** `AddMealItemRequest`

| Champ | Type | Obligatoire |
|---|---|---|
| `foodItemId` | `Guid` | ✅ |
| `quantity` | `float` (g) | ✅ |

**Response 201** `MealResponse` mis à jour. **Erreurs :** 404 (meal ou foodItem introuvable)

---

#### `DELETE /meals/{id}/items/{itemId}` — Retirer un aliment

Aucun body. **Response 204.** **Erreurs :** 404

---

### FoodItemsController — `/api/v1/food-items`

`FoodItemSearchResponse`

| Champ | Type |
|---|---|
| `id` | `Guid` |
| `name` | `string` |
| `caloriesPer100g` | `float` |
| `proteinsPer100g` | `float` |
| `carbsPer100g` | `float` |
| `fatsPer100g` | `float` |
| `allergensTags` | `List<Allergen>` |

---

#### `GET /food-items?search={motclé}` — Rechercher un aliment

**Query** `search` (string, obligatoire), `limit` (int, défaut 20)

**Response 200** `List<FoodItemSearchResponse>` — liste vide si aucun résultat (pas de 404)

---

### AdminController — `/api/v1/admin`

#### `GET /admin/dashboard` — KPIs consolidés

**Response 200** `AdminDashboardResponse`

| Champ | Type |
|---|---|
| `totalUsers` | `int` |
| `usersByTier` | `{ free, pro, business }` |
| `newUsersLast7Days` | `int` |
| `activeDiets` | `int` |
| `mealsLast7Days` | `int` |
| `usersInGracePeriod` | `int` |

---

#### `GET /admin/system/health` — Santé système

**Response 200** `SystemHealthResponse`

| Champ | Type |
|---|---|
| `foodItemsCount` | `int` |
| `lastImportAt` | `DateTime?` |
| `hangfireJobs` | `List<HangfireJobDto>` (jobName, lastRun, nextRun, status) |

---

#### `POST /admin/diet-plans/templates` — Créer un template

**Request** `CreateDietPlanRequest` — `IsTemplate` forcé à `true` côté service.

**Response 201** `DietPlanResponse`. **Erreurs :** 422 macros ≠ 100%

---

#### `PUT /admin/diet-plans/templates/{id}` — Modifier un template

**Request** `UpdateDietPlanRequest`

**Response 200** `DietPlanResponse`. **Erreurs :** 404

---

#### `DELETE /admin/diet-plans/templates/{id}` — Supprimer un template

Aucun body. **Response 204.** **Erreurs :** 404

---

## 6. Règles transverses

- **Un controller = un agrégat ou une ressource.** Ne pas créer de controller `BaseController` avec de la logique partagée.
- **`[ApiController]`** est obligatoire sur chaque controller — active la validation automatique du `ModelState` (400 sur corps invalide).
- **Aucun `try/catch` dans les controllers.** L'`ExceptionMiddleware` capture toutes les exceptions.
- **Le `UserResolutionMiddleware` garantit que `HttpContext.GetUserId()` est toujours disponible** dans une action `[Authorize]` — inutile de vérifier la nullité.
- **`[AllowAnonymous]`** est interdit sauf décision explicite et documentée.
- **Hangfire dashboard** (`/hangfire`) est exclu de la spec OpenAPI — pas de `[ApiExplorerSettings(IgnoreApi = true)]` nécessaire car il n'est pas un controller.
