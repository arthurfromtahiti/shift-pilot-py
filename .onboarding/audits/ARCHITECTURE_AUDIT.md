# Architecture — Audit

> Confiance : high

## Compréhension globale

`shift-pilot-py` est un pilote de démonstration en Python 3 pur (stdlib, pas de dépendance tierce). Le code tient en deux modules (`inventory/warehouse.py`, `inventory/orders.py`), un package `inventory/` avec un `__init__.py` vide, et une suite de tests. Il n'y a ni couche web, ni persistance, ni CLI : les fonctions sont des bibliothèques appelables, le stock est une liste Python en dur. L'objet est pédagogique et explicitement marqué comme tel (`README.md:10-14`).

## Résumé exécutif

L'architecture est intentionnellement minimaliste. Deux modules, une dépendance unidirectionnelle (`orders → warehouse`), zéro état partagé mutable, zéro framework. La structure est saine pour sa taille : la séparation des responsabilités est respectée entre le référentiel de stock (`warehouse.py`) et les opérations dérivées (`orders.py`). Les dettes architecturales sont toutes des omissions attendues dans un pilote de cette taille — pas de persistance, pas d'interface d'accès, pas de couche d'exposition — et non des décisions malformées. Le seul point de vigilance réel est `list_items()` qui expose une référence directe à `ITEMS` sans copie défensive, ce qui ouvrirait un vecteur de mutation silencieuse si une couche appelante écrivait dans la liste.

## Constats détaillés

**VÉRIFIÉ_CODE — Structure en deux modules plats.** Le code est organisé en un unique package `inventory/` (`inventory/__init__.py`, vide) contenant deux modules : `warehouse.py` (34 lignes, référentiel stock) et `orders.py` (22 lignes, opérations de commande). La séparation est fonctionnellement cohérente : `warehouse.py` détient la donnée et les opérations de base ; `orders.py` ne fait que consommer `find_by_sku` et `available_qty` de `warehouse.py` sans accès direct à `ITEMS` (`inventory/orders.py:3`).

**VÉRIFIÉ_CODE — Dépendance unidirectionnelle sans cycle.** `orders.py` importe depuis `warehouse.py` (`from inventory.warehouse import find_by_sku, available_qty`, `inventory/orders.py:3`). L'inverse n'existe pas : `warehouse.py` n'importe rien de `orders.py`. Pas de cycle de dépendances.

**VÉRIFIÉ_CODE — Absence totale de couche d'exposition.** Inventaire complet du dépôt : 2 fichiers source (`inventory/warehouse.py`, `inventory/orders.py`), 1 fichier de test, 1 `README.md`, 1 `__init__.py` vide — aucun `app.py`, `main.py`, `cli.py`, `server.py` ni équivalent. Il n'y a ni routes HTTP, ni CLI, ni interface événementielle. Les fonctions sont des callables Python nus. C'est cohérent avec l'objectif de pilote bibliothèque (`README.md:1-4`), mais cela signifie que toute future intégration (FastAPI, Flask, CLI Click…) devra ajouter une couche d'exposition sans guide architectural existant.

**VÉRIFIÉ_CODE — Donnée couplée au module.** `ITEMS` est défini en dur dans `warehouse.py` (`inventory/warehouse.py:3-8`). Il n'existe aucune interface d'injection de dépendance, de factory, ni de paramètre de configuration pour remplacer cette source de données. Toute évolution vers une vraie persistance (base de données, fichier JSON, API externe) nécessitera de modifier `warehouse.py` directement ou d'introduire une couche d'abstraction absente.

**VÉRIFIÉ_CODE — `list_items()` expose une référence directe, pas une copie.** `list_items()` retourne `ITEMS` sans `list(ITEMS)` ni `.copy()` (`inventory/warehouse.py:11-12`). Un appelant peut muter la liste globale. Dans l'état actuel (aucun appelant externe visible), l'impact est nul ; mais c'est un invariant fragile qui n'est documenté que dans les workflows, pas dans le code.

## Forces

