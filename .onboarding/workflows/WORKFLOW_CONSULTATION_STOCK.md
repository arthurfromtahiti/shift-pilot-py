# WORKFLOW_CONSULTATION_STOCK — Consultation et calcul de disponibilité du stock d'entrepôt

## Classification
- **Type** : `data_flow`
- **Sous-type** : lecture et calcul sur référentiel stock en mémoire
- **Visibilité** : `technical` — aucune interface utilisateur ni route HTTP ; les appelants sont des modules Python
- **Acteur principal** : module appelant (ex. `inventory/orders.py`)
- **Acteurs** : code appelant uniquement — aucun humain direct
- **Criticité** : Haute — domaine fondateur ; tout le reste (`can_fulfil`, `picking_list`) s'appuie sur ces fonctions
- **Confiance** : high
- **Justification** : Module `inventory/warehouse.py` lu en intégralité (34 lignes). Toutes les fonctions publiques sont visibles. Les données (`ITEMS`) sont en dur dans le fichier. Aucune couche d'abstraction cachée. Le bug volontaire est documenté dans la docstring même du code.

## Objectif
Permettre à tout code du pilote d'accéder aux articles de l'entrepôt, de les chercher par identifiant SKU ou par zone de rangement, et de calculer la quantité réellement disponible à la vente (stock brut moins réservations). Ce flux est la fondation de tout le domaine logistique : sans lui, ni la vérification de faisabilité ni la génération du prélèvement ne peuvent fonctionner. Il opère entièrement en mémoire, sans persistance ni couche réseau.

## Acteurs
- Module Python appelant (ex. `inventory/orders.py`, ou un futur test/orchestrateur)

## Points d'entrée
- `inventory.warehouse.list_items()` — retourne la liste complète des articles (`inventory/warehouse.py:11`)
- `inventory.warehouse.find_by_sku(sku)` — recherche un article par son identifiant SKU (`inventory/warehouse.py:15`)
- `inventory.warehouse.available_qty(item)` — calcule la quantité disponible à la vente pour un article donné (`inventory/warehouse.py:22`)
- `inventory.warehouse.items_in_zone(zone)` — retourne les articles d'une zone d'entrepôt (`inventory/warehouse.py:32`)

## Étapes principales

**Variante A — Obtenir tous les articles :**
1. L'appelant invoque `list_items()` (`inventory/warehouse.py:11-12`).
2. La fonction retourne directement la référence vers `ITEMS` — la liste en mémoire de tous les articles (`inventory/warehouse.py:3-8`).

**Variante B — Recherche par SKU :**
1. L'appelant invoque `find_by_sku(sku)` avec une chaîne SKU (`inventory/warehouse.py:15`).
2. Parcours linéaire de `ITEMS` : comparaison stricte `item["sku"] == sku` à chaque article (`inventory/warehouse.py:16-18`).
3. Si trouvé : retourne le dict article (`inventory/warehouse.py:18`). Si non trouvé : retourne `None` (`inventory/warehouse.py:19`).

**Variante C — Filtrage par zone :**
1. L'appelant invoque `items_in_zone(zone)` avec une chaîne de zone (`inventory/warehouse.py:32`).
2. List comprehension sur `ITEMS` filtrant `i["zone"] == zone` (`inventory/warehouse.py:33`).
3. Retourne la sous-liste correspondante (peut être vide).

**Variante D — Calcul de disponibilité vendable :**
1. L'appelant fournit un dict article (obtenu via `find_by_sku` ou `list_items`) à `available_qty(item)` (`inventory/warehouse.py:22`).
2. Calcul : `item["qty"] - item["reserved"]` (`inventory/warehouse.py:29`).
3. Retourne un entier — **potentiellement négatif** si `reserved > qty` (bug volontaire documenté, `inventory/warehouse.py:23-28`).

## Règles métier
- **Disponibilité = stock brut − réservations.** La formule est `item["qty"] - item["reserved"]` (`inventory/warehouse.py:29`). **Bug volontaire** : quand `reserved > qty`, le résultat est négatif — il n'est jamais borné à zéro. Exemple concret : `CX-330` (`qty=45`, `reserved=50`) → disponible = `-5` (`inventory/warehouse.py:6`).
- **SKU inconnu → `None`, pas d'exception.** `find_by_sku` retourne `None` si aucun article ne correspond (`inventory/warehouse.py:19`). L'appelant doit tester ce retour avant tout usage (passage à `available_qty(None)` provoque une `TypeError`).
- **Stock en lecture seule.** Aucune des quatre fonctions ne modifie `ITEMS` : il n'existe aucune fonction de création, mise à jour ou suppression d'article dans ce module (`inventory/warehouse.py:11-33`).
- **Données en dur, non persistées.** `ITEMS` est défini comme littéral Python au chargement du module (`inventory/warehouse.py:3-8`). Toute modification de la liste (ajout, suppression) ne serait visible que pour la durée de vie du processus et serait perdue au redémarrage.

## Données
- `ITEMS` : liste Python de dicts `{sku, label, qty, reserved, zone}` — seule source de vérité du stock, définie en dur (`inventory/warehouse.py:3-8`). Quatre articles : `AX-100` (zone A), `BX-220` (zone B), `CX-330` (zone A, bug actif), `DX-440` (zone C).

## Intégrations
Aucune intégration externe explicite visible. Pas d'accès base de données, pas d'appel réseau, pas d'import tiers.

## Risques
- **Invariant `available_qty` violé.** `available_qty` retourne `-5` pour `CX-330` (`inventory/warehouse.py:29`). L'invariant attendu (disponible >= 0) n'est pas respecté. Pour les appelants qui comparent ce résultat à une quantité demandée positive (ex. `can_fulfil` : `available_qty(item) >= requested`), l'effet observable est un refus — comportement correct en rupture, obtenu par accident arithmétique. L'impact sur d'autres appelants futurs (qui pourraient borner, afficher ou stocker la valeur) doit être évalué cas par cas. Prouvé par le test rouge `test_available_qty_never_negative` (`tests/test_warehouse.py:14-18`).
- **`None` non gardé → `TypeError`.** `find_by_sku` retourne `None` pour un SKU inconnu (`inventory/warehouse.py:19`). Un appel direct `available_qty(None)` provoque `TypeError: 'NoneType' object is not subscriptable`. `can_fulfil` gère ce cas (`inventory/orders.py:8-9`) ; d'autres appelants futurs pourraient l'oublier.

## Questions ouvertes
- `available_qty` est-elle prévue pour être corrigée dans ce pilote (borne à 0), ou reste-t-elle volontairement bugguée pour toute la durée du pilote d'onboarding ?
- `ITEMS` est une liste Python partagée sans verrou ni copie défensive. Dans un contexte multi-thread (serveur HTTP futur), une mutation concurrente serait corrompue. Ce dépôt ne contient ni thread, ni serveur, ni mutation de `ITEMS` — le risque est hypothétique pour l'état actuel du code ; à évaluer si une couche web est ajoutée.
- `list_items()` retourne une référence directe à `ITEMS`, non une copie : un appelant peut muter la liste. Est-ce intentionnel dans le cadre du pilote, ou un vecteur d'effet de bord non voulu ?
- Aucune fonction de mise à jour du stock n'est implémentée : s'agit-il d'une limitation volontaire du pilote ou d'une omission à compléter ?

## Preuves
- `inventory/warehouse.py` — lu en intégralité
- `tests/test_warehouse.py` — lu en intégralité (couvre `find_by_sku`, `items_in_zone`, `available_qty`)
- `CARTE_DES_DOMAINES.md` — domaine `entrepot-stock`
