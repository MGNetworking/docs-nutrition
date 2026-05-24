# Backlog Jira — Décomposition Epic / Story / Sub-task
# Source : checklist-implementation.md
# Format : jira-scrum.md §Format standard des descriptions

---

## Epic EPIC-001 — Domain Layer

---

### STORY-001 — Aggregate Roots

En tant que développeur, je veux disposer des 5 Aggregate Roots du modèle domaine afin de pouvoir construire les couches Application et Infrastructure sur des concepts métier solides.

Contexte : Les Aggregate Roots encapsulent les données et invariants métier centraux du système. Sans eux, aucune couche supérieure ne peut être construite.
Références : modele-domaine §Aggregate Roots | Diagramme-classes.md
Critères d'acceptation :
- [ ] Chaque Aggregate Root est instanciable avec des données valides
- [ ] Chaque Aggregate Root rejette les données invalides à la construction
- [ ] Les comportements métier modifient l'état de l'entité de façon contrôlée
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts

**SUB — Implémenter User**
Objectif : Modéliser l'utilisateur avec ses informations personnelles, ses allergènes, ses préférences alimentaires et sa capacité à être supprimé (RGPD).
Règles métier : Un même allergène ne peut pas être ajouté deux fois. Une même préférence alimentaire ne peut pas être dupliquée. La date de suppression est imposée par le système.
Références : modele-domaine §User | specs-fonctionnelles §2.1
Critères d'acceptation :
- [ ] User est instanciable avec des données valides
- [ ] AddAllergen rejette un allergène déjà présent
- [ ] AddDietaryPreference rejette une préférence dupliquée
- [ ] MarkAsDeleted fixe une date imposée par le système

**SUB — Implémenter DietPlan**
Objectif : Modéliser le plan alimentaire réutilisable — type de régime, objectif, poids cible et répartition des macros. Sert de modèle au lancement d'une Diet.
Règles métier : Le CalorieTarget n'appartient pas au DietPlan — il est calculé au lancement depuis le poids réel. Le DietPlan reste toujours modifiable, même après avoir servi de base à une Diet.
Références : modele-domaine §DietPlan | workflow_lancer-diet.mermaid
Critères d'acceptation :
- [ ] DietPlan est instanciable avec des données valides
- [ ] Tous les champs sont modifiables après création
- [ ] DietPlan ne contient pas de CalorieTarget

**SUB — Implémenter Diet**
Objectif : Modéliser le régime actif — snapshot immuable du DietPlan au lancement, avec CalorieTarget calculé et StartDate imposée par le système.
Règles métier : StartDate est imposée par le système à la date du lancement, sans setter public. Une Diet Active ne peut pas être modifiée. L'EndDate est fixée automatiquement lors du passage en Archived.
Références : modele-domaine §Diet | workflow_lancer-diet.mermaid | workflow_terminer-diet.mermaid
Critères d'acceptation :
- [ ] Diet est instanciable avec CalorieTarget et StartDate système
- [ ] Modification d'une Diet Active lève une exception
- [ ] Passage en Archived fixe l'EndDate automatiquement
- [ ] Passage en Archived depuis Completed est impossible

**SUB — Implémenter Meal**
Objectif : Modéliser un repas avec son type, sa date de consommation, ses notes et sa liste d'aliments consommés.
Règles métier : Un Meal doit contenir au moins un MealItem. Retirer le dernier MealItem est interdit.
Références : modele-domaine §Meal | specs-fonctionnelles §3
Critères d'acceptation :
- [ ] Meal est instanciable avec au moins un MealItem
- [ ] Création sans MealItem lève une exception
- [ ] RemoveMealItem sur un Meal à 1 item lève une exception

**SUB — Implémenter FoodItem**
Objectif : Modéliser un aliment issu d'Open Food Facts avec ses valeurs nutritionnelles pour 100g et ses allergènes.
Règles métier : Les données sont mises à jour quotidiennement par le job d'import. La table est partagée entre tous les utilisateurs.
Références : modele-domaine §FoodItem | infrastructure-import-off.md
Critères d'acceptation :
- [ ] FoodItem est instanciable avec un identifiant OFF et des valeurs nutritionnelles
- [ ] UpdateFromImport met à jour toutes les valeurs et la date de mise à jour

---

### STORY-002 — Entités Enfants

En tant que développeur, je veux disposer des 3 entités enfants afin de modéliser les données liées aux Aggregate Roots parents.

Contexte : WeightEntry, MealItem et SavedFoodItem n'ont pas d'existence indépendante — ils sont supprimés en cascade avec leur parent.
Références : modele-domaine §Entités enfants | Diagramme-classes.md
Critères d'acceptation :
- [ ] Chaque entité enfant est instanciable avec des données valides
- [ ] Les invariants propres à chaque entité sont respectés
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts

**SUB — Implémenter WeightEntry**
Objectif : Modéliser une pesée utilisateur avec son poids et sa date de mesure fournie par l'utilisateur.
Règles métier : WeightEntry est immuable après création. Le poids doit être strictement positif. La date peut être antérieure à aujourd'hui.
Références : modele-domaine §WeightEntry | workflow_gestion-poids.mermaid
Critères d'acceptation :
- [ ] WeightEntry est instanciable avec un poids positif et une date valide
- [ ] Poids nul ou négatif lève une exception

**SUB — Implémenter MealItem**
Objectif : Modéliser un aliment consommé dans un repas avec sa quantité et un snapshot nutritionnel calculé à la création.
Règles métier : La valeur nutritionnelle est un snapshot calculé au moment de l'ajout (valeurs OFF × quantité / 100) — elle ne se met pas à jour si les données OFF changent. La quantité doit être strictement positive.
Références : modele-domaine §MealItem | specs-fonctionnelles §3
Critères d'acceptation :
- [ ] MealItem est instanciable avec une quantité positive et un NutritionInfo calculé
- [ ] Quantité nulle ou négative lève une exception

**SUB — Implémenter SavedFoodItem**
Objectif : Modéliser la sauvegarde d'un aliment dans la liste personnelle d'un utilisateur.
Règles métier : SavedFoodItem est immuable après création. La date de sauvegarde est imposée par le système. La vérification du doublon est faite dans FoodItemService.
Références : modele-domaine §SavedFoodItem | specs-fonctionnelles §4
Critères d'acceptation :
- [ ] SavedFoodItem est instanciable avec un UserId et un FoodItemId valides
- [ ] La date de sauvegarde est imposée par le système

---

### STORY-003 — Value Objects

En tant que développeur, je veux disposer des 3 Value Objects immuables afin d'encapsuler les calculs et contraintes nutritionnelles dans le domaine.

Contexte : MacroDistribution, NutritionInfo et NutritionNeeds représentent des concepts sans identité propre — leur égalité est basée sur leur valeur.
Références : modele-domaine §Value Objects | Regles-metier §BMR
Critères d'acceptation :
- [ ] Chaque VO valide ses invariants à la construction
- [ ] Les VO sont immuables
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts

**SUB — Implémenter MacroDistribution**
Objectif : Modéliser la répartition cible des macronutriments en pourcentages (protéines, glucides, lipides).
Règles métier : La somme des trois pourcentages doit être exactement 100%. Toutes les valeurs sont positives ou nulles.
Références : modele-domaine §MacroDistribution
Critères d'acceptation :
- [ ] Instanciable si la somme vaut exactement 100%
- [ ] Somme différente de 100% lève une ArgumentException
- [ ] Valeur négative lève une ArgumentException

**SUB — Implémenter NutritionInfo**
Objectif : Modéliser les valeurs nutritionnelles réelles d'un MealItem (calories, protéines, glucides, lipides) calculées au moment de la consommation.
Règles métier : Toutes les valeurs sont positives ou nulles. Représente ce qui a été consommé — différent de MacroDistribution qui est un objectif en pourcentages.
Références : modele-domaine §NutritionInfo
Critères d'acceptation :
- [ ] Instanciable avec des valeurs positives ou nulles
- [ ] Valeur négative lève une exception

**SUB — Implémenter NutritionNeeds**
Objectif : Modéliser les besoins nutritionnels calculés d'un utilisateur (BMR, TDEE, CalorieTarget).
Règles métier : Toutes les valeurs sont strictement positives. NutritionNeeds n'est jamais persisté — calculé à la demande par DietService.
Références : modele-domaine §NutritionNeeds | Regles-metier §BMR-TDEE
Critères d'acceptation :
- [ ] Instanciable avec des valeurs strictement positives
- [ ] Valeur nulle ou négative lève une exception

---

### STORY-004 — Enums

En tant que développeur, je veux disposer des 8 enums du modèle domaine afin de typer les valeurs métier et éviter les chaînes de caractères libres.

Contexte : Les enums définissent les valeurs possibles pour les champs typés du domaine. Chaque enum inclut une valeur Unknown = 0 utilisée uniquement par EF Core.
Références : modele-domaine §Enums
Critères d'acceptation :
- [ ] Les 8 enums sont déclarés avec toutes leurs valeurs
- [ ] Chaque enum contient Unknown = 0
Définition of Done :
- [ ] Code review approuvé

**SUB — Déclarer ActivityLevel**
Objectif : Déclarer les niveaux d'activité physique utilisés dans le calcul du TDEE.
Règles métier : Chaque valeur correspond à un coefficient NAP : Sedentary=1.2, LightlyActive=1.375, ModeratelyActive=1.55, VeryActive=1.725, ExtremelyActive=1.9.
Références : Regles-metier §TDEE
Critères d'acceptation :
- [ ] 5 valeurs déclarées + Unknown = 0

**SUB — Déclarer Goal**
Objectif : Déclarer les objectifs de régime utilisés pour ajuster le CalorieTarget.
Règles métier : WeightLoss = TDEE × 0.82, Maintenance = TDEE, WeightGain = TDEE × 1.18.
Références : Regles-metier §CalorieTarget
Critères d'acceptation :
- [ ] 3 valeurs déclarées + Unknown = 0

**SUB — Déclarer MealType**
Objectif : Déclarer les types de repas (petit-déjeuner, déjeuner, dîner, collation).
Règles métier : Aucun.
Références : modele-domaine §MealType
Critères d'acceptation :
- [ ] 4 valeurs déclarées + Unknown = 0

**SUB — Déclarer DietType**
Objectif : Déclarer les types de régime alimentaire disponibles.
Règles métier : Aucun.
Références : modele-domaine §DietType
Critères d'acceptation :
- [ ] 8 valeurs déclarées + Unknown = 0

