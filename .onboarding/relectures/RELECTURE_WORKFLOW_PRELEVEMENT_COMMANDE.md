# Relecture — WORKFLOW_PRELEVEMENT_COMMANDE.md

## Verdict global
Bon — la description de `picking_list` correspond exactement au code après le correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-316. Tous les pas du workflow et les règles métier sont vérifiés, en particulier le cumul intra-commande. Les tests sont robustes et couvrent les cas clés.

## Problèmes bloquants
Aucun.

## Problèmes mineurs
Aucun.

## Points vérifiés et corrects
- Le point d'entrée, l'initialisation du dict `allocated`, la boucle sur `lines`, le calcul de disponibilité restante via `remaining = available_qty(item) - allocated.get(sku, 0)`, et la construction `{sku, zone, qty}` correspondent exactement à `picking_list` (`inventory/orders.py:15-35`).
- La vérification de disponibilité intégrée (sans appel à `can_fulfil()`) pour chaque ligne, incluant la vérification SKU + disponibilité, est correcte (`inventory/orders.py:27-32`).
- Le cumul intra-commande via `allocated[sku]` pour gérer plusieurs lignes du même SKU est correctement implémenté et documenté (`inventory/orders.py:33`).
- Le tri final par zone est correctement lu comme un tri lexicographique ascendant (`inventory/orders.py:35`).
- La règle "SKU inconnu ou indisponible → ligne ignorée silencieusement" est prouvée par les `continue` sans log ni exception (`inventory/orders.py:27-32`).
- La dépendance sur `find_by_sku` pour récupérer la zone de l'article est correcte (`inventory/orders.py:27`).
- Le test `tests/test_orders.py:test_plusieurs_lignes_meme_sku_depassement_exclu` valide le cumul intra-commande (CX-330, available=40, deux lignes de 30 → 1ère incluse, 2e exclue) (`tests/test_orders.py:29-34`).
- 6 autres tests couvrent : articles hors stock (BX-220), quantités nulles/négatives, cumul sans dépassement, cumul triple — cas completes du nouveau mécanisme.

## Recommandations de correction
Aucune.
