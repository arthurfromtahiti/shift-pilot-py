# Fonctionnel — Audit

> Confiance : high

## Compréhension globale

`shift-pilot-py` implémente deux domaines fonctionnels (carte des domaines validée) : la gestion du stock d'entrepôt (`warehouse.py`) et la préparation de commande (`orders.py`). Le périmètre fonctionnel est intentionnellement réduit à un pilote de démonstration. Trois workflows ont été documentés et relus : consultation du stock, vérification de faisabilité de commande, génération de la liste de prélèvement. L'audit fonctionnel vérifie la cohérence entre ce que le code fait réellement et ce que les workflows décrivent.

## Résumé exécutif

Le code est cohérent avec les workflows documentés — chaque comportement décrit correspond à une implémentation lisible dans le source. Deux changements majeurs structurent l'état actuel : **`picking_list()` vérifie la disponibilité et journalise les lignes non servies** (correctifs SHIAAAAAAAAAAAAAAAAAAAAAAAA-316 et SHIAAAAAAAAAAAAAAAAAAAAAAAA-442), et **le cycle bug-volontaire est abouti** — `available_qty()` retourne `max(0, qty - reserved)` et `CX-330` a désormais `reserved=5 → disponible=40`. `picking_list()` n'appelle pas `can_fulfil()` ; elle implémente sa propre vérification via un dict `allocated` indexé sur le SKU canonique (correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-507). Il n'y a toujours pas d'orchestrateur qui enchaîne les deux fonctions de façon visible, mais elles sont complètement indépendantes.

## Constats détaillés

**VÉRIFIÉ_CODE — Workflow CONSULTATION_STOCK : couverture complète.** Les quatre fonctions décrites dans le workflow (`list_items`, `find_by_sku`, `available_qty`, `items_in_zone`) existent et leur code source est cohérent avec le workflow documenté (`inventory/warehouse.py:11-28`). `available_qty()` retourne `max(0, item["qty"] - item["reserved"])` (`inventory/warehouse.py:24`) — le correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-231 est appliqué, l'invariant `disponible ≥ 0` est garanti. Le workflow réconcilié (WORKFLOW_CONSULTATION_STOCK.md) confirme l'absence du bug. Pas d'écart entre description et implémentation.

**VÉRIFIÉ_CODE — Workflow FAISABILITE_COMMANDE : couverture complète.** `can_fulfil(sku, requested)` existe (`inventory/orders.py:6-12`), appelle `find_by_sku` puis `available_qty`, retourne un booléen. Le comportement sur SKU inconnu (retour `False`) est implémenté (`inventory/orders.py:9-11`). `available_qty()` retourne `max(0, qty - reserved)` — pas de bug hérité actif. Le workflow réconcilié confirme l'absence du bug. Pas d'écart entre description et implémentation.

**VÉRIFIÉ_CODE — Workflow PRELEVEMENT_COMMANDE : couverture complète, vérification de disponibilité intégrée.** `picking_list(lines)` existe (`inventory/orders.py:15-46`). Pour chaque ligne, elle appelle `find_by_sku()` pour récupérer l'article (`inventory/orders.py:31-33`), puis vérifie la disponibilité via `remaining = available_qty(item) - allocated.get(canonical, 0)` et inscrit dans `skipped` si `qty > remaining` (`inventory/orders.py:35-43`). Elle accumule les allocations par SKU **canonique** (clé normalisée en majuscules via `item["sku"]`) dans un dict `allocated` pour gérer plusieurs lignes du même SKU dans la même commande, y compris avec des casses différentes (`inventory/orders.py:34, 44`). Elle effectue le tri final par zone (`inventory/orders.py:46`). Elle ignore silencieusement les SKUs inconnus et les quantités invalides (sans entrée dans `skipped`). Ces comportements correspondent exactement à leur description dans le workflow mis à jour.

**VÉRIFIÉ_CODE — Lacune fonctionnelle : pas d'orchestrateur de commande.** Le workflow complet de traitement d'une commande supposerait : (1) vérifier chaque ligne avec `can_fulfil()`, (2) générer la liste de prélèvement avec `picking_list()`. Aucune fonction n'enchaîne ces deux étapes. Il n'y a pas de point d'entrée de commande complet dans le code. Cette lacune est notée dans les questions ouvertes du workflow PRELEVEMENT_COMMANDE mais n'est pas une erreur — c'est une omission assumée du pilote.

**VÉRIFIÉ_CODE — `picking_list()` exclut les articles en rupture et journalise les lignes non servies.** `picking_list()` vérifie la disponibilité via `remaining = available_qty(item) - allocated.get(canonical, 0)` et inscrit dans `skipped` (avec `order_id`, `sku`, `qty_requested`, `qty_missing`) si `qty > remaining` (`inventory/orders.py:35-43`). `CX-330` (qty=45, reserved=5, available=40) sera correctement exclu si la demande dépasse sa disponibilité et journalisé dans `skipped`. Cette vérification est intégrée à `picking_list()` elle-même, sans appel à `can_fulfil()` — les deux fonctions sont indépendantes. La clé canonique `item["sku"]` garantit que deux lignes avec la même référence en casse différente sont cumulées sur le même article.