**SUB — Déclarer DietStatus**
Objectif : Déclarer les statuts du cycle de vie d'un régime.
Règles métier : Active = régime en cours. Archived = régime clôturé avec EndDate renseignée.
Références : modele-domaine §DietStatus | workflow_terminer-diet.mermaid
Critères d'acceptation :
- [ ] 3 valeurs déclarées + Unknown = 0

**SUB — Déclarer Gender**
Objectif : Déclarer le genre utilisé dans le calcul BMR Mifflin-St Jeor.
Règles métier : Male : +5 au BMR, Female : -161 au BMR.
Références : Regles-metier §BMR
Critères d'acceptation :
- [ ] 3 valeurs déclarées (Male, Female, Other)

**SUB — Déclarer Allergen**
Objectif : Déclarer les 14 allergènes majeurs normalisés selon la réglementation EU et Open Food Facts.
Règles métier : Calqué sur les allergènes normalisés OFF : Gluten, Crustaceans, Eggs, Fish, Peanuts, Soybeans, Milk, Nuts, Celery, Mustard, SesameSeeds, SulphurDioxide, Lupin, Molluscs.
Références : modele-domaine §Allergen | infrastructure-import-off.md
Critères d'acceptation :
- [ ] 14 valeurs déclarées + Unknown = 0

**SUB — Déclarer SubscriptionTier**
Objectif : Déclarer les niveaux d'abonnement conditionnant les limites d'utilisation.
Règles métier : Free = accès limité, Pro = accès étendu, Business = accès illimité.
Références : specs-fonctionnelles §Abonnements
Critères d'acceptation :
- [ ] 3 valeurs déclarées (Free, Pro, Business)

---

### STORY-005 — Abonnements & Templates (Domain)

En tant que développeur, je veux étendre le modèle domaine avec le tier d'abonnement et la notion de template afin de supporter les fonctionnalités d'abonnement.

Contexte : SubscriptionTier conditionne les limites d'utilisation. IsTemplate sur DietPlan permet les plans partagés entre utilisateurs Pro/Business.
Références : modele-domaine §Abonnements | specs-fonctionnelles §Abonnements
Critères d'acceptation :
- [ ] User expose un SubscriptionTier (Free par défaut)
- [ ] DietPlan expose IsTemplate (false par défaut) et UserId nullable
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts

**SUB — Ajouter User.SubscriptionTier**
Objectif : Ajouter le tier d'abonnement sur User, Free par défaut à la création.
Règles métier : Le tier n'est pas extrait du JWT — la source de vérité est la base de données.
Références : specs-fonctionnelles §Abonnements
Critères d'acceptation :
- [ ] User créé avec SubscriptionTier = Free par défaut
- [ ] SubscriptionTier est modifiable

**SUB — Ajouter DietPlan.IsTemplate et UserId nullable**
Objectif : Permettre à un DietPlan d'être un template partagé sans appartenir à un utilisateur.
Règles métier : IsTemplate = false par défaut. Si IsTemplate = true, UserId est null. Un template est accessible en lecture seule aux tiers Pro/Business uniquement.
Références : specs-fonctionnelles §Templates
Critères d'acceptation :
- [ ] DietPlan créé avec IsTemplate = false par défaut
- [ ] UserId peut être null si IsTemplate = true

---

### STORY-006 — Invariants Domaine

En tant que développeur, je veux que les invariants métier intra-agrégat soient appliqués dans le domaine afin de garantir la cohérence des données à tout moment.

Contexte : Les invariants intra-agrégat vivent dans les entités. Les invariants cross-agrégat (une seule Diet active par User, doublon SavedFoodItem) sont dans les services applicatifs.
Références : modele-domaine §Invariants | Regles-metier §Invariants
Critères d'acceptation :
- [ ] MacroDistribution : somme = 100%
- [ ] Meal : au moins un MealItem à la création et après suppression
- [ ] Diet.StartDate : imposée par le système
- [ ] Diet : non modifiable une fois Active ou Completed
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts

**SUB — MacroDistribution : somme des pourcentages = 100%**
Objectif : Garantir que la répartition des macros est toujours cohérente.
Règles métier : ProteinPercentage + CarbPercentage + FatPercentage = 100. Toutes les valeurs >= 0.
Références : modele-domaine §MacroDistribution
Critères d'acceptation :
- [ ] Somme != 100 lève ArgumentException
- [ ] Valeur négative lève ArgumentException

**SUB — Meal : au moins un MealItem obligatoire**
Objectif : Interdire la création et la modification d'un Meal vide.
Règles métier : Constructeur rejette une liste nulle ou vide. RemoveMealItem est interdit si Count <= 1.
Références : modele-domaine §Meal
Critères d'acceptation :
- [ ] Création sans item lève ArgumentException
- [ ] Suppression du dernier item lève InvalidOperationException

**SUB — Diet.StartDate imposée par le système**
Objectif : Garantir que la date de début d'un régime est toujours la date réelle du lancement.
Règles métier : StartDate = date du jour au moment de la création. Pas de setter public.
Références : modele-domaine §Diet
Critères d'acceptation :
- [ ] StartDate est égale à la date système à la création
- [ ] Aucun setter public n'est exposé sur StartDate

**SUB — Diet non modifiable une fois Active ou Completed**
Objectif : Protéger l'intégrité d'un régime en cours contre toute modification.
Règles métier : Toute tentative de modification d'une Diet Active ou Completed lève une InvalidOperationException. Seul le changement de statut reste autorisé.
Références : modele-domaine §Diet | workflow_terminer-diet.mermaid
Critères d'acceptation :
- [ ] Rename sur Diet Active lève InvalidOperationException
- [ ] ChangeDietStatus reste possible sur Diet Active
- [ ] Toute modification sur Diet Completed lève InvalidOperationException

---

## Epic EPIC-002 — Application Layer

---

### STORY-007 — UserService

En tant qu'utilisateur, je veux gérer mon profil et mes pesées afin de disposer de données personnelles à jour pour le calcul de mes besoins nutritionnels.

Contexte : UserService orchestre la création et la mise à jour du profil utilisateur ainsi que l'historique des pesées. La première WeightEntry est créée en même temps que le profil.
Références : specs-fonctionnelles §2.1 | workflow_mise-a-jour-profil.mermaid | workflow_gestion-poids.mermaid
Critères d'acceptation :
- [ ] Création de profil avec première pesée en une seule opération
- [ ] Mise à jour des champs modifiables du profil
- [ ] Ajout de pesée avec rejet des doublons à la même date
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts

**SUB — Créer le profil utilisateur avec première WeightEntry**
Objectif : Permettre la création du profil à la première connexion, en enregistrant simultanément le poids initial.
Règles métier : Un profil ne peut pas être créé deux fois pour le même identifiant Keycloak (409). La première WeightEntry est obligatoire à la création du profil.
Références : specs-fonctionnelles §2.1 | workflow_mise-a-jour-profil.mermaid
Critères d'acceptation :
- [ ] Profil et première WeightEntry créés en une transaction
- [ ] Doublon KeycloakId lève une ConflictException (409)

**SUB — Mettre à jour le profil utilisateur**
Objectif : Permettre la modification des informations personnelles, des allergènes et des préférences alimentaires.
Règles métier : Appliquer uniquement les champs fournis. Les invariants domaine (pas de doublon allergène/préférence) sont appliqués par les entités.
Références : workflow_mise-a-jour-profil.mermaid
Critères d'acceptation :
- [ ] Les champs modifiés sont persistés
- [ ] Les invariants domaine sont respectés

**SUB — Ajouter une WeightEntry**
Objectif : Permettre l'enregistrement d'une nouvelle pesée pour un utilisateur.
Règles métier : Une seule WeightEntry par date par utilisateur — doublon à la même date lève ConflictException (409).
Références : workflow_gestion-poids.mermaid
Critères d'acceptation :
- [ ] WeightEntry créée et persistée avec succès
- [ ] Doublon même date lève ConflictException (409)

---

### STORY-008 — DietPlanService

En tant qu'utilisateur, je veux gérer mes plans alimentaires personnels afin de pouvoir les réutiliser pour lancer des régimes.

Contexte : DietPlanService gère le CRUD complet des plans personnels d'un utilisateur. Les templates partagés (IsTemplate = true) sont gérés par les endpoints admin.
Références : specs-fonctionnelles §2.2 | workflow_lancer-diet.mermaid
Critères d'acceptation :
- [ ] Création, modification, suppression et listage des plans personnels
- [ ] Un utilisateur ne peut accéder qu'à ses propres plans
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts

**SUB — Créer un DietPlan**
Objectif : Permettre la création d'un plan alimentaire personnel.
Règles métier : Le plan appartient à l'utilisateur qui le crée (UserId = userId). IsTemplate = false par défaut.
Références : specs-fonctionnelles §2.2
Critères d'acceptation :
- [ ] DietPlan créé et persisté avec les données fournies
- [ ] Le plan appartient à l'utilisateur authentifié

**SUB — Modifier un DietPlan**
Objectif : Permettre la mise à jour des champs d'un plan alimentaire personnel.
Règles métier : Seul le propriétaire peut modifier son plan (403 sinon). Le plan reste modifiable même s'il a déjà servi de base à une Diet.
Références : specs-fonctionnelles §2.2
Critères d'acceptation :
- [ ] Modification réussie si le plan appartient à l'utilisateur
- [ ] Tentative de modification par un autre utilisateur lève ForbiddenException (403)

**SUB — Supprimer un DietPlan**
Objectif : Permettre la suppression d'un plan alimentaire personnel.
Règles métier : Seul le propriétaire peut supprimer son plan (403 sinon).
Références : specs-fonctionnelles §2.2
Critères d'acceptation :
- [ ] Suppression réussie si le plan appartient à l'utilisateur
- [ ] Tentative de suppression par un autre utilisateur lève ForbiddenException (403)

**SUB — Lister les DietPlans d'un utilisateur**
Objectif : Retourner tous les plans personnels de l'utilisateur authentifié.
Règles métier : Retourner uniquement les plans dont UserId correspond à l'utilisateur — pas les templates.
Références : specs-fonctionnelles §2.2
Critères d'acceptation :
- [ ] Liste retournée filtrée par UserId
- [ ] Les templates (IsTemplate = true) ne sont pas inclus

---

### STORY-009 — DietService

En tant qu'utilisateur, je veux lancer, suivre et terminer mes régimes afin de gérer mon cycle nutritionnel avec des objectifs caloriques calculés.

