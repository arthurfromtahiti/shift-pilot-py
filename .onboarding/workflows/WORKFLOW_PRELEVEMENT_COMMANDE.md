# WORKFLOW_PRELEVEMENT_COMMANDE — Génération de la liste de prélèvement triée par zone

## Classification
- **Type** : `business_process`
- **Sous-type** : transformation de lignes de commande en instructions physiques de prélèvement
- **Visibilité** : `technical` — appelé par du code, pas par une interface utilisateur
- **Acteur principal** : module appelant (ex. système d'exécution logistique)
- **Acteurs** : code appelant uniquement — aucun humain direct (le préparateur physique consommerait la sortie, mais n'est pas modélisé)
- **Criticité** : Moyenne — une erreur produit une liste de prélèvement incorrecte (article manquant, zone erronée) mais ne corrompt pas le stock
- **Confiance** : high
- **Justification** : Fonction `picking_list` lue en intégralité (`inventory/orders.py:13-24`). Sa dépendance vers `can_fulfil` et `find_by_sku` a été lue. La règle de tri et le comportement sur SKU inconnu ou indisponibilité sont directement lisibles dans le code.

## Objectif
Transformer une liste de lignes de commande (paires SKU + quantité) en une feuille de prélèvement physique, ordonnée par zone d'entrepôt (A → B → C…) pour minimiser les déplacements du préparateur. Ce workflow est l'aboutissement logistique du domaine : il convertit une intention de commande en instructions exécutables terrain. Les articles dont le SKU est inconnu ou dont la disponibilité est insuffisante sont silencieusement ignorés.

## Acteurs
- Module Python appelant (ex. système d'exécution logistique, futur contrôleur de commandes)

## Points d'entrée
- `inventory.orders.picking_list(lines)` — prend une liste de tuples `(sku, qty)` ; retourne une liste de dicts `{sku, zone, qty}` triée par zone (`inventory/orders.py:13`)

## Étapes principales
1. L'appelant invoque `picking_list(lines)` avec une liste de tuples `(sku, qty)` (`inventory/orders.py:13`).
2. Pour chaque tuple `(sku, qty)` dans `lines` (`inventory/orders.py:19`) :
   a. `can_fulfil(sku, qty)` est appelée pour vérifier que l'article existe et que sa disponibilité couvre la quantité demandée (`inventory/orders.py:20`, `inventory/orders.py:6-10`).
   b. Si la vérification échoue (SKU inexistant ou quantité insuffisante) : la ligne est ignorée silencieusement — `continue` (`inventory/orders.py:21`).
   c. `find_by_sku(sku)` est appelée pour récupérer les détails de l'article (`inventory/orders.py:22`, `inventory/warehouse.py:15-19`).
   d. L'entrée de prélèvement `{sku, zone, qty}` est construite avec la zone réelle de l'article (`inventory/orders.py:23`).
3. La liste résultante `out` est triée par la clé `"zone"` (ordre lexicographique ascendant) (`inventory/orders.py:24`).
4. La liste triée est retournée.

## Règles métier
- **Tri par zone.** La liste de prélèvement est toujours rendue dans l'ordre alphabétique croissant des zones (`sorted(..., key=lambda entry: entry["zone"])`, `inventory/orders.py:24`). Cette règle représente l'optimisation du parcours de l'entrepôt.
- **SKU inconnu ou indisponible → ligne ignorée silencieusement.** Si `can_fulfil(sku, qty)` retourne `False` (SKU inexistant ou quantité disponible insuffisante), la ligne correspondante est supprimée de la liste de prélèvement sans avertissement ni erreur (`inventory/orders.py:20-21`).
- **Vérification préalable de disponibilité.** `picking_list` appelle `can_fulfil(sku, qty)` pour chaque ligne avant inclusion dans la liste de prélèvement (`inventory/orders.py:20`, `inventory/orders.py:6-10`). Seules les lignes faisables sont incluées.
- **La zone est celle de l'article dans le stock**, sans possibilité de surcharge par la commande (`inventory/orders.py:23` : `"zone": item["zone"]`).

## Données
- Entrée : liste de tuples `(sku: str, qty: int)` — structure de données informelle, aucun objet dédié (`inventory/orders.py:19`)
- Sortie : liste de dicts `{sku: str, zone: str, qty: int}` triée par zone (`inventory/orders.py:23-24`)
- `ITEMS` (via `find_by_sku` et `can_fulfil`) : référentiel stock en mémoire pour résoudre la zone de chaque SKU et vérifier la disponibilité (`inventory/warehouse.py:3-8`)

## Intégrations
Aucune intégration externe explicite visible. Dépendances internes : `inventory.warehouse.find_by_sku` et `inventory.warehouse.available_qty` (via `can_fulfil`) (`inventory/orders.py:3, 6-10`).

## Risques
- **SKU inconnu ou indisponible supprimé silencieusement.** Si une ligne de commande contient un SKU non référencé ou dont la disponibilité est insuffisante, elle disparaît de la liste de prélèvement sans signal (`inventory/orders.py:20-21`). Le préparateur reçoit une liste incomplète sans le savoir. Aucun log, aucune exception, aucun compteur de lignes ignorées.
- **Entrée non validée.** `lines` est supposée être un itérable de tuples `(str, int)`. Si un élément ne suit pas ce format (ex. dict, str seul), le déballage `for sku, qty in lines` lèvera `ValueError` ou `TypeError`. Aucune garde n'est présente.
- **Tri lexicographique sur les zones.** Le tri est alphabétique (`"zone"` traité comme chaîne). Cela fonctionne pour des zones à une lettre (A, B, C…), mais pourrait produire un ordre inattendu si des zones à deux caractères ou numériques sont introduites (ex. `"B10" < "B2"` dans un tri lexicographique).
- **Tests limités.** `tests/test_orders.py` couvre uniquement le cas d'un article hors stock (`BX-220`). Le comportement sur liste vide, SKU inconnu seul, ou ordre de zones multiples n'est pas vérifié.

## Questions ouvertes
- Doit-on signaler (log, exception, valeur de retour enrichie) les SKUs ignorés, ou le silence est-il intentionnel pour simplifier le pilote ?
- La séparation entre `can_fulfil` (contrôle) et `picking_list` (génération) suppose un workflow appelant qui invoque les deux — ce workflow d'orchestration n'existe nulle part dans le code actuel. Est-il prévu ?
- Le tri par zone est lexicographique : est-ce suffisant pour les besoins futurs, ou faudra-t-il un ordre de zones configurable ?

## Preuves
- `inventory/orders.py` — lu en intégralité (lignes 1-25)
- `inventory/warehouse.py` — lu en intégralité (chaîne d'appel via `can_fulfil`)
- `tests/test_orders.py` — lu en intégralité (test du cas `BX-220` hors stock)
- `CARTE_DES_DOMAINES.md` — domaine `preparation-commande`
