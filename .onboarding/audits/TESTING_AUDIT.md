# Tests — Audit

> Confiance : high

## Compréhension globale

La suite de tests est composée de deux fichiers (`tests/test_warehouse.py`, 41 lignes ; `tests/test_orders.py`, 92 lignes), seize méthodes de test au total, et s'appuie sur le module `unittest` de la bibliothèque standard Python. Elle couvre le module `inventory/warehouse.py` (six tests) et le module `inventory/orders.py` (dix tests sur `picking_list()`). `can_fulfil()` reste entièrement non testée. Le projet ne dispose d'aucun outil de mesure de couverture configuré et d'aucune intégration continue localisée.

## Résumé exécutif

OBSERVÉ : seize tests au total, tous passants (`python3 -m unittest discover -s tests -t .` → `Ran 16 tests in 0.001s — OK`) — six sur `warehouse.py`, dix sur `orders.py` (couvrant `picking_list()`). La qualité des tests existants est correcte pour leur périmètre : ils couvrent les cas nominaux, les cas critiques de disponibilité insuffisante, le cumul intra-commande (après le correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-316), la journalisation des lignes non servies (SHIAAAAAAAAAAAAAAAAAAAAAAAA-442), et l'insensibilité à la casse dans le cumul (SHIAAAAAAAAAAAAAAAAAAAAAAAA-507). La couverture de `orders.py` s'est sensiblement améliorée — `picking_list()` a dix tests. `can_fulfil()` reste entièrement non testée. Il n'existe ni CI, ni configuration de coverage, ni lint. Les `__pycache__/` ne sont pas ignorés par git (absence de `.gitignore`).

## Constats détaillés

**VÉRIFIÉ_CODE — Suite de tests : deux fichiers, seize méthodes.** `tests/test_warehouse.py` contient une classe `TestWarehouse` avec six méthodes (`test_find_by_sku`, `test_items_in_zone`, `test_available_qty_cx330`, `test_available_qty_borne_a_zero_quand_reserved_superieur_a_qty`, `test_invariant_reserved_ne_depasse_pas_qty_dans_items`, `test_find_by_sku_insensible_casse`) ; `tests/test_orders.py` contient une classe `TestPickingList` avec dix méthodes (`test_article_hors_stock_exclu_des_picks`, `test_article_hors_stock_journalise_dans_skipped`, `test_cx330_inclus_dans_picks`, `test_quantite_nulle_exclue_sans_trace`, `test_quantite_negative_exclue_sans_trace`, `test_plusieurs_lignes_meme_sku_depassement_exclu_des_picks`, `test_plusieurs_lignes_meme_sku_depassement_journalise_dans_skipped`, `test_plusieurs_lignes_meme_sku_dans_les_limites`, `test_plusieurs_lignes_meme_sku_allocation_cumulative`, `test_meme_article_casse_differente_cumul_respecte`) (`tests/test_warehouse.py:6-37`, `tests/test_orders.py:6-88`). La commande de lancement est documentée dans le README (`README.md:10`).

**OBSERVÉ — Exécution de la suite de tests : 16 tests passants.** `python3 -m unittest discover -s tests -t .` → `Ran 16 tests in 0.001s` — `OK`.

**VÉRIFIÉ_CODE — `test_find_by_sku` et `test_find_by_sku_insensible_casse` : couverture partielle.** `test_find_by_sku` teste les cas nominal et absent (`tests/test_warehouse.py:7-9`). `test_find_by_sku_insensible_casse` valide l'insensibilité à la casse (`find_by_sku("ax-100")`, `find_by_sku("Ax-100")` → non nul) après le correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-452 (`tests/test_warehouse.py:33-37`). Cas non couverts : SKU avec type incorrect (ex. `None`, entier), SKU partiel.

**VÉRIFIÉ_CODE — `test_items_in_zone` : couverture minimale, assertion de comptage seulement.** Teste que `items_in_zone("A")` retourne 2 articles (`tests/test_warehouse.py:11-12`). Ne vérifie pas les identités des articles retournés, ni le cas d'une zone inexistante (devrait retourner une liste vide), ni le cas d'une zone à zéro article.