Contexte : DietService orchestre le lancement (snapshot + calcul BMR/TDEE), la clôture et la déduction de Diet par date. C'est ici que sont vérifiés les invariants cross-agrégat liés à la Diet.
Références : specs-fonctionnelles §2.3 | workflow_lancer-diet.mermaid | workflow_terminer-diet.mermaid | Regles-metier §BMR-TDEE
Critères d'acceptation :
- [ ] Lancement crée un snapshot Diet avec CalorieTarget calculé
- [ ] Lancement bloqué si une Diet est déjà Active (409)
- [ ] Lancement bloqué si aucune WeightEntry disponible (422)
- [ ] Clôture archive la Diet et fixe l'EndDate
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts

**SUB — Lancer un DietPlan et créer une Diet active**
Objectif : Créer une Diet active à partir d'un DietPlan en calculant le CalorieTarget depuis le poids réel de l'utilisateur.
Règles métier : Bloquer si une Diet Active existe déjà pour cet utilisateur (409). Bloquer si aucune WeightEntry disponible pour le calcul BMR (422). La Diet est un snapshot immuable du DietPlan.
Références : workflow_lancer-diet.mermaid | Regles-metier §BMR-TDEE
Critères d'acceptation :
- [ ] Diet créée avec CalorieTarget calculé depuis le poids le plus récent
- [ ] Diet Active existante lève ConflictException (409)
- [ ] Absence de WeightEntry lève une exception (422)

**SUB — Calculer BMR, TDEE et CalorieTarget**
Objectif : Calculer les besoins nutritionnels d'un utilisateur à partir de ses données physiques et de son objectif.
Règles métier : BMR Mifflin-St Jeor — Homme : (10×P)+(6.25×T)-(5×A)+5, Femme : -161. TDEE = BMR × coefficient NAP. CalorieTarget : WeightLoss=TDEE×0.82, Maintenance=TDEE, WeightGain=TDEE×1.18. Retourner NutritionNeeds (non persisté).
Références : Regles-metier §BMR-TDEE
Critères d'acceptation :
- [ ] BMR calculé correctement selon le genre
- [ ] TDEE calculé selon le niveau d'activité
- [ ] CalorieTarget ajusté selon l'objectif

**SUB — Terminer une Diet active**
Objectif : Permettre à l'utilisateur de clôturer son régime en cours.
Règles métier : Seul le propriétaire peut clôturer sa Diet (403 sinon). La Diet doit être Active (400 si déjà Archived). L'EndDate est fixée automatiquement par le domaine.
Références : workflow_terminer-diet.mermaid
Critères d'acceptation :
- [ ] Diet passée en Archived avec EndDate renseignée
- [ ] Tentative sur Diet déjà Archived lève une exception (400)

**SUB — Déduire la Diet active à la date d'un Meal**
Objectif : Retrouver la Diet de l'utilisateur qui était active à une date donnée, pour le calcul du bilan nutritionnel.
Règles métier : Filtrer les Diets dont StartDate <= date && (EndDate == null || EndDate >= date). Retourner null si aucune Diet trouvée.
Références : specs-fonctionnelles §Bilan
Critères d'acceptation :
- [ ] Diet correspondante retournée si elle existe
- [ ] Null retourné si aucune Diet ne couvre la date

---

### STORY-010 — MealService

En tant qu'utilisateur, je veux créer et gérer mes repas afin d'enregistrer ma consommation alimentaire quotidienne.

Contexte : MealService gère la création de repas avec calcul automatique des valeurs nutritionnelles, la liste des repas sauvegardés et la suppression.
Références : specs-fonctionnelles §3 | workflow_enregistrer-repas.mermaid
Critères d'acceptation :
- [ ] Création d'un repas avec NutritionInfo calculée par item
- [ ] Listage des repas sauvegardés
- [ ] Suppression d'un repas avec cascade sur les MealItems
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts

**SUB — Créer un Meal avec calcul NutritionInfo**
Objectif : Enregistrer un repas en calculant automatiquement les valeurs nutritionnelles de chaque aliment consommé.
Règles métier : Pour chaque item, calculer NutritionInfo = valeurs OFF × (quantité / 100). Un Meal sans item est invalide (400).
Références : specs-fonctionnelles §3 | workflow_enregistrer-repas.mermaid
Critères d'acceptation :
- [ ] Meal créé avec NutritionInfo calculée pour chaque MealItem
- [ ] Meal sans item lève une exception (400)

**SUB — Lister les repas sauvegardés**
Objectif : Retourner tous les repas marqués comme sauvegardés par l'utilisateur.
Règles métier : Filtrer par IsSaved = true et UserId.
Références : specs-fonctionnelles §3
Critères d'acceptation :
- [ ] Liste retournée filtrée par IsSaved = true et UserId

**SUB — Supprimer un Meal**
Objectif : Permettre la suppression d'un repas et de tous ses MealItems.
Règles métier : Seul le propriétaire peut supprimer son repas (403 sinon). Cascade sur MealItems.
Références : specs-fonctionnelles §3
Critères d'acceptation :
- [ ] Repas et MealItems supprimés
- [ ] Tentative par un autre utilisateur lève ForbiddenException (403)

---

### STORY-011 — FoodItemService

En tant qu'utilisateur, je veux rechercher des aliments et gérer ma liste personnelle afin de retrouver rapidement les aliments que je consomme régulièrement.

Contexte : FoodItemService gère la recherche (Redis → PostgreSQL), la sauvegarde et la gestion de la liste personnelle. L'invariant doublon SavedFoodItem est vérifié ici.
Références : specs-fonctionnelles §4 | workflow_rechercher-aliment.mermaid
Critères d'acceptation :
- [ ] Recherche retourne des résultats depuis Redis ou PostgreSQL
- [ ] Sauvegarde bloquée si doublon pour cet utilisateur (409)
- [ ] Liste personnelle retournée correctement
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts

**SUB — Rechercher un aliment par mot-clé**
Objectif : Permettre la recherche d'aliments par nom, en utilisant le cache Redis avant la base de données.
Règles métier : Chercher d'abord dans Redis. Si absent du cache, interroger PostgreSQL et mettre à jour le cache.
Références : workflow_rechercher-aliment.mermaid
Critères d'acceptation :
- [ ] Cache hit : résultat retourné depuis Redis sans requête PostgreSQL
- [ ] Cache miss : résultat retourné depuis PostgreSQL et mis en cache

**SUB — Sauvegarder un FoodItem dans la liste personnelle**
Objectif : Permettre à l'utilisateur d'ajouter un aliment à sa liste personnelle.
Règles métier : Un même aliment ne peut être sauvegardé qu'une fois par utilisateur — doublon lève ConflictException (409). L'aliment doit exister (404 sinon).
Références : specs-fonctionnelles §4
Critères d'acceptation :
- [ ] SavedFoodItem créé si l'aliment existe et n'est pas déjà sauvegardé
- [ ] Doublon lève ConflictException (409)
- [ ] Aliment inexistant lève NotFoundException (404)

**SUB — Supprimer un SavedFoodItem**
Objectif : Permettre le retrait d'un aliment de la liste personnelle.
Règles métier : Seul le propriétaire peut supprimer son SavedFoodItem (403 sinon).
Références : specs-fonctionnelles §4
Critères d'acceptation :
- [ ] SavedFoodItem supprimé
- [ ] Tentative par un autre utilisateur lève ForbiddenException (403)

**SUB — Lister les SavedFoodItems d'un utilisateur**
Objectif : Retourner tous les aliments sauvegardés de l'utilisateur avec leur détail nutritionnel.
Règles métier : Filtrer par UserId.
Références : specs-fonctionnelles §4
Critères d'acceptation :
- [ ] Liste retournée avec détail FoodItem pour chaque entrée

---

### STORY-012 — NutritionService

En tant qu'utilisateur, je veux consulter le bilan nutritionnel de mon régime afin de suivre mes apports réels et les comparer à mes objectifs.

Contexte : NutritionService agrège les MealItems par jour sur la période de la Diet, inclut les WeightEntries et calcule les moyennes.
Références : specs-fonctionnelles §Bilan | workflow_consulter-bilan.mermaid
Critères d'acceptation :
- [ ] Bilan retourné avec données journalières, pesées et résumé
- [ ] Période filtrée selon le tier d'abonnement
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts

**SUB — Calculer le bilan nutritionnel d'une Diet**
Objectif : Agréger les apports nutritionnels journaliers sur la période d'une Diet et retourner un résumé avec les pesées.
Règles métier : Agréger MealItem.NutritionInfo par jour. Inclure les WeightEntries sur la même période. Clamper la période selon le tier : Free = 7j, Pro = 1 an, Business = illimité.
Références : specs-fonctionnelles §Bilan | workflow_consulter-bilan.mermaid
Critères d'acceptation :
- [ ] dailyData contient une entrée par jour avec sommes correctes
- [ ] weightEntries incluses sur la période
- [ ] summary contient CalorieTarget, moyennes et poids début/fin
- [ ] Période clampée selon le tier

---

### STORY-013 — SubscriptionGuard

En tant que développeur, je veux un helper centralisé de vérification des limites d'abonnement afin d'appliquer les restrictions de tier de façon cohérente dans tous les services.

Contexte : Les limites varient selon le tier (Free/Pro/Business). Le guard est appelé dans DietPlanService, MealService, FoodItemService et NutritionService.
Références : specs-fonctionnelles §Abonnements
Critères d'acceptation :
- [ ] Limite atteinte lève ForbiddenException (403)
- [ ] Toutes les restrictions de tier sont appliquées via ce helper
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts

**SUB — Implémenter SubscriptionGuard**
Objectif : Centraliser la vérification des limites d'utilisation selon le tier d'abonnement.
Règles métier : Si count >= limite pour le tier → ForbiddenException (403).
Références : specs-fonctionnelles §Abonnements
Critères d'acceptation :
- [ ] Limite atteinte lève ForbiddenException avec message explicite
- [ ] Limite non atteinte ne lève aucune exception

**SUB — Limiter les plans personnels selon le tier**
Objectif : Bloquer la création d'un plan personnel si la limite du tier est atteinte.
Règles métier : Free = 2 plans max, Pro = 20 plans max, Business = illimité.
Références : specs-fonctionnelles §Abonnements
Critères d'acceptation :
- [ ] Création bloquée (403) si limite atteinte pour le tier

