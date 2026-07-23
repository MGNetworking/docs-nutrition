# Infrastructure — Hangfire (jobs récurrents)

**Ajouté le :** 2026-05-02

---

## Pourquoi Hangfire

L'application nécessite deux jobs nocturnes :

| Job | Déclenchement | Besoin |
|---|---|---|
| Import Open Food Facts | Quotidien 03h00 | Télécharger + ingérer le dump OFF |
| Purge RGPD | Quotidien 03h30 | Supprimer les comptes en grace period > 30 jours |

**Hangfire** a été retenu face à `IHostedService` pour deux raisons décisives :

1. **Historique natif** — chaque exécution est enregistrée automatiquement dans les tables PostgreSQL Hangfire. Aucune entité domaine `JobExecution` à maintenir. Le `GET /admin/system/health` lit directement ces tables.
2. **Dashboard web** — interface de monitoring et de relance manuelle intégrée, disponible sur `/hangfire` (restreint au rôle `admin`).

---

## Comment Hangfire fonctionne

### Ce n'est pas un service externe

Hangfire est une **bibliothèque .NET qui s'exécute à l'intérieur du process de l'API** — il n'y a **aucun serveur Hangfire séparé** à déployer, ni conteneur dédié, ni port à ouvrir. La seule ressource externe dont il a besoin pour vivre est une base de données où **persister son état** : ici, **le même PostgreSQL que l'application**, mais dans un schéma isolé nommé `HangFire`.

Deux conséquences directes :

- **Si l'API tourne, Hangfire tourne avec elle.** Les jobs s'exécutent dans le même process — ils accèdent donc au conteneur de dépendances (DI), aux repositories, au `DbContext`, exactement comme un controller.
- **Si plusieurs instances de l'API tournent** (plusieurs pods en production), elles **partagent le même storage PostgreSQL** et se coordonnent seules : un seul process prend chaque exécution, pas de doublon. C'est PostgreSQL qui joue le rôle d'arbitre (verrous).

### Les trois rôles

Hangfire se décompose en trois responsabilités, toutes portées par le même process :

| Rôle | Ce qu'il fait | Dans ce projet |
|---|---|---|
| **Client** | Sérialise une demande de travail (« exécute `OffImportJob.RunAsync()` ») et **l'écrit dans le storage**. Il n'exécute rien lui-même. | `RecurringJob.AddOrUpdate<IOffImportJob>(...)` au démarrage |
| **Storage** | La base PostgreSQL (schéma `HangFire`) : file d'attente, définition des jobs récurrents, **et historique de chaque exécution**. C'est le point de vérité central. | `UsePostgreSqlStorage(...)` |
| **Server** | Un processus de fond (`AddHangfireServer`) qui **interroge le storage en continu**, prend les jobs dus, les exécute via la DI, puis **écrit le résultat** (succès/échec) dans le storage. | `builder.Services.AddHangfireServer()` |

Le point clé : **le Client et le Server ne se parlent jamais directement.** Tout transite par le storage. C'est ce découplage qui permet la persistance (un job survit à un redémarrage), l'historique (tout est écrit) et le scale-out (plusieurs serveurs, un seul storage).

### Le cycle complet d'un job récurrent

```
1. Démarrage de l'API
   └─ RecurringJob.AddOrUpdate("import-off", cron "0 3 * * *")
      └─ écrit/actualise la définition dans HangFire.Hash (recurring-job:import-off)

2. Le Server tourne en fond (workers + scheduler)
   └─ à 03h00 UTC, le scheduler voit que "import-off" est dû
      └─ il crée un job à exécuter → HangFire.Job (état: Enqueued)

3. Un worker prend le job
   └─ résout IOffImportJob via la DI → appelle RunAsync()
      ├─ succès → état Succeeded  (écrit dans HangFire.Job / HangFire.State)
      └─ exception → état Failed + retry automatique planifié

4. Lecture ultérieure
   ├─ Dashboard /hangfire  → affiche l'historique et permet de relancer
   └─ GET /admin/system/health → lit HangFire.Job/State pour le statut
```

### Le stockage PostgreSQL — un schéma à part

`PrepareSchemaIfNecessary = true` fait que **Hangfire crée lui-même ses tables au premier démarrage**, dans le schéma `HangFire`. Aucune migration EF Core à écrire pour ces tables — elles ne font pas partie du modèle du domaine.

