# Hangfire — moteur de jobs récurrents

**Ajouté le :** 2026-05-02

> **Portée de ce document : le moteur de jobs, et lui seul.**
> Hangfire est un outil *partagé* — il fait tourner l'import Open Food Facts (NTR-55) et fera
> tourner la purge RGPD (NTR-56). Ce document décrit donc la mécanique commune : configuration,
> stockage, dashboard, supervision.
>
> ➜ Pour comprendre **comment fonctionne l'import des aliments de bout en bout**, lire d'abord
> [Workflow — Mise à disposition des aliments](../systemes/aliments/workflow-import.md). Ce document-ci ne sert qu'à approfondir la brique Hangfire.

---

## Pourquoi Hangfire

L'application nécessite deux jobs nocturnes :

| Job | Déclenchement | Besoin | État |
|---|---|---|---|
| Import Open Food Facts | Quotidien 03h00 | Télécharger + ingérer le dump OFF | ✅ Livré (NTR-55) |
| Purge RGPD | Quotidien 03h30 | Supprimer les comptes en grace period > 30 jours | ✅ Livré (NTR-56) |

**Hangfire** a été retenu face à `IHostedService` pour deux raisons décisives :

1. **Historique natif** — chaque exécution est enregistrée automatiquement dans les tables PostgreSQL Hangfire. Aucune entité domaine `JobExecution` à maintenir. Le `GET /admin/system/health` lit directement ces tables.
2. **Dashboard web** — interface de monitoring et de relance manuelle intégrée, disponible sur `/hangfire` (restreint au rôle `admin`).

---

## Comment Hangfire fonctionne

### Ce n'est pas un service externe

Hangfire est une **bibliothèque .NET qui s'exécute à l'intérieur du process de l'API** — il n'y a **aucun serveur Hangfire séparé** à déployer, ni conteneur dédié, ni port à ouvrir. La seule ressource externe dont il a besoin pour vivre est une base de données où **persister son état** : ici, **le même PostgreSQL que l'application**, mais dans un schéma isolé nommé `hangfire`.

Deux conséquences directes :

- **Si l'API tourne, Hangfire tourne avec elle.** Les jobs s'exécutent dans le même process — ils accèdent donc au conteneur de dépendances (DI), aux repositories, au `DbContext`, exactement comme un controller.
- **Si plusieurs instances de l'API tournent** (plusieurs pods en production), elles **partagent le même storage PostgreSQL** et se coordonnent seules : un seul process prend chaque exécution, pas de doublon. C'est PostgreSQL qui joue le rôle d'arbitre (verrous).

### Les trois rôles

Hangfire se décompose en trois responsabilités, toutes portées par le même process :

| Rôle | Ce qu'il fait | Dans ce projet |
|---|---|---|
| **Client** | Sérialise une demande de travail (« exécute `OffImportJob.RunAsync()` ») et **l'écrit dans le storage**. Il n'exécute rien lui-même. | `RecurringJobRegistrationService` (hosted service), au démarrage |
| **Storage** | La base PostgreSQL (schéma `hangfire`) : file d'attente, définition des jobs récurrents, **et historique de chaque exécution**. C'est le point de vérité central. | `UsePostgreSqlStorage(...)` dans `InfrastructureExtensions.AddInfrastructure()` |
| **Server** | Un processus de fond (`AddHangfireServer`) qui **interroge le storage en continu**, prend les jobs dus, les exécute via la DI, puis **écrit le résultat** (succès/échec) dans le storage. | `services.AddHangfireServer()` dans `InfrastructureExtensions.AddInfrastructure()` |

Le point clé : **le Client et le Server ne se parlent jamais directement.** Tout transite par le storage. C'est ce découplage qui permet la persistance (un job survit à un redémarrage), l'historique (tout est écrit) et le scale-out (plusieurs serveurs, un seul storage).

### Le cycle complet d'un job récurrent

