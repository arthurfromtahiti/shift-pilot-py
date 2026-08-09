# Modèle de données — Audit

> Confiance : high

## Compréhension globale

`shift-pilot-py` n'a ni base de données, ni ORM, ni schéma de migration. Le seul « modèle de données » est `ITEMS` : une liste Python de dicts définie en dur dans `inventory/warehouse.py`. Il n'y a pas de deuxième entité, pas de relation entre tables, pas de contrainte déclarée. Le modèle est intentionnellement minimal et non persisté : il vit uniquement en mémoire et disparaît à chaque redémarrage du processus.

## Résumé exécutif

Le modèle de données est une liste Python de quatre dicts avec cinq champs chacun (`sku`, `label`, `qty`, `reserved`, `zone`). Aucune persistance, aucune migration, aucune contrainte déclarée hors du code lui-même. Les points de fragilité sont : (1) le schéma est implicite — un champ manquant ou mal typé dans un dict produit un `KeyError` ou `TypeError` à l'exécution sans signal précoce ; (2) l'unicité du SKU n'est pas garantie par le modèle ; (3) l'invariant `reserved ≤ qty` n'est pas déclaré au niveau du modèle — il est vérifié par un test (`test_invariant_reserved_ne_depasse_pas_qty_dans_items`) et respecté dans les données seed (`tests/test_warehouse.py:25-31`). Pour un pilote de démonstration, ce modèle est approprié et cohérent avec ses objectifs.

## Constats détaillés

**VÉRIFIÉ_CODE — Structure de `ITEMS`.** `ITEMS` est une liste Python de dicts définie au niveau du module (`inventory/warehouse.py:3-8`). Chaque dict a cinq clés : `sku` (str, clé de recherche utilisée pour la recherche par `find_by_sku()` — unique sur les 4 articles du jeu de données observé, sans garantie déclarée au niveau du modèle), `label` (str, libellé lisible), `qty` (int, stock brut), `reserved` (int, quantité réservée), `zone` (str à une lettre, emplacement physique). Il n'y a ni classe, ni dataclass, ni TypedDict : la structure est informelle et non vérifiée à la déclaration.

**VÉRIFIÉ_CODE — Quatre articles.** Quatre articles sont définis : `AX-100` (zone A, qty 12, reserved 2 → disponible 10), `BX-220` (zone B, qty 0, reserved 0 → disponible 0), `CX-330` (zone A, qty 45, reserved 5 → disponible 40), `DX-440` (zone C, qty 7, reserved 1 → disponible 6) (`inventory/warehouse.py:4-7`). L'invariant `reserved ≤ qty` est respecté par les quatre articles et validé par `test_invariant_reserved_ne_depasse_pas_qty_dans_items` (`tests/test_warehouse.py:25-31`).

**VÉRIFIÉ_CODE — Aucune persistance.** `ITEMS` est un littéral Python chargé à l'import du module. Aucun appel à une base de données, aucun fichier JSON, aucun pickle. Tout état est perdu à la fin du processus. (`inventory/warehouse.py:3-8`)

**VÉRIFIÉ_CODE — Aucune contrainte déclarée au niveau du modèle.** Il n'existe ni assertion sur le schéma, ni validation (`pydantic`, `marshmallow`, `dataclasses`), ni check de contrainte dans le code. Les règles implicites du modèle (SKU unique, `qty ≥ 0`, `reserved ≥ 0`, `reserved ≤ qty`) ne sont pas enforçées au niveau du modèle. La contrainte `available ≥ 0` est cependant garantie par le code de `available_qty()` via `max(0, ...)` (`inventory/warehouse.py:24`) et encodée par deux tests verts (`tests/test_warehouse.py:14-23`). L'invariant `reserved ≤ qty` est validé par `test_invariant_reserved_ne_depasse_pas_qty_dans_items` (`tests/test_warehouse.py:25-31`).

**VÉRIFIÉ_CODE — Unicité du SKU non garantie.** `find_by_sku()` retourne le premier article dont le SKU correspond (`inventory/warehouse.py:17-18`). Si deux articles avaient le même SKU dans `ITEMS`, seul le premier serait visible — les doublons seraient silencieux. Aucune vérification d'unicité n'est présente.

**VÉRIFIÉ_CODE — Les dicts sont mutables.** `find_by_sku()` et `list_items()` retournent des références directes aux dicts de `ITEMS` (`inventory/warehouse.py:11-12`, `inventory/warehouse.py:17-18`). Un appelant qui modifie un champ du dict retourné modifie `ITEMS` en place : `item["qty"] = 0` changerait le stock pour tous les appels suivants dans le même processus.

