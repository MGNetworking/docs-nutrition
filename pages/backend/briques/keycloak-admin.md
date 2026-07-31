# Keycloak Admin API — Connexion et opérations

> **Portée de ce document : la connexion de l'API à Keycloak Admin, et elle seule.**
> ➜ Pour la suppression des comptes de bout en bout, lire [RGPD — Purge des comptes](../systemes/rgpd/purge-des-comptes.md).
>
> **État au 2026-07-27**
>
> | | |
> |---|---|
> | ✅ | `KeycloakAdminService` et `KeycloakTokenProvider` sont implémentés et couverts par 22 tests unitaires (NTR-133) |
> | ✅ | `RgpdPurgeJob` consomme `DeleteUserAsync` (NTR-56) |
> | 🔲 | `RgpdService` n'appelle pas encore `DisableUserAsync` / `EnableUserAsync` — la désactivation au moment de la demande de suppression n'est donc pas effective |
> | ✅ | Le client de service `nutrition-api-service` est déclaré dans `keycloak/realm-export.json` — créé automatiquement à l'import du realm (2026-07-30) |
> | ✅ | Le flux complet est éprouvé au niveau 3 : le test crée un compte jetable, lance la purge, et vérifie sa disparition de Keycloak **et** de la base |
> | ✅ | L'application refuse de démarrer si l'un des quatre paramètres d'administration est vide — `KeycloakAdminConfigurationValidator` (NTR-149, 2026-07-31) |

### Les trois autres clients du realm

Outre `nutrition-api-service`, l'export en déclare trois — dont deux ne servent qu'aux tests.

| Client | Type | Rôle |
|---|---|---|
| `nutrition-api` | public | celui pour lequel Keycloak émet les jetons utilisateurs ; son mapper d'audience ajoute `nutrition-api` au claim `aud` |
| `nutrition-api-tests-shortlived` | public | émet des jetons valides **une seconde**, via l'attribut `access.token.lifespan`. Le realm impose 1800 s : sans ce client, éprouver le rejet d'un jeton expiré demanderait d'attendre trente minutes |
| `nutrition-api-tests-no-audience` | public | **aucun mapper d'audience** : ses jetons ne portent pas `nutrition-api` dans leur `aud`, et l'API doit les refuser. Sans ce contrôle, un jeton obtenu pour une autre API serait accepté |

> Le service account de `nutrition-api-service` sert aussi aux tests : son rôle `manage-users` leur
> permet de créer puis supprimer un compte jetable, sans toucher aux comptes du realm dont dépendent
> les autres cas.
>
> Référence workflow : `reference/diagrammes/workflow_rgpd.mermaid`

---

## Pourquoi l'API doit parler à Keycloak Admin

L'authentification (login, token) est gérée par Keycloak de façon autonome : l'API n'intervient pas.

Mais certaines opérations RGPD nécessitent que l'API agisse **directement sur les comptes Keycloak** :

| Opération | Déclencheur | Endpoint Keycloak Admin |
|---|---|---|
| Désactiver un compte | `DELETE /users/me` — début de grace period | `PATCH /admin/realms/{realm}/users/{id}` `{ "enabled": false }` |
| Réactiver un compte | `POST /users/me/reactivate` — dans les 30 jours | `PATCH /admin/realms/{realm}/users/{id}` `{ "enabled": true }` |
| Supprimer définitivement | Job purge — `DeletedAt` > 30 jours | `DELETE /admin/realms/{realm}/users/{id}` |

Ces opérations ne peuvent pas passer par le token utilisateur : elles requièrent des droits d'administration sur le realm.

---

## Mécanisme de connexion — Client Credentials

L'API s'authentifie auprès de Keycloak en tant que **service** (machine-to-machine), via le flux OAuth2 `client_credentials`.

### Principe

