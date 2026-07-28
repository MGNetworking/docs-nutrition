# Workflow — Écrire un test de niveau 2

**Ajouté le :** 2026-07-27 · **Ticket :** NTR-134 (socle) · **Niveau :** 2 — Intégration interne

> Ce document explique **comment fonctionne le socle** des tests de niveau 2 et comment s'en servir.
> Pour savoir *ce que* chaque niveau doit couvrir, lire [Niveaux de tests](niveaux-de-tests.md) ;
> pour la liste des tests à écrire, [Recensement des tests](recensement-des-tests.md).

---

## 1. Vue d'ensemble

Un test de niveau 2 **démarre l'API et lui envoie de vraies requêtes HTTP**. Tout le pipeline
s'exécute ; seules les dépendances externes sont remplacées.

```
    ┌─────────────────── processus de test ────────────────────┐
    │                                                          │
    │   [ton test]                                             │
    │       │  client.GetAsync("/api/v1/diet-plans")           │
    │       ▼                                                  │
    │   ┌──────────────────────────────────────────────┐       │
    │   │  TON API, démarrée en mémoire                │       │
    │   │                                              │       │
    │   │   routing → auth → middlewares →             │  RÉEL │
    │   │   Controller → Service                       │       │
    │   │        │                                     │       │
    │   │        ▼  IDietPlanRepository ───────────────┼── doublure Moq
    │   │           IFoodCacheService  ────────────────┼── doublure Moq
    │   └──────────────────────────────────────────────┘       │
    └──────────────────────────────────────────────────────────┘

    Aucun port réseau ouvert · aucun conteneur · aucune base
```

**La frontière est nette :** tout ce qui est **au-dessus** des interfaces d'Application est réel,
tout ce qui est **en dessous** est une doublure.

---

## 2. Qui fait quoi

```
tests/NutritionApi.Api.Tests/Integration/
├── Fixtures/                      ← l'outillage partagé, ne teste rien
│   ├── ApiFactory.cs              — démarre l'API, substitue les dépendances
│   └── TestAuthHandler.cs         — fabrique l'identité de l'appelant
├── ApiFactoryTest.cs              — vérifie le socle lui-même
└── <Controller>IntegrationTest.cs — les tests métier (NTR-105 à NTR-111)
```

Le dossier `Fixtures/` isole la mécanique des cas d'usage, sur le même principe que
`Infrastructure/Scheduling/` séparé de `Infrastructure/Jobs/`.

| Classe | Responsabilité unique |
|---|---|
| `ApiFactory` | Démarrer l'API, substituer les 11 interfaces de frontière, fournir des clients HTTP |
| `TestAuthHandler` | Traduire des en-têtes en `ClaimsPrincipal`, à la place du JWT Keycloak |
| `ApiFactoryTest` | Prouver que le socle fonctionne avant que les tests métier ne s'y fient |

---

## 3. `ApiFactory` — le point d'entrée

### Ce dont elle hérite

`WebApplicationFactory<T>` est **fournie par Microsoft** (package `Microsoft.AspNetCore.Mvc.Testing`).
Elle sait démarrer une application ASP.NET Core dans un processus de test. `ApiFactory` ne fait
qu'en personnaliser trois aspects.

```csharp
public sealed class ApiFactory : WebApplicationFactory<Program>
```

Le paramètre `<Program>` est **le lien avec ton API** : il désigne un type de l'assembly de
l'application, ce qui permet à la fabrique de retrouver cet assembly puis son point d'entrée.

> **Pourquoi `public partial class Program;` dans `Program.cs`**
> Les instructions de haut niveau (`Program.cs` sans classe ni `Main` explicites) font générer par
> le compilateur une classe `Program` **`internal`** — invisible depuis le projet de test.
> `WebApplicationFactory<Program>` ne compilerait pas. Cette déclaration partielle vide fusionne
> avec la classe générée et la rend publique. Elle ne contient aucun code.

### Tu ne l'instancies jamais — xUnit s'en charge

```csharp
public class DietPlansIntegrationTest : IClassFixture<ApiFactory>   // ← tu déclares le besoin
{
    private readonly ApiFactory _factory;

    public DietPlansIntegrationTest(ApiFactory factory)              // ← xUnit l'injecte
        => _factory = factory;
}
```

xUnit voit `IClassFixture<ApiFactory>`, crée **une seule** instance pour toute la classe de test,
la passe au constructeur, puis la libère à la fin.

**C'est ce qui évite de redémarrer l'API à chaque test.** Sans `IClassFixture`, chaque méthode
paierait le démarrage.

### Les trois choses qu'elle fait

**a. Elle neutralise ce qui exigerait une infrastructure**

```csharp
services.RemoveAll<IHostedService>();
```

Une seule ligne, deux effets : elle retire le **serveur Hangfire** et le
**`RecurringJobRegistrationService`**. Tous deux sont des hosted services, et tous deux
contacteraient PostgreSQL au démarrage. C'est précisément pour rendre cette ligne possible que
l'enregistrement des jobs a quitté `Program.cs` (NTR-29) — un appel statique aurait échappé à
la substitution.

