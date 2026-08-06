# Points chauds du code — Audit

> Confiance : high

## Compréhension globale

Le projet fait 56 lignes de code source réparties sur deux fichiers (`inventory/warehouse.py` : 34 lignes, `inventory/orders.py` : 22 lignes). À cette taille, la notion de « fichier gros ou couplé » n'a pas de sens absolu : les deux fichiers sont courts par nature. L'analyse des points chauds se concentre sur les fonctions à risque élevé par rapport à leur périmètre fonctionnel, les absences de tests, et les couplages internes qui fragilisent le code.

Deux fonctions constituent les points chauds du projet : `available_qty()` (`inventory/warehouse.py:22-24`) parce qu'elle porte le bug documenté et est le fondement de toute la chaîne logistique, et `picking_list()` (`inventory/orders.py:15-35`) parce qu'elle combine plusieurs comportements à risque (silence sur SKU inconnu, absence de validation d'entrée, tri lexicographique non explicité). `picking_list()` a désormais une bonne couverture de tests (6 tests) après le correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-316, mais les tests ne couvrent pas tous les cas limites. `can_fulfil()` est un point chaud secondaire — logique critique, zéro test. `warehouse.py` dans son ensemble est le fichier le plus sensible : toute modification de sa structure impacte immédiatement les deux modules et la suite de tests.

## Constats détaillés

**VÉRIFIÉ_CODE — `available_qty()` : bug documenté, propagation en cascade.** Cette fonction de 2 lignes (`inventory/warehouse.py:22-24`) est le point de défaillance central du projet. Elle retourne `max(0, item["qty"] - item["reserved"])` avec une borne inférieure garantie. Pour `CX-330`, le retour est `max(0, 45-5) = 40` (et non `-5` avant le correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-231). Ce retour se propage vers `can_fulfil()` (`inventory/orders.py:10`) où il détermine une décision binaire commerciale. Un test vert valide l'invariant `disponible ≥ 0` (`tests/test_warehouse.py:14-18`). C'est la seule fonction qui dispose d'un test dédié — ce qui en fait la mieux documentée.

**VÉRIFIÉ_CODE — `can_fulfil()` : logique critique sans test.** Cette fonction de 4 lignes (`inventory/orders.py:6-10`) est la garde-barrière logistique : une fausse réponse autorise une commande infaisable ou refuse une commande réalisable. Elle n'a aucun test dans la suite de tests actuels (`tests/test_warehouse.py` n'importe pas `orders`). Elle hérite silencieusement du bug de `available_qty()` pour `CX-330`, mais par chance arithmétique le comportement reste correct pour `requested ≥ 0`.

**VÉRIFIÉ_CODE — `picking_list()` : trois comportements à risque, couverture améliorée.** Cette fonction de 21 lignes (`inventory/orders.py:15-35`) cumule : (1) déstructuration de tuple sans validation (`for sku, qty in lines` — un format incorrect lève `ValueError`), (2) abandon silencieux des SKUs inconnus (`continue`, `inventory/orders.py:28-29`), (3) tri lexicographique sur `zone` (`inventory/orders.py:35`) qui fonctionnerait mal avec des zones multi-caractères. Après le correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-316, elle implémente également le cumul intra-commande via le dict `allocated` (`inventory/orders.py:23, 30, 33`). Six tests couvrent maintenant les cas nominaux et critiques (articles hors stock, disponibles, quantités invalides, cumul intra-commande), mais les cas liste vide, SKU inconnu seul, et tri de zones multiples ne sont pas couverts.

**VÉRIFIÉ_CODE — `warehouse.py` : fichier pivot sans abstraction.** `warehouse.py` est l'unique source de données, exporteur de primitives et détenteur de l'état global `ITEMS`. Tout couplage vers lui (`orders.py:3`, `tests/test_warehouse.py:3`) crée une dépendance directe à sa structure interne. Un changement de schéma dans `ITEMS` (renommer `qty` en `quantity`) casse simultanément `orders.py`, `tests/test_warehouse.py` et `warehouse.py` lui-même.

**VÉRIFIÉ_CODE — `list_items()` : retourne une référence directe sans garde.** Une ligne (`inventory/warehouse.py:11-12`), mais un vecteur de mutation : quiconque itère et modifie `list_items()` altère `ITEMS` en place pour tous les appelants suivants.

## Forces

- **Aucun fichier de plus de 34 lignes.** La base de code est minuscule et entièrement lisible en quelques minutes — aucun hotspot de volume.
- **Bug volontaire isolé à une seule fonction.** `available_qty()` est la seule fonction défaillante ; les autres fonctions de `warehouse.py` (`find_by_sku`, `items_in_zone`, `list_items`) se comportent correctement pour leur contrat.
- **Dépendances internes visibles d'un coup d'œil.** Le graphe de dépendance est `orders → warehouse`, sans cycle, sans indirection. Un senior comprend l'ensemble du couplage en lisant la ligne d'import de `orders.py`.

