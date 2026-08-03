# Relecture — CARTE_DES_DOMAINES.md

## Verdict global
Bon — la carte décrit correctement un dépôt minuscule centré sur deux capacités métier réelles et distinctes: le stock d'entrepôt et la préparation de commande. Les domaines sont prouvés par des fichiers et symboles précis, les indices de rattachement sont discriminants, et je n'ai trouvé ni domaine inventé ni pan métier omis.

## Problèmes bloquants
Aucun.

## Problèmes mineurs
- La section "Nature du projet" sur-spécifie `Python 3.12` en s'appuyant sur des `__pycache__`, alors que le checkout contient aussi des `.cpython-313.pyc`. Ce point n'affecte pas la carte des domaines elle-même, mais la version exacte de l'interpréteur n'est pas prouvée proprement par cette seule trace.

## Points vérifiés et corrects
- Le domaine `entrepot-stock` est réel et central: `inventory/warehouse.py` porte les données (`ITEMS`) et les opérations `list_items`, `find_by_sku`, `available_qty`, `items_in_zone`.
- Le domaine `preparation-commande` est réel et séparé du précédent par sa responsabilité: `inventory/orders.py` expose `can_fulfil` et `picking_list`, tout en dépendant explicitement de `inventory.warehouse` via `from inventory.warehouse import find_by_sku, available_qty`.
- Les indices de rattachement sont discriminants et ne matchent pas "tout le repo": `available_qty`, `items_in_zone`, `reserved`, `zone` renvoient au stock; `can_fulfil`, `picking_list`, `requested`, `lines` renvoient à la préparation de commande.
- La séparation du harnais de tests hors des domaines métier est correcte: `tests/test_warehouse.py` ne porte aucune capacité produit autonome et ne couvre que `inventory/warehouse.py`; `inventory/orders.py` n'a pas de tests dédiés.
- Le cœur fonctionnel annoncé par la carte est conforme au dépôt et au `README.md`: stock en mémoire, préparation de commande dérivée, absence de couche HTTP, de base de données et de persistance.
- Je n'ai trouvé aucun autre pan métier caché dans le reste du dépôt: `inventory/__init__.py` et `tests/__init__.py` sont vides, et l'inventaire complet ne montre pas d'autres modules source.
- La vérification exécutable citée dans la carte est exacte: `python3 -m unittest discover -s tests -t .` exécute bien `3` tests avec `1` échec sur `test_available_qty_never_negative` (`-5 != 0`).

## Recommandations de correction
- Optionnel: remplace la mention `Python 3.12` par une formulation plus sobre (`Python 3`, ou `stdlib uniquement`) tant que la version exacte n'est pas prouvée autrement que par des artefacts `__pycache__`.
