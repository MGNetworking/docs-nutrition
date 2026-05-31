# Plans alimentaires (DietPlan)

**Ajouté le :** 2026-05-02
**Référence spec :** `docs/pages/backend/annexes/workflow_gestion-dietplan-et-lancement.mermaid` · `docs/pages/backend/design/design-domain.md#dietplan`

---

## Objectif

Permettre à l'utilisateur de créer des plans alimentaires réutilisables (type de régime, objectif, répartition des macros) qu'il peut lancer pour démarrer un régime. Fournir également des templates partagés créés par l'admin comme point de départ.

## Qui l'utilise

- Plans personnels : tous les utilisateurs (limités selon tier)
- Templates partagés : Pro et Business uniquement (lecture seule)
- Admin : création et gestion des templates

## Quand

- Avant de lancer un régime : l'utilisateur crée ou choisit un plan
- À tout moment : un plan personnel est toujours modifiable
- Un plan peut être relancé plusieurs fois

## Ce qu'elle fait

- Crée un plan personnel (DietType, Goal, TargetWeight, MacroDistribution)
- Modifie et supprime un plan personnel
- Liste les plans personnels de l'utilisateur
- Donne accès aux templates partagés (Pro/Business)
- Vérifie la limite de plans selon le tier avant création

## Ce qu'elle ne fait pas

- Ne stocke pas de `CalorieTarget` — calculé uniquement au lancement d'un régime
- Ne lie pas le plan aux régimes déjà créés depuis lui — snapshot indépendant
- Ne permet pas aux utilisateurs de modifier les templates

## Endpoints

| Méthode | Endpoint | Accès |
|---|---|---|
| `POST` | `/diet-plans` | Tous (limité par tier) |
| `GET` | `/diet-plans` | Tous |
| `PUT` | `/diet-plans/{id}` | Tous (plan personnel uniquement) |
| `DELETE` | `/diet-plans/{id}` | Tous (plan personnel uniquement) |
| `POST` | `/diet-plans/{id}/launch` | Tous |
| `GET` | `/diet-plans/templates` | Pro + Business |
| `POST` | `/admin/diet-plans/templates` | Admin |
| `PUT` | `/admin/diet-plans/templates/{id}` | Admin |
| `DELETE` | `/admin/diet-plans/templates/{id}` | Admin |

## Dépendances

- `Abonnements` — limite de plans selon tier, accès templates
- `Diet` — un DietPlan est le point de départ d'un régime
- `Authentification` — rôle `admin` pour les endpoints de gestion templates
