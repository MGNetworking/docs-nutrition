# Le Moteur (Engine) en architecture logicielle

**Type de document :** Concept architectural — référence et révision  
**Exemple fil conducteur :** `NutritionCalculator` — Moteur de calcul nutritionnel

---

## 1. Définition

Un **moteur** est un composant logiciel **auto-contenu**, **configurable** et **composé de plusieurs classes collaborantes** qui réalisent ensemble un traitement spécialisé et complexe.

Il n'est pas un terme officiel du GoF (Gang of Four) ni un pattern de conception au sens strict — c'est un **terme architectural** qui désigne un rôle dans le système. On dit qu'un ensemble de classes forme un moteur quand il réunit les trois caractéristiques suivantes.

---

## 2. Les trois caractéristiques d'un moteur

### 2.1 Auto-contenu

Le moteur ne dépend d'aucun système externe : pas de base de données, pas de services réseau, pas d'état partagé. Il reçoit des données en entrée, produit un résultat en sortie, et ne provoque aucun effet de bord.

```
Entrée → [ Moteur ] → Sortie
```

C'est ce qu'on appelle une **fonction pure à l'échelle composant** : pour les mêmes entrées, le moteur produira toujours les mêmes sorties.

**Exemple :**
```csharp
// NutritionCalculator ne touche ni base de données ni réseau.
// Il reçoit des données, il calcule, il retourne.
var needs = calculator.Calculate(user, weightKg, goal, macros);
```

---

### 2.2 Configurable

Le moteur peut adapter son comportement sans que son code interne ne change. Cette configuration passe généralement par une **stratégie** (pattern Strategy) ou un **paramètre de construction**.

C'est la différence clé avec un simple Calculator : un Calculator fait toujours la même chose de la même façon. Un moteur peut faire la même chose de **plusieurs façons différentes selon le contexte**.

**Exemple :**
```csharp
// Même moteur, comportement différent selon la formule choisie.
var calculatorMifflin  = NutritionCalculatorFactory.Create(BmrFormula.MifflinStJeor);
var calculatorHarris   = NutritionCalculatorFactory.Create(BmrFormula.HarrisBenedict);
```

---

### 2.3 Pluriel — plusieurs classes qui collaborent

Un moteur n'est pas une seule classe. C'est un **ensemble cohérent** de classes qui jouent chacune un rôle précis. La complexité est distribuée entre elles, pas concentrée dans une seule.

**Exemple — les classes du Moteur de calcul nutritionnel :**

| Classe | Rôle dans le moteur |
|---|---|
| `IBmrStrategy` | Contrat de la règle de calcul interchangeable |
| `MifflinStJeorStrategy` | Implémentation Mifflin-St Jeor |
| `HarrisBenedictStrategy` | Implémentation Harris-Benedict |
| `NutritionCalculator` | Orchestre les calculs (TDEE, CalorieTarget, macros) |
| `NutritionCalculatorFactory` | Instancie le moteur configuré |

Chaque classe a **une seule responsabilité** (principe SRP). Ensemble, elles forment un tout cohérent.

---

## 3. Comparaison avec les autres termes

C'est souvent là que la confusion naît. Voici comment distinguer un moteur d'un service, d'un calculator ou d'un helper.

| Terme | Dépendances externes | Configurable | Pluriel | Exemple |
|---|---|---|---|---|
| **Moteur (Engine)** | Non | Oui | Oui | `NutritionCalculator` + Factory + Strategies |
| **Service applicatif** | Oui (repositories, autres services) | Non | Non (une classe) | `DietPlansService` |
| **Calculator** | Non | Non | Non (une classe) | `TaxCalculator.Compute(price)` |
| **Helper / Util** | Non | Non | Non (méthodes statiques isolées) | `DateHelper.ComputeAge()` |
| **Processor** | Parfois | Parfois | Parfois | `CsvProcessor`, `ImageProcessor` |

### La distinction clé avec un Service applicatif

Un **Service applicatif** orchestre : il appelle des repositories, déclenche des events, coordonne plusieurs entités. Il **dépend** d'infrastructure.

Un **Moteur** calcule : il ne sait pas qu'une base de données existe. Il ne sait pas qu'il est dans une API. Il transforme des données.

```csharp
// Service applicatif — orchestre, dépend de repositories
public class DietPlansService
{
    private readonly IDietPlanRepository _dietPlanRepository; // dépendance externe
    private readonly IUserRepository _userRepository;         // dépendance externe

    public async Task<DietResponse> LaunchAsync(Guid userId, Guid planId)
    {
        // ... récupération en base, vérifications, persistance ...
        var calculator = NutritionCalculatorFactory.Create(); // <-- appel du moteur
        var needs = calculator.Calculate(user, weight, goal, macros);
        // ...
    }
}

// Moteur — calcule, ne dépend de rien d'externe
public sealed class NutritionCalculator
{
    public NutritionNeeds Calculate(User user, float weightKg, Goal goal, MacroDistribution macros)
    {
        // Calcul pur — BMR, TDEE, CalorieTarget
    }
}
```

