# PROJECT_CONTEXT — shift-pilot-py

> Confiance : high

## Résumé exécutif

`shift-pilot-py` est un **pilote de démonstration** d'une logistique d'entrepôt écrit en **Python 3 pur** (stdlib uniquement). Il modélise deux domaines métier : la **gestion du stock d'entrepôt** et la **préparation de commande**. Le projet est intentionnellement minimaliste — pas de base de données, pas de couche web, pas de dépendances externes. C'est un livrable pédagogique qui démontre l'outillage d'onboarding sur une stack non-JavaScript, avec un traitement robuste de l'allocation multi-article et du signalement de pénurie.

## Contexte métier

Le projet répond à la question : « Comment modéliser et tester une logistique d'entrepôt ? » Le contexte fonctionnel est une entreprise de distribution qui doit :

1. **Tenir un référentiel du stock en entrepôt** avec quatre articles fictifs (Ancre, Bouée, Cordage, Dérive), chacun localisé dans une zone (A, B, C), porteur d'une quantité brute et d'une quantité réservée (committée aux clients, mais pas encore prélevée).
2. **Calculer la disponibilité réelle à la vente** pour chaque article : stock brut moins quantité réservée. **Règle forte : cette disponibilité doit être ≥ 0**, puisqu'on ne peut pas vendre ce qu'on n'a pas. Implémentation : `max(0, qty - reserved)`.
3. **Vérifier qu'une commande peut être honorée** avant de lancer un prélèvement physique : pour chaque SKU demandé, il faut une disponibilité suffisante. Validation : demandes nulles/négatives rejetées.
4. **Générer une liste de prélèvement** ordonnée par zone d'entrepôt, tout en gérant les commandes multi-lignes du même SKU sans surallocation. Signalement des pénuries pour chaque ligne non servie.

## Domaines clés

Deux domaines métier, décrits dans `CARTE_DES_DOMAINES.md` :

### Entrepôt-stock (cœur)
- Référentiel des articles : SKU, label, quantité brute, quantité réservée, zone.
- Opérations : consultation (par SKU, par zone), calcul de disponibilité à la vente.
- Porteur du bug volontaire.

### Préparation-commande (support)
- Décision de faisabilité d'une commande pour une quantité demandée.
- Génération d'une liste de prélèvement triée par zone.
- Consomme entièrement le domaine entrepôt-stock.

## Stack technique

- **Langage** : Python 3 (stdlib uniquement, zéro dépendance tierce). Les `.pyc` compilés reflètent la version locale du développeur ; le code lui-même est agnostique à 3.12 vs 3.13.
- **Tests** : `unittest` (standard library).
- **Persistance** : aucune — données en mémoire.
- **Exposition** : aucune — fonctions Python pures, pas d'API REST ni CLI.
- **Outillage** : pas de CI, pas de linting configuré.

## Points d'attention

### Robustesse de l'allocation
La fonction `picking_list()` implémente une allocation cumulée par article. Si une commande contient plusieurs lignes du même SKU, l'allocation est suivi ligne par ligne : une première ligne consomme de la disponibilité, et les lignes suivantes du même SKU voient leur disponibilité réduite. Les pénuries sont signalées explicitement dans `skipped`.

**Propriété assurée** : pas de surallocation possible. Si vous demandez 30+30 d'un article avec une disponibilité de 40, vous obtenez 30 allouées et 30 refusées (pénurie de 20).

### Absence d'orchestrateur de commande
Le code expose deux fonctions indépendantes : `can_fulfil()` (décision par article) et `picking_list()` (allocation multi-article). Aucune fonction n'enchaîne les deux — c'est au caller de décider la stratégie (vérifier chaque ligne avant d'appeler `picking_list()`, ou accepter l'allocation partielle). La lacune est documentée comme question ouverte dans l'audit fonctionnel.

### Absence de couche d'exposition
Le projet est une bibliothèque Python pure. Aucune route HTTP, aucune CLI, aucun point d'entrée utilisateur.

### Unicité du SKU non garantie
Le modèle de données est implicite — une liste Python de dicts sans schéma déclaré. `find_by_sku()` retourne le premier match, et l'unicité n'est pas vérifiée.

### État actuel des tests
- `inventory/warehouse.py` : 6 tests exécutés (tous verts).
- `inventory/orders.py` : 10 tests exécutés (tous verts, couvrant `picking_list()` en intégralité).
- **Total** : 16 tests. **Couverture** : `picking_list()` complètement couverte ; `can_fulfil()` n'a aucun test direct ni indirect (pas appelée dans la suite de test ; utilisable au niveau du client, pas validée par la suite actuelle).

## Dépôt et source de vérité

Le dépôt est complet et auto-contenu :
- Code source : `inventory/warehouse.py` (29 lignes), `inventory/orders.py` (47 lignes).
- Tests : `tests/test_warehouse.py` (42 lignes, 6 tests), `tests/test_orders.py` (92 lignes, 10 tests).
- Documentation : `README.md` (15 lignes), `CARTE_DES_DOMAINES.md` (61 lignes).
- Aucune dépendance externe, aucune base de données.

## Pistes identifiées pour évolution (non décidées)

Aucune roadmap formelle n'est documentée. Les audits et workflows ont identifié des sujets ouverts pour une future évolution :

1. **Orchestrateur de commande** : enchaîner `can_fulfil()` puis `picking_list()` pour une logique complète de vérification + prélèvement.
2. **Couverture de tests complétée pour `picking_list()`** : tous les cas d'allocation et surallocation sont testés (10 tests). `can_fulfil()` reste sans test direct ni indirect (utilisable au niveau du client, pas validée par la suite actuelle).
3. **Couche d'exposition** : API HTTP ou CLI pour l'accès aux domaines (actuellement : fonctions Python pures seulement).
4. **Mécanisme de réservation/mise à jour** : permettre l'altération du stock au-delà de la lecture actuelle.
5. **Persistance** : survie des données entre redémarrages du processus.

**Statut** : aucune de ces pistes n'est décidée ni engagée. Elles figurent à titre de questions ouvertes, pas comme décisions du projet.

## Questions non tranchées

- La séparation `warehouse.py / orders.py` est-elle définitive, ou est-elle un découpage exploratoire ?
- Les zones d'entrepôt (actuellement A, B, C) peuvent-elles évoluer vers des codes multi-caractères (A1, B-12) ? Cela affecte la robustesse du tri lexicographique.
- **Note historique** : Le bug intentionnel sur `available_qty` (absence de borne inférieure) a été corrigé lors de l'onboarding (implémentation `max(0, ...)`). Les tests assocés passent tous (16 verts).

## Livrables d'onboarding

Ce pilote marque l'accomplissement de l'étape d'onboarding par :
- ✓ Carte des domaines complète et validée.
- ✓ Trois workflows documentés et relus (consultation stock, vérification faisabilité, génération prélèvement).
- ✓ Audits transverses réalisés (fonctionnel, données, architecture, tests, sécurité, hotspots).
- ✓ Bug volontaire (`available_qty` sans borne inférieure) isolé, corrigé et testé (16 tests verts).
- ✓ Documents de référence (contexte, CDC, cartographie code, cahier de recette).

**Hors scope d'onboarding** : couche d'exposition (HTTP, CLI), orchestrateur de commande, couverture de tests complète (notamment `can_fulfil()` non testé directement ; `list_items()` non testé).
