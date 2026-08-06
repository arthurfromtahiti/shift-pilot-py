# Tests — Audit

> Confiance : high

## Compréhension globale

La suite de tests est composée de deux fichiers (`tests/test_warehouse.py`, 22 lignes ; `tests/test_orders.py`, 15 lignes), quatre méthodes de test au total, et s'appuie sur le module `unittest` de la bibliothèque standard Python. Elle couvre le module `inventory/warehouse.py` (trois tests) et commence à couvrir `inventory/orders.py` (un test). Le projet ne dispose d'aucun outil de mesure de couverture configuré et d'aucune intégration continue localisée.

## Résumé exécutif

Neuf tests total : trois sur `warehouse.py` (tous verts), six sur `orders.py` (couvrant `picking_list()`). La qualité des tests existants est correcte pour leur périmètre : ils couvrent les cas nominaux, les cas critiques de disponibilité insuffisante, et le cumul intra-commande (après le correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-316). Les six tests de `picking_list()` valident l'exclusion des articles non disponibles, les quantités nulles/négatives, et la règle de cumul intra-commande pour plusieurs lignes du même SKU. La couverture de `orders.py` s'est améliorée — `picking_list()` a une bonne couverture — mais `can_fulfil()` n'a toujours aucun test. Il n'existe ni CI, ni configuration de coverage, ni lint. Les `__pycache__/` ne sont pas ignorés par git (absence de `.gitignore`).

## Constats détaillés

**VÉRIFIÉ_CODE — Suite de tests : deux fichiers, neuf méthodes.** `tests/test_warehouse.py` contient une classe `TestWarehouse` avec trois méthodes (`test_find_by_sku`, `test_items_in_zone`, `test_available_qty_never_negative`) ; `tests/test_orders.py` contient une classe `TestPickingList` avec six méthodes (`test_article_hors_stock_exclu`, `test_cx330_inclus_dans_picking_list`, `test_quantite_nulle_exclue`, `test_quantite_negative_exclue`, `test_plusieurs_lignes_meme_sku_depassement_exclu`, `test_plusieurs_lignes_meme_sku_dans_les_limites`, `test_plusieurs_lignes_meme_sku_allocation_cumulative`) (`tests/test_warehouse.py:6-18`, `tests/test_orders.py:6-46`). La commande de lancement est documentée dans le README (`README.md:10`) ; l'exécution confirme 9 tests lancés, tous passants.

**VÉRIFIÉ_CODE — `test_find_by_sku` : couverture partielle, cas nominal et absent.** Teste que `find_by_sku("AX-100")` retourne un résultat non nul, et que `find_by_sku("INEXISTANT")` retourne `None` (`tests/test_warehouse.py:7-9`). Cas couverts : SKU connu, SKU inconnu. Cas non couverts : SKU avec type incorrect (ex. `None`, entier), SKU partiel, sensibilité à la casse.

**VÉRIFIÉ_CODE — `test_items_in_zone` : couverture minimale, assertion de comptage seulement.** Teste que `items_in_zone("A")` retourne 2 articles (`tests/test_warehouse.py:11-12`). Ne vérifie pas les identités des articles retournés, ni le cas d'une zone inexistante (devrait retourner une liste vide), ni le cas d'une zone à zéro article.

**VÉRIFIÉ_CODE — `test_available_qty_never_negative` : test vert, validant le correctif CLA-177.** Teste que `available_qty(find_by_sku("CX-330"))` retourne `0` (`tests/test_warehouse.py:14-18`). Ce test PASSE car `available_qty()` retourne `max(0, 45-50) = 0`. Le correctif CLA-177 (`f3d4233`) a appliqué le `max(0, ...)` qui garantit une disponibilité jamais négative. Ce test encode un invariant métier (`disponible ≥ 0`) et vérifie que l'implémentation la respecte.

**VÉRIFIÉ_CODE — `inventory/orders.py` : couverture améliorée de `picking_list()`.** `tests/test_orders.py` contient six tests sur `picking_list()` qui valident l'exclusion des articles indisponibles, les quantités invalides, et le cumul intra-commande (après le correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-316) (`tests/test_orders.py:7-46`). `can_fulfil()` reste entièrement non testé (`inventory/orders.py:6-12`).

**VÉRIFIÉ_CODE — Aucune CI localisée.** Aucun fichier `.github/`, `.gitlab-ci.yml`, `Makefile`, `tox.ini`, `.circleci/` n'est présent dans le dépôt (inventaire complet effectué). Les tests doivent être lancés manuellement.

**VÉRIFIÉ_CODE — Tests étendus de `picking_list()` après correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-316.** `tests/test_orders.py` contient une classe `TestPickingList` avec six méthodes couvrant les cas : article hors stock (BX-220), article disponible (CX-330), quantités nulles/négatives, cumul intra-commande avec dépassement et sans dépassement, cumul triple. Le correctif 316 a introduit le dict `allocated` cumulatif, et ces tests en valident le fonctionnement (`tests/test_orders.py:6-46`).

**VÉRIFIÉ_CODE — Aucune configuration de couverture.** Pas de `.coveragerc`, `pytest.ini`, `setup.cfg` ni équivalent. Aucun outil de mesure de couverture (`coverage.py`, `pytest-cov`) n'est configuré.

