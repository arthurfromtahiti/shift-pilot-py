# Relecture — WORKFLOW_PRELEVEMENT_COMMANDE.md

## Verdict global
Bon — je ne trouve ni étape inventée ni règle métier fausse dans ce workflow. La description de `picking_list` reste proche du code et les risques cités sont concrets, directement observables dans `inventory/orders.py`.

## Problèmes bloquants
Aucun.

## Problèmes mineurs
Aucun.

## Points vérifiés et corrects
- Le point d'entrée, la boucle sur `lines`, l'appel à `find_by_sku`, le `continue` sur SKU inconnu et la construction `{sku, zone, qty}` correspondent exactement à `picking_list` (`inventory/orders.py:13-21`).
- Le tri final par zone est correctement lu comme un tri lexicographique ascendant (`inventory/orders.py:21`).
- La règle "SKU inconnu -> ligne ignorée silencieusement" est prouvée par le `continue` sans log ni exception (`inventory/orders.py:17-19`).
- La règle "la quantité prélevée est la quantité demandée" est exacte : `picking_list` n'appelle jamais `available_qty` et recopie `qty` telle quelle dans la sortie (`inventory/orders.py:16-20`).
- Le risque sur l'absence de contrôle de disponibilité est correctement borné : le code montre qu'aucun contrôle n'est réalisé ici, sans prétendre qu'un orchestrateur réel appelle forcément `can_fulfil` juste avant (`inventory/orders.py:13-21`).
- L'absence de tests sur `picking_list` est exacte : `tests/test_warehouse.py` n'importe pas `inventory.orders` (`tests/test_warehouse.py:3`).

## Recommandations de correction
Aucune.
