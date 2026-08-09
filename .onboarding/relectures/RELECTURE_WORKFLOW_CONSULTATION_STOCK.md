# Relecture — WORKFLOW_CONSULTATION_STOCK.md

## Verdict global
Bon — les points d'entrée, le déroulement, les règles métier et la traçabilité sont conformes au code courant.

## Problèmes bloquants
- Aucun.

## Problèmes mineurs
Aucun.

## Points vérifiés et corrects
- Les quatre points d'entrée existent et correspondent aux fonctions lues (`inventory/warehouse.py:11-28`).
- `find_by_sku` normalise bien les deux côtés avec `.upper()` et retourne `None` si absent (`inventory/warehouse.py:15-19`).
- `available_qty` applique `max(0, qty - reserved)` (`inventory/warehouse.py:22-24`), et le cas `reserved > qty` est testé (`tests/test_warehouse.py:20-23`).
- Les données seed et les six tests de stock concordent (`inventory/warehouse.py:3-8`, `tests/test_warehouse.py:7-37`).
- Le risque de référence mutable retournée par `list_items` est réel (`inventory/warehouse.py:11-12`) et correctement présenté comme risque, non comme comportement observé d'un appelant.

## Recommandations de correction
Aucune.