```
1. Démarrage de l'API
   └─ RecurringJobRegistrationService.StartAsync() → AddOrUpdate("import-off", "0 3 * * *")
      └─ écrit/actualise la définition dans hangfire.hash (recurring-job:import-off)

2. Le Server tourne en fond (workers + scheduler)
   └─ à 03h00 UTC, le scheduler voit que "import-off" est dû
      └─ il crée un job à exécuter → hangfire.job (état: Enqueued)

3. Un worker prend le job
   └─ résout IOffImportJob via la DI → appelle RunAsync()
      ├─ succès → état Succeeded  (écrit dans hangfire.job / hangfire.state,
      │                            et reporté dans hangfire.hash : LastJobState)
      └─ exception → état Failed + retry automatique planifié

4. Lecture ultérieure
   ├─ Dashboard /hangfire  → affiche l'historique et permet de relancer
   └─ GET /admin/system/health → lit hangfire.hash pour le statut
```

### Le stockage PostgreSQL — un schéma à part

**Hangfire crée lui-même ses tables au premier démarrage**, dans le schéma `hangfire`. Aucune migration EF Core à écrire pour ces tables — elles ne font pas partie du modèle du domaine.

Ces deux comportements sont les **valeurs par défaut** de `Hangfire.PostgreSql` : le code ne passe donc ni `SchemaName` ni `PrepareSchemaIfNecessary`, il se contente de fournir la chaîne de connexion.

Pourquoi un schéma séparé (`hangfire`) et pas les tables de l'app :

