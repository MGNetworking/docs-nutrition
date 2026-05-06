# Suivi du poids

**Ajouté le :** 2026-05-02
**Référence spec :** `docs/pages/backend/annexes/workflow_gestion-poids.mermaid`

---

## Objectif

Permettre à l'utilisateur d'enregistrer son poids au fil du temps et de suivre sa progression pondérale.

## Qui l'utilise

Tous les utilisateurs (Free, Pro, Business).
Historique affiché selon le tier : Free = 30 derniers jours · Pro = 1 an · Business = illimité.

## Quand

- À chaque pesée (quotidien ou ponctuel)
- Peut être renseigné rétroactivement (date passée)

## Ce qu'elle fait

- Enregistre une pesée avec sa date (`MeasuredAt` = aujourd'hui par défaut, modifiable)
- Interdit deux pesées à la même date pour un même utilisateur (409)
- Permet la modification d'une pesée existante
- Fournit le poids de référence au lancement d'un régime (dernier `WeightEntry`)

## Ce qu'elle ne fait pas

- Ne calcule pas l'IMC — non prévu en v1
- Sans WeightEntry, le lancement d'un régime est impossible (422)

## Endpoints

| Méthode | Endpoint | Description |
|---|---|---|
| `POST` | `/users/me/weight-entries` | Ajouter une pesée |
| `GET` | `/users/me/weight-entries` | Historique des pesées (filtré par tier) |
| `PUT` | `/users/me/weight-entries/{id}` | Modifier une pesée existante |

## Dépendances

- `Profil utilisateur` — `UserId` requis
- `Diet` — consomme le dernier `WeightEntry` au lancement
- `Abonnements` — durée d'historique limitée selon tier
