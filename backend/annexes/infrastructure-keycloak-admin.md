# Keycloak Admin API — Connexion et opérations

> Ce document décrit comment l'API ASP.NET Core se connecte à Keycloak Admin pour gérer les comptes utilisateur dans le cadre du workflow RGPD.
> Référence workflow : `workflow_rgpd.mermaid`

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

### Service dédié — `IKeycloakAdminService`

L'API expose une interface dans la couche **Infrastructure** :

```csharp
public interface IKeycloakAdminService
{
    Task DisableUserAsync(string keycloakId, CancellationToken ct);
    Task EnableUserAsync(string keycloakId, CancellationToken ct);
    Task DeleteUserAsync(string keycloakId, CancellationToken ct);
}
```

L'implémentation (`KeycloakAdminService`) :
1. Obtient un service token via `client_credentials` (mis en cache)
2. Appelle l'endpoint Admin avec `HttpClient`
3. Gère les erreurs HTTP (404 = compte déjà supprimé, 401 = token expiré → retry)

### Résilience avec Polly

Le service token peut expirer entre l'obtention et l'appel Admin. Polly gère le retry :

```
- 401 Unauthorized → invalider le cache token + retry 1 fois
- 5xx / timeout    → retry exponentiel (3 tentatives max)
```

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

La suppression dans Keycloak (`DELETE /admin/realms/{realm}/users/{id}`) est la **dernière étape** de la purge, après la suppression complète des données PostgreSQL.

---

*Référence : [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/)*