- **isolation** — les tables techniques de Hangfire ne polluent pas le modèle métier ni les migrations EF Core ;
- **cycle de vie distinct** — Hangfire gère la création et l'évolution de son propre schéma ;
- `UseSnakeCaseNamingConvention()` (appliqué au `DbContext` de l'app) **n'a aucun effet** sur ce schéma : c'est Hangfire qui nomme ses tables, pas EF Core. Le schéma, les tables et les colonnes sont **entièrement en minuscules** (`hangfire.hash`, `hangfire.job`…) — vérifié après implémentation de NTR-55.

### Pourquoi « enregistrer » les jobs au démarrage

`AddOrUpdate(...)` est appelé **à chaque démarrage** de l'API. Ce n'est pas une exécution du job — c'est l'**écriture de sa définition** (identifiant, méthode cible, expression cron) dans le storage.

- **Sans cet appel, aucun job ne se planifie** : Hangfire ne peut pas deviner qu'il existe un import quotidien.
- L'appel est **idempotent** (`AddOrUpdate`) : au premier démarrage il crée la définition, aux suivants il la met à jour si le cron ou la cible a changé. On peut donc redémarrer autant qu'on veut sans créer de doublons.

C'est aussi ce qui verrouille l'identifiant `"import-off"` : c'est sous ce nom que le job vit dans le storage, et sous ce même nom que la supervision le retrouve. D'où la constante `IJobMonitoringService.ImportOffJobName`, partagée entre l'enregistrement et la lecture.

### Où vit chaque morceau de configuration

La configuration Hangfire est **répartie entre deux couches**, et c'est le point qui surprend le plus à la lecture : on ne trouve pas tout dans `Program.cs`.

| Morceau | Emplacement réel | Pourquoi là |
|---|---|---|
| `AddHangfire(...)` + `AddHangfireServer()` | `NutritionApi.Infrastructure/DependencyInjection.cs` | Le storage PostgreSQL et le serveur d'exécution sont des **détails d'infrastructure**, au même titre que le `DbContext` ou Redis. Toute la couche s'enregistre par un seul appel `builder.Services.AddInfrastructure(configuration)` dans `Program.cs`. |
| `MapHangfireDashboard(...)` | `Program.cs`, après `app.UseAuthorization()` | C'est un **endpoint HTTP** : il appartient au pipeline web, que seule la couche API connaît. |
| `AddOrUpdate(...)` des jobs récurrents | `Infrastructure/Scheduling/RecurringJobRegistrationService.cs` | Déclaré comme hosted service, donc contrôlable par la DI : un test peut l'écarter, et un storage injoignable ne bloque plus le démarrage. |

L'ordre dans le pipeline compte pour deux raisons distinctes :

1. **`MapHangfireDashboard("/hangfire", ...)` — la raison est l'authentification.** Le filtre d'autorisation du dashboard lit `httpContext.User` pour vérifier le rôle `admin`. Or `User` n'est peuplé qu'**après** que les middlewares `UseAuthentication()` et `UseAuthorization()` se sont exécutés. Monter le dashboard **avant** ces middlewares donnerait un `User` vide → le filtre refuserait tout le monde (ou laisserait passer, selon l'implémentation). L'ordre est donc **obligatoire** pour le dashboard. Il est en revanche placé **avant** `UserResolutionMiddleware` : le dashboard n'a pas besoin de la résolution `keycloakId` → `User` interne.
2. **L'enregistrement des jobs récurrents n'a, lui, aucune contrainte d'ordre.** Il a seulement besoin que le storage soit configuré, ce qui est acquis dès `builder.Build()`, et ne dépend pas du pipeline d'authentification. C'est pourquoi il a pu quitter `Program.cs` pour un hosted service sans rien casser.

### Le dashboard et son filtre d'autorisation

`/hangfire` est une interface web servie par un middleware Hangfire. Par défaut elle est **ouverte** — il faut donc la protéger explicitement avec un `IDashboardAuthorizationFilter` (voir plus bas). Le filtre reçoit le `DashboardContext`, en extrait le `HttpContext`, et n'autorise l'accès que si l'utilisateur est authentifié **et** porte le rôle `admin`. C'est le seul point où un humain interagit directement avec Hangfire.

### La supervision : de l'historique à l'API

Le volet supervision ne fait **que lire** ce que le Server a déjà écrit. `GET /admin/system/health` interroge `hangfire.hash` pour retrouver, par job récurrent, sa dernière exécution, sa prochaine et l'état de son dernier run. L'état brut Hangfire est repris tel quel dans la réponse, avec un seul repli maison — `Scheduled` quand le job est enregistré mais n'a encore jamais tourné (voir le détail plus bas).

> C'est ce chaînage — *le Server écrit → la supervision relit* — qui explique pourquoi aucune entité `JobExecution` maison n'est nécessaire : l'historique **est** la source de vérité, et il est tenu par Hangfire.

---

## Packages NuGet

Déclarés dans `NutritionApi.Infrastructure.csproj` — c'est la couche Infrastructure, et elle seule, qui référence Hangfire :

```xml
<PackageReference Include="Hangfire.AspNetCore" Version="1.8.24" />
<PackageReference Include="Hangfire.PostgreSql" Version="1.21.1" />
```

---

## Configuration du storage — `NutritionApi.Infrastructure/DependencyInjection.cs`

```csharp
// Jobs planifiés persistés dans PostgreSQL (schéma dédié, tables créées au
// démarrage). Le serveur d'exécution tourne dans le process de l'API.
services.AddHangfire(config => config
    .SetDataCompatibilityLevel(CompatibilityLevel.Version_180)
    .UseSimpleAssemblyNameTypeSerializer()
    .UseRecommendedSerializerSettings()
    .UsePostgreSqlStorage(options => options.UseNpgsqlConnection(connectionString)));

services.AddHangfireServer();

// Supervision des jobs planifiés — lit l'état des recurring jobs dans hangfire.hash
services.AddScoped<IJobMonitoringService, JobMonitoringService>();
```

`connectionString` est la chaîne `ConnectionStrings:DefaultConnection` — **la même base que l'application**, Hangfire n'écrivant que dans son schéma `hangfire`.

Les trois appels qui précèdent `UsePostgreSqlStorage` concernent la **sérialisation des jobs** dans le storage : ils fixent le format d'écriture à celui recommandé pour Hangfire 1.8. Sans eux, Hangfire démarre sur un format hérité et l'affiche en avertissement au lancement.

## Dashboard — `NutritionApi.Api/Program.cs`

```csharp
// Dashboard Hangfire — restreint au rôle admin par HangfireAdminAuthorizationFilter.
// Placé après UseAuthorization (le filtre lit User) et avant UserResolutionMiddleware
// (le dashboard n'a pas besoin de la résolution keycloakId → User interne).
app.MapHangfireDashboard("/hangfire", new DashboardOptions
{
    Authorization = [new HangfireAdminAuthorizationFilter()]
});
```

### Filtre d'autorisation dashboard

`IDashboardAuthorizationFilter` est une interface **du package Hangfire** (namespace `Hangfire.Dashboard`) : inutile de la chercher dans le code du projet. Ce que le projet écrit, c'est son implémentation, dans `NutritionApi.Infrastructure/Scheduling/HangfireAdminAuthorizationFilter.cs` :

```csharp
public sealed class HangfireAdminAuthorizationFilter : IDashboardAuthorizationFilter
{
    public bool Authorize(DashboardContext context)
    {
        var httpContext = context.GetHttpContext();
        return httpContext.User.Identity?.IsAuthenticated == true
            && httpContext.User.IsInRole("admin");
    }
}
```

> Le test passe par `IsInRole("admin")` et non par une lecture brute du claim Keycloak `realm_access.roles` :
> `KeycloakClaimsTransformation` (enregistré dans `Program.cs`) a déjà converti ces rôles en `ClaimTypes.Role`
> standards. Le filtre s'appuie donc sur le mécanisme natif ASP.NET, exactement comme la policy `AdminOnly`
> des endpoints `/api/v1/admin`.

---

## Enregistrement des jobs récurrents

Dans `NutritionApi.Infrastructure/Scheduling/RecurringJobRegistrationService.cs`, un `IHostedService`
exécuté une fois au démarrage :

```csharp
public Task StartAsync(CancellationToken cancellationToken)
{
    try
    {
        _recurringJobs.AddOrUpdate<IOffImportJob>(
            IJobMonitoringService.ImportOffJobName,
            job => job.RunAsync(),
            ImportOffCron,                                    // "0 3 * * *"
            new RecurringJobOptions { TimeZone = TimeZoneInfo.Utc });

        _recurringJobs.AddOrUpdate<IRgpdPurgeJob>(
            IJobMonitoringService.RgpdPurgeJobName,
            job => job.RunAsync(),
            RgpdPurgeCron,                                    // "30 3 * * *"
            new RecurringJobOptions { TimeZone = TimeZoneInfo.Utc });
    }
    catch (Exception exception)
    {
        _logger.LogError(exception, "Enregistrement des jobs récurrents impossible…");
    }

    return Task.CompletedTask;
}
```

Les identifiants viennent des constantes `IJobMonitoringService.ImportOffJobName` et
`RgpdPurgeJobName`, jamais de littéraux : c'est sous ces noms que les jobs vivent dans le storage, et
sous les mêmes que la supervision les retrouve. Une seule source de vérité, pas de magic string entre
couches.

### Pourquoi un hosted service et non un appel dans `Program.cs`

L'enregistrement se faisait à l'origine par deux appels statiques `RecurringJob.AddOrUpdate(...)` en fin
de `Program.cs`. Deux raisons ont conduit à les déplacer (NTR-29) :

| Raison | Détail |
|---|---|
| **Le démarrage ne doit pas dépendre du storage** | `RecurringJob.AddOrUpdate` écrit immédiatement en base. Storage injoignable = exception non gérée = **l'API ne démarre pas du tout**, alors que le trafic HTTP n'a aucun besoin de Hangfire. Le service journalise l'échec et laisse démarrer. |
| **Les tests d'intégration doivent pouvoir l'écarter** | `WebApplicationFactory<Program>` exécute tout `Program.cs` jusqu'à `app.Run()`. Un appel statique y échappe à la DI : impossible à neutraliser. Devenu `IHostedService`, il se retire avec le serveur Hangfire en une ligne — voir plus bas. |

Contrepartie assumée : un storage injoignable ne fait plus échouer le démarrage, la panne devient donc
**silencieuse**. Le garde-fou est `GET /admin/system/health`, qui liste les jobs réellement enregistrés —
un job manquant y est visible.

### Neutraliser Hangfire dans un test d'intégration

```csharp
builder.ConfigureTestServices(services => services.RemoveAll<IHostedService>());
```

Cette seule ligne retire **le serveur Hangfire et l'enregistrement des jobs**, tous deux enregistrés
comme hosted services. C'est ce qui permet au niveau 2 (pipeline HTTP, `WebApplicationFactory`) de
tourner sans PostgreSQL — et donc d'exister séparément du niveau 3.

### État actuel : deux jobs enregistrés

`GET /admin/system/health` remonte **deux lignes**, `import-off` et `rgpd-purge`.
`JobMonitoringService` liste ce qui est réellement enregistré dans `hangfire.hash`, rien de plus.

Les crons sont écrits en littéraux et non avec `Cron.Daily(3)` / `Cron.Daily(3, 30)` : les deux sont
équivalents, mais l'expression brute est celle qui fait référence dans les tickets et la fiche RGPD.

> **Un job qui lève est un job qui sera rejoué.** `RgpdPurgeJob` s'appuie dessus : il journalise
> chaque compte en échec, poursuit avec les suivants, puis lève en fin de parcours s'il en reste.
> Sans cette exception finale, Hangfire considérerait l'exécution réussie et les comptes en échec
> attendraient le lendemain.

---

## Structure des classes — `NutritionApi.Infrastructure/`

Le **moteur** (transverse) est séparé des **jobs métier** (un dossier chacun) :

```
Scheduling/                                ← la mécanique Hangfire, partagée
├── HangfireAdminAuthorizationFilter.cs    — accès au dashboard réservé au rôle admin
├── JobMonitoringService.cs                — supervision (lecture de hangfire.hash)
└── RecurringJobRegistrationService.cs     — déclare les jobs récurrents au démarrage

Jobs/
├── OffImport/                           — job d'import Open Food Facts (NTR-55)
│   ├── IOffImportJob.cs, OffImportJob.cs
│   ├── OffDumpReader.cs                 — téléchargement + lecture du dump (streaming)
│   └── OffProduct.cs, OffProductMapper.cs
└── RgpdPurge/                           — job de purge RGPD (NTR-56)
    └── IRgpdPurgeJob.cs, RgpdPurgeJob.cs
```

> `JobMonitoringService`, le filtre d'autorisation et le service d'enregistrement **ne sont pas des
> jobs** : ils déclarent, supervisent et protègent l'exécution. D'où leur place dans `Scheduling/` et
> non dans `Jobs/`.

Les interfaces permettent à Hangfire de résoudre les jobs via le conteneur DI.

---

## Lecture de l'état des jobs pour `GET /admin/system/health`

La supervision liste les **jobs récurrents** : pour chacun, sa dernière exécution, sa prochaine
exécution et l'état de son dernier run. Ces informations vivent dans la table **`hangfire.hash`**,
sous la clé `recurring-job:<id>` — **et non** dans l'historique brut (`hangfire.job` / `hangfire.state`),
qui ne donne ni la prochaine exécution ni la liste des jobs planifiés.

`JobMonitoringService` interroge donc `hangfire.hash` directement (via Npgsql) :

```sql
select
    substring(key from 'recurring-job:(.*)')          as job_name,
    max(value) filter (where field = 'LastExecution') as last_run,
    max(value) filter (where field = 'NextExecution') as next_run,
    max(value) filter (where field = 'LastJobState')  as status
from hangfire.hash
where key like 'recurring-job:%'
group by key
order by job_name;
```

**Format des dates** : `LastExecution` et `NextExecution` sont stockées en **millisecondes Unix**
(ex : `1784862000000`), pas en ISO 8601 — à convertir via `DateTimeOffset.FromUnixTimeMilliseconds`.

**Statut retourné** (`status`) : l'état brut Hangfire du dernier run (`Succeeded`, `Failed`…),
ou `Scheduled` si le job est enregistré mais n'a encore jamais tourné (`LastJobState` absent).

---

## Tables Hangfire (créées automatiquement)

Hangfire crée ses tables au démarrage si elles n'existent pas — comportement par défaut, aucune option
à passer. Aucune migration EF Core manuelle requise pour le schéma Hangfire. Les tables sont créées dans
le schéma **`hangfire`** (minuscules), avec des noms de tables et de colonnes également en minuscules —
et non en PascalCase comme le laisserait supposer la documentation Hangfire, écrite pour SQL Server.

| Table | Contenu |
|---|---|
| `hangfire.job` | Un enregistrement par exécution ; la colonne `statename` porte l'état final |
| `hangfire.state` | Historique des transitions d'état de chaque job |
| `hangfire.counter` | Agrégats internes (succès, échecs) |
| `hangfire.hash` | Définition **et** état des jobs récurrents (`recurring-job:<id>`) — **source de la supervision** |

---

## Voir aussi

- [Source Open Food Facts — import du catalogue](../systemes/aliments/source-open-food-facts.md) — logique métier du job d'import OFF
- [Keycloak Admin API — Connexion et opérations](keycloak-admin.md) — appel Keycloak Admin pour la purge RGPD
- [Back-office Admin — API Nutrition](../7.nutrition-admin.md) — endpoint `GET /admin/system/health`
- [RGPD — Purge des comptes](../systemes/rgpd/purge-des-comptes.md) — feature RGPD (purge, grace period)
