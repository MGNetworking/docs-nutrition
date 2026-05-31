# Design technique — Couche API

> Document de référence obligatoire avant tout ticket de la couche API.
> Source de vérité : `docs/pages/backend/livrable/checklist-implementation.md`
> Contrats API par écran : `docs/pages/backend/livrable/specs-frontend.md`

---

## 1. Structure des dossiers

```
src/NutritionApi.Api/
├── Controllers/
│   ├── UsersController.cs
│   ├── DietPlansController.cs
│   ├── DietsController.cs
│   ├── MealsController.cs
│   ├── FoodItemsController.cs
│   └── AdminController.cs
├── Middleware/
│   ├── ExceptionMiddleware.cs         ← traduit les exceptions Application en ProblemDetails
│   └── UserResolutionMiddleware.cs    ← résout KeycloakId → User.Id à chaque requête
├── Extensions/
│   ├── ClaimsPrincipalExtensions.cs   ← HttpContext.GetUserId(), HttpContext.GetKeycloakId()
│   └── ServiceCollectionExtensions.cs ← helpers d'enregistrement
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
| `DietPlansController` | `/api/v1/diet-plans` | `user` |
| `DietsController` | `/api/v1/diets` | `user` |
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
| `DELETE` | `/users/me` | Demande suppression RGPD | 204 |
| `POST` | `/users/me/reactivate` | Réactivation pendant grace period | 200 |
| `GET` | `/users/me/export` | Export données RGPD | 200 |
| `POST` | `/users/me/weight-entries` | Ajouter une pesée | 201 |
| `GET` | `/users/me/weight-entries` | Historique des pesées | 200 |
| `PUT` | `/users/me/weight-entries/{id}` | Modifier une pesée | 200 |
| `GET` | `/users/me/saved-food-items` | Liste des favoris | 200 |
| `POST` | `/users/me/saved-food-items` | Sauvegarder un aliment | 201 |
| `DELETE` | `/users/me/saved-food-items/{id}` | Retirer un aliment des favoris | 204 |

#### DietPlansController — `/api/v1/diet-plans`

| Méthode | Route | Description | Code succès |
|---|---|---|---|
| `GET` | `/diet-plans` | Lister ses plans personnels | 200 |
| `POST` | `/diet-plans` | Créer un plan | 201 |
| `PUT` | `/diet-plans/{id}` | Modifier un plan | 200 |
| `DELETE` | `/diet-plans/{id}` | Supprimer un plan | 204 |
| `POST` | `/diet-plans/{id}/launch` | Lancer un plan → Diet active | 201 |
| `GET` | `/diet-plans/templates` | Lister les templates (Pro/Business) | 200 |

#### DietsController — `/api/v1/diets`

| Méthode | Route | Description | Code succès |
|---|---|---|---|
| `GET` | `/diets/active` | Récupérer le régime actif | 200 |
| `GET` | `/diets` | Historique des régimes | 200 |
| `GET` | `/diets/{id}` | Détail d'un régime | 200 |
| `POST` | `/diets/{id}/archive` | Terminer le régime actif | 200 |
| `GET` | `/diets/{id}/bilan` | Bilan nutritionnel (params : `period`, `date`, `startDate`) | 200 |

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

## 4. Middleware — ordre de la pipeline

L'ordre est critique — chaque middleware est listé dans l'ordre d'appel dans `Program.cs`.

```csharp
// Program.cs
app.UseExceptionHandler("/error");       // 1. Capture toutes les exceptions non gérées
app.UseHttpsRedirection();               // 2.
app.UseCors();                           // 3.
app.UseAuthentication();                 // 4. Valide le JWT Bearer
app.UseAuthorization();                  // 5. Vérifie les rôles / policies
app.UseMiddleware<UserResolutionMiddleware>(); // 6. Résout KeycloakId → User.Id
app.MapControllers();                    // 7.
app.MapHangfireDashboard("/hangfire", new DashboardOptions
{
    Authorization = [new HangfireAdminAuthorizationFilter()]
});
```

### Rôle de chaque middleware

| Middleware | Rôle |
|---|---|
| `ExceptionHandler` | Capture les exceptions non gérées, retourne un `ProblemDetails` |
| `HttpsRedirection` | Force HTTPS |
| `Cors` | Autorise les requêtes cross-origin (configuré par environnement) |
| `Authentication` | Valide le token JWT Bearer (signature, audience, expiration) |
| `Authorization` | Vérifie `[Authorize]` et `[Authorize(Roles = "admin")]` |
| `UserResolutionMiddleware` | Extrait le `sub` Keycloak du token, résout `User.Id` en base |
| `MapControllers` | Route vers les controllers |

### ExceptionMiddleware — mapping exceptions → ProblemDetails

```csharp
// Middleware/ExceptionMiddleware.cs
public class ExceptionMiddleware : IMiddleware
{
    public async Task InvokeAsync(HttpContext context, RequestDelegate next)
    {
        try { await next(context); }
        catch (NotFoundException ex)    { await WriteProblem(context, 404, ex.Message); }
        catch (ConflictException ex)    { await WriteProblem(context, 409, ex.Message); }
        catch (ForbiddenException ex)   { await WriteProblem(context, 403, ex.Message); }
        catch (UnprocessableException ex){ await WriteProblem(context, 422, ex.Message); }
        catch (Exception ex)            { await WriteProblem(context, 500, "Une erreur interne est survenue."); }
    }
}
```

### UserResolutionMiddleware

Résout le `sub` Keycloak en `User.Id` interne à chaque requête authentifiée, et l'ajoute au `HttpContext.Items`.

```csharp
// Middleware/UserResolutionMiddleware.cs
public class UserResolutionMiddleware : IMiddleware
{
    public async Task InvokeAsync(HttpContext context, RequestDelegate next)
    {
        if (context.User.Identity?.IsAuthenticated == true)
        {
            var keycloakId = context.User.FindFirstValue("sub");
            var user = await _userRepository.GetByKeycloakIdAsync(keycloakId!);
            if (user is null) { context.Response.StatusCode = 401; return; }
            context.Items["UserId"] = user.Id;
        }
        await next(context);
    }
}
```

**Accès dans les controllers :**

```csharp
// Extensions/ClaimsPrincipalExtensions.cs
public static Guid GetUserId(this HttpContext context)
    => (Guid)context.Items["UserId"]!;