```
API → Keycloak Token Endpoint
      POST /realms/{realm}/protocol/openid-connect/token
      grant_type=client_credentials
      client_id=nutrition-api-service
      client_secret=<secret>

Keycloak → access_token (service token, sans contexte utilisateur)

API → Keycloak Admin API
      Authorization: Bearer <service token>
      PATCH / DELETE sur les ressources utilisateur
```

Le service token est obtenu à la demande et mis en cache jusqu'à expiration (TTL Keycloak, typiquement 60–300 secondes).

---

## Configuration côté Keycloak

> **En développement, rien de tout cela n'est à faire à la main.** Le client, son service account et
> ses rôles sont déclarés dans `keycloak/realm-export.json` : le realm les crée à l'import, à chaque
> recréation du conteneur. Le secret de développement y figure en clair, ce realm étant jetable.
>
> Les trois étapes ci-dessous décrivent la création manuelle — utile pour un realm de recette ou de
> production, où le secret ne doit jamais être versionné.

### 1. Créer un client de service dans Keycloak

Dans le realm de l'application :

| Paramètre | Valeur |
|---|---|
| Client ID | `nutrition-api-service` |
| Client type | `confidential` |
| Authentication flow | `Service accounts enabled` uniquement (pas de login humain) |
| Direct Access Grants | `Désactivé` |
| Standard Flow | `Désactivé` |

Ce client représente l'API elle-même, pas un utilisateur.

### 2. Attribuer le rôle `manage-users`

Le client doit avoir le rôle `manage-users` du realm pour pouvoir désactiver / supprimer des comptes.

Dans Keycloak Admin Console :
- `Clients` → `nutrition-api-service` → `Service account roles`
- Ajouter le rôle `manage-users` depuis `realm-management`

> **Principe du moindre privilège** : n'attribuer que `manage-users`, pas `realm-admin`. L'API ne doit pas pouvoir modifier la configuration du realm.

### 3. Récupérer le secret client

Dans `Clients` → `nutrition-api-service` → `Credentials` → copier le `Client Secret`.

---

## Configuration côté ASP.NET Core

### Variables d'environnement / secrets

```
Keycloak__AdminBaseUrl=https://keycloak.example.com
Keycloak__Realm=nutrition
Keycloak__ServiceClientId=nutrition-api-service
Keycloak__ServiceClientSecret=<secret>
```

Ces valeurs ne doivent jamais être dans le code source. En développement : `dotnet user-secrets`. En production : variables d'environnement injectées par Kubernetes (Secret).

`appsettings.json` déclare les quatre clés avec des valeurs vides, à l'exception de `ServiceClientId`
qui porte sa valeur par défaut `nutrition-api-service`.

> La section `Keycloak` est **partagée** avec la validation des jetons entrants (`Authority`,
> `Audience`, `RequireHttpsMetadata`, lues dans `Program.cs`). `KeycloakAdminOptions` ne lie que les
> quatre clés d'administration ; les deux usages cohabitent sans se gêner.

### Le garde-fou au démarrage — `KeycloakAdminConfigurationValidator` (NTR-149)

Ces quatre clés étant vides dans `appsettings.json` par conception, rien ne garantissait qu'un
environnement les fournisse réellement. **L'omission ne se voyait pas au démarrage : elle se payait à
la purge de la nuit suivante**, et en silence — `RgpdPurgeJob` intercepte toute exception, la
journalise et poursuit. Une production déployée sans secret aurait produit une purge qui échoue
chaque nuit, sans autre trace que les journaux, pendant que des comptes dont le délai de grâce est
expiré restaient dans le realm.

`NutritionApi.Api/Startup/KeycloakAdminConfigurationValidator.cs` refuse le démarrage si l'une des
quatre est absente ou vide, et **nomme toutes les manquantes d'un coup** :

```
Configuration Keycloak Admin incomplète — clés absentes ou vides : Keycloak:Realm,
Keycloak:ServiceClientSecret. La purge RGPD ne pourrait pas supprimer les comptes du realm,
et son échec serait silencieux : démarrage interrompu.
```

