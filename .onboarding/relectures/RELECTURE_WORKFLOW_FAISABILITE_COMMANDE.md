# Relecture — WORKFLOW_FAISABILITE_COMMANDE.md

## Verdict global
Bon — les erreurs de raisonnement relevées au tour précédent sur `requested=0` et `requested<0` ont été corrigées. Le workflow décrit maintenant exactement la garde `item is None` puis la comparaison `available_qty(item) >= requested`, sans inventer de comportement non visible dans le code.

## Problèmes bloquants
Aucun.

## Problèmes mineurs
Aucun.

## Points vérifiés et corrects
- Le point d'entrée et les cinq étapes principales collent à `can_fulfil` : recherche par SKU, retour `False` si `item is None`, puis comparaison finale sur `available_qty(item)` (`inventory/orders.py:6-10`).
- La règle "SKU inconnu -> False" est exacte (`inventory/orders.py:8-9`).
- La règle de faisabilité "disponibilité nette >= quantité demandée" est correctement formulée à partir du code réel (`inventory/orders.py:10`, `inventory/warehouse.py:29`).
- Le traitement du bug `available_qty` est désormais calculé correctement : pour `CX-330`, la disponibilité vaut `-5`, ce qui refuse toute demande `requested >= -5` et n'autorise que des valeurs strictement inférieures à `-5`, faute de validation d'entrée (`inventory/warehouse.py:5-7`, `inventory/warehouse.py:29`, `inventory/orders.py:10`).
- Le document distingue correctement deux sujets : l'invariant violé par `available_qty` et l'absence de validation de `requested` (`inventory/warehouse.py:23-29`, `inventory/orders.py:6-10`).
- L'absence de tests sur `inventory/orders.py` est prouvée : `tests/test_warehouse.py` n'importe que `inventory.warehouse` (`tests/test_warehouse.py:3`).

## Recommandations de correction
Aucune.
