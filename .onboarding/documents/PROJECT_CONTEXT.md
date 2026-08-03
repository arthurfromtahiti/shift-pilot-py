# PROJECT_CONTEXT — shift-pilot-py

> Confiance : high

## Résumé exécutif

`shift-pilot-py` est un **pilote de démonstration** d'une logistique d'entrepôt écrit en **Python 3 pur** (stdlib uniquement). Il modélise deux domaines métier : la **gestion du stock d'entrepôt** et la **préparation de commande**. Le projet est intentionnellement minimaliste — pas de base de données, pas de couche web, pas de dépendances externes — avec un **bug volontaire** encodé et un **test rouge intentionnel** pour signaler une violation d'invariant. C'est un livrable pédagogique qui démontre l'outillage d'onboarding sur une stack non-JavaScript.

## Contexte métier

Le projet répond à la question : « Comment modéliser et tester une logistique d'entrepôt ? » Le contexte fonctionnel est une entreprise de distribution qui doit :

1. **Tenir un référentiel du stock en entrepôt** avec quatre articles fictifs (Ancre, Bouée, Cordage, Dérive), chacun localisé dans une zone (A, B, C), porteur d'une quantité brute et d'une quantité réservée (committée aux clients, mais pas encore prélevée).
2. **Calculer la disponibilité réelle à la vente** pour chaque article : stock brut moins quantité réservée. **Règle forte : cette disponibilité doit être ≥ 0**, puisqu'on ne peut pas vendre ce qu'on n'a pas.
3. **Vérifier qu'une commande peut être honorée** avant de lancer un prélèvement physique : pour chaque SKU demandé, il faut une disponibilité suffisante.
4. **Générer une liste de prélèvement** ordonnée par zone d'entrepôt, pour minimiser les déplacements du préparateur.

Cet objectif métier se heurte volontairement à un **bug intentionnel** : l'article `CX-330` porte 45 unités en stock mais 50 unités réservées, ce qui produit une disponibilité de **-5** (négative). Le code n'est pas corrigé : c'est le signal pédagogique central.

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

- **Langage** : Python 3 (stdlib uniquement, zéro dépendance tierce). **Incertitude non résolue** : le dépôt contient des `.pyc` compilés pour Python 3.13 (`inventory/__pycache__/__init__.cpython-313.pyc`), mais la carte des domaines mentionne Python 3.12. La version réellement ciblée n'est pas stabilisée. *Voir audit testing pour détails.*
- **Tests** : `unittest` (standard library).
- **Persistance** : aucune — données en mémoire.
- **Exposition** : aucune — fonctions Python pures, pas d'API REST ni CLI.
- **Outillage** : pas de CI, pas de linting configuré.

## Points d'attention

### Bug volontaire — `available_qty` ne borne pas à zéro
La fonction `available_qty()` retourne `qty - reserved` sans vérifier que le résultat est positif. Pour `CX-330` (qty=45, reserved=50), cela donne `-5`. C'est intentionnel et documenté. Un test rouge explicite (`test_available_qty_never_negative`) encode l'invariant attendu et échoue pour le signaler.

**Impact** : `can_fulfil()` absorbe correctement ce négatif (toute demande >= 0 retourne `False`), mais un futur appelant qui appellerait `picking_list()` directement sans `can_fulfil()` générerait une liste de prélèvement sur un article en rupture.

### Absence d'orchestrateur de commande
Le code expose deux fonctions indépendantes : `can_fulfil()` (vérification) et `picking_list()` (génération). Il n'existe aucune fonction qui enchaîne les deux — c'est au caller de coordonner. La lacune est documentée comme question ouverte dans l'audit fonctionnel.

### Absence de couche d'exposition
Le projet est une bibliothèque Python pure. Aucune route HTTP, aucune CLI, aucun point d'entrée utilisateur.

### Unicité du SKU non garantie
Le modèle de données est implicite — une liste Python de dicts sans schéma déclaré. `find_by_sku()` retourne le premier match, et l'unicité n'est pas vérifiée.

### Tests incomplets
- `inventory/warehouse.py` : 3 tests exécutés (2 verts, 1 rouge intentionnel).
- `inventory/orders.py` : zéro test. Les deux fonctions critiques (`can_fulfil`, `picking_list`) n'ont aucune couverture de test.

## Dépôt et source de vérité

Le dépôt est complet et auto-contenu :
- Code source : `inventory/warehouse.py` (34 lignes), `inventory/orders.py` (22 lignes).
- Tests : `tests/test_warehouse.py` (22 lignes, couvre warehouse uniquement).
- Documentation : `README.md` (15 lignes), `CARTE_DES_DOMAINES.md` (61 lignes).
- Aucune dépendance externe, aucune base de données.

## Pistes identifiées pour évolution (non décidées)

Aucune roadmap formelle n'est documentée. Les audits et workflows ont identifié des sujets ouverts pour une future évolution :

1. **Orchestrateur de commande** : enchaîner `can_fulfil()` puis `picking_list()` pour une logique complète de vérification + prélèvement.
2. **Couverture de tests** : implémenter les tests manquants pour `can_fulfil()` et `picking_list()` (actuellement 0% couverture sur `orders.py`).
3. **Couche d'exposition** : API HTTP ou CLI pour l'accès aux domaines (actuellement : fonctions Python pures seulement).
4. **Mécanisme de réservation/mise à jour** : permettre l'altération du stock au-delà de la lecture actuelle.
5. **Persistance** : survie des données entre redémarrages du processus.

**Statut** : aucune de ces pistes n'est décidée ni engagée. Elles figurent à titre de questions ouvertes, pas comme décisions du projet.

## Questions non tranchées

- Le bug `available_qty` est-il prévu pour être corrigé à la fin du pilote, ou rester volontairement cassé ?
- Le test rouge doit-il rester rouge indéfiniment, ou devenir vert une fois le bug corrigé ?
- La séparation `warehouse.py / orders.py` est-elle définitive, ou est-elle un découpage exploratoire ?
- Les zones d'entrepôt (actuellement A, B, C) peuvent-elles évoluer vers des codes multi-caractères (A1, B-12) ? Cela affecte la robustesse du tri lexicographique.

## Livrables d'onboarding

Ce pilote marque l'accomplissement de l'étape d'onboarding par :
- ✓ Carte des domaines complète et validée.
- ✓ Trois workflows documentés et relus (consultation stock, vérification faisabilité, génération prélèvement).
- ✓ Audits transverses réalisés (fonctionnel, données, architecture, tests, sécurité, hotspots).
- ✓ Bug volontaire isolé et documenté, test rouge en place.
- ✓ Documents de référence (contexte, CDC, cartographie code, cahier de recette).

**Hors scope d'onboarding** : couche d'exposition (HTTP, CLI), orchestrateur de commande, tests complets sur tous les modules.
