# WORKFLOW_CONSULTATION_STOCK — Consultation et calcul de disponibilité du stock d'entrepôt

> **RÉCONCILIÉ le 2026-08-09.** SHA de référence : `511104b`. Écarts vs version initiale : (1) `find_by_sku` est désormais insensible à la casse (`.upper()`) ; (2) `available_qty` est corrigée — résultat borné à zéro via `max(0, ...)`, jamais négatif ; (3) données `CX-330` : `reserved=5` (plus 50) ; (4) test rouge devenu vert ; (5) références de lignes mises à jour. Toutes les sections « bug volontaire » supprimées — le bug n'existe plus dans le code courant.

## Classification
- **Type** : `data_flow`
- **Sous-type** : lecture et calcul sur référentiel stock en mémoire
- **Visibilité** : `technical` — aucune interface utilisateur ni route HTTP ; les appelants sont des modules Python
- **Acteur principal** : module appelant (ex. `inventory/orders.py`)
- **Acteurs** : code appelant uniquement — aucun humain direct
- **Criticité** : Haute — domaine fondateur ; tout le reste (`can_fulfil`, `picking_list`) s'appuie sur ces fonctions
- **Confiance** : high
- **Justification** : Module `inventory/warehouse.py` lu en intégralité (29 lignes). Toutes les fonctions publiques sont visibles. Les données (`ITEMS`) sont en dur dans le fichier. Aucune couche d'abstraction cachée. La docstring de `available_qty` décrit la sémantique corrigée (« Quantité réellement disponible à la vente »).

## Objectif
Permettre à tout code du pilote d'accéder aux articles de l'entrepôt, de les chercher par identifiant SKU (insensible à la casse) ou par zone de rangement, et de calculer la quantité réellement disponible à la vente (stock brut moins réservations, bornée à zéro). Ce flux est la fondation de tout le domaine logistique : sans lui, ni la vérification de faisabilité ni la génération du prélèvement ne peuvent fonctionner. Il opère entièrement en mémoire, sans persistance ni couche réseau.

## Acteurs
- Module Python appelant (ex. `inventory/orders.py`, ou un futur test/orchestrateur)

## Points d'entrée
- `inventory.warehouse.list_items()` — retourne la liste complète des articles (`inventory/warehouse.py:11`)
- `inventory.warehouse.find_by_sku(sku)` — recherche un article par son identifiant SKU, **insensible à la casse** (`inventory/warehouse.py:15`)
- `inventory.warehouse.available_qty(item)` — calcule la quantité disponible à la vente pour un article donné, **bornée à zéro** (`inventory/warehouse.py:22`)
- `inventory.warehouse.items_in_zone(zone)` — retourne les articles d'une zone d'entrepôt (`inventory/warehouse.py:27`)

## Étapes principales

**Variante A — Obtenir tous les articles :**
1. L'appelant invoque `list_items()` (`inventory/warehouse.py:11`).
2. La fonction retourne directement la référence vers `ITEMS` — la liste en mémoire de tous les articles (`inventory/warehouse.py:3-8`).

**Variante B — Recherche par SKU (insensible à la casse) :**
1. L'appelant invoque `find_by_sku(sku)` avec une chaîne SKU (`inventory/warehouse.py:15`).
2. Parcours linéaire de `ITEMS` : comparaison normalisée `item["sku"].upper() == sku.upper()` à chaque article (`inventory/warehouse.py:17`). Un appel avec `"ax-100"` retrouve l'article `"AX-100"`.
3. Si trouvé : retourne le dict article (`inventory/warehouse.py:18`). Si non trouvé : retourne `None` (`inventory/warehouse.py:19`).

**Variante C — Filtrage par zone :**
1. L'appelant invoque `items_in_zone(zone)` avec une chaîne de zone (`inventory/warehouse.py:27`).
2. List comprehension sur `ITEMS` filtrant `i["zone"] == zone` (`inventory/warehouse.py:28`).
3. Retourne la sous-liste correspondante (peut être vide).

**Variante D — Calcul de disponibilité vendable :**
1. L'appelant fournit un dict article (obtenu via `find_by_sku` ou `list_items`) à `available_qty(item)` (`inventory/warehouse.py:22`).
2. Calcul : `max(0, item["qty"] - item["reserved"])` (`inventory/warehouse.py:24`).
3. Retourne un entier toujours supérieur ou égal à zéro.

