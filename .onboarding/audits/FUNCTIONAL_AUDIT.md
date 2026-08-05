# Fonctionnel — Audit

> Confiance : high

## Compréhension globale

`shift-pilot-py` implémente deux domaines fonctionnels (carte des domaines validée) : la gestion du stock d'entrepôt (`warehouse.py`) et la préparation de commande (`orders.py`). Le périmètre fonctionnel est intentionnellement réduit à un pilote de démonstration. Trois workflows ont été documentés et relus : consultation du stock, vérification de faisabilité de commande, génération de la liste de prélèvement. L'audit fonctionnel vérifie la cohérence entre ce que le code fait réellement et ce que les workflows décrivent.

## Résumé exécutif

Le code est cohérent avec les workflows documentés — chaque comportement décrit correspond à une implémentation lisible dans le source. Un changement majeur s'est produit : **`picking_list()` vérifie désormais la disponibilité avant d'inclure un article dans la liste** (correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-1). Cela supprime le découplage fonctionnel qui existait entre la vérification de faisabilité (`can_fulfil()`) et la génération du prélèvement (`picking_list()`). Il n'y a toujours pas d'orchestrateur qui enchaîne les deux fonctions de façon visible, mais elles sont maintenant cohérentes au niveau du code. Le bug volontaire (`available_qty` retourne `-5` pour `CX-330`) est encapsulé et documenté ; son impact fonctionnel est limité — `can_fulfil()` et désormais `picking_list()` l'absorbent correctement pour les demandes `≥ 0`.

## Constats détaillés

**VÉRIFIÉ_CODE — Workflow CONSULTATION_STOCK : couverture complète.** Les quatre fonctions décrites dans le workflow (`list_items`, `find_by_sku`, `available_qty`, `items_in_zone`) existent et se comportent comme documenté (`inventory/warehouse.py:11-33`). Le bug de `available_qty` est présent et documenté dans les deux artefacts (workflow et docstring). Pas d'écart entre description et implémentation.

**VÉRIFIÉ_CODE — Workflow FAISABILITE_COMMANDE : couverture complète, bug hérité documenté.** `can_fulfil(sku, requested)` existe (`inventory/orders.py:6-10`), appelle `find_by_sku` puis `available_qty`, retourne un booléen. Le comportement sur SKU inconnu (retour `False`) est implémenté (`inventory/orders.py:8-9`). Le bug hérité de `available_qty` est documenté dans le workflow et n'est pas un écart — c'est une limitation connue.

**VÉRIFIÉ_CODE — Workflow PRELEVEMENT_COMMANDE : couverture complète, vérification de disponibilité intégrée.** `picking_list(lines)` existe (`inventory/orders.py:13-24`), appelle `can_fulfil(sku, qty)` pour chaque ligne (`inventory/orders.py:20`, `inventory/orders.py:6-10`), effectue le tri par zone (`inventory/orders.py:24`), et ignore silencieusement les SKUs inconnus ou indisponibles (`inventory/orders.py:20-21`). Ces comportements correspondent exactement à leur description dans le workflow mise à jour.

**VÉRIFIÉ_CODE — Lacune fonctionnelle : pas d'orchestrateur de commande.** Le workflow complet de traitement d'une commande supposerait : (1) vérifier chaque ligne avec `can_fulfil()`, (2) générer la liste de prélèvement avec `picking_list()`. Aucune fonction n'enchaîne ces deux étapes. Il n'y a pas de point d'entrée de commande complet dans le code. Cette lacune est notée dans les questions ouvertes du workflow PRELEVEMENT_COMMANDE mais n'est pas une erreur — c'est une omission assumée du pilote.

**VÉRIFIÉ_CODE — `picking_list()` exclut désormais les articles en rupture.** `picking_list()` appelle `can_fulfil(sku, qty)` pour chaque ligne (`inventory/orders.py:20`, `inventory/orders.py:6-10`) et ne recopie dans la liste de prélèvement que les articles pour lesquels la vérification réussit. Un article comme `CX-330` (disponible = `-5`) n'apparaîtra pas dans la liste de prélèvement si la demande est `≥ 1`. Ce changement de comportement (correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-1) supprime le découplage fonctionnel antérieur et rend les deux fonctions cohérentes.

**VÉRIFIÉ_CODE — Stock en lecture seule : aucune mutation d'article implémentée.** Il n'existe aucune fonction pour créer, modifier ou supprimer un article de `ITEMS`. Le stock est immuable fonctionnellement (même si la liste Python est mutable techniquement). Aucun workflow de mise à jour de stock n'est implémenté, aucun n'est documenté.

