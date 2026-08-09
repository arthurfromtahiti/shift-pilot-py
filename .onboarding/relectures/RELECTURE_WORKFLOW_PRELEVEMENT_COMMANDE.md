# Relecture — WORKFLOW_PRELEVEMENT_COMMANDE.md

## Verdict global
Bon — le fil d'exécution, les règles métier, le format de sortie, la portée des tests et la traçabilité sont conformes au code courant.

## Problèmes bloquants
- Aucun.

## Problèmes mineurs
- Aucun. La justification distingue explicitement les comportements établis par lecture du code de ceux couverts par les tests (`WORKFLOW_PRELEVEMENT_COMMANDE.md:13`).

## Points vérifiés et corrects
- L'initialisation, la boucle indexée, la garde `qty <= 0`, l'ignorance d'un SKU inconnu et la clé canonique correspondent à `inventory/orders.py:25-35`.
- Le dépassement produit bien une entrée `skipped` avec `order_id`, `sku`, `qty_requested` et `qty_missing` (`inventory/orders.py:36-43`).
- Les allocations acceptées sont cumulées par SKU canonique et les picks sont triés par zone au retour (`inventory/orders.py:44-46`).
- La sortie est bien un dictionnaire `{"picks": ..., "skipped": ...}`, contrairement à l'ancienne version (`inventory/orders.py:18,46`).
- Les tests exécutés dans le checkout passent : `python3 -m unittest discover -s tests -t .` → 16 tests, OK.

## Recommandations de correction
Aucune.
