# RGPD

**Ajouté le :** 2026-05-02
**Référence spec :** `docs/pages/backend/annexes/workflow_rgpd.mermaid` · `docs/pages/backend/annexes/infrastructure-keycloak-admin.md`

---

## Objectif

Garantir la conformité RGPD de l'application en permettant à l'utilisateur d'exercer ses droits sur ses données personnelles (export, suppression, réactivation).

## Qui l'utilise

Tous les utilisateurs — droits non conditionnés au tier (obligations légales).

## Quand

- Export : à tout moment, sur demande de l'utilisateur
- Suppression : à tout moment, avec grace period de 30 jours
- Réactivation : dans les 30 jours suivant la demande de suppression
- Purge : automatique après 30 jours (job Infrastructure nocturne)

## Ce qu'elle fait

- Exporte toutes les données personnelles en JSON (Art. 20 — portabilité)
- Soft delete du compte : `User.DeletedAt = maintenant` + désactivation Keycloak
- Envoie un email avec un lien signé valable 30 jours pour annuler
- Réactive le compte si le lien est cliqué dans les 30 jours
- Purge automatique après 30 jours : suppression cascade PostgreSQL + suppression définitive Keycloak

## Ce qu'elle ne fait pas

- Ne supprime pas immédiatement — grace period obligatoire de 30 jours
- Après purge : données irrécupérables (pas de backup individuel)

## Endpoints

| Méthode | Endpoint | Description |
|---|---|---|
| `GET` | `/users/me/export` | Exporter toutes ses données (Art. 20) |
| `DELETE` | `/users/me` | Demander la suppression du compte (Art. 17) |
| `POST` | `/users/me/reactivate` | Annuler la suppression (< 30 jours) |

## Export RGPD — implémentation technique

### Principe en mémoire

L'export ne touche jamais le disque — tout se passe en RAM.

```
RgpdService                    UsersController
    │                               │
    │   ExportUserDataAsync()       │
    │ ◄─────────────────────────── │
    │                               │
    │   UserExportResponse (DTO)    │
    │ ──────────────────────────── ►│
    │                               │
    │                    Sérialise en JSON (WriteIndented)
    │                               │
    │                    Crée un ZipArchive en MemoryStream
    │                    Ajoute "User-Data.json" dans le ZIP
    │                               │
    │                    File(bytes, "application/zip", "export-yyyy-MM-dd.zip")
```

### DTO — `UserExportResponse`

```csharp
public record UserExportResponse(
    UserProfileResponse         Profile,
    List<WeightEntryResponse>   WeightHistory,
    List<DietPlanResponse>      DietPlans,
    List<DietResponse>          Diets,
    List<MealResponse>          Meals,
    List<SavedFoodItemResponse> SavedFoodItems
);
```

Toutes les données que l'utilisateur a fournies ou générées par son activité — conformément à l'Art. 20 RGPD (droit à la portabilité).

### Implémentation controller

```csharp
[HttpGet("me/export")]
public async Task<IActionResult> ExportUserData()
{
    var keycloakId = User.FindFirstValue(ClaimTypes.NameIdentifier);
    var export = await _rgpdService.ExportUserDataAsync(keycloakId);

    var json = JsonSerializer.Serialize(export, new JsonSerializerOptions
    {
        WriteIndented = true
    });
    var jsonBytes = Encoding.UTF8.GetBytes(json);

    using var memoryStream = new MemoryStream();
    using (var archive = new ZipArchive(memoryStream, ZipArchiveMode.Create, leaveOpen: true))
    {
        var entry = archive.CreateEntry("mon-export.json");
        using var entryStream = entry.Open();
        entryStream.Write(jsonBytes);
    }

    return File(
        memoryStream.ToArray(),
        "application/zip",
        $"export-{DateTime.UtcNow:yyyy-MM-dd}.zip"
    );
}
```

### Points clés

| Élément | Rôle |
|---|---|
| `MemoryStream` | Stocke le ZIP en RAM — pas d'écriture sur disque |
| `ZipArchive` | Gestionnaire du fichier ZIP |
| `CreateEntry("mon-export.json")` | Crée le fichier JSON à l'intérieur du ZIP |
| `leaveOpen: true` | Garde le stream ouvert après la fermeture du ZipArchive |
| `memoryStream.ToArray()` | Convertit en `byte[]` pour la réponse HTTP |
| `Content-Disposition` | Géré automatiquement par `File()` — force le téléchargement |

### Pourquoi un `RgpdService` dédié ?

`ExportUserDataAsync` doit agréger les données de **6 agrégats** (User, WeightEntry, DietPlan, Diet, Meal, SavedFoodItem). Placer cette méthode dans `UserService` imposerait 5 repositories supplémentaires à une classe qui ne gère que l'agrégat `User`. La création de `RgpdService` respecte le principe de responsabilité unique et la frontière des agrégats DDD.

### Responsabilités par couche

| Couche | Responsabilité |
|---|---|
| `RgpdService` | Agréger les données de tous les agrégats → retourner `UserExportResponse` |
| `UsersController` | Sérialiser en JSON → emballer dans un ZIP → retourner le fichier |

Le service ne sait pas comment les données sont livrées — c'est la responsabilité exclusive de la couche API.

---

## Dépendances

- Keycloak Admin API — désactivation / réactivation / suppression du compte Keycloak
- `infrastructure-keycloak-admin.md` — mécanisme de connexion service account
- Service email — envoi du lien de réactivation signé
- Job purge RGPD (Hangfire — quotidien)
