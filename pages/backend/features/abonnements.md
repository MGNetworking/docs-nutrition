# Abonnements & tiers

**Ajouté le :** 2026-05-02
**Référence spec :** `docs/pages/backend/7.nutrition-abonnements.md`

---

## Objectif

Contrôler l'accès aux fonctionnalités et les limites d'usage selon le tier d'abonnement de l'utilisateur (Free, Pro, Business), afin de monétiser le service SaaS.

## Qui l'utilise

Tous les utilisateurs — le tier est attribué à la création (Free par défaut).

## Quand

Les vérifications de tier s'effectuent automatiquement à chaque opération limitée — transparentes pour l'utilisateur sauf en cas de dépassement (403).

## Ce qu'elle fait

- Stocke le tier sur `User.SubscriptionTier` (source de vérité en base, jamais dans le JWT)
- Bloque la création de plans personnels si la limite tier est atteinte
- Bloque l'accès aux templates partagés pour le tier Free
- Limite la période du bilan nutritionnel selon le tier
- Limite le nombre de repas sauvegardés selon le tier
- Limite le nombre de SavedFoodItems selon le tier
- Retourne 403 avec un message explicite en cas de dépassement

## Ce qu'elle ne fait pas

- Ne gère pas le paiement — hors scope API (Stripe ou autre en externe)
- Ne change pas le tier automatiquement — opération manuelle ou via webhook paiement (v2)

## Limites par tier

| Fonctionnalité | Free | Pro | Business |
|---|---|---|---|
| DietPlans personnels | 2 | 20 | Illimité |
| Templates partagés | ❌ | Lecture | Lecture |
| Historique pesées | 30 jours | 1 an | Illimité |
| Historique diets | 1 | 6 mois | Illimité |
| Bilan nutritionnel | 7 jours | 1 an | Illimité |
| Repas sauvegardés | 5 | 50 | Illimité |
| SavedFoodItems | 10 | 100 | Illimité |

## Dépendances

- `SubscriptionGuard` (couche Application) — helper centralisé pour toutes les vérifications
- Toutes les fonctionnalités avec limites (DietPlan, Repas, Aliments, Bilan)