Pourquoi un schéma séparé (`HangFire`) et pas les tables de l'app :

- **isolation** — les tables techniques de Hangfire ne polluent pas le modèle métier ni les migrations EF Core ;
- **cycle de vie distinct** — Hangfire gère la création et l'évolution de son propre schéma ;
- `UseSnakeCaseNamingConvention()` (appliqué au `DbContext` de l'app) **n'a aucun effet** sur ce schéma : c'est Hangfire qui nomme ses tables, pas EF Core. ⚠️ Point à vérifier lors de l'implémentation : la casse réelle des tables/colonnes créées par `Hangfire.PostgreSql` (voir la note dans `mise-a-disposition-aliments`).

### Pourquoi « enregistrer » les jobs au démarrage

`RecurringJob.AddOrUpdate(...)` est appelé **à chaque démarrage** de l'API. Ce n'est pas une exécution du job — c'est l'**écriture de sa définition** (identifiant, méthode cible, expression cron) dans le storage.

- **Sans cet appel, aucun job ne se planifie** : Hangfire ne peut pas deviner qu'il existe un import quotidien.
- L'appel est **idempotent** (`AddOrUpdate`) : au premier démarrage il crée la définition, aux suivants il la met à jour si le cron ou la cible a changé. On peut donc redémarrer autant qu'on veut sans créer de doublons.

C'est aussi ce qui verrouille l'identifiant `"import-off"` : c'est sous ce nom que le job vit dans le storage, et sous ce même nom que la supervision le retrouve.

### Pourquoi dans `Program.cs`, après `app.UseAuthorization()`

Deux choses différentes se placent à cet endroit, avec deux justifications distinctes :

1. **`MapHangfireDashboard("/hangfire", ...)` — la raison est l'authentification.** Le filtre d'autorisation du dashboard lit `httpContext.User` pour vérifier le rôle `admin`. Or `User` n'est peuplé qu'**après** que les middlewares `UseAuthentication()` et `UseAuthorization()` se sont exécutés. Monter le dashboard **avant** ces middlewares donnerait un `User` vide → le filtre refuserait tout le monde (ou laisserait passer, selon l'implémentation). L'ordre est donc **obligatoire** pour le dashboard.
2. **`RecurringJob.AddOrUpdate(...)` — la raison est la commodité.** Cet enregistrement a seulement besoin que le storage soit configuré (fait au `builder.Build()`). Il n'a aucune dépendance au pipeline d'auth. On le place ici simplement pour **regrouper toute la configuration Hangfire post-`Build()` au même endroit**, à la suite du dashboard.

### Le dashboard et son filtre d'autorisation

`/hangfire` est une interface web servie par un middleware Hangfire. Par défaut elle est **ouverte** — il faut donc la protéger explicitement avec un `IDashboardAuthorizationFilter` (voir plus bas). Le filtre reçoit le `DashboardContext`, en extrait le `HttpContext`, et n'autorise l'accès que si l'utilisateur est authentifié **et** porte le rôle `admin`. C'est le seul point où un humain interagit directement avec Hangfire.

### La supervision : de l'historique à l'API

Le volet supervision ne fait **que lire** ce que le Server a déjà écrit. `GET /admin/system/health` interroge `HangFire.Job`/`HangFire.State` pour retrouver, par job, la dernière exécution et son état. Ces états internes Hangfire sont ensuite **traduits en statuts d'API** stables (le mapping est détaillé plus bas), pour que le contrat de l'endpoint ne dépende pas du vocabulaire interne de Hangfire.

> C'est ce chaînage — *le Server écrit → la supervision relit* — qui explique pourquoi aucune entité `JobExecution` maison n'est nécessaire : l'historique **est** la source de vérité, et il est tenu par Hangfire.

---

## Packages NuGet

```xml
<PackageReference Include="Hangfire.AspNetCore" Version="1.8.*" />
<PackageReference Include="Hangfire.PostgreSql" Version="1.20.*" />
```

---

## Configuration — `Program.cs`

```csharp
// Stockage dans PostgreSQL (mêmes tables que l'app, schéma "HangFire")
builder.Services.AddHangfire(config => config
    .UsePostgreSqlStorage(builder.Configuration.GetConnectionString("Default"),
        new PostgreSqlStorageOptions
        {
            SchemaName = "HangFire",
            PrepareSchemaIfNecessary = true
        }));

builder.Services.AddHangfireServer();

// Dashboard restreint au rôle admin
app.MapHangfireDashboard("/hangfire", new DashboardOptions
{
    Authorization = [new HangfireAdminAuthorizationFilter()]
});
```

### Filtre d'autorisation dashboard

```csharp
public class HangfireAdminAuthorizationFilter : IDashboardAuthorizationFilter
{
    public bool Authorize(DashboardContext context)
    {
        var http = context.GetHttpContext();
        return http.User.Identity?.IsAuthenticated == true
            && http.User.HasClaim("realm_access_roles", "admin");
    }
}
```

---

## Enregistrement des jobs récurrents

À faire dans `Program.cs` après `app.UseAuthorization()` :

```csharp
RecurringJob.AddOrUpdate<IOffImportJob>(
    "import-off",          // = IJobMonitoringService.ImportOffJobName (le contrat fait foi)
    job => job.RunAsync(),
    "0 3 * * *",            // chaque nuit à 03h00 UTC
    new RecurringJobOptions { TimeZone = TimeZoneInfo.Utc });

RecurringJob.AddOrUpdate<IRgpdPurgeJob>(
    "rgpd-purge",
    job => job.RunAsync(),
    "30 3 * * *",           // chaque nuit à 03h30 UTC
    new RecurringJobOptions { TimeZone = TimeZoneInfo.Utc });
```

---

## Structure des classes — `NutritionApi.Infrastructure/Jobs/`

```
Jobs/
├── HangfireAdminAuthorizationFilter.cs   — accès au dashboard réservé au rôle admin
├── JobMonitoringService.cs               — supervision (lecture de hangfire.hash)
├── IOffImportJob.cs, OffImportJob.cs      — job d'import Open Food Facts
├── OffDumpReader.cs                        — téléchargement + lecture du dump (streaming)
├── OffProduct.cs, OffProductMapper.cs      — produit normalisé + traduction OFF → FoodItem
└── (à venir, NTR-56) RgpdPurgeJob.cs       — purge RGPD
```

Les interfaces permettent à Hangfire de résoudre les jobs via le conteneur DI.

---

## Lecture de l'état des jobs pour `GET /admin/system/health`

> ⚠️ **Corrigé après implémentation (NTR-55).** Le schéma réel créé par `Hangfire.PostgreSql`
> est **entièrement en minuscules** (`hangfire.hash`, `hangfire.job`…), et non en PascalCase
> comme le laissait croire la version initiale de cette doc (convention SQL Server).

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
group by key;
```

**Format des dates** : `LastExecution` et `NextExecution` sont stockées en **millisecondes Unix**
(ex : `1784862000000`), pas en ISO 8601 — à convertir via `DateTimeOffset.FromUnixTimeMilliseconds`.

**Statut retourné** (`status`) : l'état brut Hangfire du dernier run (`Succeeded`, `Failed`…),
ou `Scheduled` si le job est enregistré mais n'a encore jamais tourné (`LastJobState` absent).

---

## Tables Hangfire (créées automatiquement)

`PrepareSchemaIfNecessary = true` crée les tables au démarrage si elles n'existent pas.  
Aucune migration EF Core manuelle requise pour le schéma Hangfire. Les tables sont créées dans
le schéma **`hangfire`** (minuscules), avec des noms de tables et de colonnes également en minuscules.

| Table | Contenu |
|---|---|
| `hangfire.job` | Un enregistrement par exécution ; la colonne `statename` porte l'état final |
| `hangfire.state` | Historique des transitions d'état de chaque job |
| `hangfire.counter` | Agrégats internes (succès, échecs) |
| `hangfire.hash` | Définition **et** état des jobs récurrents (`recurring-job:<id>`) — **source de la supervision** |

---

## Voir aussi

- `infrastructure-import-off.md` — logique métier du job d'import OFF
- `infrastructure-keycloak-admin.md` — appel Keycloak Admin pour la purge RGPD
- `docs/pages/backend/8.nutrition-admin.md` — endpoint `GET /admin/system/health`
- `docs/pages/backend/features/interne/rgpd-purge-comptes.md` — feature RGPD (purge, grace period)
