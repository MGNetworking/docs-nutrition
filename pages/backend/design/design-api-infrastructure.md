# Design technique — Infrastructure couche API

> Configuration technique de la couche API : pipeline middleware, JWT, Swagger, CORS, DI.
> Pour les contrats d'endpoints : voir `design-api.md`

---

## 1. Packages NuGet requis

```xml
<!-- Supprimer -->
<PackageReference Include="Microsoft.AspNetCore.OpenApi" Version="10.0.8" />

<!-- Ajouter -->
<PackageReference Include="Microsoft.AspNetCore.Authentication.JwtBearer" Version="10.0.8" />
<PackageReference Include="Swashbuckle.AspNetCore" Version="7.2.0" />
```

---

## 2. Pipeline middleware — ordre critique

L'ordre est critique — chaque middleware est listé dans l'ordre d'appel dans `Program.cs`.

```csharp
app.UseMiddleware<ExceptionMiddleware>();      // 1. Capture toutes les exceptions non gérées
app.UseHttpsRedirection();                    // 2. Force HTTPS
// TODO : configurer AddCors() dans builder.Services
app.UseCors();                                // 3. Autorise les requêtes cross-origin
app.UseAuthentication();                      // 4. Valide le JWT Bearer
app.UseAuthorization();                       // 5. Vérifie les rôles / policies
app.UseMiddleware<UserResolutionMiddleware>(); // 6. Résout keycloakId → User.Id interne
app.MapControllers();                         // 7. Route vers les controllers
```

### Enregistrement DI dans `builder.Services`

```csharp
builder.Services.AddControllers();
builder.Services.AddApplication();
builder.Services.AddScoped<ExceptionMiddleware>();
builder.Services.AddScoped<UserResolutionMiddleware>();
```

### Rôle de chaque middleware

| Middleware | Rôle |
|---|---|
| `ExceptionMiddleware` | Capture les exceptions, retourne un `ProblemDetails` |
| `HttpsRedirection` | Force HTTPS — inclus dans le Web SDK |
| `Cors` | Autorise les requêtes cross-origin — configuré par environnement |
| `Authentication` | Valide le token JWT Bearer (signature, audience, expiration) |
| `Authorization` | Vérifie `[Authorize]` et policies sur les endpoints |
| `UserResolutionMiddleware` | Extrait le `sub` Keycloak, résout `User.Id` en base |
| `MapControllers` | Route les requêtes vers les controllers |

---

## 3. ExceptionMiddleware

Intercepte toutes les exceptions levées par les services Application et les traduit en réponses HTTP `ProblemDetails`.

**Fichier : `Middleware/ExceptionMiddleware.cs`**

```csharp
namespace NutritionApi.Api.Middleware;

using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using NutritionApi.Application.Exceptions;

public class ExceptionMiddleware : IMiddleware
{
    public async Task InvokeAsync(HttpContext context, RequestDelegate next)
    {
        try { await next(context); }
        catch (NotFoundException ex)     { await WriteProblem(context, 404, ex.Message); }
        catch (ConflictException ex)     { await WriteProblem(context, 409, ex.Message); }
        catch (ForbiddenException ex)    { await WriteProblem(context, 403, ex.Message); }
        catch (UnprocessableException ex){ await WriteProblem(context, 422, ex.Message); }
        catch (Exception)                { await WriteProblem(context, 500, "Une erreur interne est survenue."); }
    }

    private static async Task WriteProblem(HttpContext context, int statusCode, string detail)
    {
        context.Response.StatusCode = statusCode;
        context.Response.ContentType = "application/problem+json";
        await context.Response.WriteAsJsonAsync(new ProblemDetails
        {
            Status = statusCode,
            Detail = detail
        });
    }
}
```

---

## 4. UserResolutionMiddleware

Résout le `sub` Keycloak en `User.Id` interne à chaque requête authentifiée et l'ajoute à `HttpContext.Items`.

### Parcours du token dans la pipeline

```
Requête HTTP
Header: Authorization: Bearer eyJhbGc...
        ↓
UseAuthentication
  → lit le header Authorization
  → extrait le token après "Bearer "
  → vérifie la signature avec la clé publique Keycloak
  → si valide → remplit context.User avec les claims du token
  → context.User.Identity.IsAuthenticated = true
        ↓
UserResolutionMiddleware
  → vérifie context.User.Identity.IsAuthenticated
    (= "est-ce que UseAuthentication a validé le token ?")
  → extrait le claim "sub" = "keycloak-abc-123"
  → cherche en BDD → User.Id = Guid("...")
  → stocke dans context.Items["UserId"]
        ↓
Controller
  → HttpContext.User.FindFirstValue("sub") → "keycloak-abc-123"
  → HttpContext.GetUserId()                → Guid("...")
```

