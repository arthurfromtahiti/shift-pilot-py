# WORKFLOW_PRELEVEMENT_COMMANDE — Génération de la liste de prélèvement triée par zone

> **RÉCONCILIÉ le 2026-08-09.** SHA de référence : `511104b`. Écarts majeurs vs version initiale : (1) `picking_list` retourne désormais `{"picks": [...], "skipped": [...]}` — plus une liste plate ; (2) le stock insuffisant n'est plus silencieux : il est **journalisé** dans `skipped` avec `order_id`, `sku`, `qty_requested`, `qty_missing` ; (3) seules les lignes invalides (qty <= 0, SKU inconnu) restent silencieuses ; (4) l'allocation cumulative utilise le **SKU canonique** (`item["sku"]`, via `canonical`) et non le SKU saisi — couvre les casses différentes du même article ; (5) `enumerate(lines)` fournit `idx` (index 0-based) comme `order_id` dans `skipped` ; (6) tous les numéros de ligne mis à jour ; (7) 10 tests (était 7).

## Classification
- **Type** : `business_process`
- **Sous-type** : transformation de lignes de commande en instructions physiques de prélèvement
- **Visibilité** : `technical` — appelé par du code, pas par une interface utilisateur
- **Acteur principal** : module appelant (ex. système d'exécution logistique)
- **Acteurs** : code appelant uniquement — aucun humain direct (le préparateur physique consommerait la sortie, mais n'est pas modélisé)
- **Criticité** : Moyenne — une erreur produit une liste de prélèvement incorrecte (article manquant, zone erronée) mais ne corrompt pas le stock
- **Confiance** : high
- **Justification** : Fonction `picking_list` lue en intégralité (`inventory/orders.py:15-46`). Ses dépendances vers `find_by_sku` et `available_qty` ont été lues. La docstring (`inventory/orders.py:16-24`) documente explicitement la distinction entre lignes invalides (silence) et lignes non servies par stock insuffisant (`skipped`). Les 10 tests de `tests/test_orders.py` ont été lus ; ils couvrent le stock insuffisant, les quantités invalides, le cumul et la casse différente. Le tri final par zones, le comportement silencieux des SKUs inconnus, l'absence de validation du format d'entrée et l'indépendance vis-à-vis de `can_fulfil` sont prouvés par lecture du code uniquement, non par les tests.

## Objectif
Transformer une liste de lignes de commande (paires SKU + quantité) en une feuille de prélèvement physique ordonnée par zone d'entrepôt (A → B → C…) pour minimiser les déplacements du préparateur, accompagnée d'un rapport des lignes non servies. Les lignes invalides (quantité nulle ou négative, SKU inconnu) sont silencieusement ignorées. Les lignes dont le stock est insuffisant sont journalisées dans `skipped` avec le détail de la carence.

## Acteurs
- Module Python appelant (ex. système d'exécution logistique, futur contrôleur de commandes)

## Points d'entrée
- `inventory.orders.picking_list(lines)` — prend une liste de tuples `(sku, qty)` ; retourne un dict `{"picks": [...], "skipped": [...]}` où `picks` est triée par zone et `skipped` liste les lignes non servies (`inventory/orders.py:15`)

## Étapes principales
1. L'appelant invoque `picking_list(lines)` avec une liste de tuples `(sku, qty)` (`inventory/orders.py:15`).
2. Initialisation de `picks = []`, `skipped = []`, et `allocated = {}` pour cumuler les allocations par SKU canonique dans la même commande (`inventory/orders.py:25-27`).
3. Pour chaque tuple `(sku, qty)` dans `lines`, avec son index `idx` (via `enumerate`) (`inventory/orders.py:28`) :
   a. **Rejet silencieux des quantités invalides :** si `qty <= 0`, la ligne est ignorée sans trace dans `picks` ni `skipped` (`inventory/orders.py:29-30`).
   b. `find_by_sku(sku)` est appelée pour récupérer l'article ; si `None`, **la ligne est ignorée silencieusement** — SKU inconnu ne figure pas dans `skipped` (`inventory/orders.py:31-33`).
   c. `canonical = item["sku"]` — le SKU canonique de l'article (majuscules du référentiel) est extrait pour normaliser les allocations quelle que soit la casse saisie (`inventory/orders.py:34`).
   d. Calcul de la disponibilité restante : `remaining = available_qty(item) - allocated.get(canonical, 0)` — soustrait les allocations déjà cumulées pour ce SKU canonique dans cette commande (`inventory/orders.py:35`).
   e. **Stock insuffisant → journalisation dans `skipped` :** si `qty > remaining`, la ligne est ajoutée à `skipped` avec `{"order_id": idx, "sku": sku, "qty_requested": qty, "qty_missing": qty - remaining}` — `idx` est la position 0-based de la ligne dans `lines` (`inventory/orders.py:36-43`).
   f. **Stock suffisant → allocation et prélèvement :** mise à jour de `allocated[canonical]`, ajout de `{"sku": sku, "zone": item["zone"], "qty": qty}` à `picks` (`inventory/orders.py:44-45`).
4. `picks` est triée par la clé `"zone"` (ordre lexicographique ascendant) et le résultat final `{"picks": sorted_picks, "skipped": skipped}` est retourné (`inventory/orders.py:46`).

## Règles métier
- **Tri par zone.** La liste `picks` est toujours rendue dans l'ordre alphabétique croissant des zones (`sorted(..., key=lambda entry: entry["zone"])`, `inventory/orders.py:46`). Cette règle représente l'optimisation du parcours de l'entrepôt.
- **Distinction silence vs journalisation.** Deux classes de lignes exclues : (a) **silencieuses** — `qty <= 0` ou SKU inconnu : aucune trace dans `picks` ni `skipped` (`inventory/orders.py:29-33`) ; (b) **journalisées** — stock insuffisant : entrée dans `skipped` avec le détail de la carence (`inventory/orders.py:36-43`). La docstring énonce cette distinction explicitement (`inventory/orders.py:21-24`).
- **Allocation cumulative par SKU canonique.** Plusieurs lignes du même article (même SKU, même casse ou casse différente) cumulent leurs allocations via `allocated[canonical]`. La disponibilité restante pour la n-ième ligne est `available_qty(item) - sum(allocations précédentes du même canonical)` (`inventory/orders.py:35, 44`). Exemple : `AX-100` (available=10) avec lignes `("AX-100", 6)` puis `("ax-100", 6)` → même `canonical="AX-100"` → remaining=4 pour la 2e ligne → skipped avec `qty_missing=2`.
- **La zone est celle de l'article dans le stock**, sans possibilité de surcharge par la commande (`inventory/orders.py:45` : `"zone": item["zone"]`).
- **`order_id` = index de la ligne dans `lines` (0-based).** La valeur provient de `enumerate(lines)` (`inventory/orders.py:28`). Elle permet à l'appelant de relier chaque entrée `skipped` à sa ligne d'origine dans le tableau de commande.
- **`can_fulfil` n'est pas appelé.** `picking_list` effectue sa propre vérification de disponibilité de façon cumulative, indépendamment de `can_fulfil` (`inventory/orders.py:35-36`). Un appel préalable à `can_fulfil` ne garantit pas l'inclusion dans `picks` si plusieurs lignes du même SKU sont présentes.

## Données
- **Entrée :** liste de tuples `(sku: str, qty: int)` — structure de données informelle, aucun objet dédié (`inventory/orders.py:28`)
- **Sortie :** dict `{"picks": [{"sku": str, "zone": str, "qty": int}, ...], "skipped": [{"order_id": int, "sku": str, "qty_requested": int, "qty_missing": int}, ...]}` — `picks` triée par zone, `skipped` dans l'ordre des lignes d'origine (`inventory/orders.py:46`)
- `ITEMS` (via `find_by_sku` et `available_qty`) : référentiel stock en mémoire pour résoudre la zone de chaque SKU et vérifier la disponibilité (`inventory/warehouse.py:3-8`)

## Intégrations
Aucune intégration externe explicite visible. Dépendances internes directes : `inventory.warehouse.find_by_sku` et `inventory.warehouse.available_qty` (`inventory/orders.py:3, 31, 35`). `can_fulfil()` n'est pas appelée par `picking_list()`.

## Risques
- **SKU inconnu supprimé silencieusement (sans trace dans `skipped`).** Si une ligne contient un SKU non référencé, elle disparaît sans signal — ni dans `picks`, ni dans `skipped` (`inventory/orders.py:32-33`). Le préparateur reçoit une liste incomplète sans le savoir. Ce comportement est documenté dans la docstring (`inventory/orders.py:23`), mais l'appelant doit le connaître pour ne pas interpréter silence comme succès.
- **Entrée non validée en type.** `lines` est supposée être un itérable de tuples `(str, int)`. Si un élément ne suit pas ce format (ex. dict, str seul, tuple à trois éléments), le déballage `for idx, (sku, qty) in enumerate(lines)` lèvera `ValueError` ou `TypeError`. Aucune garde n'est présente.
- **Tri lexicographique sur les zones.** Le tri est alphabétique (`"zone"` traité comme chaîne). Cela fonctionne pour des zones à une lettre (A, B, C…), mais pourrait produire un ordre inattendu si des zones à deux caractères ou numériques sont introduites (ex. `"B10" < "B2"` dans un tri lexicographique).
- **Cumul intra-commande peut dérouter un appelant ignorant de son existence.** La disponibilité restante pour la n-ième ligne du même SKU prend en compte les allocations des lignes précédentes de la même commande. Un appelant qui ne lit pas la doc peut s'attendre à ce que chaque ligne soit vérifiée contre la capacité totale du stock, et non contre le résiduel après allocations précédentes.

## Questions ouvertes
- Doit-on journaliser les SKUs inconnus dans `skipped`, ou le silence est-il intentionnel pour simplifier le pilote ? La distinction actuelle (silence pour inconnu, journalisation pour insuffisant) est cohérente mais asymétrique.
- Le tri par zone est lexicographique : est-ce suffisant pour les besoins futurs, ou faudra-t-il un ordre de zones configurable (ex. plan d'entrepôt) ?
- `picking_list` et `can_fulfil` sont indépendantes : si on les compose (appel de `can_fulfil` par SKU puis `picking_list` sur la commande), les résultats peuvent diverger sur des commandes multi-lignes pour le même SKU. Cette divergence doit-elle être documentée ou résolue par une API unifiée ?

## Preuves
- `inventory/orders.py` — lu en intégralité (lignes 1-46)
- `inventory/warehouse.py` — lu en intégralité (chaîne d'appel directe via `find_by_sku` et `available_qty`)
- `tests/test_orders.py` — lu en intégralité (10 tests : `test_article_hors_stock_exclu_des_picks`, `test_article_hors_stock_journalise_dans_skipped`, `test_cx330_inclus_dans_picks`, `test_quantite_nulle_exclue_sans_trace`, `test_quantite_negative_exclue_sans_trace`, `test_plusieurs_lignes_meme_sku_depassement_exclu_des_picks`, `test_plusieurs_lignes_meme_sku_depassement_journalise_dans_skipped`, `test_plusieurs_lignes_meme_sku_dans_les_limites`, `test_plusieurs_lignes_meme_sku_allocation_cumulative`, `test_meme_article_casse_differente_cumul_respecte`)
- `.onboarding/domaines/CARTE_DES_DOMAINES.md` — domaine `preparation-commande` (réconcilié)
