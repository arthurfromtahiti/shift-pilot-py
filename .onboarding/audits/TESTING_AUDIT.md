# Tests — Audit

> Confiance : high

## Compréhension globale

La suite de tests est composée de deux fichiers (`tests/test_warehouse.py`, 22 lignes ; `tests/test_orders.py`, 15 lignes), quatre méthodes de test au total, et s'appuie sur le module `unittest` de la bibliothèque standard Python. Elle couvre le module `inventory/warehouse.py` (trois tests) et commence à couvrir `inventory/orders.py` (un test). Le projet ne dispose d'aucun outil de mesure de couverture configuré et d'aucune intégration continue localisée.

## Résumé exécutif

Quatre tests total : trois sur `warehouse.py` (un rouge volontaire), un sur `orders.py`. La qualité des tests existants est correcte pour leur périmètre : ils couvrent les cas nominaux et un cas critique de disponibilité insuffisante. Le test `test_article_hors_stock_exclu` valide que `picking_list` exclut correctement les articles non disponibles. La couverture de `orders.py` reste partielle — seul `picking_list` avec indisponibilité est testé — et `can_fulfil()` n'a aucun test. Il n'existe ni CI, ni configuration de coverage, ni lint. Les `__pycache__/` ne sont pas ignorés par git (absence de `.gitignore`).

## Constats détaillés

**VÉRIFIÉ_CODE — Suite de tests : deux fichiers, quatre méthodes.** `tests/test_warehouse.py` contient une classe `TestWarehouse` avec trois méthodes (`test_find_by_sku`, `test_items_in_zone`, `test_available_qty_never_negative`) ; `tests/test_orders.py` contient une classe `TestPickingList` avec une méthode (`test_article_hors_stock_exclu`) (`tests/test_warehouse.py:6-18`, `tests/test_orders.py:6-10`). La commande de lancement est documentée dans le README (`README.md:10`) ; l'exécution confirme 4 tests lancés, tous passants.

**VÉRIFIÉ_CODE — `test_find_by_sku` : couverture partielle, cas nominal et absent.** Teste que `find_by_sku("AX-100")` retourne un résultat non nul, et que `find_by_sku("INEXISTANT")` retourne `None` (`tests/test_warehouse.py:7-9`). Cas couverts : SKU connu, SKU inconnu. Cas non couverts : SKU avec type incorrect (ex. `None`, entier), SKU partiel, sensibilité à la casse.

**VÉRIFIÉ_CODE — `test_items_in_zone` : couverture minimale, assertion de comptage seulement.** Teste que `items_in_zone("A")` retourne 2 articles (`tests/test_warehouse.py:11-12`). Ne vérifie pas les identités des articles retournés, ni le cas d'une zone inexistante (devrait retourner une liste vide), ni le cas d'une zone à zéro article.

**VÉRIFIÉ_CODE — `test_available_qty_never_negative` : test vert, validant le correctif CLA-177.** Teste que `available_qty(find_by_sku("CX-330"))` retourne `0` (`tests/test_warehouse.py:14-18`). Ce test PASSE car `available_qty()` retourne `max(0, 45-50) = 0`. Le correctif CLA-177 (`f3d4233`) a appliqué le `max(0, ...)` qui garantit une disponibilité jamais négative. Ce test encode un invariant métier (`disponible ≥ 0`) et vérifie que l'implémentation la respecte.

**VÉRIFIÉ_CODE — `inventory/orders.py` : test nouveau sur `picking_list`.** `tests/test_orders.py` contient un premier test sur `picking_list()` qui valide l'exclusion des articles indisponibles. `can_fulfil()` reste entièrement non testé (`inventory/orders.py:6-10`).

**VÉRIFIÉ_CODE — Aucune CI localisée.** Aucun fichier `.github/`, `.gitlab-ci.yml`, `Makefile`, `tox.ini`, `.circleci/` n'est présent dans le dépôt (inventaire complet effectué). Les tests doivent être lancés manuellement.

**VÉRIFIÉ_CODE — Nouveau test sur `orders.py` : `test_article_hors_stock_exclu`.** `tests/test_orders.py` contient une classe `TestPickingList` avec une méthode `test_article_hors_stock_exclu` (`tests/test_orders.py:6-10`). Ce test valide que `picking_list([("BX-220", 1)])` retourne une liste vide, vérifiant que les articles sans disponibilité suffisante sont exclus de la liste de prélèvement.

**VÉRIFIÉ_CODE — Aucune configuration de couverture.** Pas de `.coveragerc`, `pytest.ini`, `setup.cfg` ni équivalent. Aucun outil de mesure de couverture (`coverage.py`, `pytest-cov`) n'est configuré.

**VÉRIFIÉ_CODE — Pas de `.gitignore`.** Les répertoires `__pycache__/` et fichiers `.pyc` ne sont pas ignorés par git. Ils apparaissent dans `git status` (`inventory/__pycache__/__init__.cpython-313.pyc`, `tests/__pycache__/…`). Note : les `.pyc` en cache sont Python 3.13, alors que la carte des domaines mentionne 3.12 (les deux environnements ont peut-être co-existé).

