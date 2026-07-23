# RGPD — Purge des comptes

**Ajouté le :** 2026-05-02
**Type :** Interne
**Référence spec :** `docs/pages/backend/annexes/workflow_rgpd.mermaid` · `docs/pages/backend/annexes/infrastructure-keycloak-admin.md`

> Les droits exercés par l'utilisateur (export, demande de suppression, réactivation) sont une fonctionnalité distincte — voir `features/utilisateur/rgpd-droits-utilisateur.md`.

---

## Objectif

Supprimer définitivement les comptes dont la demande de suppression dépasse la grace period de 30 jours, afin d'honorer le droit à l'effacement (Art. 17) sans intervention humaine.

## Qui l'utilise

Aucun acteur humain — job de fond déclenché par le planificateur (Hangfire).

## Quand

- Quotidien, chaque nuit (job Infrastructure nocturne)
- Cible les comptes en grace period depuis plus de 30 jours (`User.DeletedAt` > 30 jours)

## Ce qu'elle fait

- Sélectionne les comptes dont la grace period est expirée
- Supprime les données en cascade dans PostgreSQL
- Supprime définitivement le compte correspondant dans Keycloak
- Enregistre l'exécution dans l'historique Hangfire (visible depuis le back-office admin)

## Ce qu'elle ne fait pas

- Ne supprime jamais un compte avant l'expiration des 30 jours de grace period
- Ne conserve aucun backup individuel — après purge, les données sont irrécupérables
- N'envoie pas de notification — la communication a lieu au moment de la demande (fiche droits utilisateur)

## Déclenchement

| Élément | Valeur |
|---|---|
| Planificateur | Hangfire (`RecurringJob`) |
| Fréquence | Quotidienne, nuit (`rgpd-purge`) |
| Historique | Tables Hangfire — lues par `GET /admin/system/health` |

## Dépendances

- Hangfire — planification et historique d'exécution (`annexes/infrastructure-hangfire.md`)
- Keycloak Admin API — suppression définitive du compte (`annexes/infrastructure-keycloak-admin.md`)
- PostgreSQL — suppression cascade des données de l'utilisateur
- `features/utilisateur/rgpd-droits-utilisateur.md` — l'amont : c'est la demande de suppression qui met le compte en grace period