- **Dépendance directionnelle propre.** `orders → warehouse`, jamais l'inverse. Un refactoring reste possible sans démêler un graphe circulaire. (`inventory/orders.py:3`, `inventory/warehouse.py`)
- **Aucune dépendance tierce.** Aucun `requirements.txt`, `Pipfile`, `pyproject.toml` ni `setup.py` trouvé dans le dépôt (inventaire complet). Le projet tourne avec la stdlib Python uniquement — pas de dépendance à maintenir, pas de surface de vulnérabilité de supply chain. (`CARTE_DES_DOMAINES.md`, `README.md`)
- **Responsabilités séparées.** `warehouse.py` détient la donnée et les primitives de lecture ; `orders.py` ne contient que la logique métier de commande. La frontière est nette et cohérente avec la carte des domaines.

## Dettes techniques

- **Pas d'interface d'abstraction sur la source de données.** `warehouse.py` couple directement la logique de lecture à `ITEMS` (littéral inline). Toute future source de données alternative (base, fichier, API) exige une réécriture du module ou l'introduction d'une couche de repository absente. (`inventory/warehouse.py:3-12`)
- **`list_items()` retourne une référence mutable.** Sans `copy()`, l'appelant peut altérer `ITEMS` et corrompre l'état global pour tous les appels suivants. (`inventory/warehouse.py:11-12`)
- **Pas de `__init__.py` actif.** Le `__init__.py` du package `inventory/` est vide : aucune API publique n'est déclarée, aucun `__all__` n'est défini. Pour un pilote, c'est acceptable ; pour un vrai module réutilisable, c'est une dette d'interface.

## Zones critiques

- **`inventory/warehouse.py` — seule source de donnée.** Tout repose sur ce fichier de 34 lignes. Si la structure de `ITEMS` change (un champ renommé, un type différent), les deux modules et les tests cassent simultanément. C'est le point de défaillance unique du projet.

## Risques

- **HYPOTHÈSE — Mutation silencieuse de `ITEMS`.** Si un futur code client itère `list_items()` et modifie la liste retournée (pop, append, mutation in-place d'un dict), l'état de `ITEMS` est corrompu pour tous les appelants suivants dans le même processus. Risque nul dans l'état actuel (pas d'appelant externe), mais réel si une couche web ou un thread concurrent est ajouté.
- **HYPOTHÈSE — Fragilité d'interface.** L'absence de typage (pas de `TypedDict`, pas de dataclass, pas de type hints) signifie que l'interface des dicts `{sku, label, qty, reserved, zone}` n'est pas contrôlée. Une faute de frappe dans une clé dans un futur test ou appelant donnerait un `KeyError` à l'exécution, pas à l'import. (`inventory/warehouse.py:3-8`)

## Recommandations priorisées

1. **Documenter l'API publique du package** — Ajouter au minimum des type hints et un `__all__` dans `inventory/__init__.py` pour exposer une interface contractualisée. Bénéfice immédiat pour un futur outil de vérification statique. (`inventory/__init__.py`, `inventory/warehouse.py`)
2. **Protéger `list_items()`** — Retourner `list(ITEMS)` au lieu de `ITEMS` directement, pour éviter toute mutation externe de l'état global. (`inventory/warehouse.py:11-12`)
3. **Introduire une abstraction source de données** — Si le pilote est amené à être étendu, isoler `ITEMS` derrière une interface (`get_all_items()` ou un repository injectable) pour découpler la logique de la donnée en dur. (`inventory/warehouse.py:3-12`)

## Questions ouvertes

- Une couche d'exposition (HTTP, CLI) est-elle prévue dans ce pilote, ou le code restera-t-il une bibliothèque pure ? La réponse change l'ampleur de la dette d'interface.
- Le choix de séparer `warehouse.py` et `orders.py` plutôt qu'un seul module `inventory.py` est-il figé pour le pilote ? (`CARTE_DES_DOMAINES.md` — incertitude notée)
- Aucun fichier `.gitignore` n'est localisé dans le dépôt (malgré recherche sur `.gitignore`). Les fichiers `__pycache__/` sont non-ignorés. Est-ce une omission volontaire du seed ?
