# Stripe — Intégration webhooks & abonnements

> Ce document décrit comment Stripe communique avec l'API ASP.NET Core pour synchroniser les changements d'abonnement.
> Référence feature : `docs/pages/backend/features/abonnements.md`

---

## Pourquoi l'API doit parler à Stripe

La gestion du paiement est déléguée à Stripe (Stripe Checkout). L'API n'encaisse jamais directement.

Mais quand un abonnement change dans Stripe (upgrade, downgrade, annulation, échec de paiement), l'API doit en être informée pour mettre à jour `User.SubscriptionTier` en base — source de vérité pour toute la logique métier.

Ce canal de communication est le **webhook Stripe** : Stripe envoie un `POST` sur un endpoint de l'API à chaque événement de facturation.

---

## Vue d'ensemble

```
Frontend              Stripe                 API ASP.NET Core         PostgreSQL
   │                    │                          │                      │
   │──Stripe Checkout───▶│                          │                      │
   │                    │──traitement paiement      │                      │
   │                    │                          │                      │
   │                    │──POST /webhooks/stripe───▶│                      │
   │                    │  Stripe-Signature: xxx    │──vérif signature     │
   │                    │                          │                      │
   │                    │                          │──UPDATE User─────────▶│
   │                    │                          │  SubscriptionTier     │
   │                    │                          │  StripeCustomerId     │
   │                    │◀──────────────────────── 200 OK                 │
   │                    │                          │                      │
   │◀──redirect success─│                          │                      │
```

La prochaine requête de l'utilisateur → `UserResolutionMiddleware` lit le tier mis à jour → `SubscriptionGuard` applique les bonnes limites.

---

## Données partagées entre l'API et Stripe

Deux champs à ajouter sur l'entité `User` :

| Champ | Type | Rôle |
|---|---|---|
| `StripeCustomerId` | `string?` | Clé de liaison — retrouver le `User` depuis un événement Stripe |
| `StripeSubscriptionId` | `string?` | Identifier l'abonnement actif (utile pour les annulations) |

`StripeCustomerId` est créé lors du premier paiement et stocké en PostgreSQL. Tous les événements Stripe contiennent ce `customer_id` — l'API s'en sert pour retrouver le bon `User`.

---

## Événements Stripe à écouter

| Événement | Déclencheur | Action dans la DB |
|---|---|---|
| `checkout.session.completed` | Paiement initial réussi | Stocker `StripeCustomerId` + `StripeSubscriptionId`, mettre à jour `SubscriptionTier` |
| `customer.subscription.updated` | Upgrade / downgrade | Mettre à jour `SubscriptionTier` |
| `customer.subscription.deleted` | Annulation (fin de période) | Repasser en `Free` |
| `invoice.payment_failed` | Échec de paiement | Repasser en `Free` (ou grace period selon politique) |

---

## Configuration côté Stripe

### 1. Créer un webhook dans le dashboard Stripe

Dans `Developers` → `Webhooks` → `Add endpoint` :

| Paramètre | Valeur |
|---|---|
| Endpoint URL | `https://api.example.com/api/v1/webhooks/stripe` |
| Événements | `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed` |

Stripe génère un **Webhook Signing Secret** (`whsec_...`) — à récupérer et stocker dans les secrets de l'API.

### 2. Récupérer les clés

| Clé | Usage |
|---|---|
| `sk_live_...` / `sk_test_...` | Clé secrète Stripe — pour créer des sessions Checkout côté API |
| `whsec_...` | Secret de signature webhook — pour vérifier les événements entrants |

---

## Configuration côté ASP.NET Core

### Variables d'environnement / secrets

```
Stripe__SecretKey=sk_live_...
Stripe__WebhookSecret=whsec_...
```

Ces valeurs ne doivent jamais être dans le code source. En développement : `dotnet user-secrets`. En production : variables d'environnement injectées par Kubernetes (Secret).

### Endpoint webhook — `POST /api/v1/webhooks/stripe`

Cet endpoint est **exclu de l'authentification Keycloak** (`[AllowAnonymous]`) mais sécurisé par la vérification de signature Stripe.

