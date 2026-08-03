# Fonctionnel — Audit

> Confiance : high

## Compréhension globale

`shift-pilot-py` implémente deux domaines fonctionnels (carte des domaines validée) : la gestion du stock d'entrepôt (`warehouse.py`) et la préparation de commande (`orders.py`). Le périmètre fonctionnel est intentionnellement réduit à un pilote de démonstration. Trois workflows ont été documentés et relus : consultation du stock, vérification de faisabilité de commande, génération de la liste de prélèvement. L'audit fonctionnel vérifie la cohérence entre ce que le code fait réellement et ce que les workflows décrivent.

## Résumé exécutif

Le code est cohérent avec les workflows documentés — chaque comportement décrit correspond à une implémentation lisible dans le source. Les deux incohérences notables sont des omissions fonctionnelles connues et assumées : (1) il n'y a pas d'orchestrateur qui enchaîne `can_fulfil()` puis `picking_list()` — les deux fonctions sont conçues pour être appelées séparément, sans workflow de commande complet ; (2) `picking_list()` ne vérifie pas la disponibilité avant d'inclure un article dans la liste, ce qui crée un découplage fonctionnel entre la vérification de faisabilité et la génération du prélèvement. Le bug volontaire (`available_qty` retourne `-5` pour `CX-330`) est encapsulé et documenté ; son impact fonctionnel est limité dans le périmètre actuel du pilote — `can_fulfil()` l'absorbe correctement pour les demandes `≥ 0` — mais un appelant qui appelle `picking_list()` directement sans passer par `can_fulfil()` peut générer un prélèvement sur un article en rupture sans signal.

## Constats détaillés

**VÉRIFIÉ_CODE — Workflow CONSULTATION_STOCK : couverture complète.** Les quatre fonctions décrites dans le workflow (`list_items`, `find_by_sku`, `available_qty`, `items_in_zone`) existent et se comportent comme documenté (`inventory/warehouse.py:11-33`). Le bug de `available_qty` est présent et documenté dans les deux artefacts (workflow et docstring). Pas d'écart entre description et implémentation.

**VÉRIFIÉ_CODE — Workflow FAISABILITE_COMMANDE : couverture complète, bug hérité documenté.** `can_fulfil(sku, requested)` existe (`inventory/orders.py:6-10`), appelle `find_by_sku` puis `available_qty`, retourne un booléen. Le comportement sur SKU inconnu (retour `False`) est implémenté (`inventory/orders.py:8-9`). Le bug hérité de `available_qty` est documenté dans le workflow et n'est pas un écart — c'est une limitation connue.

**VÉRIFIÉ_CODE — Workflow PRELEVEMENT_COMMANDE : couverture complète, silences documentés.** `picking_list(lines)` existe (`inventory/orders.py:13-21`), effectue le tri par zone (`inventory/orders.py:21`), et ignore silencieusement les SKUs inconnus (`inventory/orders.py:18-19`). Ces comportements correspondent exactement à leur description dans le workflow.

**VÉRIFIÉ_CODE — Lacune fonctionnelle : pas d'orchestrateur de commande.** Le workflow complet de traitement d'une commande supposerait : (1) vérifier chaque ligne avec `can_fulfil()`, (2) générer la liste de prélèvement avec `picking_list()`. Aucune fonction n'enchaîne ces deux étapes. Il n'y a pas de point d'entrée de commande complet dans le code. Cette lacune est notée dans les questions ouvertes du workflow PRELEVEMENT_COMMANDE mais n'est pas une erreur — c'est une omission assumée du pilote.

**VÉRIFIÉ_CODE — `picking_list()` inclut des articles en rupture.** `picking_list()` n'appelle pas `can_fulfil()` ni `available_qty()` (`inventory/orders.py:13-21`). Un article comme `CX-330` (disponible = `-5`) peut apparaître dans la liste de prélèvement si son SKU est fourni en entrée, même si la commande est infaisable selon `can_fulfil()`. Ce découplage est documenté dans le workflow comme une règle métier (`la quantité prélevée est celle demandée par la commande, non la disponibilité`) mais crée une incohérence fonctionnelle potentielle si les deux fonctions sont utilisées sans coordination.