**b. Elle substitue les 11 interfaces de frontière**

| | |
|---|---|
| 7 repositories | `IUserRepository`, `IDietPlanRepository`, `IDietRepository`, `IMealRepository`, `IFoodItemRepository`, `IWeightEntryRepository`, `ISavedFoodItemRepository` |
| Unité de travail | `IUnitOfWork` |
| Services externes | `IFoodCacheService`, `IKeycloakAdminService`, `IJobMonitoringService` |

Chacune est exposée en propriété publique, pour que le test décide de ses réponses :

```csharp
_factory.DietPlans
        .Setup(r => r.GetUserPlansAsync(It.IsAny<Guid>()))
        .ReturnsAsync([unPlan]);
```

**c. Elle fournit des clients HTTP**

```csharp
_factory.CreateAnonymousClient()                    // aucune identité   → teste les 401
_factory.CreateAuthenticatedClient()                // utilisateur normal
_factory.CreateAuthenticatedClient(roles: "admin")  // administrateur    → teste les 403
```

---

## 4. `TestAuthHandler` — l'identité sans Keycloak

### Le problème qu'il résout

En production, l'appelant envoie `Authorization: Bearer eyJhbG…`, et ASP.NET valide la signature
auprès de Keycloak. **En test, il n'y a pas de Keycloak : aucun jeton valide n'est productible.**

Sans solution, tous les endpoints `[Authorize]` répondraient 401 et rien ne serait testable.

### Comment il s'articule avec le reste

`AuthenticationHandler` est une classe **d'ASP.NET Core**. On en écrit une implémentation de test,
`ApiFactory` la déclare comme schéma par défaut, et **tout le reste du pipeline continue de
fonctionner sans savoir que le jeton est faux** :

```
CreateAuthenticatedClient(roles: "admin")
   │  pose les en-têtes X-Test-Sub et X-Test-Roles sur le HttpClient
   ▼
TestAuthHandler.HandleAuthenticateAsync()
   │  lit les en-têtes → construit un ClaimsPrincipal
   ▼
HttpContext.User  ← rempli, exactement comme avec un vrai JWT
   │
   ├──► [Authorize]                  fonctionne
   ├──► policy AdminOnly             fonctionne
   └──► UserResolutionMiddleware     lit le claim "sub", interroge IUserRepository
```

| | Production | Test |
|---|---|---|
| L'appelant envoie | `Authorization: Bearer eyJ…` | `X-Test-Sub: 1111-…` |
| Qui vérifie | JwtBearer → clés Keycloak | `TestAuthHandler` |
| Résultat | `HttpContext.User` rempli | `HttpContext.User` rempli — **identique** |

### Deux détails qui comptent

**Sans en-tête, pas d'authentification.** Le handler renvoie `NoResult()`, ce qui produit un vrai
401 — c'est ainsi que `CreateAnonymousClient()` permet de tester les endpoints protégés.

**Le claim s'appelle `sub`, pas autre chose.** L'API configure `MapInboundClaims = false` et
`UserResolutionMiddleware` lit littéralement `"sub"`. Le handler pose donc ce nom exact.

**Le type de rôle est déclaré explicitement** dans le `ClaimsIdentity`, faute de quoi `IsInRole` et
la policy `AdminOnly` ne reconnaîtraient pas les rôles posés.

---

## 5. Le piège à connaître — `UserResolutionMiddleware`

Ce middleware s'exécute sur **chaque requête authentifiée** :

```csharp
var user = await _userRepository.GetByKeycloakIdAsync(keycloakId!);
if (user is null) { context.Response.StatusCode = 401; return; }
```

Si la doublure d'`IUserRepository` n'est pas armée, elle renvoie `null` → **401**, et le test échoue
avec un code sans rapport avec ce qu'il vérifie.

`ApiFactory` arme donc une valeur par défaut pour `DefaultSubject`. Un test qui utilise un autre
sujet doit l'armer lui-même — ou s'en servir volontairement, comme le fait
`AuthenticatedRequest_WithUnknownUser_Returns401`.

---

## 6. Écrire un test — le gabarit

```csharp
namespace NutritionApi.Api.Tests.Integration;

using NutritionApi.Api.Tests.Integration.Fixtures;
using System.Net;

public class DietPlansIntegrationTest : IClassFixture<ApiFactory>
{
    private readonly ApiFactory _factory;

    public DietPlansIntegrationTest(ApiFactory factory) => _factory = factory;

    [Fact]
    public async Task GetAll_WhenAuthenticated_Returns200()
    {
        _factory.DietPlans
                .Setup(r => r.GetUserPlansAsync(It.IsAny<Guid>()))
                .ReturnsAsync([]);

        var response = await _factory.CreateAuthenticatedClient().GetAsync("/api/v1/diet-plans");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task GetAll_WithoutToken_Returns401()
    {
        var response = await _factory.CreateAnonymousClient().GetAsync("/api/v1/diet-plans");

        Assert.Equal(HttpStatusCode.Unauthorized, response.StatusCode);
    }
}
```