Les nommer toutes évite de corriger un déploiement par redémarrages successifs, une clé à la fois.
Une variable d'environnement définie mais vide arrive comme une suite d'espaces : le contrôle utilise
`IsNullOrWhiteSpace`, pas `IsNullOrEmpty`.

#### Pourquoi un `IHostedService` et non `ValidateOnStart()`

Le mécanisme natif des options aurait fait le même travail, mais il s'exécute **toujours** : depuis
.NET 8 la validation est déclenchée par `Host.StartAsync` via `IStartupValidator`, hors de la liste
des services hébergés. Or les tests de niveau 2 substituent `IKeycloakAdminService` et ne renseignent
aucune de ces clés — ils n'en ont pas besoin. Ils ne s'en sortent que parce que `ApiFactory` fait
`services.RemoveAll<IHostedService>()`, ce qui n'atteint pas un validateur d'options.

En `IHostedService`, le contrôle disparaît avec cette ligne, exactement comme
`KeycloakAvailabilityService`. Aucune fixture à modifier.

#### Les deux vérifications Keycloak au démarrage

| Service | Ce qu'il vérifie | Réseau |
|---|---|---|
| `KeycloakAdminConfigurationValidator` | les quatre paramètres d'administration sont renseignés | non — quatre chaînes en mémoire |
| `KeycloakAvailabilityService` (NTR-147) | le realm répond et publie ses clés de signature | oui — attente bornée à 60 s |

Le premier détecte un **oubli de déploiement**, le second une **panne**. Le validateur est enregistré
en premier dans `Program.cs` : si les deux doivent échouer, autant échouer sur celui qui répond
immédiatement plutôt qu'après l'attente réseau.

#### Ce que chaque niveau de test établit

Les deux niveaux sont nécessaires, et aucun ne remplace l'autre.

| Niveau | Fichier | Ce qu'il prouve |
|---|---|---|
| 1 | `Api.Tests/Level1/KeycloakAdminConfigurationValidatorTest.cs` | la classe lève quand une clé est vide — les quatre clés, l'espace assimilé au vide, le message qui les nomme toutes |
| 3 | `ExternalIntegration.Tests/Startup/KeycloakAdminConfigurationTest.cs` | **l'application** refuse de démarrer — donc que la classe est bien enregistrée dans `Program.cs` et que son exception remonte jusqu'à l'hôte |

Le niveau 1 ne dit rien du branchement : la classe pourrait n'être appelée nulle part et ses sept
tests resteraient verts. Vérification faite en débranchant la ligne de `Program.cs` — le cas de
niveau 3 échoue alors sur `No exception was thrown`, l'API démarrant avec un secret vide.

Le cas de niveau 3 ne coupe aucun conteneur : il vide une clé par `WithWebHostBuilder`, dont le
délégué s'applique après le `ConfigureWebHost` de la fabrique. `CreateClient()` déclenche le
démarrage de l'hôte, et c'est là que l'échec se produit.

> La fabrique de niveau 3 injecte par ailleurs `AdminBaseUrl`, `Realm` et `ServiceClientSecret`
> depuis `keycloak/realm-export.json`, et `ServiceClientId` porte sa valeur par défaut
> d'`appsettings.json` : les 23 autres cas du niveau démarrent donc normalement.

### Le contrat — `IKeycloakAdminService`

L'interface vit dans la couche **Application** (`Application/Interfaces/ExternalServices/`) : c'est
Application qui a besoin d'agir sur les comptes, Infrastructure ne fait qu'obéir au contrat. Elle ne
porte pas de `CancellationToken` — les appelants sont un job de fond et un service applicatif, aucun
n'a de jeton d'annulation à propager.

```csharp
public interface IKeycloakAdminService
{
    Task DisableUserAsync(string keycloakId);
    Task EnableUserAsync(string keycloakId);
    Task DeleteUserAsync(string keycloakId);
}
```