**VÉRIFIÉ_CODE — Stock en lecture seule : aucune mutation d'article implémentée.** Il n'existe aucune fonction pour créer, modifier ou supprimer un article de `ITEMS`. Le stock est immuable fonctionnellement (même si la liste Python est mutable techniquement). Aucun workflow de mise à jour de stock n'est implémenté, aucun n'est documenté.

**VÉRIFIÉ_CODE — Aucune couche d'exposition.** Il n'y a ni CLI, ni API REST, ni interface utilisateur. Les fonctions sont accessibles uniquement par import Python direct. Fonctionnellement, le pilote est une bibliothèque sans point d'entrée utilisateur.

## Forces

- **Cohérence code-workflow : totale.** Les trois workflows documentés correspondent précisément au code lu. Aucun écart entre description et implémentation.
- **Bug volontaire traçable de bout en bout.** `CX-330` est identifié dans les données, documenté dans la docstring, capturé par un test rouge, documenté dans les workflows et la carte des domaines. C'est le livrable pédagogique le plus complet du pilote.
- **Séparation fonctionnelle claire.** Le stock (lecture pure) et la préparation de commande (logique dérivée) sont deux modules distincts avec des responsabilités non mélangées.

## Dettes techniques

- **Pas d'orchestrateur de commande.** L'enchaînement `can_fulfil()` → `picking_list()` n'est nulle part implémenté ni testé. Un appelant doit le reconstruire lui-même, sans exemple ni guide.
- **`picking_list()` décorrélée de la disponibilité.** La liste de prélèvement peut inclure des articles en rupture ou en disponibilité négative. Si l'intention est de toujours produire une liste faisable, il manque une étape de filtrage par `can_fulfil()`.
- **Aucune mutation de stock.** Pas de `reserve()`, `release()`, ni `update_qty()`. Le stock est figé à l'initialisation, ce qui rend le pilote non réaliste pour une logistique réelle (les réservations doivent être mises à jour après un prélèvement).

## Zones critiques

- **Découplage fonctionnel `can_fulfil / picking_list`** — Ces deux fonctions couvrent des étapes logiquement séquentielles d'une même commande mais n'ont pas de point de coordination. Un futur développeur devra comprendre implicitement qu'il doit les enchaîner.

## Risques

- **HYPOTHÈSE — Commande produite sans vérification de faisabilité.** Un appelant qui appelle directement `picking_list()` sans passer par `can_fulfil()` obtiendra une liste de prélèvement pour des articles potentiellement en rupture. Ce comportement n'est pas défendu par le code.
- **HYPOTHÈSE — Données périmées dès le premier prélèvement réel.** `ITEMS` ne se met jamais à jour : après un prélèvement réel de 10 unités d'`AX-100`, le stock reste affiché à 12. Pour un pilote de démonstration, c'est attendu ; pour un usage réel, c'est une incohérence fonctionnelle critique.

## Recommandations priorisées

1. **Implémenter une fonction d'orchestration `process_order(lines)`** — Enchaîne `can_fulfil()` pour chaque ligne, rejette les infaisables, puis appelle `picking_list()` sur les lignes valides. Documente le workflow complet. (`inventory/orders.py`)
2. **Documenter explicitement le découplage `can_fulfil / picking_list`** — Si la séparation est intentionnelle (responsabilité de l'appelant de les enchaîner), le dire dans la docstring de `picking_list()`. (`inventory/orders.py:13`)
3. **Envisager un mécanisme de réservation / mise à jour de stock** — Même symbolique (une fonction `reserve(sku, qty)` qui modifie `reserved` en mémoire), pour rendre le pilote fonctionnellement plus réaliste.

## Questions ouvertes

- L'orchestrateur de commande (enchaînement `can_fulfil` + `picking_list`) est-il prévu dans le périmètre du pilote, ou délibérément absent (exercice pour l'apprenant) ?
- La gestion des réservations (`reserved`) est-elle censée rester en lecture seule dans ce pilote, ou une fonction de mise à jour est-elle prévue ?
- Le pilote est-il conçu pour rester une bibliothèque pure, ou une couche CLI ou HTTP est-elle prévue comme prochaine étape ?