**SUB — Bloquer l'accès aux templates si tier Free**
Objectif : Réserver l'accès aux templates partagés aux tiers Pro et Business.
Règles métier : Tier Free → ForbiddenException (403) à la tentative de listage des templates.
Références : specs-fonctionnelles §Templates
Critères d'acceptation :
- [ ] Tier Free → 403 sur GetTemplatesAsync

**SUB — Lister les templates partagés**
Objectif : Retourner tous les DietPlan marqués comme templates (IsTemplate = true).
Règles métier : Accessible aux tiers Pro et Business uniquement.
Références : specs-fonctionnelles §Templates
Critères d'acceptation :
- [ ] Liste des templates retournée pour Pro et Business
- [ ] 403 pour tier Free

**SUB — Limiter les repas sauvegardés selon le tier**
Objectif : Bloquer la sauvegarde d'un repas si la limite du tier est atteinte.
Règles métier : Free = 5 repas sauvegardés max, Pro = 50 max, Business = illimité.
Références : specs-fonctionnelles §Abonnements
Critères d'acceptation :
- [ ] Sauvegarde bloquée (403) si limite atteinte pour le tier

**SUB — Limiter les SavedFoodItems selon le tier**
Objectif : Bloquer l'ajout d'un aliment sauvegardé si la limite du tier est atteinte.
Règles métier : Free = 10 max, Pro = 100 max, Business = illimité.
Références : specs-fonctionnelles §Abonnements
Critères d'acceptation :
- [ ] Ajout bloqué (403) si limite atteinte pour le tier

**SUB — Restreindre la période du bilan selon le tier**
Objectif : Limiter la plage de dates consultable dans le bilan nutritionnel selon le tier.
Règles métier : Free = 7 jours max, Pro = 1 an max, Business = illimité.
Références : specs-fonctionnelles §Abonnements
Critères d'acceptation :
- [ ] Période effective clampée à 7j pour Free, 1 an pour Pro

---

### STORY-014 — AdminService

En tant qu'administrateur, je veux consulter les KPIs et l'état du système afin de surveiller l'activité et la santé de la plateforme.

Contexte : AdminService agrège les métriques utilisateurs, l'activité et l'état des jobs Hangfire depuis les tables système.
Références : specs-fonctionnelles §Admin
Critères d'acceptation :
- [ ] KPIs utilisateurs agrégés correctement
- [ ] Métriques activité retournées
- [ ] État des jobs Hangfire retourné
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests unitaires verts

**SUB — Agréger les KPIs utilisateurs**
Objectif : Calculer le nombre total d'utilisateurs, la répartition par tier et les nouveaux inscrits des 7 derniers jours.
Règles métier : Requêtes agrégées sur la table Users.
Références : specs-fonctionnelles §Admin
Critères d'acceptation :
- [ ] Total, répartition par tier et nouveaux 7j retournés correctement

**SUB — Agréger les métriques d'activité**
Objectif : Calculer le nombre de Diets actives, de repas créés cette semaine et de comptes en grace period.
Règles métier : Diets Active, Meals créés dans les 7 derniers jours, Users avec DeletedAt non null.
Références : specs-fonctionnelles §Admin
Critères d'acceptation :
- [ ] Les 3 métriques retournées correctement

**SUB — Agréger l'état des jobs depuis Hangfire**
Objectif : Retourner le statut et la date du dernier import OFF et de la dernière purge RGPD.
Règles métier : Requêtes directes sur les tables HangFire.Job et HangFire.State.
Références : infrastructure-hangfire.md
Critères d'acceptation :
- [ ] Statut (success/failed/never_run) et date retournés pour chaque job

---

### STORY-015 — DTOs Application

En tant que développeur, je veux disposer des DTOs Request et Response pour chaque use case afin de découpler les contrats API des entités domaine.

Contexte : Un DTO Request (input) et un DTO Response (output) par use case. NutritionBilanResponse est le plus complexe avec ses trois sections.
Références : specs-fonctionnelles §Contrats API | specs-frontend.md
Critères d'acceptation :
- [ ] Tous les use cases ont leurs DTOs correspondants
- [ ] Les DTOs ne référencent pas les entités domaine directement
Définition of Done :
- [ ] Code review approuvé

**SUB — CreateUserProfileRequest et UserProfileResponse**
Objectif : Modéliser l'input de création de profil et l'output incluant BMR/TDEE calculés.
Règles métier : Weight dans la request sert à créer la première WeightEntry. BMR et TDEE dans la response sont calculés à la demande.
Références : specs-fonctionnelles §2.1
Critères d'acceptation :
- [ ] Request contient tous les champs profil + Weight initial
- [ ] Response inclut Bmr et Tdee

**SUB — CreateDietPlanRequest et DietPlanResponse**
Objectif : Modéliser l'input de création d'un plan et son output.
Règles métier : MacroDistribution dans la request doit avoir une somme de 100%.
Références : specs-fonctionnelles §2.2
Critères d'acceptation :
- [ ] Request contient Name, DietType, Goal, TargetWeight, MacroDistribution
- [ ] Response inclut Id et tous les champs du plan

**SUB — LaunchDietPlanRequest et DietResponse**
Objectif : Modéliser le lancement d'un plan et l'output de la Diet créée.
Règles métier : La request ne contient que DietPlanId — tout le reste est calculé ou copié depuis le plan.
Références : specs-fonctionnelles §2.3
Critères d'acceptation :
- [ ] Request contient uniquement DietPlanId
- [ ] Response inclut CalorieTarget, MacroDistribution, Status, StartDate

**SUB — CreateMealRequest et MealResponse**
Objectif : Modéliser la création d'un repas et son output avec NutritionInfo.
Règles métier : La request doit contenir au moins un item (FoodItemId + Quantity).
Références : specs-fonctionnelles §3
Critères d'acceptation :
- [ ] Request contient Name, MealType, ConsumedAt, Items
- [ ] Response inclut NutritionInfo par item et total agrégé

**SUB — FoodItemSearchResponse, SaveFoodItemRequest et NutritionBilanResponse**
Objectif : Modéliser la recherche d'aliments, la sauvegarde et le bilan nutritionnel complet.
Règles métier : NutritionBilanResponse contient dailyData (par jour), weightEntries et summary (moyennes + poids).
Références : specs-fonctionnelles §4 | specs-fonctionnelles §Bilan
Critères d'acceptation :
- [ ] FoodItemSearchResponse inclut valeurs nutritionnelles et allergènes
- [ ] NutritionBilanResponse contient les 3 sections (dailyData, weightEntries, summary)

---

## Epic EPIC-003 — Infrastructure Layer

---

### STORY-016 — EF Core Configurations

En tant que développeur, je veux configurer le mapping EF Core avec Fluent API afin de persister le modèle domaine en base de données sans polluer les entités avec des annotations.

Contexte : Toute la configuration de persistance est centralisée dans des classes de configuration EF Core. Les Value Objects MacroDistribution et NutritionInfo sont des owned entities.
Références : specs-techniques §EF Core | modele-domaine §Diagramme-classes
Critères d'acceptation :
- [ ] Toutes les entités sont mappées sans annotations sur les classes domaine
- [ ] Les owned entities sont configurées en colonnes inline
- [ ] Les index uniques sont créés en base
Définition of Done :
- [ ] Code review approuvé
- [ ] Migration générée sans erreur

**SUB — Configurer UserConfiguration**
Objectif : Définir le mapping de User avec index unique sur KeycloakId et stockage JSON pour les listes.
Règles métier : KeycloakId doit être unique en base. Allergies et DietaryPreferences stockés en JSON.
Références : modele-domaine §User
Critères d'acceptation :
- [ ] Index unique sur KeycloakId
- [ ] Allergies et DietaryPreferences persistés correctement

**SUB — Configurer DietPlanConfiguration**
Objectif : Définir le mapping de DietPlan avec UserId nullable et owned entity MacroDistribution.
Règles métier : UserId est nullable (null si IsTemplate = true). MacroDistribution en colonnes inline.
Références : modele-domaine §DietPlan
Critères d'acceptation :
- [ ] UserId nullable accepté en base
- [ ] MacroDistribution en owned entity avec colonnes inline
- [ ] Index sur IsTemplate pour filtrage rapide

**SUB — Configurer DietConfiguration**
Objectif : Définir le mapping de Diet avec owned entity MacroDistribution et colonnes DateOnly.
Règles métier : StartDate et EndDate en colonnes DateOnly. MacroDistribution en owned entity.
Références : modele-domaine §Diet
Critères d'acceptation :
- [ ] StartDate et EndDate mappés en DateOnly
- [ ] MacroDistribution en owned entity

**SUB — Configurer MealConfiguration**
Objectif : Définir le mapping de Meal avec cascade delete sur MealItems.
Règles métier : Suppression d'un Meal supprime ses MealItems en cascade.
Références : modele-domaine §Meal
Critères d'acceptation :
- [ ] Cascade delete configuré sur MealItems

**SUB — Configurer MealItemConfiguration**
Objectif : Définir le mapping de MealItem avec owned entity NutritionInfo.
Règles métier : NutritionInfo en colonnes inline (Calories, Proteins, Carbs, Fats).
Références : modele-domaine §MealItem
Critères d'acceptation :
- [ ] NutritionInfo en owned entity avec colonnes inline

**SUB — Configurer FoodItemConfiguration**
Objectif : Définir le mapping de FoodItem avec index unique sur OffId et stockage JSON pour les allergènes.
Règles métier : OffId doit être unique en base. AllergensTags stockés en JSON.
Références : modele-domaine §FoodItem
Critères d'acceptation :
- [ ] Index unique sur OffId
- [ ] AllergensTags persistés correctement

**SUB — Configurer WeightEntryConfiguration**
Objectif : Définir le mapping de WeightEntry avec index unique composite (UserId + MeasuredAt) et cascade delete.
Règles métier : Une seule WeightEntry par date par utilisateur — garanti par l'index unique composite. Supprimé en cascade à la suppression du User.
Références : modele-domaine §WeightEntry
Critères d'acceptation :
- [ ] Index unique composite (UserId, MeasuredAt)
- [ ] Cascade delete sur suppression du User

**SUB — Configurer SavedFoodItemConfiguration**
Objectif : Définir le mapping de SavedFoodItem avec index unique composite (UserId + FoodItemId) et cascade delete.
Règles métier : Un même aliment ne peut être sauvegardé qu'une fois par utilisateur — garanti par l'index unique. Supprimé en cascade à la suppression du User.
Références : modele-domaine §SavedFoodItem
Critères d'acceptation :
- [ ] Index unique composite (UserId, FoodItemId)
- [ ] Cascade delete sur suppression du User