### Les deux classes d'implémentation

`NutritionApi.Infrastructure/ExternalServices/Keycloak/` :

| Classe | Responsabilité unique | Durée de vie |
|---|---|---|
| `KeycloakAdminOptions` | Porter les 4 paramètres de la section `Keycloak` | — |
| `IKeycloakTokenProvider` / `KeycloakTokenProvider` | Obtenir et **mémoriser** le jeton de service | **Singleton** |
| `KeycloakAdminService` | Appeler l'API Admin avec ce jeton | Transient (client typé) |

Le fournisseur de jetons est séparé du service pour une raison précise : le jeton doit survivre aux
requêtes, alors que l'appel Admin est sans état. Les fusionner aurait forcé le service entier en
singleton, ou le jeton à être redemandé à chaque appel.

#### Le cache du jeton

`KeycloakTokenProvider` conserve le jeton et sa date d'expiration, et le renouvelle **30 secondes
avant** son échéance réelle : sans cette marge, un jeton obtenu juste avant l'expiration pourrait
périmer entre son obtention et l'appel Admin qui l'utilise.

Un `SemaphoreSlim` protège le renouvellement — au démarrage, dix requêtes simultanées ne déclenchent
qu'une seule demande de jeton, les autres attendant le résultat. Le motif est un double contrôle :
le cache est testé une première fois sans verrou, puis une seconde fois après l'avoir obtenu.

L'horloge est injectée (`TimeProvider`), ce qui permet aux tests de vérifier l'expiration sans
attendre réellement.

### Résilience — deux mécanismes distincts

| Cas | Traité par | Comment |
|---|---|---|
| **401** Unauthorized | `KeycloakAdminService` lui-même | Invalide le jeton mémorisé, puis **rejoue une fois**. Un second 401 lève. |
| **5xx / 408 / 429 / timeout** | `AddStandardResilienceHandler()` (`Microsoft.Extensions.Http.Resilience`) | Retry exponentiel, disjoncteur et délai d'attente standards, posés sur le client HTTP |
| **404** Not Found | `KeycloakAdminService` lui-même | Le compte n'existe plus côté Keycloak : l'opération est sans objet, journalisée en avertissement, **pas d'exception** |
| **Keycloak injoignable** | `KeycloakAdminService` lui-même | `ServiceUnavailableException("Keycloak")` → **503** avec `Retry-After` (NTR-135) |

Le 401 ne peut pas être délégué au handler standard : seul le service sait qu'il faut **invalider le
cache du jeton** avant de rejouer — un simple retry rejouerait avec le même jeton périmé.

> `Microsoft.Extensions.Http.Resilience` remplace l'ancien `Polly.Extensions.Http`. Polly reste le
> moteur sous-jacent, mais la configuration passe désormais par le `IHttpClientBuilder`.

#### Quand toutes les tentatives ont échoué — le 503 (NTR-135)

Une fois le handler de résilience épuisé, l'échec réseau remonte. `KeycloakAdminService` le traduit
alors en `ServiceUnavailableException`, que le middleware d'exceptions convertit en **503** :

```csharp
catch (HttpRequestException exception) when (exception.StatusCode is null)
{
    throw new ServiceUnavailableException("Keycloak", exception);
}
catch (TaskCanceledException exception)
{
    throw new ServiceUnavailableException("Keycloak", exception);
}
```

**La clause `when` est le cœur de la distinction.** `HttpRequestException` recouvre deux situations
très différentes :

| `StatusCode` | Situation | Traitement |
|---|---|---|
| `null` | Aucune réponse — Keycloak est injoignable | **503**, panne passagère |
| renseigné | Keycloak a répondu par une erreur HTTP (via `EnsureSuccessStatusCode`) | remonte tel quel → **500** |

