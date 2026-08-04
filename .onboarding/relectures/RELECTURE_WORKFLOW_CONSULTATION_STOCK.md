# Relecture — WORKFLOW_CONSULTATION_STOCK.md

## Verdict global
Bon — le workflow reste au niveau de preuve du code et ne sur-interprète plus l'impact aval du bug `available_qty`. Les points d'entrée, règles métier, risques et questions ouvertes sont alignés avec `inventory/warehouse.py`, `inventory/orders.py` et les tests présents.

## Problèmes bloquants
Aucun.

## Problèmes mineurs
Aucun.

## Points vérifiés et corrects
- Les quatre points d'entrée cités existent bien : `list_items`, `find_by_sku`, `available_qty`, `items_in_zone` (`inventory/warehouse.py:11-33`).
- Les variantes A à D reflètent le code lu : retour direct de `ITEMS`, recherche linéaire par SKU, filtrage par zone, calcul `item["qty"] - item["reserved"]` (`inventory/warehouse.py:12-33`).
- La règle "SKU inconnu -> None" est exacte et cohérente avec le risque sur un appel direct à `available_qty(None)` (`inventory/warehouse.py:19`, `inventory/warehouse.py:29`).
- Le risque principal est correctement formulé au niveau prouvé : l'invariant `available >= 0` est violé pour `CX-330`, et le test rouge le démontre sans inventer un effet faux chez les appelants (`inventory/warehouse.py:3-8`, `tests/test_warehouse.py:14-18`).
- Le déplacement du point "non thread-safe" en question ouverte est justifié : je ne trouve ni serveur, ni thread, ni mutation concurrente de `ITEMS` dans le dépôt (`inventory/warehouse.py:3-33`, `inventory/orders.py:1-21`).

## Recommandations de correction
Aucune.
