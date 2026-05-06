# Profil utilisateur

**Ajouté le :** 2026-05-02
**Référence spec :** `docs/pages/backend/annexes/workflow_creation-profil-utilisateur.mermaid` · `workflow_mise-a-jour-profil.mermaid`

---

## Objectif

Permettre à l'utilisateur de créer et maintenir son profil physiologique — données nécessaires au calcul de ses besoins nutritionnels (BMR / TDEE).

## Qui l'utilise

Tous les utilisateurs (Free, Pro, Business).

## Quand

- À la première connexion : création obligatoire avant tout usage de l'app
- À tout moment : mise à jour des données personnelles

## Ce qu'elle fait

- Crée le profil utilisateur depuis les données Keycloak (`sub` → `KeycloakId`)
- Stocke les données physiologiques : date de naissance, sexe, taille, niveau d'activité
- Enregistre les allergènes et préférences alimentaires (choix explicite obligatoire)
- Calcule BMR et TDEE à la demande (formule Mifflin-St Jeor) — non persistés
- Met à jour les champs modifiables du profil

## Ce qu'elle ne fait pas

- Ne stocke pas le poids sur le profil — géré via `WeightEntry` (voir `suivi-poids.md`)
- Ne calcule pas le `CalorieTarget` — calculé au lancement d'un régime (voir `diet.md`)

## Endpoints

| Méthode | Endpoint | Description |
|---|---|---|
| `POST` | `/users/me` | Créer le profil (première connexion) |
| `GET` | `/users/me` | Lire le profil + BMR/TDEE calculés |
| `PUT` | `/users/me` | Mettre à jour le profil |

## Dépendances

- Keycloak (extraction `sub` → `KeycloakId`)
- `WeightEntry` — poids géré séparément