**VÉRIFIÉ_CODE — Trois tests sur `available_qty()` et l'invariant du stock.** `test_available_qty_cx330` vérifie que `CX-330` (qty=45, reserved=5) retourne `40` (`tests/test_warehouse.py:14-18`). `test_available_qty_borne_a_zero_quand_reserved_superieur_a_qty` vérifie qu'un article synthétique `{qty=10, reserved=15}` retourne `0` (`tests/test_warehouse.py:20-23`). `test_invariant_reserved_ne_depasse_pas_qty_dans_items` vérifie que tous les articles du seed respectent `reserved ≤ qty` (`tests/test_warehouse.py:25-31`). Ces trois tests encodent les invariants clés (la confirmation d'exécution est dans l'entrée OBSERVÉ de ce même audit).

**VÉRIFIÉ_CODE — `inventory/orders.py` : dix tests sur `picking_list()`.** `tests/test_orders.py` contient dix tests sur `picking_list()` (`tests/test_orders.py:7-88`) : exclusion des articles hors stock (`test_article_hors_stock_exclu_des_picks`), journalisation dans `skipped` (`test_article_hors_stock_journalise_dans_skipped`), article disponible (`test_cx330_inclus_dans_picks`), quantités invalides (`test_quantite_nulle_exclue_sans_trace`, `test_quantite_negative_exclue_sans_trace`), cumul intra-commande avec dépassement (`test_plusieurs_lignes_meme_sku_depassement_exclu_des_picks`, `test_plusieurs_lignes_meme_sku_depassement_journalise_dans_skipped`), cumul dans les limites (`test_plusieurs_lignes_meme_sku_dans_les_limites`), cumul triple (`test_plusieurs_lignes_meme_sku_allocation_cumulative`), et insensibilité à la casse dans le cumul (`test_meme_article_casse_differente_cumul_respecte`). `can_fulfil()` reste entièrement non testé (`inventory/orders.py:6-12`).

**VÉRIFIÉ_CODE — Aucune CI localisée.** Aucun fichier `.github/`, `.gitlab-ci.yml`, `Makefile`, `tox.ini`, `.circleci/` n'est présent dans le dépôt (inventaire complet effectué). Les tests doivent être lancés manuellement.

**VÉRIFIÉ_CODE — Tests accumulés par plusieurs correctifs successifs.** `tests/test_orders.py` a évolué via trois séries de correctifs : SHIAAAAAAAAAAAAAAAAAAAAAAAA-316 (cumul intra-commande via `allocated`), SHIAAAAAAAAAAAAAAAAAAAAAAAA-442 (journalisation des lignes hors stock dans `skipped`) et SHIAAAAAAAAAAAAAAAAAAAAAAAA-507 (insensibilité à la casse dans le cumul via clé `canonical`). La classe `TestPickingList` compte désormais dix méthodes couvrant l'ensemble de ces comportements (`tests/test_orders.py:6-88`).

**VÉRIFIÉ_CODE — Aucune configuration de couverture.** Pas de `.coveragerc`, `pytest.ini`, `setup.cfg` ni équivalent. Aucun outil de mesure de couverture (`coverage.py`, `pytest-cov`) n'est configuré.

**VÉRIFIÉ_CODE — Pas de `.gitignore` dans l'arborescence.** Aucun fichier `.gitignore` n'est présent dans le dépôt (inventaire complet effectué). Les répertoires `__pycache__/` et fichiers `.pyc` ne sont donc pas exclus du suivi git.

**OBSERVÉ — Fichiers `.pyc` non suivis listés dans `git status`.** `git status` rapporte les fichiers suivants comme non suivis : `inventory/__pycache__/__init__.cpython-313.pyc`, `inventory/__pycache__/orders.cpython-313.pyc`, `inventory/__pycache__/warehouse.cpython-313.pyc`, `tests/__pycache__/__init__.cpython-313.pyc`, `tests/__pycache__/test_orders.cpython-313.pyc`, `tests/__pycache__/test_warehouse.cpython-313.pyc`. Note : les `.pyc` sont compilés pour Python 3.13, alors que la carte des domaines mentionne 3.12 (les deux environnements ont peut-être co-existé).

## Forces

- **Tests verts validant l'invariant métier.** `test_available_qty_cx330` et `test_available_qty_borne_a_zero_quand_reserved_superieur_a_qty` encodent l'invariant métier (`disponible ≥ 0`) et passent avec l'implémentation actuelle `max(0, ...)`. C'est le bon niveau d'abstraction pour des tests qui documentent une intention et valident qu'elle est respectée. (`tests/test_warehouse.py:14-23`)
- **Tests organisés en classe `unittest`.** L'organisation en `TestCase` est correcte et permet l'extension sans refactoring structurel.
- **Commande de lancement documentée dans le README.** `python3 -m unittest discover -s tests -t .` est explicite et reproductible. (`README.md:10`)

## Dettes techniques

