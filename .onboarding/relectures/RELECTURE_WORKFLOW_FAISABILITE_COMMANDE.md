# Relecture — WORKFLOW_FAISABILITE_COMMANDE.md

## Verdict global
Bon — la séquence de `can_fulfil`, ses règles, ses limites d'entrée et la traçabilité sont conformes au code courant.

## Problèmes bloquants
- Aucun.

## Problèmes mineurs
- Aucun.

## Points vérifiés et corrects
- La garde `requested <= 0`, la recherche, le rejet de `None`, puis la comparaison sur la disponibilité sont exactement ceux du code (`inventory/orders.py:6-12`).
- La disponibilité dépend de `max(0, qty - reserved)` (`inventory/warehouse.py:22-24`).
- `find_by_sku` est insensible à la casse (`inventory/warehouse.py:15-19`).
- L'absence de test direct de `can_fulfil` est vérifiée : `tests/test_orders.py:3` importe seulement `picking_list`, et le fichier ne contient aucun test de `can_fulfil`.

## Recommandations de correction
Aucune.
