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
    "off-import",
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
├── IOffImportJob.cs          ← interface (enregistrée dans DI)
├── OffImportJob.cs           ← implémentation
├── IRgpdPurgeJob.cs
└── RgpdPurgeJob.cs
```

Les interfaces permettent à Hangfire de résoudre les jobs via le conteneur DI.

---

## Lecture de l'historique pour `GET /admin/system/health`

Hangfire stocke chaque exécution dans la table `HangFire.Job` (état final dans `HangFire.State`).  
L'`AdminService` interroge directement ces tables via EF Core (ou Dapper) :

```sql
-- Dernière exécution du job "off-import"
SELECT j.CreatedAt, s.Name AS StateName, s.Data
FROM "HangFire"."Job" j
JOIN "HangFire"."State" s ON s.Id = j.StateId
WHERE j.InvocationData::text LIKE '%OffImportJob%'
ORDER BY j.CreatedAt DESC
LIMIT 1;
```

**Mapping des états Hangfire → statuts API :**

| État Hangfire | Statut retourné par l'API |
|---|---|
| `Succeeded` | `success` |
| `Failed` | `failed` |
| aucun enregistrement | `never_run` |

---

## Tables Hangfire (créées automatiquement)

`PrepareSchemaIfNecessary = true` crée les tables au démarrage si elles n'existent pas.  
Aucune migration EF Core manuelle requise pour le schéma Hangfire.

| Table | Contenu |
|---|---|
| `HangFire.Job` | Un enregistrement par exécution (scheduled, enqueued, processing, succeeded, failed) |
| `HangFire.State` | Historique des transitions d'état de chaque job |
| `HangFire.Counter` | Agrégats internes (succès, échecs) |
| `HangFire.Hash` | Données de configuration des jobs récurrents |

---

## Voir aussi

- `infrastructure-import-off.md` — logique métier du job d'import OFF
- `infrastructure-keycloak-admin.md` — appel Keycloak Admin pour la purge RGPD
- `docs/backend/8.nutrition-admin.md` — endpoint `GET /admin/system/health`
- `docs/backend/features/rgpd.md` — feature RGPD (purge, grace period)