- **`can_fulfil()` entièrement non testée ; `picking_list()` bonne couverture.** `can_fulfil()` reste entièrement non testée — SKU inconnu, quantité zéro/négative, et cas nominal ne sont vérifiés par aucun test. `picking_list()` dispose maintenant d'une bonne couverture (10 tests) — articles hors stock, disponibles, quantités nulles/négatives, cumul intra-commande, journalisation `skipped`, insensibilité à la casse — bien que les cas liste vide et ordre de zones multiples ne soient pas spécifiés. (`inventory/orders.py:6-46`)
- **Couverture de `items_in_zone()` insuffisante.** Le test ne vérifie qu'un comptage sur la zone `A`, pas les identités des articles, pas la zone inexistante, pas la zone vide. (`tests/test_warehouse.py:11-12`)
- **Aucune CI, aucune vérification automatique à chaque commit.** Sans CI, rien ne garantit que les tests sont lancés avant chaque commit. Des régressions peuvent passer inaperçues sans relecture manuelle.
- **Pas de `.gitignore`.** Les artefacts de build (`__pycache__/`, `.pyc`) sont tracés par git sans nécessité.

## Zones critiques

- **Couverture fonctionnelle de `picking_list()` bonne, mais `can_fulfil()` non testé** — `picking_list()` dispose de 10 tests couvrant exclusion, journalisation `skipped`, quantités invalides, cumul, casse. `can_fulfil()` est une décision commerciale binaire mais reste entièrement non testé.

## Risques

- **VÉRIFIÉ_CODE — `can_fulfil()` sans test ; couverture bonne de `picking_list()`.** `tests/test_orders.py` importe uniquement `picking_list` et teste dix cas ; `can_fulfil()` reste entièrement non testé (`inventory/orders.py:6-12`).
- **HYPOTHÈSE — Régression silencieuse sur `can_fulfil()` si elle est modifiée.** Toute modification de `can_fulfil()` peut introduire une régression non détectée : la fonction n'est couverte par aucun test.
- **VÉRIFIÉ_CODE — Comportement de `picking_list()` bien spécifié sur les cas principaux, lacunaire sur les cas limites.** Dix tests couvrent les cas nominaux, la journalisation `skipped`, le cumul intra-commande et l'insensibilité à la casse. Le comportement sur liste vide, SKU inconnu seul, ou tri de zones multiples n'est pas testé.
- **HYPOTHÈSE — Stabilité implicite de `picking_list()` non garantie sur les cas limites.** En l'absence de couverture sur ces cas, un refactoring de `picking_list()` ne peut pas garantir la stabilité de tous les comportements implicites.
- **HYPOTHÈSE — Confusion d'environnement Python.** Les `.pyc` en cache sont compilés pour Python 3.13 (`inventory/__pycache__/__init__.cpython-313.pyc`) alors que la carte des domaines documente Python 3.12. Si les deux versions co-existent, des comportements subtils peuvent différer. `INCONNU` : la version réellement utilisée pour les tests n'est pas vérifiable sans exécution.

## Recommandations priorisées

1. **Créer des tests pour `can_fulfil()`** — Cas minimaux : SKU connu disponible, SKU inconnu, quantité nulle, quantité négative, SKU en rupture. C'est la priorité : décision commerciale binaire entièrement non testée. (`tests/test_orders.py`, `inventory/orders.py:6-12`)
2. **Compléter les tests de `picking_list()` sur les cas limites** — Ajouter : liste vide, SKU inconnu seul (vérifier qu'il n'apparaît pas dans `skipped`), ordre de tri sur zones multiples. (`tests/test_orders.py`)
3. **Compléter `test_items_in_zone()`** — Ajouter les assertions sur les identités des articles retournés, le cas d'une zone inexistante (liste vide), et optionnellement la zone B (0 article).
4. **Ajouter un `.gitignore`** — Exclure `__pycache__/`, `*.pyc`, `*.pyo` pour éviter de tracer des artefacts de build.
5. **Configurer une CI minimale** — Un workflow GitHub Actions ou GitLab CI en 5 lignes suffit à lancer `python3 -m unittest discover -s tests -t .` à chaque push.

## Questions ouvertes

- Les tests pour `can_fulfil()` sont-ils un exercice intentionnel laissé à l'apprenant, ou une omission ?
- La version Python de référence est-elle 3.12 ou 3.13 ? Les `.pyc` en cache sont en `cpython-313`, mais la carte des domaines documente 3.12. La commande officielle (`README.md:10`) ne spécifie pas de version.
