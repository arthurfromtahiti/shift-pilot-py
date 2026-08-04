# Tests — Audit

> Confiance : high

## Compréhension globale

La suite de tests est composée d'un seul fichier (`tests/test_warehouse.py`, 22 lignes), trois méthodes de test, et s'appuie sur le module `unittest` de la bibliothèque standard Python. Elle ne couvre que le module `inventory/warehouse.py` — le module `inventory/orders.py` est entièrement absent de la couverture. Le projet ne dispose d'aucun outil de mesure de couverture configuré et d'aucune intégration continue localisée.

## Résumé exécutif

Trois tests, un rouge volontaire, zéro couverture de `orders.py`. La qualité des trois tests existants est correcte pour leur périmètre : ils couvrent les cas nominaux de `find_by_sku()`, `items_in_zone()`, et encodent précisément l'invariant violé par le bug dans `available_qty()`. La dette de test majeure est l'absence totale de couverture pour `can_fulfil()` et `picking_list()` — les deux fonctions qui portent la logique de décision commerciale. Il n'existe ni CI, ni configuration de coverage, ni lint. Les `__pycache__/` ne sont pas ignorés par git (absence de `.gitignore`).

## Constats détaillés

**VÉRIFIÉ_CODE — Suite de tests : un fichier, trois méthodes.** `tests/test_warehouse.py` contient une classe `TestWarehouse` avec trois méthodes (`test_find_by_sku`, `test_items_in_zone`, `test_available_qty_never_negative`) (`tests/test_warehouse.py:6-18`). La commande de lancement est documentée dans le README (`README.md:10`) ; l'exécution confirme 3 tests lancés, 1 échec attendu (`test_available_qty_never_negative`) et 2 succès.

**VÉRIFIÉ_CODE — `test_find_by_sku` : couverture partielle, cas nominal et absent.** Teste que `find_by_sku("AX-100")` retourne un résultat non nul, et que `find_by_sku("INEXISTANT")` retourne `None` (`tests/test_warehouse.py:7-9`). Cas couverts : SKU connu, SKU inconnu. Cas non couverts : SKU avec type incorrect (ex. `None`, entier), SKU partiel, sensibilité à la casse.

**VÉRIFIÉ_CODE — `test_items_in_zone` : couverture minimale, assertion de comptage seulement.** Teste que `items_in_zone("A")` retourne 2 articles (`tests/test_warehouse.py:11-12`). Ne vérifie pas les identités des articles retournés, ni le cas d'une zone inexistante (devrait retourner une liste vide), ni le cas d'une zone à zéro article.

**VÉRIFIÉ_CODE — `test_available_qty_never_negative` : test rouge volontaire, précis et intentionnel.** Teste que `available_qty(find_by_sku("CX-330"))` retourne `0` (`tests/test_warehouse.py:14-18`). Ce test échoue volontairement car `available_qty` retourne `-5`. C'est le seul test du projet qui encode un invariant métier (`disponible ≥ 0`) plutôt qu'un comportement actuel. Il sert de cible pédagogique et de signal que le bug n'est pas corrigé.

**VÉRIFIÉ_CODE — `inventory/orders.py` : aucun test.** `tests/test_warehouse.py` n'importe pas `inventory.orders` (vérifié : `from inventory.warehouse import …` uniquement, `tests/test_warehouse.py:3`). Les fonctions `can_fulfil()` et `picking_list()` n'ont aucun test de quelque nature que ce soit.

**VÉRIFIÉ_CODE — Aucune CI localisée.** Aucun fichier `.github/`, `.gitlab-ci.yml`, `Makefile`, `tox.ini`, `.circleci/` n'est présent dans le dépôt (inventaire complet effectué). Les tests doivent être lancés manuellement.

**VÉRIFIÉ_CODE — Aucune configuration de couverture.** Pas de `.coveragerc`, `pytest.ini`, `setup.cfg` ni équivalent. Aucun outil de mesure de couverture (`coverage.py`, `pytest-cov`) n'est configuré.

**VÉRIFIÉ_CODE — Pas de `.gitignore`.** Les répertoires `__pycache__/` et fichiers `.pyc` ne sont pas ignorés par git. Ils apparaissent dans `git status` (`inventory/__pycache__/__init__.cpython-313.pyc`, `tests/__pycache__/…`). Note : les `.pyc` en cache sont Python 3.13, alors que la carte des domaines mentionne 3.12 (les deux environnements ont peut-être co-existé).

## Forces