## Forces

- **Test vert validant l'invariant métier.** `test_available_qty_never_negative` encode l'invariant métier (`disponible ≥ 0`) et passe avec l'implémentation actuelle `max(0, ...)`. C'est le bon niveau d'abstraction pour un test qui documente une intention et valide qu'elle est respectée. (`tests/test_warehouse.py:14-18`)
- **Tests organisés en classe `unittest`.** L'organisation en `TestCase` est correcte et permet l'extension sans refactoring structurel.
- **Commande de lancement documentée dans le README.** `python3 -m unittest discover -s tests -t .` est explicite et reproductible. (`README.md:10`)

## Dettes techniques

- **`can_fulfil()` entièrement non testée ; `picking_list()` partiellement couverte.** `can_fulfil()` reste entièrement non testée — SKU inconnu, quantité zéro, bug de disponibilité négative propagé ne sont vérifiés par aucun test. `picking_list()` n'est couverte que pour un cas d'indisponibilité (`test_article_hors_stock_exclu`) — les cas liste vide, SKU inconnu seul, et ordre de zones multiples ne sont pas spécifiés. (`inventory/orders.py:6-21`)
- **Couverture de `items_in_zone()` insuffisante.** Le test ne vérifie qu'un comptage sur la zone `A`, pas les identités des articles, pas la zone inexistante, pas la zone vide. (`tests/test_warehouse.py:11-12`)
- **Aucune CI, aucune vérification automatique à chaque commit.** Sans CI, rien ne garantit que les tests sont lancés avant chaque commit. Des régressions peuvent passer inaperçues sans relecture manuelle.
- **Pas de `.gitignore`.** Les artefacts de build (`__pycache__/`, `.pyc`) sont tracés par git sans nécessité.

## Zones critiques

- **Couverture incomplète de `orders.py`** — `picking_list()` a désormais un premier test (exclusion sur indisponibilité) mais reste partiellement couverte. `can_fulfil()` est une décision commerciale binaire mais reste entièrement non testé.

## Risques

- **VÉRIFIÉ_CODE — `can_fulfil()` et couverture partielle de `picking_list()`.** `tests/test_orders.py` importe `picking_list` et teste un cas (article hors stock) ; `can_fulfil()` reste entièrement non testé. HYPOTHÈSE : toute modification de `can_fulfil()` peut introduire une régression non détectée ; le comportement de `picking_list()` sur liste vide, SKU inconnu seul, ou articles mixtes est toujours non spécifié.
- **VÉRIFIÉ_CODE — Comportement de `picking_list()` partiellement spécifié.** Un seul test (`test_article_hors_stock_exclu`) documente un cas (article sans disponibilité sufisante). Le comportement sur liste vide, SKU inconnu seul, ou ordre de zones multiples n'est pas testé. HYPOTHÈSE : en l'absence de couverture complète, un refactoring de `picking_list()` ne peut pas distinguer un comportement intentionnel d'une régression.
- **HYPOTHÈSE — Confusion d'environnement Python.** Les `.pyc` en cache sont compilés pour Python 3.13 (`inventory/__pycache__/__init__.cpython-313.pyc`) alors que la carte des domaines documente Python 3.12. Si les deux versions co-existent, des comportements subtils peuvent différer. `INCONNU` : la version réellement utilisée pour les tests n'est pas vérifiable sans exécution.

## Recommandations priorisées

1. **Étendre les tests de `picking_list()` dans `tests/test_orders.py`** — Ajouter des cas : liste vide, SKU inconnu, SKU disponible (nominal), SKU mixte (connu disponible + connu indisponible + inconnu), ordre de zones.
2. **Créer des tests pour `can_fulfil()`** — Cas minimaux : SKU connu/inconnu, quantité demandée positive/zéro/négative, comportement du bug sur `CX-330`.
3. **Compléter `test_items_in_zone()`** — Ajouter les assertions sur les identités des articles retournés, le cas d'une zone inexistante (liste vide), et optionnellement la zone B (0 article).
4. **Ajouter un `.gitignore`** — Exclure `__pycache__/`, `*.pyc`, `*.pyo` pour éviter de tracer des artefacts de build.
5. **Configurer une CI minimale** — Un workflow GitHub Actions ou GitLab CI en 5 lignes suffit à lancer `python3 -m unittest discover -s tests -t .` à chaque push.

## Questions ouvertes

- Les tests pour `orders.py` sont-ils un exercice intentionnel laissé à l'apprenant, ou une omission du seed ?
- La version Python de référence est-elle 3.12 ou 3.13 ? Les `.pyc` en cache suggèrent que les deux ont peut-être servi. La commande officielle (`README.md:10`) ne spécifie pas de version.
- Le test rouge doit-il rester rouge indefiniment (pilote pédagogique), ou est-il prévu de le faire passer vert une fois le bug corrigé ?
