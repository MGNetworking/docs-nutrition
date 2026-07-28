# OpenAPI / Swagger UI

**Ajouté le :** 2026-05-02
**Type :** Interne
**Référence spec :** [Installer ReportGenerator (une seule fois, outil global)](../../4.nutrition-specifications-techniques.md)

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

### Pourquoi `/hangfire` n'apparaît pas — aucune exclusion à écrire

Swashbuckle ne documente que les `ApiDescription` produites par le routage MVC, c'est-à-dire les
actions de controllers. `MapHangfireDashboard("/hangfire", …)` monte un **middleware**, pas une
action : il ne produit aucune `ApiDescription` et reste donc invisible pour la génération.

Aucun `DocumentFilter` n'est nécessaire. Le jour où l'on voudrait exclure une route MVC réelle, il
faudrait en revanche en écrire un.

## Validation du contrat

Le contrat est verrouillé à deux niveaux, et un seul est automatisé.

| Vérification | Comment | Statut |
|---|---|---|
| Chaque action déclare Summary et Description | `OpenApiContractTest` — réflexion sur `[SwaggerOperation]` | ✅ automatisé |
| Chaque action déclare un code de succès | `OpenApiContractTest` — `[ProducesResponseType]` 2xx | ✅ automatisé |
| Chaque action protégée déclare son 401 | `OpenApiContractTest` — croise `[Authorize]` et `[ProducesResponseType]` | ✅ automatisé |
| `swagger.json` généré valide et importable (Postman, NSwag/Kiota) | Lancement réel de l'API | ⚠️ manuel |

`OpenApiContractTest` tourne **sans démarrer l'API** : il parcourt les types de l'assembly par
réflexion. C'est ce qui lui permet d'exister avant les tests de niveau 3, qui eux exigent
docker-compose (NTR-28). La contrepartie est qu'il valide les **attributs**, pas le JSON produit :
un défaut de sérialisation Swashbuckle lui échapperait.

## État de confiance

| Marque | Élément |
|---|---|
| ✅ | Summary, Description, codes de réponse et 401 sur toutes les actions — vérifié par test |
| ⚠️ | Absence de `/hangfire` dans la spec — établi par le fonctionnement de Swashbuckle, non constaté sur un `swagger.json` réel |
| ❌ | Validité et exploitabilité du `swagger.json` généré (import Postman, génération de client) |

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