// Dans un controller
var userId = HttpContext.GetUserId();
```

---

## 5. Authentification / Autorisation

### Validation JWT Keycloak

```csharp
// Program.cs
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.Authority = builder.Configuration["Keycloak:Authority"];
        options.Audience  = builder.Configuration["Keycloak:Audience"];
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer           = true,
            ValidateAudience         = true,
            ValidateLifetime         = true,
            ValidateIssuerSigningKey = true
        };
    });
```

**Variables de configuration (`appsettings.json`) :**

```json
"Keycloak": {
  "Authority": "https://{keycloak-host}/realms/{realm}",
  "Audience":  "nutrition-api"
}
```

Keycloak expose ses clés publiques sur `{Authority}/.well-known/openid-configuration` — le middleware JWT les récupère automatiquement.

### Rôles Keycloak

| Rôle | Claim dans le JWT | Accès |
|---|---|---|
| `user` | `realm_access.roles[]` | Toutes les routes `/api/v1/**` (hors `/admin`) |
| `admin` | `realm_access.roles[]` | Routes `/api/v1/admin/**` + dashboard Hangfire |

**Extraction du rôle Keycloak** (le claim `realm_access.roles` n'est pas le claim standard `role`) :

```csharp
// Program.cs — mapper le claim Keycloak vers le claim standard
builder.Services.AddAuthentication(...)
    .AddJwtBearer(options =>
    {
        options.Events = new JwtBearerEvents
        {
            OnTokenValidated = ctx =>
            {
                var roles = ctx.Principal!
                    .FindFirst("realm_access")?.Value;
                // Parser le JSON et ajouter des ClaimsIdentity avec Role
                return Task.CompletedTask;
            }
        };
    });
```

> Alternative plus simple : utiliser `options.MapInboundClaims = false` + un `IClaimsTransformation` personnalisé qui lit `realm_access.roles` et crée des claims `ClaimTypes.Role` standards.

### Déclaration des policies d'autorisation

```csharp
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("AdminOnly", policy =>
        policy.RequireRole("admin"));
});
```

**Usage dans les controllers :**

```csharp
[Authorize]                          // toutes les routes du controller → rôle user
public class DietPlansController : ControllerBase

[Authorize(Policy = "AdminOnly")]    // rôle admin requis
public class AdminController : ControllerBase

[AllowAnonymous]                     // aucune route anonyme prévue en v1
```

### Routes protégées vs publiques

| Routes | Protection |
|---|---|
| `/api/v1/**` | `[Authorize]` — JWT valide requis |
| `/api/v1/admin/**` | `[Authorize(Policy = "AdminOnly")]` — rôle `admin` requis |
| `/hangfire` | `HangfireAdminAuthorizationFilter` — rôle `admin` requis |
| `/swagger` | Accessible uniquement hors production |

---

## 6. Documentation OpenAPI (Swagger)

### Configuration

```csharp
// Program.cs
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new OpenApiInfo
    {
        Title   = "Nutrition API",
        Version = "v1"
    });

    // Authentification JWT dans l'UI Swagger
    options.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Type        = SecuritySchemeType.Http,
        Scheme      = "bearer",
        BearerFormat = "JWT",
        Description = "Token JWT Keycloak — format : Bearer {token}"
    });

    options.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme
            {
                Reference = new OpenApiReference
                    { Type = ReferenceType.SecurityScheme, Id = "Bearer" }
            },
            Array.Empty<string>()
        }
    });

    // Commentaires XML pour la documentation des endpoints
    var xmlFile = $"{Assembly.GetExecutingAssembly().GetName().Name}.xml";
    options.IncludeXmlComments(Path.Combine(AppContext.BaseDirectory, xmlFile));
});

// Uniquement hors production
if (!app.Environment.IsProduction())
{
    app.UseSwagger();
    app.UseSwaggerUI(options =>
        options.SwaggerEndpoint("/swagger/v1/swagger.json", "Nutrition API v1"));
}
```

**Activer les commentaires XML dans le `.csproj` :**

```xml
<PropertyGroup>
  <GenerateDocumentationFile>true</GenerateDocumentationFile>
  <NoWarn>$(NoWarn);1591</NoWarn>
</PropertyGroup>
```

### Convention d'annotation sur les controllers

```csharp
/// <summary>Créer le profil utilisateur à la première connexion.</summary>
[HttpPost("me")]
[ProducesResponseType(typeof(UserProfileResponse), StatusCodes.Status201Created)]
[ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status409Conflict)]
public async Task<IActionResult> CreateProfile([FromBody] CreateUserProfileRequest request)
```

**Règle :** Déclarer `[ProducesResponseType]` pour tous les codes HTTP possibles (succès + erreurs métier). Le code 401 et 403 sont implicites sur toutes les routes `[Authorize]` — pas besoin de les répéter.

---

## 7. Injection de dépendances

```csharp
// Program.cs
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddApplication();        // ← couche Application
builder.Services.AddInfrastructure(builder.Configuration);  // ← couche Infrastructure

// Middleware custom
builder.Services.AddTransient<ExceptionMiddleware>();
builder.Services.AddTransient<UserResolutionMiddleware>();

// CORS
builder.Services.AddCors(options =>
    options.AddDefaultPolicy(policy =>
        policy.WithOrigins(builder.Configuration.GetSection("Cors:Origins").Get<string[]>()!)
              .AllowAnyHeader()
              .AllowAnyMethod()));
```

---

## 8. Structure type d'un controller

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

## 9. Règles transverses

- **Un controller = un agrégat ou une ressource.** Ne pas créer de controller `BaseController` avec de la logique partagée.
- **`[ApiController]`** est obligatoire sur chaque controller — active la validation automatique du `ModelState` (400 sur corps invalide).
- **Aucun `try/catch` dans les controllers.** L'`ExceptionMiddleware` capture toutes les exceptions.
- **Le `UserResolutionMiddleware` garantit que `HttpContext.GetUserId()` est toujours disponible** dans une action `[Authorize]` — inutile de vérifier la nullité.
- **`[AllowAnonymous]`** est interdit sauf décision explicite et documentée.
- **Hangfire dashboard** (`/hangfire`) est exclu de la spec OpenAPI — pas de `[ApiExplorerSettings(IgnoreApi = true)]` nécessaire car il n'est pas un controller.