---

## 4. Les patterns de conception dans un moteur

Un moteur s'appuie typiquement sur deux patterns du GoF.

### 4.1 Strategy — rendre le comportement interchangeable

Le pattern **Strategy** définit une famille d'algorithmes, les encapsule chacun dans une classe, et les rend interchangeables. C'est ce qui rend le moteur **configurable**.

```
IBmrStrategy
    ├── MifflinStJeorStrategy   → formule prioritaire
    └── HarrisBenedictStrategy  → formule alternative
```

Sans Strategy, `NutritionCalculator` aurait un `if (formula == MifflinStJeor) { ... } else { ... }` en dur — non extensible, difficile à tester.

Avec Strategy, ajouter une troisième formule BMR demain (ex. Katch-McArdle) revient à créer une nouvelle classe sans toucher au moteur.

### 4.2 Factory — contrôler la construction

Le pattern **Factory** centralise la création d'objets complexes. Il **cache les détails d'instanciation** à l'appelant et garantit que le moteur est toujours dans un état valide.

```csharp
// Sans factory — l'appelant doit connaître les détails internes
var strategy = new MifflinStJeorStrategy();
var calculator = new NutritionCalculator(strategy); // constructeur internal exposé

// Avec factory — l'appelant ne voit qu'une intention
var calculator = NutritionCalculatorFactory.Create(BmrFormula.MifflinStJeor);
```

Le constructeur de `NutritionCalculator` est marqué `internal` : il ne peut être appelé que depuis le même assembly, forçant l'usage du factory. C'est un **garde-fou architectural**.

---

## 5. Quand créer un moteur ?

Trois signaux indiquent qu'un moteur est la bonne solution :

**Signal 1 — La logique est complexe et réutilisée par plusieurs services**

Si `DietPlansService` et `UserService` ont tous les deux besoin de calculer des besoins caloriques, mettre ce calcul dans les deux services crée de la duplication. Un moteur centralise.

**Signal 2 — Il existe plusieurs variantes d'un même algorithme**

Dès qu'on a "formule A ou formule B selon le contexte", Strategy + Factory = moteur. Sans ça, on accumule des `if`/`switch` qui grossissent à chaque nouvelle variante.

**Signal 3 — Le calcul ne doit pas dépendre de l'infrastructure**

Si la logique n'a pas besoin de base de données, elle ne doit pas être dans un service qui en dépend. Le moteur isole le calcul pur.

---

## 6. Où placer un moteur dans l'architecture DDD 4 couches ?

```
Domain          → Entités, Value Objects, Enums (NutritionNeeds, MacroGrams, BmrFormula)
Application     → Moteur (NutritionCalculator, Factory, Strategies) + Services applicatifs
Infrastructure  → Base de données, Redis, Hangfire
API             → Controllers, Middleware
```

Le moteur vit dans la couche **Application** parce que :
- Il utilise des entités et value objects du **Domain**
- Il est appelé par les **Services applicatifs**
- Il n'a pas besoin de l'**Infrastructure**

Il est organisé dans un sous-dossier dédié (`Services/Nutrition/`) pour signaler visuellement qu'il forme un tout cohérent, distinct des services applicatifs.

---

## 7. Structure type d'un moteur

```
Services/
└── Nutrition/                        ← dossier = frontière du moteur
    ├── IBmrStrategy.cs               ← contrat Strategy
    ├── MifflinStJeorStrategy.cs      ← implémentation 1
    ├── HarrisBenedictStrategy.cs     ← implémentation 2
    ├── NutritionCalculator.cs        ← cœur du moteur
    └── NutritionCalculatorFactory.cs ← point d'entrée unique
```

**Règle :** un appelant extérieur ne devrait interagir qu'avec le **Factory** et le **moteur principal**. Les stratégies sont des détails d'implémentation.

---

## 8. Ce qu'un moteur ne fait pas

- Il ne persiste rien en base de données
- Il ne lance pas d'events de domaine
- Il ne connaît pas les repositories
- Il ne fait pas de validation métier au sens "est-ce que cet utilisateur a le droit de faire ça" — c'est le rôle du service applicatif

Ces responsabilités appartiennent aux services applicatifs et à l'infrastructure. Le moteur calcule, point.

---

## Résumé en une phrase

> Un **moteur** est un composant auto-contenu, configurable via Strategy, instancié via Factory, qui encapsule une logique complexe réutilisable sans aucune dépendance externe.
