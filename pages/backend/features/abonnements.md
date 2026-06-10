# Abonnements & tiers

**Ajouté le :** 2026-05-02
**Référence spec :** `docs/pages/backend/6.nutrition-abonnements.md`

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

- Ne gère pas le paiement — délégué à Stripe (voir `annexes/infrastructure-stripe.md`)
- Ne stocke jamais le tier dans le JWT — `User.SubscriptionTier` en DB est la seule source de vérité

## Intégration Stripe

La synchronisation entre Stripe et la DB se fait via webhook. Stripe envoie les événements de facturation à l'API qui met à jour `User.SubscriptionTier` en temps réel.

Deux champs de liaison sur `User` :

| Champ | Type | Rôle |
|---|---|---|
| `StripeCustomerId` | `string?` | Retrouver le User depuis un événement Stripe |
| `StripeSubscriptionId` | `string?` | Identifier l'abonnement actif |

**Détail complet :** `docs/pages/backend/annexes/infrastructure-stripe.md`

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
- `IStripeWebhookService` (couche Application) — mise à jour du tier sur événement Stripe
- Toutes les fonctionnalités avec limites (DietPlan, Repas, Aliments, Bilan)
- `annexes/infrastructure-stripe.md` — workflow webhook, configuration, événements