Les confondre masquerait un défaut de configuration — un client de service mal déclaré, un rôle
`manage-users` absent — en panne passagère. L'administrateur attendrait que « ça revienne », alors
que rien ne reviendrait.

C'est cette traduction qui évite à la couche API de connaître `HttpRequestException` : elle ne voit
qu'une abstraction d'Application. Voir [Exception Filter](../systemes/plateforme/exception-filter.md).

### Enregistrement — `NutritionApi.Infrastructure/DependencyInjection.cs`

```csharp
services.Configure<KeycloakAdminOptions>(configuration.GetSection(KeycloakAdminOptions.SectionName));
services.AddSingleton(TimeProvider.System);

services.AddHttpClient(KeycloakTokenProvider.HttpClientName)
        .AddStandardResilienceHandler();

services.AddSingleton<IKeycloakTokenProvider>(sp => new KeycloakTokenProvider(
    sp.GetRequiredService<IHttpClientFactory>().CreateClient(KeycloakTokenProvider.HttpClientName),
    sp.GetRequiredService<IOptions<KeycloakAdminOptions>>(),
    sp.GetRequiredService<TimeProvider>()));

services.AddHttpClient<IKeycloakAdminService, KeycloakAdminService>(KeycloakAdminService.HttpClientName)
        .AddStandardResilienceHandler();
```

Le fournisseur est enregistré par fabrique et non par `AddHttpClient<,>` : cette dernière n'enregistre
qu'en `Transient`, ce qui viderait le cache du jeton à chaque requête.

---

## Flux complet — Suppression de compte

```
1. API reçoit DELETE /users/me
2. API appelle KeycloakAdminService.DisableUserAsync(keycloakId)
   └─ KeycloakAdminService :
       a. GET service token (cache ou nouveau)
       b. PATCH /admin/realms/nutrition/users/{keycloakId} { "enabled": false }
       c. Keycloak refuse tous les nouveaux logins pour cet utilisateur
3. API met à jour User.DeletedAt = maintenant (PostgreSQL)
4. API envoie l'email de confirmation avec lien signé (30 jours)
5. Retour 200 OK
```

À partir de l'étape 2c, l'utilisateur ne peut plus se connecter — son token actuel reste valide jusqu'à expiration naturelle (durée configurée dans Keycloak, typiquement 5–15 min).

---

## Données partagées entre l'API et Keycloak

| Donnée | Stockée dans | Rôle |
|---|---|---|
| `KeycloakId` (UUID) | PostgreSQL `User.KeycloakId` | Clé de liaison — permet à l'API d'agir sur le bon compte Keycloak |
| Email, Nom | Keycloak (source de vérité) | L'API ne stocke pas ces données — elle les lit depuis le token JWT à la création du profil |
| `enabled` (flag) | Keycloak | Bloque l'authentification pendant la grace period |

Le `KeycloakId` est extrait du JWT à chaque requête (claim `sub`) et utilisé pour retrouver le `User` en base.

---

## Ce que Keycloak Admin NE fait PAS

- Il ne supprime pas les données de l'application (repas, poids, plans) — c'est la responsabilité du job de purge PostgreSQL
- Il ne gère pas la logique des 30 jours — c'est l'API qui contrôle `DeletedAt`
- Il ne déclenche pas d'email — c'est le service email de l'application

La suppression dans Keycloak (`DELETE /admin/realms/{realm}/users/{id}`) est la **première étape** de
la purge, avant la suppression des données PostgreSQL — et non l'inverse, comme le prévoyait la
spécification initiale.

La raison est l'idempotence du job : si l'appel Keycloak échoue, rien n'est supprimé et le compte
reste sélectionnable au passage suivant. Dans l'ordre inverse, un échec Keycloak après une base déjà
purgée laisserait un compte orphelin que plus aucune exécution ne sélectionnerait.
Voir [RGPD — Purge des comptes](../systemes/rgpd/purge-des-comptes.md).

---

*Référence : [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/)*