---

## 7. Lancer les tests

Aucune commande spécifique : ce sont des tests xUnit ordinaires.

```bash
dotnet test
```

Pour ne lancer que les tests d'intégration :

```bash
dotnet test --filter "FullyQualifiedName~Integration"
```

### Comment fonctionne ce filtre

`--filter` est une option **native de `dotnet test`**. Elle porte sur des propriétés du test :

| Élément | Signification |
|---|---|
| `FullyQualifiedName` | Le nom complet du test, **namespace compris** — par exemple `NutritionApi.Api.Tests.Integration.ApiFactoryTest.ProtectedEndpoint_WithoutIdentity_Returns401` |
| `~` | « contient » (les autres opérateurs sont `=`, `!=`, `!~`) |

Tous les tests de niveau 2 vivent dans le namespace `NutritionApi.Api.Tests.Integration`, donc leur
nom complet contient `Integration`. **C'est le namespace, et lui seul, qui rend cette sélection
possible** — d'où la règle : un test de niveau 2 se place dans `Integration/`, sans exception.

Quelques variantes utiles :

```bash
dotnet test --filter "FullyQualifiedName!~Integration"                    # tout sauf le niveau 2
dotnet test --filter "FullyQualifiedName~Integration.DietPlans"           # un seul fichier
dotnet test --filter "FullyQualifiedName~ApiFactoryTest"                  # le socle seul
```

---

## 8. Décisions et leurs raisons

| Décision | Pourquoi | Option écartée |
|---|---|---|
| Doublures aux interfaces d'Application | Le niveau 2 répond à « le pipeline HTTP fonctionne-t-il ? » — aucune de ces questions n'exige une base. La persistance réelle est le sujet du niveau 3. | Base réelle : le niveau 2 deviendrait un niveau 3 lent, et les deux feraient doublon. |
| **Ni InMemory ni SQLite** | Ils ignorent `UseSnakeCaseNamingConvention`, les colonnes `text[]` avec `ValueComparer`, et les `ON DELETE CASCADE` dont dépend `RgpdPurgeJob`. Ils donneraient une **fausse** confiance. | EF Core InMemory — déconseillé par l'équipe EF elle-même pour tester. |
| `TestAuthHandler` | Sans Keycloak, aucun jeton signé n'est productible. | JWT auto-signés + serveur JWKS factice : lourd, et la validation réelle appartient au niveau 3. |
| La validation JWT n'est **pas** testée ici | Le handler remplace précisément le composant qu'il s'agirait d'éprouver. | La tester quand même : elle ne prouverait rien. → NTR-28. |
| `IClassFixture` | Une seule instance par classe de test : l'API ne démarre qu'une fois. | Une fabrique par méthode : le démarrage serait payé à chaque test. |
| Dossier `Fixtures/` | L'outillage partagé ne se mêle pas aux cas d'usage. | Tout à plat : dix fichiers de nature différente dans un même dossier. |

---

## 9. Ce qui n'est pas couvert

| Manque | Statut |
|---|---|
| Validation réelle des jetons (signature, issuer, expiration) | Volontaire — NTR-28 |
| Requêtes SQL, migrations, cascades PostgreSQL | Volontaire — NTR-28 |
| TTL Redis, orchestration cache/base | Volontaire — NTR-73 |
| CORS | **Non testable ici** — Postman et `HttpClient` n'envoient pas d'en-tête `Origin` et n'appliquent pas la politique du navigateur |
| Dashboard Hangfire | Retiré du pipeline de test avec les hosted services |

**Limite de performance connue :** le démarrage de l'hôte prend environ **38 secondes**, cause non
identifiée — Hangfire, Redis, Keycloak et l'instrumentation de couverture ont été écartés par mesure.
Il est payé une fois par classe de test. Passer en `ICollectionFixture` le ramènerait à une fois
pour l'ensemble de la suite, au prix d'un état partagé entre classes.

---

## 10. État de confiance

| Marque | Élément |
|---|---|
| ✅ | Le socle démarre sans PostgreSQL, Redis ni Keycloak — `ApiFactoryTest` |
| ✅ | 401 sans identité, 403 sans rôle admin, accès admin, 401 sur profil absent |
| ✅ | La substitution des doublures est effective — prouvée par le test du profil inconnu |
| ⚠️ | Les 38 s de démarrage sont mesurées, pas expliquées |
| ❌ | Aucun test métier écrit à ce jour — c'est l'objet de NTR-105 à NTR-111 |

---

## 11. Où creuser

- [Niveaux de tests](niveaux-de-tests.md) — ce que chaque niveau doit couvrir
- [Recensement des tests](recensement-des-tests.md) — la liste des cas à écrire
- [Pipeline HTTP](../systemes/plateforme/pipeline-http.md) — l'ordre des middlewares traversés
- [Hangfire](../briques/hangfire.md) — pourquoi l'enregistrement des jobs est un hosted service
