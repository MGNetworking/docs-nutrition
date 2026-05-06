# Authentification

**Ajouté le :** 2026-05-02
**Référence spec :** `docs/pages/backend/annexes/workflow_Flux_authentification.mermaid` · `docs/pages/backend/domaine/Modele-domaine.md#authentification`

---

## Objectif

Permettre à un utilisateur de s'authentifier de façon sécurisée via Keycloak et d'accéder à l'API avec un token JWT valide.

## Qui l'utilise

Tous les utilisateurs (Free, Pro, Business) — prérequis à toute autre fonctionnalité.

## Quand

À chaque ouverture de session. Le token est ensuite envoyé dans chaque requête API.

## Ce qu'elle fait

- Délègue l'authentification à Keycloak (OAuth2 / OIDC — Authorization Code Flow + PKCE)
- Émet un `access_token` JWT contenant le `sub` (= `KeycloakId`)
- L'API valide le JWT à chaque requête (signature + audience + expiration)
- L'API résout `sub` → `User.KeycloakId` → `User.Id` interne

## Ce qu'elle ne fait pas

- L'API ne gère pas les mots de passe — Keycloak s'en charge
- L'API ne stocke pas les tokens — gestion côté client

## Endpoints

Aucun endpoint API direct — flux géré entre le client et Keycloak.
Le middleware JWT s'applique sur **tous** les endpoints protégés.

## Dépendances

- Keycloak (fournisseur d'identité)
- Middleware JWT ASP.NET Core