---

### STORY-017 — Repositories

En tant que développeur, je veux disposer des interfaces et implémentations de repositories afin de découpler les services applicatifs de la persistance.

Contexte : Les interfaces sont définies dans la couche Application, les implémentations dans la couche Infrastructure. Chaque repository expose les méthodes nécessaires aux services applicatifs.
Références : specs-techniques §Repositories | modele-domaine §Aggregate Roots
Critères d'acceptation :
- [ ] 7 paires interface/implémentation créées
- [ ] Les services applicatifs utilisent uniquement les interfaces
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests d'intégration verts

**SUB — IUserRepository et UserRepository**
Objectif : Persister et récupérer les utilisateurs par Id ou KeycloakId.
Règles métier : GetByKeycloakIdAsync nécessaire pour la résolution JWT.
Références : specs-techniques §Repositories
Critères d'acceptation :
- [ ] GetByIdAsync, GetByKeycloakIdAsync, AddAsync, UpdateAsync, DeleteAsync opérationnels

**SUB — IDietPlanRepository et DietPlanRepository**
Objectif : Persister et récupérer les plans alimentaires personnels et templates.
Règles métier : GetTemplatesAsync retourne uniquement IsTemplate = true.
Références : specs-techniques §Repositories
Critères d'acceptation :
- [ ] GetAllByUserIdAsync, GetTemplatesAsync, AddAsync, UpdateAsync, DeleteAsync opérationnels

**SUB — IDietRepository et DietRepository**
Objectif : Persister et récupérer les régimes, notamment la Diet active courante.
Règles métier : GetActiveByUserIdAsync retourne null si aucune Diet Active.
Références : specs-techniques §Repositories
Critères d'acceptation :
- [ ] GetActiveByUserIdAsync, GetAllByUserIdAsync, AddAsync, UpdateAsync opérationnels

**SUB — IMealRepository et MealRepository**
Objectif : Persister et récupérer les repas avec leurs MealItems.
Règles métier : GetAllByUserIdAsync supporte le filtre par date. GetSavedByUserIdAsync filtre IsSaved = true.
Références : specs-techniques §Repositories
Critères d'acceptation :
- [ ] Récupération avec Include MealItems
- [ ] Filtres par date et IsSaved opérationnels

**SUB — IFoodItemRepository et FoodItemRepository**
Objectif : Persister et rechercher les aliments par mot-clé ou identifiant OFF.
Règles métier : SearchByKeywordAsync utilise ILIKE pour la recherche insensible à la casse sur PostgreSQL.
Références : specs-techniques §Repositories
Critères d'acceptation :
- [ ] SearchByKeywordAsync retourne des résultats pertinents
- [ ] GetByOffIdAsync retourne null si absent

**SUB — IWeightEntryRepository et WeightEntryRepository**
Objectif : Persister et récupérer les pesées d'un utilisateur.
Règles métier : GetLatestByUserIdAsync retourne la pesée la plus récente. ExistsAsync vérifie le doublon par date.
Références : specs-techniques §Repositories
Critères d'acceptation :
- [ ] GetLatestByUserIdAsync retourne la pesée la plus récente
- [ ] ExistsAsync détecte le doublon correctement

**SUB — ISavedFoodItemRepository et SavedFoodItemRepository**
Objectif : Persister et récupérer les aliments sauvegardés d'un utilisateur.
Règles métier : ExistsAsync vérifie le doublon (UserId + FoodItemId).
Références : specs-techniques §Repositories
Critères d'acceptation :
- [ ] ExistsAsync détecte le doublon correctement
- [ ] GetAllByUserIdAsync retourne les entrées avec détail FoodItem

---

### STORY-018 — Cache Redis

En tant que développeur, je veux un service de cache Redis pour les recherches d'aliments afin de réduire la charge sur PostgreSQL.

Contexte : La recherche d'aliments est l'opération la plus fréquente. Redis stocke les résultats par mot-clé avec un TTL court.
Références : specs-techniques §Cache
Critères d'acceptation :
- [ ] Cache hit retourne les données sans requête PostgreSQL
- [ ] Cache miss interroge PostgreSQL et met à jour le cache
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests d'intégration verts

**SUB — Configurer IConnectionMultiplexer Redis**
Objectif : Enregistrer la connexion Redis au démarrage de l'application.
Règles métier : Gérer les erreurs de connexion au démarrage sans bloquer le démarrage de l'application.
Références : specs-techniques §Cache
Critères d'acceptation :
- [ ] Connexion Redis disponible via injection de dépendance

**SUB — IFoodCacheService et FoodCacheService**
Objectif : Implémenter le service de cache avec get/set par mot-clé et TTL configurable.
Règles métier : TTL configurable via appsettings. Sérialisation JSON des données.
Références : specs-techniques §Cache
Critères d'acceptation :
- [ ] GetAsync retourne null en cas de cache miss
- [ ] SetAsync + GetAsync retourne les données mises en cache

---

### STORY-019 — Job Import Open Food Facts

En tant que système, je veux importer quotidiennement le dump Open Food Facts afin de maintenir la base d'aliments à jour.

Contexte : Le job télécharge le dump OFF, traite les aliments par batch et planifie l'exécution via Hangfire.
Références : infrastructure-import-off.md
Critères d'acceptation :
- [ ] FoodItems créés au premier import
- [ ] FoodItems mis à jour (UpdateFromImport) aux imports suivants
- [ ] Retry automatique en cas d'échec
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests d'intégration verts

**SUB — Télécharger le dump Open Food Facts**
Objectif : Récupérer le dump quotidien OFF et le préparer pour le traitement.
Règles métier : Téléchargement dans un fichier temporaire, décompression GZIP, retour du flux de lignes.
Références : infrastructure-import-off.md
Critères d'acceptation :
- [ ] Dump téléchargé et décompressé sans erreur

**SUB — Traiter le dump par batch**
Objectif : Insérer ou mettre à jour les FoodItems depuis le dump par lots pour éviter les timeouts.
Règles métier : Si OffId existant → UpdateFromImport. Sinon → création. Traitement par batch de 1000 lignes. Ignorer les lignes malformées.
Références : infrastructure-import-off.md
Critères d'acceptation :
- [ ] FoodItems existants mis à jour, nouveaux créés
- [ ] Lignes malformées ignorées sans interruption

**SUB — Planifier et gérer les erreurs du job**
Objectif : Enregistrer le job avec une planification quotidienne et un retry automatique.
Règles métier : Planification cron 0 3 * * * (03h00). AutomaticRetry(Attempts = 3). Les erreurs par lot sont loggées sans interrompre le traitement global.
Références : infrastructure-hangfire.md | infrastructure-import-off.md
Critères d'acceptation :
- [ ] Job planifié à 03h00 quotidiennement
- [ ] Retry automatique après échec (3 tentatives max)

---

### STORY-020 — Job Purge RGPD

En tant que système, je veux purger quotidiennement les comptes supprimés depuis plus de 30 jours afin de respecter les obligations RGPD.

Contexte : Le job sélectionne les Users soft-deleted depuis > 30 jours, supprime leurs données en cascade et les retire de Keycloak.
Références : workflow_rgpd.mermaid | infrastructure-keycloak-admin.md
Critères d'acceptation :
- [ ] Données utilisateur supprimées en cascade
- [ ] Compte Keycloak supprimé
- [ ] Indisponibilité Keycloak gérée avec retry
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests d'intégration verts

**SUB — Sélectionner et supprimer les comptes expirés**
Objectif : Identifier les utilisateurs soft-deleted depuis > 30 jours et supprimer leurs données en cascade.
Règles métier : DeletedAt <= maintenant - 30 jours. Cascade dans l'ordre : MealItems → Meals → WeightEntries → SavedFoodItems → DietPlans → Diets → User. Une transaction par utilisateur.
Références : workflow_rgpd.mermaid
Critères d'acceptation :
- [ ] Tous les enregistrements liés supprimés en cascade
- [ ] Transaction par utilisateur garantit la cohérence

**SUB — Supprimer l'utilisateur dans Keycloak et gérer les erreurs**
Objectif : Appeler l'API Keycloak Admin pour supprimer le compte et gérer les cas d'indisponibilité.
Règles métier : Ignorer 404 (compte déjà absent). Retry Polly (3 tentatives, backoff exponentiel) si Keycloak indisponible. Si échec après retries → logger et passer à l'utilisateur suivant.
Références : infrastructure-keycloak-admin.md
Critères d'acceptation :
- [ ] Compte Keycloak supprimé
- [ ] 404 ignoré sans erreur
- [ ] Indisponibilité gérée sans interruption du job

**SUB — Planifier le job avec Hangfire**
Objectif : Enregistrer le job avec une planification quotidienne décalée de 30 minutes après l'import OFF.
Règles métier : Planification cron 30 3 * * * (03h30). AutomaticRetry(Attempts = 3).
Références : infrastructure-hangfire.md
Critères d'acceptation :
- [ ] Job planifié à 03h30 quotidiennement
- [ ] Retry automatique après échec

---

### STORY-021 — Migrations EF Core

En tant que développeur, je veux générer et appliquer les migrations EF Core afin de créer le schéma de base de données depuis le modèle domaine.

Contexte : La migration initiale crée toutes les tables, index et contraintes. L'import initial du dump OFF peuple la table FoodItem au premier déploiement.
Références : specs-techniques §Migrations
Critères d'acceptation :
- [ ] Migration générée sans erreur
- [ ] Toutes les tables, index uniques et owned entities présents
Définition of Done :
- [ ] Code review approuvé
- [ ] Migration appliquée sur base de test sans erreur

**SUB — Créer la migration initiale**
Objectif : Générer la migration EF Core initiale couvrant toutes les entités du modèle.
Règles métier : Vérifier la présence de tous les index uniques (WeightEntry, SavedFoodItem, FoodItem.OffId) et des owned entities en colonnes.
Références : specs-techniques §Migrations
Critères d'acceptation :
- [ ] Toutes les tables créées
- [ ] Index uniques présents
- [ ] Owned entities en colonnes inline

**SUB — Préparer le premier import du dump OFF**
Objectif : Déclencher le premier import Open Food Facts au déploiement initial pour peupler la table FoodItem.
Règles métier : La table FoodItem doit être peuplée avant la mise en production.
Références : infrastructure-import-off.md
Critères d'acceptation :
- [ ] Table FoodItem peuplée après le premier déploiement

---