**VÉRIFIÉ_CODE — Aucune entité propre dans `orders.py`.** Le domaine `preparation-commande` ne définit aucune structure de données. Il manipule des tuples `(sku, qty)` en entrée (informels) et produit un dictionnaire `{"picks": [...], "skipped": [...]}` en sortie (informel). Aucune classe ou type dédié. (`inventory/orders.py:15-46`)

## Forces

- **Modèle compact et lisible.** Quatre articles, cinq champs, une liste : le modèle tient en 6 lignes et est immédiatement compréhensible. Adapté à l'objectif de démonstration.
- **Aucune migration à gérer.** L'absence de persistance élimine la problématique des migrations de schéma.
- **Cycle rouge→vert abouti et encodé.** `CX-330` illustre un invariant métier traçable : les données seed respectent désormais `reserved ≤ qty` (`reserved=5, qty=45`) et `available_qty()` retourne `40`. Le correctif (données + borne `max(0, ...)`) est validé par des tests verts. Le modèle de démonstration est cohérent de bout en bout. (`inventory/warehouse.py:4-7`, `tests/test_warehouse.py:14-31`)

## Dettes techniques

- **Schéma implicite, non contrôlé.** La structure `{sku, label, qty, reserved, zone}` n'est nulle part déclarée comme un type (dataclass, TypedDict, Pydantic BaseModel). Un dict malformé dans `ITEMS` (champ manquant, type incorrect) produit une erreur à l'usage, pas à la déclaration. (`inventory/warehouse.py:3-8`)
- **Référence mutable exposée.** `find_by_sku()` et `list_items()` retournent des objets mutables sans copie défensive. Un appelant peut corrompre `ITEMS` silencieusement. (`inventory/warehouse.py:11-12`, `inventory/warehouse.py:17-18`)
- **Aucune unicité de SKU garantie.** Si deux articles partageaient le même SKU, `find_by_sku()` n'en verrait qu'un. (`inventory/warehouse.py:15-18`)

## Zones critiques

- **`inventory/warehouse.py:3-8` — définition de `ITEMS`.** Point unique de vérité du modèle. Toute modification ici se propage à l'ensemble du système (tests compris). `CX-330` est l'article témoin des invariants : ses valeurs (`qty=45, reserved=5`) sont directement référencées dans `test_available_qty_cx330` (`tests/test_warehouse.py:14-18`).

## Risques

- **HYPOTHÈSE — Mutation silencieuse par un appelant.** Tout code client qui modifie un dict retourné par `find_by_sku()` ou un élément de `list_items()` altère `ITEMS` de façon permanente dans le processus. Ce risque est nul aujourd'hui (pas d'appelant externe), mais devient réel dès qu'une couche web ou concurrente est introduite.
- **HYPOTHÈSE — SKU dupliqué non détecté.** Si le seed est étendu avec un deuxième article portant le même SKU, `find_by_sku()` retournerait silencieusement le premier sans signaler le doublon. (`inventory/warehouse.py:15-19`)
- **HYPOTHÈSE — Type incorrect dans `ITEMS`.** Si un champ `qty` ou `reserved` était une chaîne (ex. `"45"` au lieu de `45`), `available_qty()` échouerait avec `TypeError` à l'exécution, pas à l'import. Sans validation de schéma, ce défaut ne serait détecté qu'à l'usage.

## Recommandations priorisées

1. **Typer `ITEMS` avec un `TypedDict`** — Déclarer `class Item(TypedDict): sku: str; label: str; qty: int; reserved: int; zone: str` pour faire vérifier la structure par un outil statique (mypy, pyright) sans overhead d'exécution. (`inventory/warehouse.py:3-8`)
2. **Retourner des copies dans `find_by_sku()` et `list_items()`** — `list(ITEMS)` et `dict(item)` protègent `ITEMS` contre les mutations externes. (`inventory/warehouse.py:11-18`)
3. **Ajouter une assertion d'unicité des SKUs** — Un `assert len({i["sku"] for i in ITEMS}) == len(ITEMS)` au niveau module détecte les doublons au chargement. (`inventory/warehouse.py:8`)

## Questions ouvertes

- Le modèle de données en mémoire est-il definitif pour ce pilote, ou une évolution vers un fichier JSON ou une base légère (SQLite) est-elle prévue ?
- Les zones sont actuellement des chaînes à une lettre (A, B, C) : s'agit-il d'une convention stable ou susceptible d'évoluer vers des codes multi-caractères (A1, B-12…) ? La réponse affecte la robustesse du tri lexicographique de `picking_list()`.
