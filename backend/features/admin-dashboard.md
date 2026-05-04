# Back-office Admin

**Ajouté le :** 2026-05-02
**Référence spec :** `docs/backend/8.nutrition-admin.md`

---

## Objectif

Fournir à l'administrateur une vue d'ensemble de l'activité globale de l'application et la capacité de gérer le contenu partagé accessible à tous les utilisateurs.

## Qui l'utilise

Administrateur uniquement — rôle `admin` Keycloak requis.

## Quand

- Surveillance quotidienne : vérifier la santé des jobs et l'activité des utilisateurs
- Gestion du contenu : créer et maintenir les templates partagés

## Ce qu'elle fait

- Affiche les KPIs consolidés : total utilisateurs, répartition par tier, nouveaux inscrits
- Affiche les métriques d'activité : diets actives, repas enregistrés, comptes en grace period
- Affiche la santé des jobs planifiés : statut et date du dernier import OFF et de la dernière purge RGPD
- Crée, modifie et supprime les DietPlan templates partagés

## Ce qu'elle ne fait pas

- N'expose jamais les données personnelles d'un utilisateur individuel (RGPD)
- Ne permet pas de modifier le tier d'un utilisateur (v2)
- Ne permet pas de rechercher un utilisateur par nom ou email

## Endpoints

| Méthode | Endpoint | Description |
|---|---|---|
| `GET` | `/admin/dashboard` | KPIs consolidés |
| `GET` | `/admin/system/health` | Santé des jobs planifiés |
| `GET` | `/admin/diet-plans/templates` | Lister les templates |
| `POST` | `/admin/diet-plans/templates` | Créer un template |
| `PUT` | `/admin/diet-plans/templates/{id}` | Modifier un template |
| `DELETE` | `/admin/diet-plans/templates/{id}` | Supprimer un template |

## Dépendances

- Keycloak — rôle `admin` (claim `realm_access.roles`)
- Hangfire — source des données de santé des jobs (`lastRunAt`, `status`)
- PostgreSQL — source des agrégats utilisateurs et activité
