# WORKFLOW_PRELEVEMENT_COMMANDE — Génération de la liste de prélèvement triée par zone

## Classification
- **Type** : `business_process`
- **Sous-type** : transformation de lignes de commande en instructions physiques de prélèvement
- **Visibilité** : `technical` — appelé par du code, pas par une interface utilisateur
- **Acteur principal** : module appelant (ex. système d'exécution logistique)
- **Acteurs** : code appelant uniquement — aucun humain direct (le préparateur physique consommerait la sortie, mais n'est pas modélisé)
- **Criticité** : Moyenne — une erreur produit une liste de prélèvement incorrecte (article manquant, zone erronée) mais ne corrompt pas le stock
- **Confiance** : high
- **Justification** : Fonction `picking_list` lue en intégralité (`inventory/orders.py:15-35`). Ses dépendances vers `find_by_sku` et `available_qty` ont été lues. La règle de tri et le comportement sur SKU inconnu ou indisponibilité, ainsi que le cumul intra-commande, sont directement lisibles dans le code.

## Objectif
Transformer une liste de lignes de commande (paires SKU + quantité) en une feuille de prélèvement physique, ordonnée par zone d'entrepôt (A → B → C…) pour minimiser les déplacements du préparateur. Ce workflow est l'aboutissement logistique du domaine : il convertit une intention de commande en instructions exécutables terrain. Les articles dont le SKU est inconnu ou dont la disponibilité est insuffisante sont silencieusement ignorés.

## Acteurs
- Module Python appelant (ex. système d'exécution logistique, futur contrôleur de commandes)

## Points d'entrée
- `inventory.orders.picking_list(lines)` — prend une liste de tuples `(sku, qty)` ; retourne une liste de dicts `{sku, zone, qty}` triée par zone (`inventory/orders.py:15`)

## Étapes principales
1. L'appelant invoque `picking_list(lines)` avec une liste de tuples `(sku, qty)` (`inventory/orders.py:15`).
2. Initialisation d'un dict `allocated` pour cumuler les allocations par SKU dans la même commande (`inventory/orders.py:23`).
3. Pour chaque tuple `(sku, qty)` dans `lines` (`inventory/orders.py:24`) :
   a. Rejet des quantités nulles ou négatives (`inventory/orders.py:25-26`).
   b. `find_by_sku(sku)` est appelée pour récupérer l'article ; si `None`, la ligne est ignorée silencieusement (`inventory/orders.py:27-29`, `inventory/warehouse.py:15-19`).
   c. Calcul de la disponibilité restante : `remaining = available_qty(item) - allocated.get(sku, 0)` (`inventory/orders.py:30`). Cela soustrait les allocations précédentes du même SKU déjà cumulées dans cette commande.
   d. Si `qty > remaining`, la ligne est ignorée silencieusement (`inventory/orders.py:31-32`).
   e. Mise à jour de l'allocation cumulative : `allocated[sku] = allocated.get(sku, 0) + qty` (`inventory/orders.py:33`).
   f. L'entrée de prélèvement `{sku, zone, qty}` est construite avec la zone réelle de l'article et ajoutée à la liste (`inventory/orders.py:34`).
4. La liste résultante `out` est triée par la clé `"zone"` (ordre lexicographique ascendant) (`inventory/orders.py:35`).
5. La liste triée est retournée.

## Règles métier
- **Tri par zone.** La liste de prélèvement est toujours rendue dans l'ordre alphabétique croissant des zones (`sorted(..., key=lambda entry: entry["zone"])`, `inventory/orders.py:35`). Cette règle représente l'optimisation du parcours de l'entrepôt.
- **SKU inconnu ou indisponible → ligne ignorée silencieusement.** Si le SKU est introuvable ou si la disponibilité restante (après cumul intra-commande) est insuffisante, la ligne correspondante est supprimée de la liste de prélèvement sans avertissement ni erreur (`inventory/orders.py:27-32`).
- **Vérification de disponibilité intégrée.** `picking_list()` vérifie la disponibilité directement, sans appeler `can_fulfil()`. Pour chaque ligne, elle calcule `remaining = available_qty(item) - allocated.get(sku, 0)` et exclut si `qty > remaining` (`inventory/orders.py:30-32`). Seules les lignes faisables sont incluées.
- **Cumul intra-commande.** Plusieurs lignes du même SKU dans la même commande cumulent leurs allocations. La disponibilité restante pour la n-ième ligne est `available_qty(item)` moins la somme des allocations précédentes du même SKU (`inventory/orders.py:30, 33`). Un exemple : CX-330 (available=40) avec deux lignes de 30 et 30 → la 1ère incluse (30 ≤ 40), la 2e exclue (30 > 40-30).
- **La zone est celle de l'article dans le stock**, sans possibilité de surcharge par la commande (`inventory/orders.py:34` : `"zone": item["zone"]`).

## Données
- Entrée : liste de tuples `(sku: str, qty: int)` — structure de données informelle, aucun objet dédié (`inventory/orders.py:24`)
- Sortie : liste de dicts `{sku: str, zone: str, qty: int}` triée par zone (`inventory/orders.py:34-35`)
- `ITEMS` (via `find_by_sku` et `available_qty`) : référentiel stock en mémoire pour résoudre la zone de chaque SKU et vérifier la disponibilité (`inventory/warehouse.py:3-8`)

## Intégrations
Aucune intégration externe explicite visible. Dépendances internes directes : `inventory.warehouse.find_by_sku` et `inventory.warehouse.available_qty` (`inventory/orders.py:3, 27, 30`). `can_fulfil()` n'est pas appelée par `picking_list()` — les deux fonctions restent indépendantes.

## Risques
- **SKU inconnu ou indisponible supprimé silencieusement.** Si une ligne de commande contient un SKU non référencé ou dont la disponibilité est insuffisante, elle disparaît de la liste de prélèvement sans signal (`inventory/orders.py:27-32`). Le préparateur reçoit une liste incomplète sans le savoir. Aucun log, aucune exception, aucun compteur de lignes ignorées.
- **Entrée non validée.** `lines` est supposée être un itérable de tuples `(str, int)`. Si un élément ne suit pas ce format (ex. dict, str seul), le déballage `for sku, qty in lines` lèvera `ValueError` ou `TypeError`. Aucune garde n'est présente.
- **Tri lexicographique sur les zones.** Le tri est alphabétique (`"zone"` traité comme chaîne). Cela fonctionne pour des zones à une lettre (A, B, C…), mais pourrait produire un ordre inattendu si des zones à deux caractères ou numériques sont introduites (ex. `"B10" < "B2"` dans un tri lexicographique).
- **Cumul intra-commande peut dérouter un appelant ignorant de son existence.** La disponibilité restante pour la n-ième ligne du même SKU prend en compte les allocations des lignes précédentes. Un appelant qui ne lit pas le code ou la doc peut s'attendre à ce que chaque ligne soit vérifiée indépendamment (capacité totale du stock), et non cumulativement (capacité restante après allocations précédentes de la même commande).

## Questions ouvertes
- Doit-on signaler (log, exception, valeur de retour enrichie) les SKUs ignorés, ou le silence est-il intentionnel pour simplifier le pilote ?
- Après le correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-316, `can_fulfil()` et `picking_list()` sont maintenant complètement indépendantes et se comportent différemment sur le cumul intra-commande : `can_fulfil(sku, qty)` vérifie si le stock total peut satisfaire la quantité (statique), tandis que `picking_list()` cumule les allocations dans une même commande (dynamique). Cette divergence intentionnelle doit-elle être documentée dans la couche métier ou dans l'orchestrateur futur qui les utiliserait ensemble ?
- Le tri par zone est lexicographique : est-ce suffisant pour les besoins futurs, ou faudra-t-il un ordre de zones configurable ?

## Preuves
- `inventory/orders.py` — lu en intégralité (lignes 1-36)
- `inventory/warehouse.py` — lu en intégralité (chaîne d'appel directe via `find_by_sku` et `available_qty`)
- `tests/test_orders.py` — lu en intégralité (7 tests couvrant cumul intra-commande, quantités nulles/négatives, articles hors stock)
- `CARTE_DES_DOMAINES.md` — domaine `preparation-commande`
