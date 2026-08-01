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

Le contrat est verrouillé à deux niveaux, tous deux automatisés.

| Vérification | Comment | Niveau |
|---|---|---|
| Chaque action déclare Summary et Description | `OpenApiContractTest` — réflexion sur `[SwaggerOperation]` | 1 |
| Chaque action déclare un code de succès | `OpenApiContractTest` — `[ProducesResponseType]` 2xx | 1 |
| Chaque action protégée déclare son 401 | `OpenApiContractTest` — croise `[Authorize]` et `[ProducesResponseType]` | 1 |
| Le document est servi, en `application/json` | `OpenApiDocumentTest` — appel réel à `/swagger/v1/swagger.json` | 3 |
| Le document est lu sans erreur par un parseur OpenAPI | `OpenApiDocumentTest` — `OpenApiStringReader`, diagnostic vide | 3 |
| Chaque action exposée figure dans le document | `OpenApiDocumentTest` — croise les `ApiDescription` réelles avec les chemins du document | 3 |
| Le schéma de sécurité Bearer est déclaré | `OpenApiDocumentTest` — `Components.SecuritySchemes` | 3 |
| `/hangfire` est absent du document | `OpenApiDocumentTest` | 3 |

**Les deux niveaux ne prouvent pas la même chose.** `OpenApiContractTest` tourne sans démarrer l'API :
il parcourt les types de l'assembly par réflexion, et valide donc les **attributs**, pas le JSON
produit — un défaut de sérialisation Swashbuckle lui échapperait. `OpenApiDocumentTest` démarre
l'application réelle et lit le document tel qu'il sort.

**Sur « importable ».** Un test ne peut pas lancer Postman ni Kiota. Ce qu'il fait à la place : faire
lire le document par `OpenApiStringReader`, le parseur de `Microsoft.OpenApi`, et exiger un
diagnostic sans erreur. Un document que ce parseur accepte est celui que les générateurs de clients
savent consommer. C'est la garantie la plus proche qu'un test automatisé puisse offrir.

**La liste des endpoints attendus n'est écrite nulle part.** Le test croise les chemins du document
avec les `ApiDescription` que le routage MVC produit réellement, résolues depuis le conteneur. Une
action ajoutée est donc attendue dans le document dès le run suivant, sans qu'aucune liste ne soit à
tenir à jour.

Couvert par NTR-155.

## État de confiance

| Marque | Élément |
|---|---|
| ✅ | Summary, Description, codes de réponse et 401 sur toutes les actions — vérifié par test |
| ✅ | Absence de `/hangfire` dans la spec — désormais constatée sur le `swagger.json` réel, et non plus seulement déduite du fonctionnement de Swashbuckle |
| ✅ | Validité du `swagger.json` généré — lu sans erreur par un parseur OpenAPI, endpoints et schéma de sécurité vérifiés |
| ⚠️ | Génération effective d'un client (NSwag, Kiota) et import Postman — non exécutés par un test, aucun outil externe n'est lancé |

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
