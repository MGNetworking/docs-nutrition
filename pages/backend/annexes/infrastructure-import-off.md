# Infrastructure — Import Open Food Facts

> Ce document décrit le mécanisme d'alimentation de la table `FoodItem` depuis Open Food Facts.
> C'est une responsabilité de la **couche Infrastructure** — indépendante des actions utilisateur.

---

## Contexte

Open Food Facts est une base de données alimentaire open-source (licence ODbL) contenant 3M+ produits.
Ils publient des exports complets de leur base (dump) mis à jour quotidiennement, téléchargeables librement.

**Pourquoi un import de dump et non des appels API à la demande ?**

| Approche | Problème |
|---|---|
| Appel API OFF à chaque recherche utilisateur | Dépendance forte à un service externe, latence, risque de blocage |
| Appel API OFF automatisé en masse | Usage abusif de leur API — contre leurs conditions d'utilisation |
| **Import du dump officiel** | Légal, complet, indépendant des utilisateurs, recommandé par OFF |

---

## Mécanisme

### Job planifié (couche Infrastructure)

Un job de fond s'exécute quotidiennement pour maintenir la table `FoodItem` à jour :

1. Téléchargement du dump OFF (format JSONL ou CSV)
2. Pour chaque produit du dump :
   - Si `OffId` absent en base → `INSERT FoodItem`
   - Si `OffId` présent en base → `UPDATE FoodItem` (valeurs nutritionnelles, allergènes)
3. Mise à jour du champ `CachedAt` à la date d'import

### Fréquence

| Fréquence | Justification |
|---|---|
| **Quotidienne** | OFF met à jour son dump chaque jour — synchronisation au plus proche |

### Données importées

| Champ OFF | Champ FoodItem |
|---|---|
| `code` (code-barres) | `OffId` |
| `product_name` | `Name` |
| `energy-kcal_100g` | `CaloriesPer100g` |
| `proteins_100g` | `ProteinsPer100g` |
| `carbohydrates_100g` | `CarbsPer100g` |
| `fat_100g` | `FatsPer100g` |
| `allergens_tags` | `AllergensTags` |

### Produits introuvables lors d'une recherche

Si un utilisateur cherche un produit absent de la base locale, le système retourne une liste vide.
Le produit sera disponible après le prochain import quotidien.

> Les produits ajoutés à OFF dans les dernières 24h ne sont pas disponibles immédiatement — cas marginal, accepté.

---

## Impact sur l'architecture de recherche

La recherche utilisateur n'appelle **jamais** l'API OFF directement. Elle opère sur 2 niveaux :

```text
Recherche utilisateur
├── Niveau 1 — Cache Redis   → réponse immédiate si mot-clé récent
└── Niveau 2 — PostgreSQL    → lecture FoodItem + alimentation cache
    └── Introuvable           → liste vide (pas d'appel OFF)

Job Infrastructure (indépendant)
└── Import dump OFF quotidien → alimente PostgreSQL FoodItem
```

---

## Considérations techniques (à préciser lors de l'implémentation)

- **Taille du dump** : plusieurs centaines de Mo — prévoir un traitement par batch
- **Première installation** : import initial complet avant la mise en production
- **Outil** : Hangfire ou un IHostedService ASP.NET Core pour le job planifié
- **Licence** : données sous ODbL — mention obligatoire dans les CGU de l'application