```csharp
[ApiController]
[Route("api/v1/webhooks")]
[AllowAnonymous]
public class StripeWebhookController : ControllerBase
{
    [HttpPost("stripe")]
    public async Task<IActionResult> Handle()
    {
        var json = await new StreamReader(HttpContext.Request.Body).ReadToEndAsync();

        var stripeEvent = EventUtility.ConstructEvent(
            json,
            Request.Headers["Stripe-Signature"],
            _stripeWebhookSecret   // depuis configuration
        );

        return stripeEvent.Type switch
        {
            Events.CheckoutSessionCompleted  => await HandleCheckoutCompleted(stripeEvent),
            Events.CustomerSubscriptionUpdated => await HandleSubscriptionUpdated(stripeEvent),
            Events.CustomerSubscriptionDeleted => await HandleSubscriptionDeleted(stripeEvent),
            Events.InvoicePaymentFailed        => await HandlePaymentFailed(stripeEvent),
            _                                  => Ok()
        };
    }
}
```

### Vérification de signature — obligatoire

`EventUtility.ConstructEvent` (SDK Stripe) vérifie la signature `Stripe-Signature` automatiquement. Si la signature est invalide → exception → 400 Bad Request. **Ne jamais traiter un événement sans vérification.**

### Service dédié — `IStripeWebhookService`

La logique de mise à jour de la DB est isolée dans la couche **Application** :

```csharp
public interface IStripeWebhookService
{
    Task HandleCheckoutCompletedAsync(string stripeCustomerId, string subscriptionId, CancellationToken ct);
    Task HandleSubscriptionUpdatedAsync(string stripeCustomerId, string stripePriceId, CancellationToken ct);
    Task HandleSubscriptionDeletedAsync(string stripeCustomerId, CancellationToken ct);
    Task HandlePaymentFailedAsync(string stripeCustomerId, CancellationToken ct);
}
```

Le controller ne contient aucune logique métier — il délègue à `IStripeWebhookService`.

---

## Correspondance Stripe Price → SubscriptionTier

Stripe identifie les offres par des **Price IDs** (`price_...`). L'API doit faire la correspondance :

| Stripe Price ID | SubscriptionTier |
|---|---|
| `price_xxx_pro_monthly` | `Pro` |
| `price_xxx_pro_annual` | `Pro` |
| `price_xxx_business_monthly` | `Business` |
| `price_xxx_business_annual` | `Business` |

Cette correspondance est stockée dans la configuration (pas en dur dans le code) :

```
Stripe__Prices__Pro=price_xxx_pro_monthly,price_xxx_pro_annual
Stripe__Prices__Business=price_xxx_business_monthly,price_xxx_business_annual
```

---

## Flux complet — Upgrade Free → Pro

```
1. User clique "Passer en Pro" → frontend ouvre Stripe Checkout
2. User saisit sa carte → Stripe traite le paiement
3. Stripe envoie checkout.session.completed → POST /api/v1/webhooks/stripe
4. API vérifie la signature Stripe-Signature
5. API appelle StripeWebhookService.HandleCheckoutCompletedAsync()
   └─ Retrouve le User par StripeCustomerId (ou KeycloakId dans la session)
   └─ Met à jour User.SubscriptionTier = Pro
   └─ Stocke User.StripeCustomerId + User.StripeSubscriptionId
6. API retourne 200 OK à Stripe
7. Prochaine requête de l'user → UserResolutionMiddleware lit Pro → SubscriptionGuard lève les limites
```

---

## Ce que Stripe NE fait PAS

- Il ne modifie pas directement la base de données — seul le webhook handler le fait
- Il ne gère pas la logique métier des limites — c'est `SubscriptionGuard` dans la couche Application
- Il ne connaît pas les entités du domaine (DietPlan, Meal, etc.) — il ne sait que facturer
- Il ne gère pas l'authentification utilisateur — c'est Keycloak

---

*Référence : [Stripe Webhooks](https://stripe.com/docs/webhooks) · [Stripe .NET SDK](https://github.com/stripe/stripe-dotnet)*