### STORY-022 — Abonnements & Templates (Infrastructure)

En tant que développeur, je veux mettre à jour la configuration EF Core pour les templates et créer les données initiales afin de rendre la fonctionnalité opérationnelle dès le premier déploiement.

Contexte : DietPlanConfiguration doit gérer UserId nullable et IsTemplate. 3 templates initiaux sont seedés en base.
Références : specs-fonctionnelles §Templates
Critères d'acceptation :
- [ ] UserId nullable configuré en base
- [ ] 3 templates initiaux présents au démarrage
Définition of Done :
- [ ] Code review approuvé
- [ ] Migration appliquée sans erreur

**SUB — Mettre à jour DietPlanConfiguration**
Objectif : Ajouter le support de UserId nullable, IsTemplate et un index sur IsTemplate.
Règles métier : UserId nullable → IsRequired(false). Index sur IsTemplate pour les requêtes de filtrage.
Références : specs-fonctionnelles §Templates
Critères d'acceptation :
- [ ] UserId nullable accepté en base
- [ ] Index sur IsTemplate créé

**SUB — Seed des templates initiaux**
Objectif : Insérer les 3 templates partagés initiaux au démarrage.
Règles métier : 3 templates : Équilibré (50/30/20), Protéiné (40/30/30), Keto (5/70/25). IsTemplate = true, UserId = null.
Références : specs-fonctionnelles §Templates
Critères d'acceptation :
- [ ] 3 templates présents en base après le premier déploiement

---

### STORY-023 — Configuration Hangfire

En tant que développeur, je veux configurer Hangfire avec stockage PostgreSQL et dashboard sécurisé afin de planifier et surveiller les jobs.

Contexte : Hangfire utilise le même PostgreSQL que l'application (schéma HangFire séparé). Le dashboard /hangfire est accessible aux administrateurs uniquement.
Références : infrastructure-hangfire.md
Critères d'acceptation :
- [ ] Jobs planifiés visibles et exécutables depuis le dashboard
- [ ] Dashboard accessible aux admins uniquement
Définition of Done :
- [ ] Code review approuvé

**SUB — Configurer Hangfire avec stockage PostgreSQL**
Objectif : Enregistrer Hangfire avec PostgreSqlStorage dans le schéma HangFire.
Règles métier : PrepareSchemaIfNecessary = true — crée le schéma automatiquement.
Références : infrastructure-hangfire.md
Critères d'acceptation :
- [ ] Hangfire démarre sans erreur avec le stockage PostgreSQL

**SUB — Sécuriser le dashboard Hangfire**
Objectif : Restreindre l'accès au dashboard /hangfire au rôle admin Keycloak.
Règles métier : Vérifier token JWT valide + claim realm_access.roles contient admin.
Références : infrastructure-keycloak-admin.md
Critères d'acceptation :
- [ ] Dashboard inaccessible sans token admin valide
- [ ] Dashboard accessible avec token admin valide

**SUB — Enregistrer les jobs récurrents au démarrage**
Objectif : Planifier l'import OFF (03h00) et la purge RGPD (03h30) au démarrage de l'application.
Règles métier : RecurringJob.AddOrUpdate pour chaque job — idempotent (pas de doublon si le job existe déjà).
Références : infrastructure-hangfire.md
Critères d'acceptation :
- [ ] Les 2 jobs apparaissent dans le dashboard Hangfire au démarrage

---

## Epic EPIC-004 — API Layer

---

### STORY-024 — UsersController

En tant qu'utilisateur, je veux gérer mon profil, mes pesées et mes aliments sauvegardés via l'API afin d'interagir avec le système depuis n'importe quel client.

Contexte : UsersController expose 12 endpoints sous /users/me. L'identité est extraite du token JWT (claim sub → User.KeycloakId).
Références : specs-fonctionnelles §2.1 | specs-frontend.md §Profil | workflow_mise-a-jour-profil.mermaid | workflow_gestion-poids.mermaid | workflow_rgpd.mermaid
Critères d'acceptation :
- [ ] Profil créable, lisible et modifiable
- [ ] Pesées ajoutables et listables
- [ ] Aliments sauvegardés gérables
- [ ] Endpoints RGPD (suppression, réactivation, export) opérationnels
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests API verts

**SUB — POST /users/me**
Objectif : Créer le profil utilisateur à la première connexion Keycloak.
Règles métier : Déclenché automatiquement côté client à la première connexion. UserId extrait du claim sub. 409 si profil déjà existant.
Références : specs-fonctionnelles §2.1
Critères d'acceptation :
- [ ] 201 Created + UserProfileResponse
- [ ] 409 si profil déjà existant

**SUB — GET /users/me**
Objectif : Retourner le profil de l'utilisateur authentifié avec BMR et TDEE calculés à la demande.
Règles métier : 404 si profil non encore créé.
Références : specs-fonctionnelles §2.1
Critères d'acceptation :
- [ ] 200 OK + UserProfileResponse avec Bmr et Tdee
- [ ] 404 si profil absent

**SUB — PUT /users/me**
Objectif : Mettre à jour les informations personnelles de l'utilisateur.
Règles métier : Seuls les champs fournis sont mis à jour.
Références : workflow_mise-a-jour-profil.mermaid
Critères d'acceptation :
- [ ] 200 OK + UserProfileResponse mis à jour

**SUB — POST /users/me/weight-entries**
Objectif : Ajouter une nouvelle pesée pour l'utilisateur.
Règles métier : 409 si une pesée existe déjà à cette date.
Références : workflow_gestion-poids.mermaid
Critères d'acceptation :
- [ ] 201 Created
- [ ] 409 si doublon même date

**SUB — GET /users/me/weight-entries**
Objectif : Retourner l'historique des pesées trié par date décroissante.
Références : workflow_gestion-poids.mermaid
Critères d'acceptation :
- [ ] 200 OK + List<WeightEntryResponse> triée par date DESC

**SUB — PUT /users/me/weight-entries/{id}**
Objectif : Modifier une pesée existante.
Règles métier : 404 si introuvable. 403 si n'appartient pas à l'utilisateur.
Références : workflow_gestion-poids.mermaid
Critères d'acceptation :
- [ ] 200 OK après mise à jour
- [ ] 403 si autre utilisateur, 404 si absent

**SUB — GET /users/me/saved-food-items**
Objectif : Retourner la liste personnelle d'aliments sauvegardés avec leur détail nutritionnel.
Références : specs-fonctionnelles §4
Critères d'acceptation :
- [ ] 200 OK + List<FoodItemSearchResponse>

**SUB — POST /users/me/saved-food-items**
Objectif : Sauvegarder un aliment dans la liste personnelle.
Règles métier : 404 si FoodItem inconnu. 409 si déjà sauvegardé.
Références : specs-fonctionnelles §4
Critères d'acceptation :
- [ ] 201 Created
- [ ] 404 si FoodItem inconnu, 409 si doublon

**SUB — DELETE /users/me/saved-food-items/{id}**
Objectif : Retirer un aliment de la liste personnelle.
Règles métier : 404 si introuvable. 403 si n'appartient pas à l'utilisateur.
Références : specs-fonctionnelles §4
Critères d'acceptation :
- [ ] 204 No Content
- [ ] 403 si autre utilisateur, 404 si absent

**SUB — DELETE /users/me, POST /users/me/reactivate, GET /users/me/export**
Objectif : Permettre la suppression RGPD du compte, sa réactivation pendant la grace period et l'export des données personnelles.
Règles métier : DELETE → soft delete + désactivation Keycloak. Réactivation bloquée si grace period expirée (400). Export contient toutes les données personnelles (RGPD Art. 17 et 20).
Références : workflow_rgpd.mermaid
Critères d'acceptation :
- [ ] DELETE → 204 No Content
- [ ] POST reactivate → 200 si dans la grace period, 400 sinon
- [ ] GET export → 200 + toutes les données personnelles en JSON

---

### STORY-025 — DietPlansController

En tant qu'utilisateur, je veux gérer mes plans alimentaires et en lancer un pour démarrer un régime via l'API.

Contexte : DietPlansController expose 5 endpoints sous /diet-plans. Le lancement crée une Diet active avec CalorieTarget calculé.
Références : specs-fonctionnelles §2.2 | specs-frontend.md §Plans | workflow_lancer-diet.mermaid
Critères d'acceptation :
- [ ] CRUD plans personnels opérationnel
- [ ] Lancement crée une Diet active (409 si Diet active existante, 422 si pas de pesée)
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests API verts

**SUB — POST /diet-plans et GET /diet-plans**
Objectif : Créer un nouveau plan alimentaire et lister les plans personnels de l'utilisateur.
Règles métier : Création retourne 201. Liste filtrée par l'utilisateur authentifié.
Références : specs-fonctionnelles §2.2
Critères d'acceptation :
- [ ] POST → 201 Created + DietPlanResponse
- [ ] GET → 200 OK + List<DietPlanResponse>

**SUB — PUT /diet-plans/{id} et DELETE /diet-plans/{id}**
Objectif : Modifier ou supprimer un plan alimentaire personnel.
Règles métier : 403 si n'appartient pas à l'utilisateur. 404 si introuvable.
Références : specs-fonctionnelles §2.2
Critères d'acceptation :
- [ ] PUT → 200 OK + DietPlanResponse mis à jour
- [ ] DELETE → 204 No Content
- [ ] 403 si autre utilisateur

**SUB — POST /diet-plans/{id}/launch**
Objectif : Lancer un plan et créer une Diet active avec CalorieTarget calculé.
Règles métier : 409 si Diet Active existante. 422 si aucune WeightEntry disponible pour le calcul BMR.
Références : workflow_lancer-diet.mermaid
Critères d'acceptation :
- [ ] 201 Created + DietResponse avec CalorieTarget calculé
- [ ] 409 si Diet Active existante
- [ ] 422 si aucune WeightEntry

---

### STORY-026 — DietsController

En tant qu'utilisateur, je veux consulter mes régimes, les terminer et accéder à mon bilan nutritionnel via l'API.

Contexte : DietsController expose 5 endpoints sous /diets. Le bilan est calculé à la demande — pas d'entité SavedBilan.
Références : specs-fonctionnelles §2.3 | specs-frontend.md §Diet active | workflow_terminer-diet.mermaid
Critères d'acceptation :
- [ ] Diet active lisible
- [ ] Historique des régimes lisible
- [ ] Clôture d'un régime opérationnelle
- [ ] Bilan nutritionnel calculé et retourné
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests API verts

