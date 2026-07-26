# Catalogue des systèmes — API Nutrition

> Une porte d'entrée par système. Chaque dossier contient **tout ce qui appartient à ce système**
> et rien d'autre : le besoin, le fonctionnement, et les documents qui ne servent qu'à lui.
>
> Les technologies tierces (Redis, Hangfire, Keycloak, Stripe…) vivent à part, dans `briques/` :
> elles sont partagées et ne dépendent d'aucun système en particulier.

---

## Les systèmes

| Système | Ce que le dossier contient en plus |
|---|---|
| [Authentification](authentification/index.md) | — |
| [Profil utilisateur](profil-utilisateur/index.md) | — |
| [Plans alimentaires (DietPlan)](diet-plan/index.md) | — |
| [Régimes (Diet)](diet/index.md) | — |
| [Repas](repas/index.md) | — |
| [Suivi du poids](suivi-poids/index.md) | — |
| [Aliments](aliments/index.md) | [cache des recherches](aliments/cache-recherche.md) et [son workflow](aliments/workflow-cache-recherche.md), [mise à disposition du catalogue](aliments/mise-a-disposition.md) et [son workflow](aliments/workflow-import.md), [source Open Food Facts](aliments/source-open-food-facts.md) |
| [Bilan nutritionnel](bilan-nutritionnel/index.md) | [moteur de calcul](bilan-nutritionnel/moteur-de-calcul.md) |
| [Abonnements & tiers](abonnements/index.md) | — |
| [RGPD — Droits de l'utilisateur](rgpd/index.md) | [purge des comptes](rgpd/purge-des-comptes.md) |
| [Back-office Admin](administration/index.md) | — |
| [OpenAPI / Swagger UI](plateforme/openapi.md) | [Exception Filter](plateforme/exception-filter.md) — le comportement transverse de l'API |

---

## Utilisateur ou interne ?

La distinction existe toujours, mais **elle ne classe plus les dossiers** : une fiche destinée à
l'utilisateur et une fiche interne du même système vivent côte à côte. Le lecteur qui veut
comprendre les aliments trouve tout au même endroit, au lieu de naviguer entre trois dossiers.

La nature d'une fiche se lit dans son en-tête `**Type :** Utilisateur | Interne`.

| Type | Ce que c'est |
|---|---|
| **Utilisateur** | un écran ou une action déclenchée par l'utilisateur final |
| **Interne** | fonctionnement applicatif — jobs, filtres, moteur, outillage |

---

## Ailleurs

| Sujet | Où |
|---|---|
| Les technologies tierces | [Redis](../briques/redis.md) et les autres pages de `briques/` |
| La démarche de test | [Niveaux de tests — définitions et périmètres](../qualite/niveaux-de-tests.md) |
| Les vues transverses (diagramme de classes, flux métier) | [Diagramme de classes — API Nutrition](../reference/diagramme-classes.md) |

---

## Convention d'ajout

1. **Est-ce une technologie tierce ?** → `briques/`, même si un seul système la consomme.
2. **Sinon** → dans le dossier de son système ; `reference/` si plusieurs systèmes la partagent.
3. Renseigner l'en-tête `**Type :** Utilisateur` ou `**Type :** Interne`.
4. **Une fiche = un seul type.** Si une notion mêle les deux natures (droit utilisateur *et*
   traitement automatique), la scinder — voir RGPD (droits / purge).
5. Ajouter la page à la `nav:` de `mkdocs.yml`, sinon elle n'est pas publiée.
6. Un nouveau système = une ligne dans le tableau ci-dessus.

La règle complète : `.claude/rules/documentation-projet.md` du dépôt `nutrition-api`.
