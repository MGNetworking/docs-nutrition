# Régimes (Diet)

**Ajouté le :** 2026-05-02
**Référence spec :** `docs/pages/backend/annexes/workflow_gestion-dietplan-et-lancement.mermaid` · `workflow_terminer-diet.mermaid` · `docs/pages/backend/domaine/Modele-domaine.md#diet`

---

## Objectif

Gérer le cycle de vie d'un régime actif : lancement depuis un plan, suivi sur la période, archivage. La Diet est le référentiel central pour le calcul nutritionnel de l'utilisateur.

## Qui l'utilise

Tous les utilisateurs (Free, Pro, Business).

## Quand

- Au lancement : l'utilisateur active un DietPlan pour démarrer un régime
- Pendant le régime : consultation de la Diet active
- À la fin : l'utilisateur archive le régime pour en démarrer un nouveau

## Ce qu'elle fait

- Lance un DietPlan → crée une Diet (snapshot complet : attributs copiés + CalorieTarget calculé)
- Calcule le CalorieTarget au lancement (BMR Mifflin-St Jeor + TDEE + Goal + dernier WeightEntry)
- Impose StartDate = date du lancement (non modifiable)
- Bloque le lancement si une Diet est déjà active (409)
- Bloque le lancement si aucun WeightEntry n'existe (422)
- Archive un régime actif (EndDate = aujourd'hui, statut = Archived)
- Expose le régime actif et l'historique des régimes

## Ce qu'elle ne fait pas

- Une Diet lancée n'est plus modifiable (sauf EndDate)
- Ne conserve pas de lien avec le DietPlan d'origine après lancement

## Endpoints

| Méthode | Endpoint | Description |
|---|---|---|
| `POST` | `/diet-plans/{id}/launch` | Lancer un plan → créer une Diet active |
| `GET` | `/diets/active` | Récupérer le régime en cours |
| `GET` | `/diets` | Historique des régimes |
| `GET` | `/diets/{id}` | Détail d'un régime |
| `POST` | `/diets/{id}/archive` | Terminer le régime actif |

## Dépendances

- `DietPlan` — source du snapshot
- `Suivi du poids` — dernier WeightEntry requis au lancement
- `Bilan nutritionnel` — agrège les Meals de la période de la Diet
