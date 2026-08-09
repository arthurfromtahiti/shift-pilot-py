# Points chauds du code — Audit

> Confiance : high

## Compréhension globale

Le projet fait 74 lignes de code source réparties sur deux fichiers (`inventory/warehouse.py` : 28 lignes, `inventory/orders.py` : 46 lignes). À cette taille, la notion de « fichier gros ou couplé » n'a pas de sens absolu : les deux fichiers sont courts par nature. L'analyse des points chauds se concentre sur les fonctions à risque élevé par rapport à leur périmètre fonctionnel, les absences de tests, et les couplages internes qui fragilisent le code.

Deux fonctions constituent les points chauds du projet : `available_qty()` (`inventory/warehouse.py:22-24`) qui est le fondement de toute la chaîne logistique et dont l'invariant est maintenant garanti par `max(0, ...)` et encodé par des tests présents, et `picking_list()` (`inventory/orders.py:15-46`) parce qu'elle combine plusieurs comportements à risque (silence sur SKU inconnu, absence de validation d'entrée, tri lexicographique non explicité). `picking_list()` a une bonne couverture de tests (10 tests) après les correctifs SHIAAAAAAAAAAAAAAAAAAAAAAAA-316, -442 et -507, mais les cas liste vide, SKU inconnu seul, et tri de zones multiples ne sont pas couverts. `can_fulfil()` est un point chaud secondaire — logique critique, zéro test. `warehouse.py` dans son ensemble est le fichier le plus sensible : toute modification de sa structure impacte immédiatement les deux modules et la suite de tests.

## Constats détaillés

**VÉRIFIÉ_CODE — `available_qty()` : invariant garanti, fondement de la chaîne.** Cette fonction de 2 lignes (`inventory/warehouse.py:22-24`) retourne `max(0, item["qty"] - item["reserved"])` avec une borne inférieure garantie. Pour `CX-330` (qty=45, reserved=5), le retour est `40`. Ce retour se propage vers `can_fulfil()` (`inventory/orders.py:12`) et `picking_list()` (`inventory/orders.py:35`). Deux tests encodent l'invariant `disponible ≥ 0` et le cas `reserved > qty` (`tests/test_warehouse.py:14-23`) — voir TESTING_AUDIT.md pour la confirmation d'exécution.

**VÉRIFIÉ_CODE — `can_fulfil()` : logique critique sans test.** Cette fonction de 7 lignes (`inventory/orders.py:6-12`) est la garde-barrière logistique : elle rejette les quantités nulles ou négatives (`inventory/orders.py:7-8`), puis vérifie la disponibilité via `available_qty()`. Une fausse réponse autoriserait une commande infaisable ou refuserait une commande réalisable. Elle n'a aucun test dans la suite de tests actuels — `tests/test_orders.py` importe uniquement `picking_list`, pas `can_fulfil`.

**VÉRIFIÉ_CODE — `picking_list()` : plusieurs comportements à risque, couverture bonne.** Cette fonction de 32 lignes (`inventory/orders.py:15-46`) cumule : (1) déstructuration de tuple sans validation (`for idx, (sku, qty) in enumerate(lines)` — un format incorrect lève `ValueError`, `inventory/orders.py:28`), (2) abandon silencieux des SKUs inconnus (`continue`, `inventory/orders.py:32-33`), (3) tri lexicographique sur `zone` (`inventory/orders.py:46`) — l'ordre lexicographique est correct pour les zones à une lettre existantes (A, B, C) ; HYPOTHÈSE : un ordre lexicographique peut ne pas correspondre à l'ordre métier attendu si des zones multi-caractères sont introduites. Elle implémente le cumul intra-commande via le dict `allocated` indexé sur le SKU canonique (`inventory/orders.py:27, 35, 44`) et journalise les lignes hors stock dans `skipped`. Dix tests couvrent les cas nominaux et critiques (articles hors stock, journalisation `skipped`, disponibles, quantités invalides, cumul intra-commande, casse), mais les cas liste vide, SKU inconnu seul, et tri de zones multiples ne sont pas couverts.

**VÉRIFIÉ_CODE — `warehouse.py` : fichier pivot sans abstraction.** `warehouse.py` est l'unique source de données, exporteur de primitives et détenteur de l'état global `ITEMS`. Tout couplage vers lui (`orders.py:3`, `tests/test_warehouse.py:3`) crée une dépendance directe à sa structure interne. Un changement de schéma dans `ITEMS` (renommer `qty` en `quantity`) casse simultanément `orders.py`, `tests/test_warehouse.py` et `warehouse.py` lui-même.

**VÉRIFIÉ_CODE — `list_items()` : retourne une référence directe sans garde.** Une ligne (`inventory/warehouse.py:11-12`), mais un vecteur de mutation : quiconque itère et modifie `list_items()` altère `ITEMS` en place pour tous les appelants suivants.

## Forces

- **Aucun fichier de plus de 46 lignes.** La base de code est minuscule et entièrement lisible en quelques minutes — aucun hotspot de volume.
- **Invariant de disponibilité garanti par le code et encodé par des tests.** `available_qty()` retourne `max(0, qty - reserved)` ; les autres fonctions de `warehouse.py` (`find_by_sku`, `items_in_zone`, `list_items`) se comportent correctement pour leur contrat (voir TESTING_AUDIT.md pour la confirmation d'exécution).
- **Dépendances internes visibles d'un coup d'œil.** Le graphe de dépendance est `orders → warehouse`, sans cycle, sans indirection. Un senior comprend l'ensemble du couplage en lisant la ligne d'import de `orders.py`.

## Dettes techniques

- **`can_fulfil()` sans test, `picking_list()` bonne couverture.** `can_fulfil()` reste entièrement non testée. `picking_list()` dispose de 10 tests couvrant les cas nominaux et critiques, mais `can_fulfil()` n'est couverte par aucun test (`tests/test_orders.py` importe uniquement `picking_list`). (`inventory/orders.py:6-46`)
- **`picking_list()` silencieuse sur SKU inconnu et quantités invalides.** Le `continue` sur SKU inconnu (`inventory/orders.py:32-33`) et sur quantité invalide (`inventory/orders.py:29-30`) transforme un problème de données en résultat silencieusement tronqué. Seul le stock insuffisant est journalisé dans `skipped` ; les SKUs inconnus disparaissent sans trace.
- **Couplage fort à la structure du dict `ITEMS`.** Les fonctions de `warehouse.py` et `orders.py` accèdent directement aux clés de dict (`item["qty"]`, `item["reserved"]`, `item["zone"]`). Un renommage exige une recherche manuelle dans tout le code.

## Zones critiques

- **`inventory/warehouse.py:22-24` (`available_qty`)** — Fondement de toute la chaîne ; invariant `disponible ≥ 0` garanti par `max(0, ...)` et encodé par deux tests présents. Toute modification de cette fonction impacte `can_fulfil()` et `picking_list()` en cascade.
- **`inventory/orders.py:15-46` (`picking_list`)** — Fonction la plus complexe du projet (5 comportements distincts en 32 lignes : rejet des quantités invalides, recherche du SKU, vérification de disponibilité via `allocated`, cumul intra-commande sur SKU canonique, journalisation `skipped`, tri). Dix tests couvrent les cas principaux.
- **`inventory/warehouse.py:3-8` (`ITEMS`)** — Source de vérité unique. Toute modification ici se propage à tout le code.

## Risques

- **VÉRIFIÉ_CODE — `can_fulfil()` : zéro test, dépendance directe à `available_qty()`.** `can_fulfil()` n'a aucun test dans la suite existante (`tests/test_orders.py` importe uniquement `picking_list`, `inventory/orders.py:6-12`) et appelle directement `available_qty()` (`inventory/orders.py:12`).
- **HYPOTHÈSE — Régression invisible sur `can_fulfil()` si `available_qty()` est modifié.** Toute modification de `available_qty()` (changement de formule, suppression du `max(0, ...)`) change silencieusement le comportement de `can_fulfil()` sans qu'aucun test l'intercepte — la régression ne serait détectée qu'à l'exécution manuelle ou via des tests manuels.
- **VÉRIFIÉ_CODE — `picking_list()` : `continue` silencieux sur SKU inconnu.** Lorsque `find_by_sku(sku)` retourne `None`, `picking_list()` exécute un `continue` sans log, sans compteur et sans valeur de retour enrichie (`inventory/orders.py:32-33`). Ce silence est distinct du mécanisme `skipped` qui journalise uniquement les stocks insuffisants.
- **HYPOTHÈSE — Prélèvement incomplet sans signal si un SKU est absent de `ITEMS`.** Dans un contexte où une ligne de commande contient un SKU absent, ce silence constitue un vecteur d'incident : un article non trouvé disparaît de la liste de picking sans signal vers l'appelant.
- **HYPOTHÈSE — Casse en cascade sur changement de schéma `ITEMS`.** Renommer ou ajouter un champ dans les dicts de `ITEMS` sans mettre à jour toutes les références (5 accès de clé différents dans les deux modules) produirait des `KeyError` à l'exécution.

## Recommandations priorisées

1. **Ajouter des tests pour `can_fulfil()`** — À minima : SKU inconnu, quantité demandée nulle ou négative, SKU disponible, SKU en rupture. `picking_list()` dispose maintenant d'une bonne couverture. (`tests/test_orders.py`)
2. **Ajouter un signal explicite dans `picking_list()` sur SKU inconnu ignoré** — Un `warnings.warn()` ou une entrée dans un troisième retour (ex. `"invalid"`) évite le résultat silencieusement incomplet. (`inventory/orders.py:32-33`)
3. **Typer `ITEMS` pour externaliser le couplage de schéma** — Un `TypedDict` ou une dataclass centralise la définition du schéma et rend les accès de clé vérifiables statiquement. (`inventory/warehouse.py:3-8`)

## Questions ouvertes

- `picking_list()` est-elle censée appeler `can_fulfil()` avant de construire la liste, ou la vérification de disponibilité appartient-elle à l'orchestrateur appelant ? La séparation actuelle crée un flux à deux appels sans orchestrateur visible.
- La décision de ne pas avoir de tests pour `orders.py` est-elle une omission ou un exercice intentionnel laissé à l'apprenant ?
