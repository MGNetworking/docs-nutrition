# Cache des recherches d'aliments

**Ajouté le :** 2026-07-23
**Type :** Interne
**Référence spec :** `docs/pages/backend/annexes/workflow-cache-recherche-aliments.md` (fonctionnement de bout en bout)

> Fonctionnalité de fonctionnement applicatif : elle accélère la recherche d'aliments
> (`features/utilisateur/aliments.md`) sans jamais être visible par l'utilisateur.

---

## Objectif

Éviter de refaire la même requête SQL à chaque fois qu'un mot-clé déjà cherché revient. Les
recherches d'aliments sont massivement répétitives (« poulet », « riz », « pain »…) et portent
sur un catalogue partagé, identique pour tous les utilisateurs — le résultat est donc
mutualisable entre eux.

## Qui l'utilise

Aucun acteur humain directement. Le cache est interrogé par `FoodItemService` à chaque
recherche ; l'utilisateur ne perçoit qu'un temps de réponse plus court.

## Quand

À chaque appel de recherche d'aliments. Les entrées expirent d'elles-mêmes au bout de 24 heures
(durée configurable).

## Ce qu'elle fait

- Interroge Redis avant PostgreSQL (stratégie *cache-first*)
- En l'absence d'entrée, interroge PostgreSQL puis met le résultat en cache
- Normalise les mots-clés (minuscules, espaces de bord retirés) pour que « Poulet » et
  « poulet » partagent la même entrée
- Expire automatiquement les entrées après 24 h — aucune purge périodique nécessaire
- **Se replie sur PostgreSQL si Redis est indisponible** : la recherche continue de répondre,
  la dégradation est journalisée en avertissement

## Ce qu'elle ne fait pas

- Ne met jamais en cache de données propres à un utilisateur — le catalogue est partagé
- Ne conserve rien au-delà de 24 h, ni entre deux imports : le job d'import vide le cache dès
  qu'il a modifié le catalogue

## Limite connue

⚠️ **Une panne de Redis ralentit les recherches sans les interrompre.** Le repli est immédiat
côté résultat, mais chaque requête tente d'abord de joindre Redis et attend l'expiration du délai
avant de basculer sur la base. Si la panne dure, cette attente s'ajoute à chaque appel. Un
disjoncteur (*circuit breaker*) supprimerait ce coût ; il a été écarté tant qu'aucune panne
durable n'est constatée — voir le workflow, §4.

## Dépendances

- Redis — stockage des entrées de cache. La brique elle-même (client, configuration par
  environnement, débogage) est décrite dans `annexes/infrastructure-redis.md`
- PostgreSQL — source de vérité du catalogue `FoodItem`
- `features/utilisateur/aliments.md` — la fonctionnalité utilisateur accélérée par ce cache
- `features/interne/mise-a-disposition-aliments.md` — le job qui met à jour le catalogue mis en cache
