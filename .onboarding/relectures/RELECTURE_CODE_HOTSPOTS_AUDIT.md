# Relecture — CODE_HOTSPOTS_AUDIT.md

## Verdict global
À corriger — l'analyse des zones sensibles est pertinente, mais la section **Risques** relève abusivement au statut `VÉRIFIÉ_CODE` des scénarios futurs qui restent hypothétiques. C'est précisément le glissement fait/hypothèse à corriger avant validation.

## Problèmes bloquants
- Le risque `VÉRIFIÉ_CODE — Régression invisible sur can_fulfil()` est mal qualifié. Le code prouve deux faits : [can_fulfil](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/inventory/orders.py:6) dépend de [available_qty](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/inventory/warehouse.py:22), et il n'existe aucun test sur `orders.py` dans [tests/test_warehouse.py](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/tests/test_warehouse.py:1). En revanche, une "régression invisible" est un scénario futur conditionnel ; ce statut doit rester `HYPOTHÈSE`.
- Le risque `VÉRIFIÉ_CODE — Prélèvement incomplet sans signal` est lui aussi trop affirmatif dans sa formulation. Le `continue` silencieux sur SKU inconnu est bien prouvé en [inventory/orders.py](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/inventory/orders.py:18), mais une liste "incomplète" n'apparaît que sous condition d'entrée contenant un SKU non résolu. Le fait prouvé est le silence du code ; le scénario d'incident doit être formulé conditionnellement.

## Problèmes mineurs
Aucun.

## Points vérifiés et corrects
- `available_qty()` est bien un point sensible central, prouvé par son appel depuis [inventory/orders.py](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/inventory/orders.py:10) et par l'échec observé du test rouge dans [tests/test_warehouse.py](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/tests/test_warehouse.py:14).
- L'absence totale de tests sur `can_fulfil()` et `picking_list()` est correctement prouvée par lecture de [tests/test_warehouse.py](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/tests/test_warehouse.py:1) et confirmée par l'exécution `python3 -m unittest discover -s tests -t .`, qui n'exécute que 3 tests.
- Le rôle pivot de [inventory/warehouse.py](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/inventory/warehouse.py:1) est correctement décrit.

## Recommandations de correction
- Requalifier les deux risques bloquants en `HYPOTHÈSE`, en gardant séparés les faits prouvés (`dépendance`, `absence de tests`, `continue` silencieux) et le scénario d'impact conditionnel.
