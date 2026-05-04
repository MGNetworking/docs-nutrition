# OpenAPI / Swagger UI

**Ajouté le :** 2026-05-02
**Référence spec :** `docs/backend/4.nutrition-specifications-techniques.md`

---

## Objectif

Exposer une documentation interactive de l'API REST, permettant aux développeurs (frontend, intégrateurs) de consulter les contrats d'interface et de tester les endpoints directement depuis un navigateur, y compris les endpoints protégés par JWT.

## Qui l'utilise

- Développeurs frontend — consultation des contrats API (routes, body, réponses)
- Développeurs backend — validation des endpoints pendant le développement
- Non accessible en production (désactivé hors `dev` et `staging`)

## Quand

- En permanence sur les environnements `dev` et `staging`
- Désactivé en `prod` (variable d'environnement)

## Ce qu'elle fait

- Génère la spec OpenAPI 3.0 depuis les controllers et les attributs XML (`GET /swagger/v1/swagger.json`)
- Expose Swagger UI sur `/swagger` avec liste de tous les endpoints groupés par tag
- Permet d'authentifier les requêtes de test via un token JWT Bearer saisi dans l'UI
- Documente les réponses 401 et 403 automatiquement sur les endpoints protégés
- Exclut le dashboard Hangfire (`/hangfire`) de la spec OpenAPI

## Ce qu'elle ne fait pas

- N'est pas accessible en production
- Ne génère pas de SDK client (hors scope — outil externe si besoin)
- Ne valide pas les requêtes entrantes (rôle du middleware de validation)

## Endpoints exposés par Swashbuckle

| Méthode | Endpoint | Description |
|---|---|---|
| `GET` | `/swagger` | Interface Swagger UI (navigateur) |
| `GET` | `/swagger/v1/swagger.json` | Spec OpenAPI 3.0 au format JSON |

## Configuration clé

```csharp
// Program.cs
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo { Title = "Nutrition API", Version = "v1" });

    // Authentification JWT Bearer dans l'UI
    c.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Type = SecuritySchemeType.Http,
        Scheme = "bearer",
        BearerFormat = "JWT",
        Description = "Token JWT Keycloak"
    });
    c.AddSecurityRequirement(/* Bearer requis sur endpoints [Authorize] */);

    // Commentaires XML des controllers et DTOs
    var xmlFile = $"{Assembly.GetExecutingAssembly().GetName().Name}.xml";
    c.IncludeXmlComments(Path.Combine(AppContext.BaseDirectory, xmlFile));
});

// Activé uniquement hors prod
if (!app.Environment.IsProduction())
{
    app.UseSwagger();
    app.UseSwaggerUI(c => c.SwaggerEndpoint("/swagger/v1/swagger.json", "Nutrition API v1"));
}
```

## Dépendances

- `Swashbuckle.AspNetCore` (NuGet) — déjà listé dans les dépendances du projet
- Keycloak JWT — le token Bearer est obtenu depuis Keycloak pour tester les endpoints protégés
- Hangfire dashboard — exclu de la spec (route `/hangfire` gérée séparément)