**SUB — GET /diets/active et GET /diets**
Objectif : Retourner la Diet active courante et l'historique des régimes.
Règles métier : 404 si aucune Diet active. Historique trié par StartDate DESC.
Références : specs-fonctionnelles §2.3
Critères d'acceptation :
- [ ] GET active → 200 OK + DietResponse, 404 si aucune
- [ ] GET → 200 OK + List<DietResponse>

**SUB — GET /diets/{id} et POST /diets/{id}/archive**
Objectif : Retourner le détail d'un régime et permettre sa clôture.
Règles métier : 403 si n'appartient pas à l'utilisateur. 404 si introuvable. Archive → 400 si déjà Archived.
Références : workflow_terminer-diet.mermaid
Critères d'acceptation :
- [ ] GET → 200 OK + DietResponse
- [ ] POST archive → 200 OK + DietResponse avec EndDate
- [ ] 400 si déjà Archived

**SUB — GET /diets/{id}/bilan**
Objectif : Retourner le bilan nutritionnel d'un régime sur une période donnée.
Règles métier : Query params : period (day/week/month/full), date, startDate. Période clampée selon le tier.
Références : workflow_consulter-bilan.mermaid | specs-fonctionnelles §Bilan
Critères d'acceptation :
- [ ] 200 OK + NutritionBilanResponse (dailyData + weightEntries + summary)
- [ ] Période clampée selon le tier

---

### STORY-027 — MealsController

En tant qu'utilisateur, je veux créer et gérer mes repas ainsi que leurs aliments via l'API.

Contexte : MealsController expose 6 endpoints sous /meals. L'ajout et le retrait d'items modifient le repas existant.
Références : specs-fonctionnelles §3 | specs-frontend.md §Repas | workflow_enregistrer-repas.mermaid
Critères d'acceptation :
- [ ] CRUD repas opérationnel
- [ ] Ajout et retrait de MealItems opérationnels
- [ ] Dernier MealItem non supprimable (400)
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests API verts

**SUB — POST /meals, GET /meals et GET /meals/{id}**
Objectif : Créer un repas, lister les repas et consulter le détail d'un repas.
Règles métier : POST → 400 si aucun item. GET filtre par ?saved=true ou ?date=. GET /{id} → 403 si autre utilisateur.
Références : specs-fonctionnelles §3
Critères d'acceptation :
- [ ] POST → 201 Created + MealResponse avec NutritionInfo
- [ ] GET → 200 OK + List<MealResponse>
- [ ] GET /{id} → 200 OK + MealResponse, 403 si autre utilisateur

**SUB — DELETE /meals/{id}, POST /meals/{id}/items et DELETE /meals/{id}/items/{itemId}**
Objectif : Supprimer un repas, ajouter un aliment et retirer un aliment d'un repas.
Règles métier : DELETE repas → 403 si autre utilisateur. DELETE item → 400 si dernier item (invariant domaine). POST item → 201 + MealResponse mis à jour.
Références : workflow_enregistrer-repas.mermaid
Critères d'acceptation :
- [ ] DELETE repas → 204 No Content
- [ ] POST item → 201 + MealResponse mis à jour
- [ ] DELETE item → 204, 400 si dernier item

---

### STORY-028 — FoodItemsController

En tant qu'utilisateur, je veux rechercher des aliments par mot-clé via l'API afin de sélectionner ce que j'ai consommé.

Contexte : FoodItemsController expose un seul endpoint GET /food-items?search={motclé}. La recherche passe par Redis avant PostgreSQL.
Références : specs-fonctionnelles §4 | workflow_rechercher-aliment.mermaid
Critères d'acceptation :
- [ ] Résultats retournés depuis Redis ou PostgreSQL selon disponibilité du cache
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests API verts

**SUB — GET /food-items**
Objectif : Rechercher des aliments par mot-clé avec stratégie cache-first.
Règles métier : Paramètre ?search requis. Retourner une liste vide si aucun résultat.
Références : workflow_rechercher-aliment.mermaid
Critères d'acceptation :
- [ ] 200 OK + List<FoodItemSearchResponse>
- [ ] Résultats cohérents avec la base de données

---

### STORY-029 — Middleware HTTP

En tant que développeur, je veux des middlewares de validation JWT, de gestion des erreurs et de logging afin de centraliser les préoccupations transverses de l'API.

Contexte : 3 middlewares : JWT (validation + résolution User), Exception (mapping erreurs → codes HTTP), Logging (traçabilité des requêtes).
Références : specs-techniques §Middleware | infrastructure-keycloak-admin.md
Critères d'acceptation :
- [ ] Token invalide → 401 automatiquement
- [ ] Exceptions domaine mappées en codes HTTP corrects
- [ ] Toutes les requêtes loggées
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests API verts

**SUB — Validation JWT Keycloak et résolution User**
Objectif : Valider le token JWT Keycloak et résoudre l'identité de l'utilisateur depuis le claim sub.
Règles métier : Valider signature, audience et expiration. Extraire claim sub → résoudre User.KeycloakId → User.Id. Stocker dans HttpContext.
Références : infrastructure-keycloak-admin.md
Critères d'acceptation :
- [ ] Token absent → 401
- [ ] Token expiré → 401
- [ ] Token valide → User.Id disponible dans HttpContext

**SUB — Gestion globale des erreurs**
Objectif : Mapper les exceptions domaine et applicatives en codes HTTP standardisés.
Règles métier : ArgumentException → 400, UnauthorizedException → 401, ForbiddenException → 403, NotFoundException → 404, ConflictException → 409, autres → 500.
Références : specs-techniques §Middleware
Critères d'acceptation :
- [ ] Chaque type d'exception retourne le bon code HTTP
- [ ] Body de réponse contient un message d'erreur lisible

**SUB — Logging des requêtes**
Objectif : Tracer toutes les requêtes entrantes avec méthode, path, status et durée.
Règles métier : Logger : méthode HTTP, path, status code, durée en ms.
Références : specs-techniques §Middleware
Critères d'acceptation :
- [ ] Chaque requête produit une ligne de log avec les 4 informations

---

### STORY-030 — Auth & Templates — Endpoints

En tant qu'administrateur, je veux gérer les templates partagés et contrôler l'accès selon le tier via l'API.

