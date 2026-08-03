# WORKFLOW_PRELEVEMENT_COMMANDE — Génération de la liste de prélèvement triée par zone

## Classification
- **Type** : `business_process`
- **Sous-type** : transformation de lignes de commande en instructions physiques de prélèvement
- **Visibilité** : `technical` — appelé par du code, pas par une interface utilisateur
- **Acteur principal** : module appelant (ex. système d'exécution logistique)
- **Acteurs** : code appelant uniquement — aucun humain direct (le préparateur physique consommerait la sortie, mais n'est pas modélisé)
- **Criticité** : Moyenne — une erreur produit une liste de prélèvement incorrecte (article manquant, zone erronée) mais ne corrompt pas le stock
- **Confiance** : high
- **Justification** : Fonction `picking_list` lue en intégralité (`inventory/orders.py:13-21`). Sa dépendance vers `find_by_sku` a été lue. La règle de tri et le comportement sur SKU inconnu sont directement lisibles dans le code.

## Objectif
Transformer une liste de lignes de commande (paires SKU + quantité) en une feuille de prélèvement physique, ordonnée par zone d'entrepôt (A → B → C…) pour minimiser les déplacements du préparateur. Ce workflow est l'aboutissement logistique du domaine : il convertit une intention de commande en instructions exécutables terrain. Les articles dont le SKU est inconnu sont silencieusement ignorés.

## Acteurs
- Module Python appelant (ex. système d'exécution logistique, futur contrôleur de commandes)

## Points d'entrée
- `inventory.orders.picking_list(lines)` — prend une liste de tuples `(sku, qty)` ; retourne une liste de dicts `{sku, zone, qty}` triée par zone (`inventory/orders.py:13`)

## Étapes principales
1. L'appelant invoque `picking_list(lines)` avec une liste de tuples `(sku, qty)` (`inventory/orders.py:13`).
2. Pour chaque tuple `(sku, qty)` dans `lines` (`inventory/orders.py:16`) :
   a. `find_by_sku(sku)` est appelée pour localiser l'article dans le stock (`inventory/orders.py:17`, `inventory/warehouse.py:15-19`).
   b. Si l'article n'existe pas (`item is None`) : la ligne est ignorée silencieusement — `continue` (`inventory/orders.py:18-19`).
   c. L'entrée de prélèvement `{sku, zone, qty}` est construite avec la zone réelle de l'article (`inventory/orders.py:20`).
3. La liste résultante `out` est triée par la clé `"zone"` (ordre lexicographique ascendant) (`inventory/orders.py:21`).
4. La liste triée est retournée.

## Règles métier
- **Tri par zone.** La liste de prélèvement est toujours rendue dans l'ordre alphabétique croissant des zones (`sorted(..., key=lambda entry: entry["zone"])`, `inventory/orders.py:21`). Cette règle représente l'optimisation du parcours de l'entrepôt.
- **SKU inconnu → ligne ignorée silencieusement.** Si `find_by_sku` retourne `None` pour un SKU de la commande, la ligne correspondante est supprimée de la liste de prélèvement sans avertissement ni erreur (`inventory/orders.py:18-19`).
- **La quantité prélevée est celle demandée par la commande**, non la disponibilité du stock. `picking_list` n'appelle pas `available_qty` et ne contrôle pas si la quantité est couverte par le stock (`inventory/orders.py:13-21`). Aucun contrôle de disponibilité n'est réalisé dans cette fonction ; s'il doit exister, il appartient à l'appelant ou à un autre point d'entrée.
- **La zone est celle de l'article dans le stock**, sans possibilité de surcharge par la commande (`inventory/orders.py:20` : `"zone": item["zone"]`).

## Données
- Entrée : liste de tuples `(sku: str, qty: int)` — structure de données informelle, aucun objet dédié (`inventory/orders.py:16`)
- Sortie : liste de dicts `{sku: str, zone: str, qty: int}` triée par zone (`inventory/orders.py:20-21`)
- `ITEMS` (via `find_by_sku`) : référentiel stock en mémoire pour résoudre la zone de chaque SKU (`inventory/warehouse.py:3-8`)

## Intégrations
Aucune intégration externe explicite visible. Dépendance interne : `inventory.warehouse.find_by_sku` (`inventory/orders.py:3`).

## Risques
- **SKU inconnu supprimé silencieusement.** Si une ligne de commande contient un SKU non référencé, elle disparaît de la liste de prélèvement sans signal (`inventory/orders.py:18-19`). Le préparateur reçoit une liste incomplète sans le savoir. Aucun log, aucune exception, aucun compteur de lignes ignorées.
- **Quantité non contrôlée.** `picking_list` ne vérifie pas si la quantité demandée est disponible (`available_qty` n'est pas appelée). La liste peut inclure un article en rupture ou réservé au-delà du stock — ex. `CX-330` avec `reserved=50, qty=45` apparaîtra normalement dans la liste si son SKU est fourni.
- **Entrée non validée.** `lines` est supposée être un itérable de tuples `(str, int)`. Si un élément ne suit pas ce format (ex. dict, str seul), le déballage `for sku, qty in lines` lèvera `ValueError` ou `TypeError`. Aucune garde n'est présente.
- **Tri lexicographique sur les zones.** Le tri est alphabétique (`"zone"` traité comme chaîne). Cela fonctionne pour des zones à une lettre (A, B, C…), mais pourrait produire un ordre inattendu si des zones à deux caractères ou numériques sont introduites (ex. `"B10" < "B2"` dans un tri lexicographique).
- **Aucun test.** `inventory/orders.py` n'a aucune suite de test (`tests/test_warehouse.py` ne l'importe pas). Le comportement sur liste vide, SKU inconnu, ou ordre de zones n'est pas vérifié automatiquement.

## Questions ouvertes
- Doit-on signaler (log, exception, valeur de retour enrichie) les SKUs ignorés, ou le silence est-il intentionnel pour simplifier le pilote ?
- La séparation entre `can_fulfil` (contrôle) et `picking_list` (génération) suppose un workflow appelant qui invoque les deux — ce workflow d'orchestration n'existe nulle part dans le code actuel. Est-il prévu ?
- Le tri par zone est lexicographique : est-ce suffisant pour les besoins futurs, ou faudra-t-il un ordre de zones configurable ?

## Preuves
- `inventory/orders.py` — lu en intégralité
- `inventory/warehouse.py` — lu en intégralité (chaîne d'appel `find_by_sku`)
- `tests/test_warehouse.py` — lu en intégralité (absence de test sur `picking_list` confirmée)
- `CARTE_DES_DOMAINES.md` — domaine `preparation-commande`