**VÉRIFIÉ_CODE — Stock en lecture seule : aucune mutation d'article implémentée.** Il n'existe aucune fonction pour créer, modifier ou supprimer un article de `ITEMS`. Le stock est immuable fonctionnellement (même si la liste Python est mutable techniquement). Aucun workflow de mise à jour de stock n'est implémenté, aucun n'est documenté.

**VÉRIFIÉ_CODE — Aucune couche d'exposition.** Il n'y a ni CLI, ni API REST, ni interface utilisateur. Les fonctions sont accessibles uniquement par import Python direct. Fonctionnellement, le pilote est une bibliothèque sans point d'entrée utilisateur.

## Forces

- **Cohérence code-workflow : totale.** Les trois workflows documentés correspondent précisément au code lu. Aucun écart entre description et implémentation.
- **Invariant métier traçable de bout en bout.** `CX-330` est identifié dans les données avec une réservation correcte (qty=45, reserved=5, available=40 après le correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-231), géré correctement par `available_qty()` qui retourne `max(0, ...)`, couvert par un test (`test_available_qty_cx330`, `tests/test_warehouse.py:14`), et documenté dans les workflows et la carte des domaines. C'est une démonstration complète d'un invariant métier et de sa validation.
- **Séparation fonctionnelle claire.** Le stock (lecture pure) et la préparation de commande (logique dérivée) sont deux modules distincts avec des responsabilités non mélangées.

## Dettes techniques

- **Pas d'orchestrateur explicite de commande.** L'enchaînement logique `can_fulfil()` → `picking_list()` est maintenant cohérent au niveau du code, mais il n'y a pas de point d'entrée unique qui les orchestrerait. Un appelant doit les invoquer séquentiellement, sans exemple ni guide.
- **Aucune mutation de stock.** Pas de `reserve()`, `release()`, ni `update_qty()`. Le stock est figé à l'initialisation, ce qui rend le pilote non réaliste pour une logistique réelle (les réservations doivent être mises à jour après un prélèvement).
- **Couverture de tests bonne sur `orders.py`, lacunaire sur `can_fulfil()`.** 10 tests couvrent désormais `picking_list()` dans `tests/test_orders.py` (articles hors stock, journalisation `skipped`, cumul intra-commande, insensibilité à la casse, quantités nulles/négatives, tri par zone). `can_fulfil()` reste entièrement non testé.

## Zones critiques

- **Absence de point de coordination visible entre `can_fulfil` et `picking_list`** — Bien que les deux fonctions soient maintenant cohérentes (toutes deux rejettent les articles indisponibles), il n'y a pas de fonction unique qui les orchestrerait. Un futur développeur pourrait ne pas réaliser qu'elles doivent être utilisées ensemble pour un résultat complet.

## Risques

- **VÉRIFIÉ_CODE — Vérification de faisabilité intégrée à `picking_list()`.** Après le correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-316, `picking_list()` vérifie la disponibilité via un dict `allocated` cumulatif (sans appel à `can_fulfil()`) et exclut les articles non faisables. D'après le code lu, un appelant qui appelle `picking_list()` directement obtiendra une liste de prélèvement structurellement cohérente avec le stock disponible au moment de l'appel — les articles en rupture sont exclus et les SKUs dupliqués sont cumulés. Cette propriété est garantie par la logique lue dans le code source (`inventory/orders.py:15-46`) ; elle n'a pas été vérifiée par exécution dans cet audit. Le risque antérieur est éliminé d'après la lecture du code.
- **HYPOTHÈSE — Données périmées dès le premier prélèvement réel.** `ITEMS` ne se met jamais à jour : après un prélèvement réel de 10 unités d'`AX-100`, le stock reste affiché à 12. Pour un pilote de démonstration, c'est attendu ; pour un usage réel, c'est une incohérence fonctionnelle critique.

## Recommandations priorisées

1. **Ajouter des tests pour `can_fulfil()`** — Documenter par les tests le comportement de `can_fulfil()` directement (SKU connu disponible, SKU inconnu, quantité nulle/négative, SKU en rupture). (`tests/test_orders.py`)
2. **Clarifier la docstring de `picking_list()`** — Le commentaire de docstring est présent et correct depuis le correctif 316 (`inventory/orders.py:16-20`), décrivant le cumul intra-commande. À maintenir.
3. **Envisager un mécanisme de réservation / mise à jour de stock** — Même symbolique (une fonction `reserve(sku, qty)` qui modifie `reserved` en mémoire), pour rendre le pilote fonctionnellement plus réaliste.

## Questions ouvertes

- L'orchestrateur de commande (enchaînement `can_fulfil` + `picking_list`) est-il prévu dans le périmètre du pilote, ou délibérément absent (exercice pour l'apprenant) ?
- La gestion des réservations (`reserved`) est-elle censée rester en lecture seule dans ce pilote, ou une fonction de mise à jour est-elle prévue ?
- Le pilote est-il conçu pour rester une bibliothèque pure, ou une couche CLI ou HTTP est-elle prévue comme prochaine étape ?