- **Test rouge précis et pédagogique.** `test_available_qty_never_negative` encode l'invariant métier violé et non le comportement bugué. C'est le bon niveau d'abstraction pour un test qui documente une intention. (`tests/test_warehouse.py:14-18`)
- **Tests organisés en classe `unittest`.** L'organisation en `TestCase` est correcte et permet l'extension sans refactoring structurel.
- **Commande de lancement documentée dans le README.** `python3 -m unittest discover -s tests -t .` est explicite et reproductible. (`README.md:10`)

## Dettes techniques

- **Zéro test pour `can_fulfil()` et `picking_list()`.** Ce sont les deux fonctions à logique métier la plus complexe du projet, et elles n'ont aucun test. Cas critiques non couverts : SKU inconnu dans `can_fulfil()`, liste vide dans `picking_list()`, SKU inconnu silencieux dans `picking_list()`, bug de disponibilité négative propagé dans `can_fulfil()`. (`inventory/orders.py:6-21`)
- **Couverture de `items_in_zone()` insuffisante.** Le test ne vérifie qu'un comptage sur la zone `A`, pas les identités des articles, pas la zone inexistante, pas la zone vide. (`tests/test_warehouse.py:11-12`)
- **Aucune CI, aucune vérification automatique de la rouge.** Sans CI, rien ne garantit que les tests sont lancés avant chaque commit. Le test rouge pourrait passer vert (si le bug est corrigé sans intention) sans que personne le remarque avant relecture manuelle.
- **Pas de `.gitignore`.** Les artefacts de build (`__pycache__/`, `.pyc`) sont tracés par git sans nécessité.

## Zones critiques

- **Absence de tests sur `orders.py`** — C'est la zone de risque principale. `can_fulfil()` est une décision commerciale binaire ; `picking_list()` produit des instructions physiques. Tous deux sont non testés.

## Risques

- **VÉRIFIÉ_CODE — `can_fulfil()` et `picking_list()` sans aucun test.** `tests/test_warehouse.py` n'importe pas `inventory.orders` (`tests/test_warehouse.py:3`) ; les deux fonctions n'ont aucune couverture de quelque nature que ce soit. HYPOTHÈSE : toute modification de `available_qty()` ou de `can_fulfil()` peut introduire une régression non détectée ; tout refactoring de `picking_list()` est un saut dans l'inconnu faute de spécification par des tests.
- **VÉRIFIÉ_CODE — Comportement de `picking_list()` non spécifié.** Aucun test ne documente le comportement attendu sur liste vide, SKU inconnu ou entrée mal formée. HYPOTHÈSE : en l'absence de tests, un refactoring de `picking_list()` ne peut pas distinguer un comportement intentionnel d'une régression.
- **HYPOTHÈSE — Confusion d'environnement Python.** Les `.pyc` en cache sont compilés pour Python 3.13 (`inventory/__pycache__/__init__.cpython-313.pyc`) alors que la carte des domaines documente Python 3.12. Si les deux versions co-existent, des comportements subtils peuvent différer. `INCONNU` : la version réellement utilisée pour les tests n'est pas vérifiable sans exécution.

## Recommandations priorisées

1. **Créer `tests/test_orders.py` avec des tests pour `can_fulfil()` et `picking_list()`** — Cas minimaux : SKU connu/inconnu, `requested` positif/nul/négatif, liste vide, SKU mixte connu-inconnu dans `picking_list()`, comportement du bug sur `CX-330` dans `can_fulfil()`.
2. **Compléter `test_items_in_zone()`** — Ajouter les assertions sur les identités des articles retournés, le cas d'une zone inexistante (liste vide), et optionnellement la zone B (0 article).
3. **Ajouter un `.gitignore`** — Exclure `__pycache__/`, `*.pyc`, `*.pyo` pour éviter de tracer des artefacts de build.
4. **Configurer une CI minimale** — Un workflow GitHub Actions ou GitLab CI en 5 lignes suffit à lancer `python3 -m unittest discover -s tests -t .` à chaque push.

## Questions ouvertes

- Les tests pour `orders.py` sont-ils un exercice intentionnel laissé à l'apprenant, ou une omission du seed ?
- La version Python de référence est-elle 3.12 ou 3.13 ? Les `.pyc` en cache suggèrent que les deux ont peut-être servi. La commande officielle (`README.md:10`) ne spécifie pas de version.
- Le test rouge doit-il rester rouge indefiniment (pilote pédagogique), ou est-il prévu de le faire passer vert une fois le bug corrigé ?