## Règles métier
- **Disponibilité = max(0, stock brut − réservations).** La formule est `max(0, item["qty"] - item["reserved"])` (`inventory/warehouse.py:24`). Si `reserved > qty` (données corrompues), le résultat est 0, jamais négatif. L'invariant est explicitement testé (`tests/test_warehouse.py:20-23`).
- **Recherche SKU insensible à la casse.** `find_by_sku` normalise en majuscules des deux côtés de la comparaison (`item["sku"].upper() == sku.upper()`, `inventory/warehouse.py:17`). `"ax-100"`, `"Ax-100"` et `"AX-100"` retournent le même article. Testé par `test_find_by_sku_insensible_casse` (`tests/test_warehouse.py:33-37`).
- **SKU inconnu → `None`, pas d'exception.** `find_by_sku` retourne `None` si aucun article ne correspond (`inventory/warehouse.py:19`). L'appelant doit tester ce retour avant tout usage (passage à `available_qty(None)` provoque une `TypeError`).
- **Stock en lecture seule.** Aucune des quatre fonctions ne modifie `ITEMS` : il n'existe aucune fonction de création, mise à jour ou suppression d'article dans ce module (`inventory/warehouse.py:11-28`).
- **Données en dur, non persistées.** `ITEMS` est défini comme littéral Python au chargement du module (`inventory/warehouse.py:3-8`). Toute modification de la liste (ajout, suppression) ne serait visible que pour la durée de vie du processus et serait perdue au redémarrage.

## Données
- `ITEMS` : liste Python de dicts `{sku, label, qty, reserved, zone}` — seule source de vérité du stock, définie en dur (`inventory/warehouse.py:3-8`). Quatre articles : `AX-100` (zone A, qty=12, reserved=2), `BX-220` (zone B, qty=0, reserved=0 — indisponible), `CX-330` (zone A, qty=45, reserved=5 — disponible=40), `DX-440` (zone C, qty=7, reserved=1). Invariant respecté : `reserved <= qty` pour chaque article (`tests/test_warehouse.py:25-31`).

## Intégrations
Aucune intégration externe explicite visible. Pas d'accès base de données, pas d'appel réseau, pas d'import tiers.

## Risques
- **`None` non gardé → `TypeError`.** `find_by_sku` retourne `None` pour un SKU inconnu (`inventory/warehouse.py:19`). Un appel direct `available_qty(None)` provoque `TypeError: 'NoneType' object is not subscriptable`. `can_fulfil` gère ce cas (`inventory/orders.py:10-11`) ; `picking_list` aussi (`inventory/orders.py:32-33`) ; d'autres appelants futurs pourraient l'oublier.
- **`list_items()` retourne une référence directe à `ITEMS`, non une copie.** Un appelant peut muter la liste (`inventory/warehouse.py:12`). Dans ce pilote sans mutation prévue, le risque est hypothétique ; à surveiller si une couche d'écriture est ajoutée.
- **Tri lexicographique des zones dans `items_in_zone`.** Aucun tri n'est appliqué dans `items_in_zone` ; c'est `picking_list` qui trie. Si des zones à deux caractères ou numériques sont introduites, l'ordre n'est pas garanti sans tri explicite. Actuellement, seules des zones à une lettre (A, B, C) existent.

## Questions ouvertes
- `ITEMS` est une liste Python partagée sans verrou ni copie défensive. Dans un contexte multi-thread (serveur HTTP futur), une mutation concurrente serait corrompue. Ce dépôt ne contient ni thread, ni serveur, ni mutation de `ITEMS` — le risque est hypothétique pour l'état actuel du code ; à évaluer si une couche web est ajoutée.
- Aucune fonction de mise à jour du stock n'est implémentée : s'agit-il d'une limitation volontaire du pilote ou d'une omission à compléter ?

## Preuves
- `inventory/warehouse.py` — lu en intégralité
- `tests/test_warehouse.py` — lu en intégralité (6 tests : `test_find_by_sku`, `test_items_in_zone`, `test_available_qty_cx330`, `test_available_qty_borne_a_zero_quand_reserved_superieur_a_qty`, `test_invariant_reserved_ne_depasse_pas_qty_dans_items`, `test_find_by_sku_insensible_casse`)
- `.onboarding/domaines/CARTE_DES_DOMAINES.md` — domaine `entrepot-stock` (réconcilié)
