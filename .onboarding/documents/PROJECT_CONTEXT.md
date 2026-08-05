# PROJECT_CONTEXT — shift-pilot-py

> Confiance : high

## Résumé exécutif

`shift-pilot-py` est un **pilote de démonstration** d'une logistique d'entrepôt écrit en **Python 3 pur** (stdlib uniquement). Il modélise deux domaines métier : la **gestion du stock d'entrepôt** et la **préparation de commande**. Le projet est intentionnellement minimaliste — pas de base de données, pas de couche web, pas de dépendances externes. C'est un livrable pédagogique qui démontre l'outillage d'onboarding sur une stack non-JavaScript.

## Contexte métier

Le projet répond à la question : « Comment modéliser et tester une logistique d'entrepôt ? » Le contexte fonctionnel est une entreprise de distribution qui doit :

1. **Tenir un référentiel du stock en entrepôt** avec quatre articles fictifs (Ancre, Bouée, Cordage, Dérive), chacun localisé dans une zone (A, B, C), porteur d'une quantité brute et d'une quantité réservée (committée aux clients, mais pas encore prélevée).
2. **Calculer la disponibilité réelle à la vente** pour chaque article : stock brut moins quantité réservée. **Règle forte : cette disponibilité doit être ≥ 0**, puisqu'on ne peut pas vendre ce qu'on n'a pas.
3. **Vérifier qu'une commande peut être honorée** avant de lancer un prélèvement physique : pour chaque SKU demandé, il faut une disponibilité suffisante.
4. **Générer une liste de prélèvement** ordonnée par zone d'entrepôt, pour minimiser les déplacements du préparateur.

Ce modèle de données inclut un cas limite : l'article `CX-330` porte 45 unités en stock mais 50 unités réservées. La disponibilité à la vente doit être bornée à 0 (rupture), ce que le code implémente correctement via `max(0, qty - reserved)`.

## Domaines clés

Deux domaines métier, décrits dans `CARTE_DES_DOMAINES.md` :

### Entrepôt-stock (cœur)
- Référentiel des articles : SKU, label, quantité brute, quantité réservée, zone.
- Opérations : consultation (par SKU, par zone), calcul de disponibilité à la vente (borné à zéro).

### Préparation-commande (support)
- Décision de faisabilité d'une commande pour une quantité demandée.
- Génération d'une liste de prélèvement triée par zone.
- Consomme entièrement le domaine entrepôt-stock.

## Stack technique

- **Langage** : Python 3 (stdlib uniquement, zéro dépendance tierce). **Incertitude non résolue** : le dépôt contient des `.pyc` compilés pour Python 3.13 (`inventory/__pycache__/__init__.cpython-313.pyc`), mais la carte des domaines mentionne Python 3.12. La version réellement ciblée n'est pas stabilisée. *Voir audit testing pour détails.*
- **Tests** : `unittest` (standard library).
- **Persistance** : aucune — données en mémoire.
- **Exposition** : aucune — fonctions Python pures, pas d'API REST ni CLI.
- **Outillage** : pas de CI, pas de linting configuré.

## Points d'attention

### Calcul de disponibilité borné à zéro
La fonction `available_qty()` retourne `max(0, qty - reserved)` pour assurer que la disponibilité est toujours non-négative. Pour `CX-330` (qty=45, reserved=50), cela donne `0` (rupture). Ce comportement est documenté et testé (`test_available_qty_never_negative` est vert).

### Orchestration intégrée dans picking_list
`picking_list()` appelle désormais `can_fulfil()` en interne pour chaque ligne avant inclusion. Les lignes avec stock insuffisant sont exclues silencieusement. L'appelant n'a plus besoin de coordonner les deux fonctions pour la sécurité d'un prélèvement.

### Absence de couche d'exposition
Le projet est une bibliothèque Python pure. Aucune route HTTP, aucune CLI, aucun point d'entrée utilisateur.

### Unicité du SKU non garantie
Le modèle de données est implicite — une liste Python de dicts sans schéma déclaré. `find_by_sku()` retourne le premier match, et l'unicité n'est pas vérifiée.

### Couverture de test
- `inventory/warehouse.py` : 3 tests (tous verts).
- `inventory/orders.py` : 7 tests couvrant `picking_list` (tous verts). `can_fulfil` est couvert indirectement.

## Dépôt et source de vérité

Le dépôt est complet et auto-contenu :
- Code source : `inventory/warehouse.py` (34 lignes), `inventory/orders.py` (22 lignes).
- Tests : `tests/test_warehouse.py` (warehouse), `tests/test_orders.py` (7 cas pour `picking_list`).
- Documentation : `README.md` (15 lignes), `CARTE_DES_DOMAINES.md` (61 lignes).
- Aucune dépendance externe, aucune base de données.

## Pistes identifiées pour évolution (non décidées)

Aucune roadmap formelle n'est documentée. Les audits et workflows ont identifié des sujets ouverts pour une future évolution :

1. **Orchestrateur de commande** : enchaîner `can_fulfil()` puis `picking_list()` pour une logique complète de vérification + prélèvement.
2. **Couverture de tests** : compléter les tests pour `can_fulfil()` directement et les cas limites de `picking_list()` (robustesse, entrées invalides).
3. **Couche d'exposition** : API HTTP ou CLI pour l'accès aux domaines (actuellement : fonctions Python pures seulement).
4. **Mécanisme de réservation/mise à jour** : permettre l'altération du stock au-delà de la lecture actuelle.
5. **Persistance** : survie des données entre redémarrages du processus.

**Statut** : aucune de ces pistes n'est décidée ni engagée. Elles figurent à titre de questions ouvertes, pas comme décisions du projet.

## Questions non tranchées

- La séparation `warehouse.py / orders.py` est-elle définitive, ou est-elle un découpage exploratoire ?
- Les zones d'entrepôt (actuellement A, B, C) peuvent-elles évoluer vers des codes multi-caractères (A1, B-12) ? Cela affecte la robustesse du tri lexicographique.

## Livrables d'onboarding

Ce pilote marque l'accomplissement de l'étape d'onboarding par :
- ✓ Carte des domaines complète et validée.
- ✓ Trois workflows documentés et relus (consultation stock, vérification faisabilité, génération prélèvement).
- ✓ Audits transverses réalisés (fonctionnel, données, architecture, tests, sécurité, hotspots).
- ✓ Invariants métier implémentés (disponibilité bornée à zéro), test en place et vert.
- ✓ Documents de référence (contexte, CDC, cartographie code, cahier de recette).

**Hors scope d'onboarding** : couche d'exposition (HTTP, CLI), orchestrateur de commande, tests complets sur tous les modules.
