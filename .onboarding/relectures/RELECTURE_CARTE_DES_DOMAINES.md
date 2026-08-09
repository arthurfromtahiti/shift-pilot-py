# Relecture — CARTE_DES_DOMAINES.md

## Verdict global
Bon — la carte est exploitable et son découpage en deux domaines métier est confirmé par le code : `entrepot-stock` et `preparation-commande`. Les preuves citées existent, les indices principaux sont vérifiables, la granularité réduite est explicitement justifiée par la petite taille du dépôt, et aucun domaine inventé ou pan métier oublié n'a été trouvé.

## Problèmes bloquants
Aucun.

## Problèmes mineurs
- La section « Nature du projet » présente `Python 3.12` comme fait vérifié à partir de `inventory/__pycache__/*.cpython-312.pyc`. Un bytecode ne prouve pas l'interpréteur d'exécution, et l'inventaire contient aussi des artefacts `cpython-313`. Cette précision est périphérique à la carte des domaines ; elle devrait être reformulée en `Python 3` ou `stdlib uniquement`.
- Certains indices annoncés (`sku`, `qty`, `zone`) sont génériques et apparaissent dans les deux domaines. Le rattachement reste fiable grâce au chemin de module et aux symboles discriminants (`ITEMS`, `available_qty`, `items_in_zone`, `can_fulfil`, `picking_list`), mais les exemples d'indices pourraient privilégier ces derniers.

## Points vérifiés et corrects
- **Réalité du stock** : ouverture de `inventory/warehouse.py` : `ITEMS` contient quatre articles avec `sku`, `label`, `qty`, `reserved`, `zone`; `list_items`, `find_by_sku`, `available_qty` et `items_in_zone` opèrent sur cette collection. Les tests `tests/test_warehouse.py:7-37` couvrent recherche, zones, disponibilité, bornage et invariant.
- **Réalité de la préparation** : ouverture de `inventory/orders.py` : `can_fulfil` et `picking_list` sont des capacités distinctes, et l'import `from inventory.warehouse import find_by_sku, available_qty` prouve la dépendance directionnelle au stock. Les dix tests de `tests/test_orders.py:6-88` couvrent picks, skipped, quantités invalides, cumul et casse.
- **Indices discriminants** : `rg` sur `inventory`, `tests` et `README.md` retrouve `ITEMS`/`items_in_zone`/`available_qty` dans le périmètre stock et `can_fulfil`/`picking_list`/`allocated`/`skipped` dans le périmètre commande ; ces symboles ne sont pas diffusés dans les autres modules.
- **Granularité** : deux domaines pour deux fichiers métier et une dépendance consommateur/producteur est un découpage défendable malgré le repère indicatif de 4–12. Les fusionner ou promouvoir `unittest` créerait respectivement une perte de responsabilité ou un faux domaine technique ; la carte explique correctement cette exception.
- **Cœur et priorité** : le stock porte la donnée source (`ITEMS`), tandis que la commande consomme `find_by_sku` et `available_qty` ; la distinction cœur/support est donc étayée par le code, même si la priorité reste une convention de pilotage.
- **Oublis et séparation technique** : `rg --files -uu -g '!.git/**'` ne montre, hors `.onboarding`, que `README.md`, `inventory/*.py` et `tests/*.py` (plus caches locaux). `inventory/__init__.py` et `tests/__init__.py` sont vides ; aucun autre module métier, route HTTP, job ou intégration n'est présent. Les tests sont correctement traités comme outillage hors-domaines.
- **Dépendance à la base** : `warehouse.py` contient une liste Python littérale et aucun import/accès de persistance ; `orders.py` importe uniquement le module de stock. Le `non` indiqué pour la base est vérifiable, non une supposition.
- **État courant** : exécution de `python3 -m unittest discover -s tests -t .` : 16 tests, `OK`. La carte actuelle décrit donc bien le code courant ; l'ancien récit « 3 tests, 1 échec » se trouve seulement dans la relecture existante périmée, pas dans la carte relue.

## Recommandations de correction
- Reformuler la preuve de version Python comme indiqué dans les problèmes mineurs.
- Remplacer, si souhaité, les indices génériques par les symboles propres à chaque domaine. Aucune correction de périmètre ou de domaine n'est requise.
