# RGPD

**Ajouté le :** 2026-05-02
**Référence spec :** `docs/backend/annexes/workflow_rgpd.mermaid` · `docs/backend/annexes/infrastructure-keycloak-admin.md`

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

## Dépendances

- Keycloak Admin API — désactivation / réactivation / suppression du compte Keycloak
- `infrastructure-keycloak-admin.md` — mécanisme de connexion service account
- Service email — envoi du lien de réactivation signé
- Job purge RGPD (Hangfire — quotidien)