## Dettes techniques

- **`can_fulfil()` sans test, `picking_list()` couverture améliorée.** `can_fulfil()` reste entièrement non testée. `picking_list()` dispose maintenant de 6 tests couvrant les cas nominaux et critiques, mais `can_fulfil()` n'est pas couverte du tout (`tests/test_warehouse.py` ne l'importe pas). (`inventory/orders.py:6-35`)
- **`picking_list()` avale les erreurs silencieusement.** Le `continue` sur SKU inconnu (`inventory/orders.py:18-19`) transforme un problème de données en résultat silencieusement tronqué. Aucun mécanisme de feedback (retour enrichi, log, exception) n'est présent.
- **Couplage fort à la structure du dict `ITEMS`.** Les fonctions de `warehouse.py` et `orders.py` accèdent directement aux clés de dict (`item["qty"]`, `item["reserved"]`, `item["zone"]`). Un renommage exige une recherche manuelle dans tout le code.

## Zones critiques

- **`inventory/warehouse.py:22-24` (`available_qty`)** — Porteur du bug corrigé (après SHIAAAAAAAAAAAAAAAAAAAAAAAA-231), fondement de toute la chaîne. Si cette fonction est modifiée, l'impact remonte jusqu'aux tests et à `can_fulfil()`.
- **`inventory/orders.py:15-35` (`picking_list`)** — Fonction complexe du projet (4 comportements distincts en 21 lignes : rejet des quantités invalides, recherche du SKU, vérification de disponibilité intégrée via `allocated`, cumul intra-commande, tri). Six tests couvrent maintenant les cas nominaux et critiques.
- **`inventory/warehouse.py:3-8` (`ITEMS`)** — Source de vérité unique. Toute modification ici se propage à tout le code.

## Risques

- **VÉRIFIÉ_CODE — `can_fulfil()` : zéro test, dépendance directe à `available_qty()`.** `can_fulfil()` n'a aucun test dans la suite existante (`tests/test_warehouse.py` n'importe pas `orders`, `inventory/orders.py:6-12`) et appelle directement `available_qty()` (`inventory/orders.py:12`).
- **HYPOTHÈSE — Régression invisible sur `can_fulfil()` si `available_qty()` est modifié.** Toute modification de `available_qty()` (changement de formule, suppression du `max(0, ...)`) change silencieusement le comportement de `can_fulfil()` sans qu'aucun test l'intercepte — la régression ne serait détectée qu'à l'exécution manuelle ou via des tests manuels.
- **VÉRIFIÉ_CODE — `picking_list()` : `continue` silencieux sur SKU inconnu.** Lorsque `find_by_sku(sku)` retourne `None`, `picking_list()` exécute un `continue` sans log, sans compteur et sans valeur de retour enrichie (`inventory/orders.py:28-29`).
- **HYPOTHÈSE — Prélèvement incomplet sans signal si un SKU est absent de `ITEMS`.** Dans un contexte où une ligne de commande contient un SKU absent, ce silence constitue un vecteur d'incident : un article non trouvé disparaît de la liste de picking sans signal vers l'appelant.
- **HYPOTHÈSE — Casse en cascade sur changement de schéma `ITEMS`.** Renommer ou ajouter un champ dans les dicts de `ITEMS` sans mettre à jour toutes les références (5 accès de clé différents dans les deux modules) produirait des `KeyError` à l'exécution.

## Recommandations priorisées

1. **Ajouter des tests pour `can_fulfil()`** — À minima : SKU inconnu, quantité demandée nulle ou négative, SKU disponible, SKU en rupture. `picking_list()` dispose maintenant d'une bonne couverture. (`tests/test_orders.py`)
2. **Ajouter un signal explicite dans `picking_list()` sur SKU ignoré** — Un `warnings.warn()` ou un second retour (ex. `(list, list_of_ignored_skus)`) évite le résultat silencieusement incomplet. (`inventory/orders.py:18-19`)
3. **Typer `ITEMS` pour externaliser le couplage de schéma** — Un `TypedDict` ou une dataclass centralise la définition du schéma et rend les accès de clé vérifiables statiquement. (`inventory/warehouse.py:3-8`)

## Questions ouvertes

- `picking_list()` est-elle censée appeler `can_fulfil()` avant de construire la liste, ou la vérification de disponibilité appartient-elle à l'orchestrateur appelant ? La séparation actuelle crée un flux à deux appels sans orchestrateur visible.
- La décision de ne pas avoir de tests pour `orders.py` est-elle une omission ou un exercice intentionnel laissé à l'apprenant ?
