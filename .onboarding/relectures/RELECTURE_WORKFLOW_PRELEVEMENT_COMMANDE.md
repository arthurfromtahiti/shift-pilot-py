# Relecture — WORKFLOW_PRELEVEMENT_COMMANDE.md

## Verdict global
Bon — la description de `picking_list` correspond exactement au code après le correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-1. Tous les pas du workflow et les règles métier sont vérifiés. Les tests commencent à émerger.

## Problèmes bloquants
Aucun.

## Problèmes mineurs
Aucun.

## Points vérifiés et corrects
- Le point d'entrée, la boucle sur `lines`, l'appel à `can_fulfil()` avant chaque inclusion, et la construction `{sku, zone, qty}` correspondent exactement à `picking_list` (`inventory/orders.py:13-24`).
- L'appel à `can_fulfil(sku, qty)` pour chaque ligne, incluant la vérification SKU + disponibilité, est correct (`inventory/orders.py:20`, `inventory/orders.py:6-10`).
- Le tri final par zone est correctement lu comme un tri lexicographique ascendant (`inventory/orders.py:24`).
- La règle "SKU inconnu ou indisponible → ligne ignorée silencieusement" est prouvée par le `continue` sans log ni exception (`inventory/orders.py:20-21`).
- La dépendance sur `find_by_sku` pour récupérer la zone de l'article est correcte (`inventory/orders.py:22`).
- Le test `tests/test_orders.py:test_article_hors_stock_exclu` valide le cas `BX-220` (quantité = 0, demandée = 1) → exclusion correcte (`tests/test_orders.py:7-10`).

## Recommandations de correction
Aucune.
