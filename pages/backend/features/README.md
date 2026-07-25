# Catalogue des fonctionnalités — API Nutrition

> Une fiche par fonctionnalité — objectif, acteurs, endpoints, dépendances.
> Centralisé ici pour tous les modules (backend, frontend, SDK...).
> Mis à jour à chaque ajout de fonctionnalité.

Les fonctionnalités sont réparties en deux familles :

- **Utilisateur** (`utilisateur/`) — un écran ou une action déclenchée par l'utilisateur final.
- **Interne** (`interne/`) — fonctionnement applicatif : jobs, filtres, moteur, outillage. L'utilisateur final n'y accède pas directement.

---

## Utilisateur

| Fonctionnalité | Fichier | Ajouté le |
|---|---|---|
| Authentification | [utilisateur/authentification.md](utilisateur/authentification.md) | 2026-05-02 |
| Profil utilisateur | [utilisateur/profil-utilisateur.md](utilisateur/profil-utilisateur.md) | 2026-05-02 |
| Suivi du poids | [utilisateur/suivi-poids.md](utilisateur/suivi-poids.md) | 2026-05-02 |
| Plans alimentaires (DietPlan) | [utilisateur/diet-plan.md](utilisateur/diet-plan.md) | 2026-05-02 |
| Régimes (Diet) | [utilisateur/diet.md](utilisateur/diet.md) | 2026-05-02 |
| Bilan nutritionnel | [utilisateur/bilan-nutritionnel.md](utilisateur/bilan-nutritionnel.md) | 2026-05-02 |
| Repas | [utilisateur/repas.md](utilisateur/repas.md) | 2026-05-02 |
| Aliments | [utilisateur/aliments.md](utilisateur/aliments.md) | 2026-05-02 |
| Abonnements & tiers | [utilisateur/abonnements.md](utilisateur/abonnements.md) | 2026-05-02 |
| RGPD — Droits de l'utilisateur | [utilisateur/rgpd-droits-utilisateur.md](utilisateur/rgpd-droits-utilisateur.md) | 2026-05-02 |

## Interne

| Fonctionnalité | Fichier | Ajouté le |
|---|---|---|
| Back-office admin | [interne/admin-dashboard.md](interne/admin-dashboard.md) | 2026-05-02 |
| RGPD — Purge des comptes | [interne/rgpd-purge-comptes.md](interne/rgpd-purge-comptes.md) | 2026-05-02 |
| OpenAPI / Swagger UI | [interne/openapi.md](interne/openapi.md) | 2026-05-02 |
| Exception Filter (Middleware) | [interne/exception-filter.md](interne/exception-filter.md) | 2026-05-25 |
| Moteur de calcul nutritionnel | [interne/nutrition-calculator.md](interne/nutrition-calculator.md) | 2026-06-12 |
| Niveaux de tests — définitions et périmètres | [interne/niveaux-de-tests.md](interne/niveaux-de-tests.md) | 2026-05-02 |
| Recensement des tests | [interne/recensement-des-tests.md](interne/recensement-des-tests.md) | 2026-07-23 |
| Mise à disposition des aliments | [interne/mise-a-disposition-aliments.md](interne/mise-a-disposition-aliments.md) | 2026-07-23 |
| Cache des recherches d'aliments | [interne/recherche-aliments-cache.md](interne/recherche-aliments-cache.md) | 2026-07-23 |

---

## Convention d'ajout

Toute nouvelle fonctionnalité → un nouveau fichier + une ligne dans le tableau correspondant.

1. **Choisir la famille** : l'utilisateur final déclenche-t-il la fonctionnalité directement ? Oui → `utilisateur/`. Non (job, filtre, moteur, outillage) → `interne/`.
2. **Placer la fiche** dans le sous-dossier correspondant.
3. **Renseigner l'en-tête** `**Type :** Utilisateur` ou `**Type :** Interne`.
4. **Une fiche = un seul type.** Si une notion mêle les deux natures (droit utilisateur + traitement automatique, par ex.), la scinder en deux fiches distinctes — voir RGPD (droits / purge).
5. Format du corps : voir n'importe quel fichier existant.
