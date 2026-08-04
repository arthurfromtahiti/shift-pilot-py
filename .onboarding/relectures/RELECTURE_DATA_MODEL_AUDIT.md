# Relecture — DATA_MODEL_AUDIT.md

## Verdict global
À corriger — l'audit est solide sur la plupart des constats, mais il surqualifie un point de preuve au cœur de son propre diagnostic. Il présente `sku` comme un "identifiant unique" en `VÉRIFIÉ_CODE` alors que la même note explique ensuite que l'unicité n'est pas garantie par le modèle.

## Problèmes bloquants
- Le constat `VÉRIFIÉ_CODE` "Chaque dict a cinq clés : `sku` (str, identifiant unique)" n'est pas correctement qualifié. Le code prouve que chaque article observé porte une clé `sku` et que [find_by_sku](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/inventory/warehouse.py:15) recherche dessus, mais il ne prouve pas une propriété d'unicité du modèle. L'audit dit d'ailleurs plus bas "Unicité du SKU non garantie" en s'appuyant sur le même fichier. Cette contradiction mélange fait observé sur l'échantillon et propriété garantie du modèle.

## Problèmes mineurs
Aucun.

## Points vérifiés et corrects
- Le modèle en mémoire réduit à `ITEMS` est correctement décrit et prouvé dans [inventory/warehouse.py](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/inventory/warehouse.py:3).
- Le caractère mutable des dicts et de la liste retournée par `find_by_sku()` / `list_items()` est correctement lu dans [inventory/warehouse.py](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/inventory/warehouse.py:11) et [inventory/warehouse.py](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/inventory/warehouse.py:15).
- L'absence de persistance, de types dédiés et de contraintes déclarées est correctement sourcée par lecture de [inventory/warehouse.py](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/inventory/warehouse.py:1) et [inventory/orders.py](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/inventory/orders.py:13).

## Recommandations de correction
- Remplacer "identifiant unique" par une formulation prouvable, par exemple "clé métier utilisée pour la recherche" ou "unique dans l'échantillon observé `ITEMS`, sans garantie déclarée dans le modèle".