> `IsAuthenticated == true` signifie simplement que `UseAuthentication` a validé le token JWT. Sans ce check, le middleware essaierait de chercher un `sub` dans un token inexistant.

**Fichier : `Middleware/UserResolutionMiddleware.cs`**

```csharp
namespace NutritionApi.Api.Middleware;

using System.Security.Claims;
using Microsoft.AspNetCore.Http;
using NutritionApi.Application.Interfaces.Repositories;

public class UserResolutionMiddleware : IMiddleware
{
    private readonly IUserRepository _userRepository;

    public UserResolutionMiddleware(IUserRepository userRepository)
        => _userRepository = userRepository;

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

**Accès dans les controllers via `Extensions/ClaimsPrincipalExtensions.cs` :**

```csharp
public static class ClaimsPrincipalExtensions
{
    public static Guid GetUserId(this HttpContext context)
        => (Guid)context.Items["UserId"]!;
}

// Dans un controller :
var userId = HttpContext.GetUserId();
```

---

## 5. Authentification JWT Keycloak

### Configuration `AddAuthentication`

```csharp
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.Authority = builder.Configuration["Keycloak:Authority"];
        options.Audience  = builder.Configuration["Keycloak:Audience"];
        options.RequireHttpsMetadata = builder.Configuration.GetValue<bool>("Keycloak:RequireHttpsMetadata");
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer           = true,  // Active la vérification de l'émetteur
            ValidateAudience         = true,  // Active la vérification du destinataire
            ValidateLifetime         = true,  // Active la vérification de l'expiration
            ValidateIssuerSigningKey = true   // Active la vérification de la signature
        };
    });
```

**`appsettings.json`** (valeurs vides — surchargées par environnement) :

```json
"Keycloak": {
  "Authority": "",
  "Audience": "nutrition-api",
  "RequireHttpsMetadata": true
}
```

**`appsettings.Development.json`** :

```json
"Keycloak": {
  "Authority": "http://localhost:8080/realms/nutrition",
  "RequireHttpsMetadata": false
}
```

Keycloak expose ses clés publiques sur `{Authority}/.well-known/openid-configuration` — le middleware JWT les récupère automatiquement au démarrage.

### Rôles Keycloak — KeycloakClaimsTransformation

Keycloak stocke les rôles dans `realm_access.roles` (format non standard). `IClaimsTransformation` les convertit en `ClaimTypes.Role` standards à chaque requête authentifiée.

**Fichier : `Extensions/KeycloakClaimsTransformation.cs`**

```csharp
namespace NutritionApi.Api.Extensions;

using System.Security.Claims;
using System.Text.Json;
using Microsoft.AspNetCore.Authentication;

public class KeycloakClaimsTransformation : IClaimsTransformation
{
    public Task<ClaimsPrincipal> TransformAsync(ClaimsPrincipal principal)
    {
        var realmAccess = principal.FindFirstValue("realm_access");
        if (realmAccess is null) return Task.FromResult(principal);

        var json = JsonDocument.Parse(realmAccess);
        if (!json.RootElement.TryGetProperty("roles", out var roles))
            return Task.FromResult(principal);

        var identity = new ClaimsIdentity();
        foreach (var role in roles.EnumerateArray())
        {
            var roleName = role.GetString();
            if (roleName is not null)
                identity.AddClaim(new Claim(ClaimTypes.Role, roleName));
        }

        principal.AddIdentity(identity);
        return Task.FromResult(principal);
    }
}
```

**Enregistrement :**

```csharp
builder.Services.AddSingleton<IClaimsTransformation, KeycloakClaimsTransformation>();
```

### Policies d'autorisation

```csharp
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("AdminOnly", policy => policy.RequireRole("admin"));
});
```

| Routes | Protection |
|---|---|
| `/api/v1/**` | `[Authorize]` — JWT valide requis |
| `/api/v1/admin/**` | `[Authorize(Policy = "AdminOnly")]` — rôle `admin` requis |
| `/hangfire` | `HangfireAdminAuthorizationFilter` — rôle `admin` requis |
| `/swagger` | Accessible uniquement hors production |

---

## 6. Swagger / OpenAPI

```csharp
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new OpenApiInfo { Title = "Nutrition API", Version = "v1" });

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
                Reference = new OpenApiReference { Type = ReferenceType.SecurityScheme, Id = "Bearer" }
            },
            Array.Empty<string>()
        }
    });

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

---

## 7. CORS (à configurer)

```csharp
// builder.Services — avant app.Build()
builder.Services.AddCors(options =>
    options.AddDefaultPolicy(policy =>
        policy.WithOrigins(builder.Configuration.GetSection("Cors:Origins").Get<string[]>()!)
              .AllowAnyHeader()
              .AllowAnyMethod()));

// pipeline — après UseHttpsRedirection
app.UseCors();
```