**VÉRIFIÉ_CODE — Aucune couche d'exposition.** Il n'y a ni CLI, ni API REST, ni interface utilisateur. Les fonctions sont accessibles uniquement par import Python direct. Fonctionnellement, le pilote est une bibliothèque sans point d'entrée utilisateur.

## Forces

- **Cohérence code-workflow : totale.** Les trois workflows documentés correspondent précisément au code lu. Aucun écart entre description et implémentation.
- **Invariant métier traçable de bout en bout.** `CX-330` est identifié dans les données avec disponibilité négative (qty=45, reserved=50), géré correctement par `available_qty()` qui retourne `max(0, ...)`, validé par un test vert (`test_available_qty_never_negative`), et documenté dans les workflows et la carte des domaines. C'est une démonstration complète d'un invariant métier et de sa validation.
- **Séparation fonctionnelle claire.** Le stock (lecture pure) et la préparation de commande (logique dérivée) sont deux modules distincts avec des responsabilités non mélangées.

## Dettes techniques

- **Pas d'orchestrateur explicite de commande.** L'enchaînement logique `can_fulfil()` → `picking_list()` est maintenant cohérent au niveau du code, mais il n'y a pas de point d'entrée unique qui les orchestrerait. Un appelant doit les invoquer séquentiellement, sans exemple ni guide.
- **Aucune mutation de stock.** Pas de `reserve()`, `release()`, ni `update_qty()`. Le stock est figé à l'initialisation, ce qui rend le pilote non réaliste pour une logistique réelle (les réservations doivent être mises à jour après un prélèvement).
- **Couverture de tests incomplète sur `orders.py`.** Un seul test (`test_article_hors_stock_exclu`) valide le nouveau comportement de `picking_list()`. Le test de `can_fulfil()` est absent.

## Zones critiques

- **Absence de point de coordination visible entre `can_fulfil` et `picking_list`** — Bien que les deux fonctions soient maintenant cohérentes (toutes deux rejettent les articles indisponibles), il n'y a pas de fonction unique qui les orchestrerait. Un futur développeur pourrait ne pas réaliser qu'elles doivent être utilisées ensemble pour un résultat complet.

## Risques

- **VÉRIFIÉ_CODE — Vérification de faisabilité intégrée à `picking_list()`.** Après le correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-1, `picking_list()` appelle `can_fulfil()` pour chaque ligne et exclut les articles non faisables. Un appelant qui appelle `picking_list()` directement obtiendra une liste de prélèvement garantie faisable (tant que le stock ne change pas entre l'appel et l'utilisation). Le risque antérieur est éliminé.
- **HYPOTHÈSE — Données périmées dès le premier prélèvement réel.** `ITEMS` ne se met jamais à jour : après un prélèvement réel de 10 unités d'`AX-100`, le stock reste affiché à 12. Pour un pilote de démonstration, c'est attendu ; pour un usage réel, c'est une incohérence fonctionnelle critique.

## Recommandations priorisées

1. **Ajouter des tests pour `can_fulfil()` et compléter ceux de `picking_list()`** — Documenter par les tests le nouveau comportement de filtrage par disponibilité. Cas minimaux : SKU connu/inconnu, quantité demandée positive/zéro/négative, comportement du bug `CX-330` dans `can_fulfil()`, liste vide dans `picking_list()`, SKU mixte. (`tests/test_orders.py`)
2. **Documenter explicitement dans la docstring de `picking_list()` le filtrage par disponibilité** — Clarifier que les lignes infaisables sont silencieusement exclues et que le comportement est déterministe. (`inventory/orders.py:13`)
3. **Envisager un mécanisme de réservation / mise à jour de stock** — Même symbolique (une fonction `reserve(sku, qty)` qui modifie `reserved` en mémoire), pour rendre le pilote fonctionnellement plus réaliste.

## Questions ouvertes

- L'orchestrateur de commande (enchaînement `can_fulfil` + `picking_list`) est-il prévu dans le périmètre du pilote, ou délibérément absent (exercice pour l'apprenant) ?
- La gestion des réservations (`reserved`) est-elle censée rester en lecture seule dans ce pilote, ou une fonction de mise à jour est-elle prévue ?
- Le pilote est-il conçu pour rester une bibliothèque pure, ou une couche CLI ou HTTP est-elle prévue comme prochaine étape ?
