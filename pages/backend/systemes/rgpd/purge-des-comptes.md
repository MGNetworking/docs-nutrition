# RGPD — Purge des comptes

**Ajouté le :** 2026-05-02
**Type :** Interne
**Référence spec :** `reference/diagrammes/workflow_rgpd.mermaid` · [Keycloak Admin API — Connexion et opérations](../../briques/keycloak-admin.md)

> Les droits exercés par l'utilisateur (export, demande de suppression, réactivation) sont une fonctionnalité distincte — voir [RGPD — Droits de l'utilisateur](index.md).

---

## Objectif

Supprimer définitivement les comptes dont la demande de suppression dépasse la grace period de 30 jours, afin d'honorer le droit à l'effacement (Art. 17) sans intervention humaine.

## Qui l'utilise

Aucun acteur humain — job de fond déclenché par le planificateur (Hangfire).

## Quand

- Quotidien, chaque nuit (job Infrastructure nocturne)
- Cible les comptes en grace period depuis plus de 30 jours (`User.DeletedAt` > 30 jours)

## Ce qu'elle fait

- Sélectionne les comptes dont la grace period est expirée (`DeletedAt <= J-30`)
- Supprime définitivement le compte dans Keycloak
- Supprime ensuite les données dans PostgreSQL, en cascade
- Enregistre l'exécution dans l'historique Hangfire (visible depuis le back-office admin)

> **État au 2026-07-27** — livré (NTR-56).
>
> | | |
> |---|---|
> | ✅ | Le job `RgpdPurgeJob` et son enregistrement Hangfire, couverts par 9 tests unitaires |
> | ✅ | L'accès à Keycloak Admin — `KeycloakAdminService.DeleteUserAsync` (NTR-133) |
> | ✅ | L'infrastructure Hangfire qui le fait tourner (NTR-55) |
> | ✅ | Test d'intégration niveau 3 — purge déclenchée manuellement contre un vrai Keycloak et une vraie base (NTR-28, IT-EXT-08) |
> | ⚠️ | Le test a révélé que la purge **ne pouvait fonctionner nulle part** : le client de service `nutrition-api-service` n'existait pas dans le realm, et `AdminBaseUrl`, `Realm` et `ServiceClientSecret` étaient vides dans les trois fichiers de configuration. Corrigé pour le développement le 2026-07-30 — **reste à vérifier que la production injecte bien ces valeurs** |
> | ❌ | `RgpdService` n'appelle toujours pas `DisableUserAsync` à la demande de suppression : le compte reste actif dans Keycloak pendant la grace period |

## L'ordre des suppressions — Keycloak d'abord

C'est l'inverse de ce que prévoyait la spécification initiale, et la raison tient à l'idempotence du
job.

| Scénario | Avec Keycloak d'abord | Avec PostgreSQL d'abord |
|---|---|---|
| Keycloak indisponible | Rien n'est supprimé, le compte reste sélectionnable au prochain passage | Les données sont parties, le compte n'est plus sélectionné → **compte Keycloak orphelin définitif** |
| Keycloak passe, PostgreSQL échoue | Au passage suivant, `DeleteUserAsync` renvoie 404 (ignoré), puis la base est purgée | — |

Un compte orphelin dans Keycloak est une violation persistante du droit à l'effacement : c'est le
seul état dont le job ne peut pas se relever seul. L'ordre retenu rend chaque tentative rejouable.

## La cascade PostgreSQL

Le job n'écrit **aucune suppression table par table**. Toutes les clés étrangères qui pointent vers
`users` sont déclarées `ON DELETE CASCADE` dès la migration initiale :

```
users ←cascade─ meals ←cascade─ meal_items
      ←cascade─ weight_entries
      ←cascade─ saved_food_items
      ←cascade─ diet_plans
      ←cascade─ diets
```

Un unique `DELETE` sur `users` suffit donc, et l'ordre est garanti par la base. Réécrire la cascade
dans le job aurait créé un second endroit où maintenir cet ordre le jour où une table s'ajoute.

## Ce qu'elle ne fait pas

- Ne supprime jamais un compte avant l'expiration des 30 jours de grace period
- Ne conserve aucun backup individuel — après purge, les données sont irrécupérables
- N'envoie pas de notification — la communication a lieu au moment de la demande (fiche droits utilisateur)

## Déclenchement

| Élément | Valeur |
|---|---|
| Planificateur | Hangfire (`RecurringJob`) |
| Identifiant | `rgpd-purge` — constante `IJobMonitoringService.RgpdPurgeJobName` |
| Fréquence | `30 3 * * *` — chaque nuit à 03h30 UTC, 30 min après l'import Open Food Facts |
| Échec | Un compte en échec fait échouer le job entier, ce qui déclenche le retry Hangfire. Les comptes déjà purgés ne sont pas repris — ils ne sont plus sélectionnés. |
| Historique | Tables Hangfire — lues par `GET /admin/system/health` |

## Dépendances

- Hangfire — planification et historique d'exécution ([Hangfire — moteur de jobs récurrents](../../briques/hangfire.md))
- Keycloak Admin API — suppression définitive du compte ([Keycloak Admin API — Connexion et opérations](../../briques/keycloak-admin.md))
- PostgreSQL — suppression cascade des données de l'utilisateur
- [RGPD — Droits de l'utilisateur](index.md) — l'amont : c'est la demande de suppression qui met le compte en grace period