**VÉRIFIÉ_CODE — Pas de `.gitignore`.** Les répertoires `__pycache__/` et fichiers `.pyc` ne sont pas ignorés par git. Ils apparaissent dans `git status` (`inventory/__pycache__/__init__.cpython-313.pyc`, `tests/__pycache__/…`). Note : les `.pyc` en cache sont Python 3.13, alors que la carte des domaines mentionne 3.12 (les deux environnements ont peut-être co-existé).

## Forces

- **Test vert validant l'invariant métier.** `test_available_qty_never_negative` encode l'invariant métier (`disponible ≥ 0`) et passe avec l'implémentation actuelle `max(0, ...)`. C'est le bon niveau d'abstraction pour un test qui documente une intention et valide qu'elle est respectée. (`tests/test_warehouse.py:14-18`)
- **Tests organisés en classe `unittest`.** L'organisation en `TestCase` est correcte et permet l'extension sans refactoring structurel.
- **Commande de lancement documentée dans le README.** `python3 -m unittest discover -s tests -t .` est explicite et reproductible. (`README.md:10`)

## Dettes techniques

- **`can_fulfil()` entièrement non testée ; `picking_list()` couverture améliorée.** `can_fulfil()` reste entièrement non testée — SKU inconnu, quantité zéro, bug de disponibilité négative propagé ne sont vérifiés par aucun test. `picking_list()` dispose maintenant d'une bonne couverture (6 tests) — articles hors stock, disponibles, quantités nulles/négatives, cumul intra-commande — bien que les cas liste vide et ordre de zones multiples ne soient pas spécifiés. (`inventory/orders.py:6-35`)
- **Couverture de `items_in_zone()` insuffisante.** Le test ne vérifie qu'un comptage sur la zone `A`, pas les identités des articles, pas la zone inexistante, pas la zone vide. (`tests/test_warehouse.py:11-12`)
- **Aucune CI, aucune vérification automatique à chaque commit.** Sans CI, rien ne garantit que les tests sont lancés avant chaque commit. Des régressions peuvent passer inaperçues sans relecture manuelle.
- **Pas de `.gitignore`.** Les artefacts de build (`__pycache__/`, `.pyc`) sont tracés par git sans nécessité.

## Zones critiques

- **Couverture améliorée mais incomplète de `orders.py`** — `picking_list()` dispose maintenant de 6 tests (exclusion sur indisponibilité, quantités nulles/négatives, cumul intra-commande) et sa couverture s'est sensiblement améliorée. `can_fulfil()` est une décision commerciale binaire mais reste entièrement non testé.

## Risques

- **VÉRIFIÉ_CODE — `can_fulfil()` sans test ; couverture améliorée de `picking_list()`.** `tests/test_orders.py` importe `picking_list` et teste six cas (article hors stock, article disponible, quantités nulles/négatives, cumul intra-commande) ; `can_fulfil()` reste entièrement non testé. HYPOTHÈSE : toute modification de `can_fulfil()` peut introduire une régression non détectée. Le comportement de `picking_list()` sur liste vide, SKU inconnu seul, ou tri de zones multiples est toujours non spécifié.
- **VÉRIFIÉ_CODE — Comportement de `picking_list()` partiellement spécifié.** Six tests couvrent les cas nominaux et les cas limites du cumul intra-commande (après correctif 316). Le comportement sur liste vide, SKU inconnu seul, ou ordre de zones multiples n'est pas testé. HYPOTHÈSE : en l'absence de couverture complète, un refactoring de `picking_list()` ne peut pas distinguer un comportement intentionnel d'une régression.
- **HYPOTHÈSE — Confusion d'environnement Python.** Les `.pyc` en cache sont compilés pour Python 3.13 (`inventory/__pycache__/__init__.cpython-313.pyc`) alors que la carte des domaines documente Python 3.12. Si les deux versions co-existent, des comportements subtils peuvent différer. `INCONNU` : la version réellement utilisée pour les tests n'est pas vérifiable sans exécution.

## Recommandations priorisées

1. **Compléter les tests de `picking_list()` dans `tests/test_orders.py`** — Ajouter les cas manquants : liste vide, SKU inconnu seul, ordre de zones multiples. Les cas nominaux (SKU disponible, quantités nulles/négatives, cumul intra-commande) sont maintenant couverts.
2. **Créer des tests pour `can_fulfil()`** — Cas minimaux : SKU connu/inconnu, quantité demandée positive/zéro/négative, comportement du bug sur `CX-330`.
3. **Compléter `test_items_in_zone()`** — Ajouter les assertions sur les identités des articles retournés, le cas d'une zone inexistante (liste vide), et optionnellement la zone B (0 article).
4. **Ajouter un `.gitignore`** — Exclure `__pycache__/`, `*.pyc`, `*.pyo` pour éviter de tracer des artefacts de build.
5. **Configurer une CI minimale** — Un workflow GitHub Actions ou GitLab CI en 5 lignes suffit à lancer `python3 -m unittest discover -s tests -t .` à chaque push.

## Questions ouvertes

- Les tests pour `orders.py` sont-ils un exercice intentionnel laissé à l'apprenant, ou une omission du seed ?
- La version Python de référence est-elle 3.12 ou 3.13 ? Les `.pyc` en cache suggèrent que les deux ont peut-être servi. La commande officielle (`README.md:10`) ne spécifie pas de version.
- Le test rouge doit-il rester rouge indefiniment (pilote pédagogique), ou est-il prévu de le faire passer vert une fois le bug corrigé ?