Contexte : Nouveaux endpoints pour les templates partagés et le back-office admin. Accès conditionné par tier (Pro/Business) ou rôle admin Keycloak.
Références : specs-fonctionnelles §Templates | specs-fonctionnelles §Admin
Critères d'acceptation :
- [ ] GET /diet-plans/templates → 403 pour tier Free
- [ ] Endpoints /admin/** → 403 sans rôle admin
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests API verts

**SUB — GET /diet-plans/templates**
Objectif : Lister les templates partagés accessibles aux tiers Pro et Business.
Règles métier : 403 si tier Free.
Références : specs-fonctionnelles §Templates
Critères d'acceptation :
- [ ] 200 OK + List<DietPlanResponse> pour Pro/Business
- [ ] 403 pour tier Free

**SUB — POST et PUT /admin/diet-plans/templates**
Objectif : Permettre à l'administrateur de créer et modifier des templates partagés.
Règles métier : Rôle admin Keycloak requis (403 sinon).
Références : specs-fonctionnelles §Admin
Critères d'acceptation :
- [ ] POST → 201 Created si rôle admin
- [ ] PUT → 200 OK si rôle admin
- [ ] 403 sans rôle admin

**SUB — Réponses 403 avec message explicite sur le tier**
Objectif : Informer l'utilisateur du tier requis quand une fonctionnalité lui est inaccessible.
Règles métier : Body 403 : { message: "This feature requires a Pro subscription" }.
Références : specs-fonctionnelles §Abonnements
Critères d'acceptation :
- [ ] 403 retourne un message explicite sur le tier requis

---

### STORY-031 — AdminController

En tant qu'administrateur, je veux accéder aux KPIs et à l'état du système via l'API afin de surveiller la plateforme.

Contexte : AdminController expose 3 endpoints sous /admin. Tous nécessitent le rôle admin Keycloak.
Références : specs-fonctionnelles §Admin
Critères d'acceptation :
- [ ] Dashboard KPIs retourné
- [ ] État des jobs retourné
- [ ] 403 sans rôle admin sur tous les endpoints
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests API verts

**SUB — GET /admin/dashboard et GET /admin/system/health**
Objectif : Retourner les KPIs consolidés et l'état des jobs Hangfire.
Règles métier : Rôle admin requis. GET dashboard → KPIs utilisateurs + activité. GET health → statut jobs + count FoodItems.
Références : specs-fonctionnelles §Admin | infrastructure-hangfire.md
Critères d'acceptation :
- [ ] GET dashboard → 200 OK + KPIs
- [ ] GET health → 200 OK + statut jobs
- [ ] 403 sans rôle admin

**SUB — DELETE /admin/diet-plans/templates/{id}**
Objectif : Permettre la suppression d'un template partagé par l'administrateur.
Règles métier : Rôle admin requis. 404 si introuvable.
Références : specs-fonctionnelles §Admin
Critères d'acceptation :
- [ ] 204 No Content si rôle admin et template existant
- [ ] 403 sans rôle admin
- [ ] 404 si template introuvable

---

### STORY-032 — OpenAPI / Swagger UI

En tant que développeur, je veux une documentation API interactive afin de faciliter les tests et l'intégration des clients.

Contexte : Swagger UI disponible uniquement hors production. JWT Bearer configuré pour tester les endpoints protégés. Dashboard Hangfire exclu de la spec.
Références : specs-techniques §OpenAPI
Critères d'acceptation :
- [ ] Swagger UI accessible sur /swagger hors production
- [ ] JWT Bearer configurable depuis l'interface
- [ ] /hangfire absent de la spec OpenAPI
Définition of Done :
- [ ] Code review approuvé

**SUB — Configurer Swagger avec JWT Bearer et commentaires XML**
Objectif : Configurer AddSwaggerGen avec sécurité JWT Bearer et documentation XML générée depuis les commentaires de code.
Règles métier : Swagger désactivé en production. GenerateDocumentationFile = true sur les projets API et Application.
Références : specs-techniques §OpenAPI
Critères d'acceptation :
- [ ] Swagger UI accessible sur /swagger hors production
- [ ] Bouton Authorize disponible pour le JWT Bearer

**SUB — Exclure /hangfire de la spec OpenAPI**
Objectif : Empêcher les routes Hangfire d'apparaître dans swagger.json.
Règles métier : Configurer un filtre Swashbuckle pour exclure les routes /hangfire.
Références : specs-techniques §OpenAPI
Critères d'acceptation :
- [ ] Routes /hangfire absentes de swagger.json

---

## Epic EPIC-005 — Tests

---

### STORY-033 — Tests Unitaires Domain

En tant que développeur, je veux des tests unitaires couvrant les invariants du domaine afin de garantir leur respect au fil des modifications.

Contexte : Tests écrits avant le code de production (TDD). Couvrir les Value Objects, les invariants des entités et les comportements critiques.
Références : modele-domaine §Invariants | Regles-metier §Invariants
Critères d'acceptation :
- [ ] MacroDistribution : invariant somme 100% couvert
- [ ] NutritionInfo : calcul snapshot couvert
- [ ] Diet : immuabilité Active/Completed et StartDate système couverts
- [ ] Meal : rejet liste vide couvert
- [ ] SavedFoodItem et WeightEntry : validations constructeur couvertes
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests verts en CI

**SUB — Tester MacroDistribution**
Objectif : Vérifier que l'invariant somme = 100% est appliqué à la construction.
Règles métier : Somme != 100 → ArgumentException. Valeur négative → ArgumentException. Somme = 100 → instanciation réussie.
Références : modele-domaine §MacroDistribution
Critères d'acceptation :
- [ ] 40/30/30 → instanciation réussie
- [ ] 50/30/30 → ArgumentException (somme = 110)
- [ ] Valeur négative → ArgumentException

**SUB — Tester NutritionInfo**
Objectif : Vérifier le calcul du snapshot nutritionnel et le rejet des valeurs négatives.
Règles métier : Valeur négative → exception. Calcul : valeurs × quantité / 100.
Références : modele-domaine §NutritionInfo
Critères d'acceptation :
- [ ] Calcul snapshot correct (ex: 150g × 20g/100g = 30g)
- [ ] Valeur négative → exception

**SUB — Tester Diet — immuabilité et StartDate**
Objectif : Vérifier que Diet est immuable après lancement et que StartDate est imposée par le système.
Règles métier : Modification Active → InvalidOperationException. Modification Completed → InvalidOperationException. StartDate = date système à la création.
Références : modele-domaine §Diet
Critères d'acceptation :
- [ ] Rename sur Diet Active → InvalidOperationException
- [ ] ChangeDietStatus Active → Archived reste possible
- [ ] ChangeDietStatus Completed → exception
- [ ] StartDate == DateOnly.FromDateTime(DateTime.UtcNow)

**SUB — Tester Meal — rejet liste vide**
Objectif : Vérifier que Meal ne peut pas être créé sans MealItem et que le dernier item ne peut pas être retiré.
Règles métier : Liste vide → ArgumentException. Liste null → ArgumentException. RemoveMealItem sur 1 item → InvalidOperationException.
Références : modele-domaine §Meal
Critères d'acceptation :
- [ ] Création liste vide → ArgumentException
- [ ] Création liste null → ArgumentException
- [ ] RemoveMealItem dernier item → InvalidOperationException

**SUB — Tester SavedFoodItem et WeightEntry**
Objectif : Vérifier les validations de construction et l'immuabilité de ces entités.
Règles métier : WeightEntry : poids > 0, UserId non vide. SavedFoodItem : UserId non vide, FoodItemId non vide, SavedAt imposé système.
Références : modele-domaine §WeightEntry | modele-domaine §SavedFoodItem
Critères d'acceptation :
- [ ] WeightEntry poids <= 0 → exception
- [ ] SavedFoodItem avec Guid.Empty → exception

---

### STORY-034 — Tests Unitaires Application

En tant que développeur, je veux des tests unitaires couvrant les cas d'erreur des services applicatifs afin de garantir la gestion des règles métier cross-agrégat.

Contexte : Tests avec mocks (Moq). Couvrir les invariants cross-agrégat et les cas d'erreur métier des services.
Références : specs-fonctionnelles §Invariants
Critères d'acceptation :
- [ ] Doublon WeightEntry → 409 couvert
- [ ] Lancement Diet sans WeightEntry → 422 couvert
- [ ] Lancement avec Diet active existante → 409 couvert
- [ ] Doublon SavedFoodItem → 409 couvert
- [ ] Agrégation bilan journalier correcte couverte
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests verts en CI

**SUB — Tester UserService — doublon WeightEntry**
Objectif : Vérifier que UserService lève ConflictException si une WeightEntry existe déjà à cette date.
Règles métier : ExistsAsync(userId, date) → true → ConflictException (409).
Références : workflow_gestion-poids.mermaid
Critères d'acceptation :
- [ ] Mock ExistsAsync → true → ConflictException (409)

**SUB — Tester DietService — lancement sans WeightEntry et avec Diet active**
Objectif : Vérifier les deux cas de blocage du lancement d'un régime.
Règles métier : Aucune WeightEntry → exception 422. Diet Active existante → ConflictException (409).
Références : workflow_lancer-diet.mermaid
Critères d'acceptation :
- [ ] Mock GetLatestByUserId → null → exception 422
- [ ] Mock GetActiveByUserId → Diet existante → ConflictException (409)

**SUB — Tester MealService et FoodItemService — invariants cross-agrégat**
Objectif : Vérifier le rejet de Meal sans item et le rejet du doublon SavedFoodItem.
Règles métier : Items vides → ArgumentException domaine remonte. ExistsAsync doublon → ConflictException (409).
Références : specs-fonctionnelles §3 | specs-fonctionnelles §4
Critères d'acceptation :
- [ ] Items vides → ArgumentException
- [ ] Mock ExistsAsync doublon → ConflictException (409)

**SUB — Tester NutritionService — agrégation journalière**
Objectif : Vérifier que le bilan agrège correctement les MealItems par jour.
Règles métier : Repas sur 3 jours → dailyData avec 3 entrées et sommes correctes.
Références : specs-fonctionnelles §Bilan
Critères d'acceptation :
- [ ] dailyData contient 3 entrées pour 3 jours distincts
- [ ] Sommes Calories/Proteins/Carbs/Fats correctes par jour

**SUB — Tester SubscriptionGuard — restrictions tier**
Objectif : Vérifier les blocages par tier pour les plans, repas sauvegardés et SavedFoodItems.
Règles métier : Free : 3ème plan → 403. Free : templates → 403. Free : période bilan 30j → clampée à 7j.
Références : specs-fonctionnelles §Abonnements
Critères d'acceptation :
- [ ] Création 3ème plan Free → ForbiddenException (403)
- [ ] Accès templates Free → ForbiddenException (403)
- [ ] Période bilan Free clampée à 7j

---

### STORY-035 — Tests d'Intégration Infrastructure

En tant que développeur, je veux des tests d'intégration avec vraie base de données afin de valider le comportement réel des repositories et du cache.

Contexte : Testcontainers démarre un PostgreSQL réel et un Redis réel pour les tests. Les contraintes d'unicité en base sont vérifiées.
Références : specs-techniques §Tests
Critères d'acceptation :
- [ ] 7 repositories testés avec vraie base
- [ ] Contraintes d'unicité vérifiées en base
- [ ] Cache Redis testé avec vrai Redis
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests verts en CI

**SUB — Tester les repositories avec Testcontainers PostgreSQL**
Objectif : Valider le comportement des 7 repositories avec une vraie base de données PostgreSQL.
Règles métier : Appliquer les migrations avant les tests. Vérifier les contraintes d'unicité en base (WeightEntry, SavedFoodItem).
Références : specs-techniques §Tests
Critères d'acceptation :
- [ ] Les 7 repositories opérationnels avec vraie base
- [ ] Violation contrainte unicité → exception base de données

**SUB — Tester FoodCacheService avec Testcontainers Redis**
Objectif : Valider le comportement du cache avec un vrai Redis.
Règles métier : Cache miss → null. SetAsync + GetAsync → données retrouvées.
Références : specs-techniques §Tests
Critères d'acceptation :
- [ ] Cache miss retourne null
- [ ] Cache hit retourne les données mises en cache

**SUB — Tester le job import OFF avec dump de test**
Objectif : Valider que le job crée les FoodItems au premier import et les met à jour aux suivants.
Règles métier : Fichier dump de test (50 lignes). Premier passage → FoodItems créés. Second passage → FoodItems mis à jour.
Références : infrastructure-import-off.md
Critères d'acceptation :
- [ ] FoodItems créés au premier passage
- [ ] FoodItems mis à jour (UpdateFromImport) au second passage

---

### STORY-036 — Tests API Endpoints

En tant que développeur, je veux des tests end-to-end couvrant tous les endpoints afin de valider le comportement de l'API dans des conditions réelles.

Contexte : WebApplicationFactory + Testcontainers PostgreSQL. Couvrir cas nominaux et cas d'erreur pour chaque endpoint.
Références : specs-techniques §Tests
Critères d'acceptation :
- [ ] Cas nominaux (201/200/204) couverts pour tous les endpoints
- [ ] Cas d'erreur (400/401/403/404/409) couverts
- [ ] Validation JWT couverte
Définition of Done :
- [ ] Code review approuvé
- [ ] Tests verts en CI

**SUB — Tester tous les endpoints — cas nominaux et cas d'erreur**
Objectif : Valider le comportement HTTP de chaque endpoint dans les cas nominaux et d'erreur.
Règles métier : WebApplicationFactory<Program> + Testcontainers PostgreSQL réel.
Références : specs-techniques §Tests
Critères d'acceptation :
- [ ] 201, 200, 204 pour les cas nominaux
- [ ] 400, 403, 404, 409 pour les cas d'erreur correspondants

**SUB — Tester la validation JWT**
Objectif : Vérifier que les endpoints protégés rejettent les tokens invalides.
Règles métier : Absent → 401. Expiré → 401. Valide sans profil → 404. Valide avec profil → 200.
Références : infrastructure-keycloak-admin.md
Critères d'acceptation :
- [ ] Token absent → 401
- [ ] Token expiré → 401
- [ ] Token valide + profil existant → 200

**SUB — Tester les endpoints admin et restrictions tier**
Objectif : Vérifier les protections admin et les blocages par tier dans les tests API.
Règles métier : Sans rôle admin → 403 sur /admin/**. Tier Free → 403 sur /diet-plans/templates.
Références : specs-fonctionnelles §Admin | specs-fonctionnelles §Abonnements
Critères d'acceptation :
- [ ] /admin/** sans rôle admin → 403
- [ ] GET /diet-plans/templates tier Free → 403
