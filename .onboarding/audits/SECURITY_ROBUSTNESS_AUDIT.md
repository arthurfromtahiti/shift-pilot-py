# Sécurité & Robustesse — Audit

> Confiance : high

## Compréhension globale

`shift-pilot-py` est une bibliothèque Python sans surface réseau, sans authentification, sans base de données et sans secrets. La surface d'attaque est donc très réduite dans le périmètre du dépôt inspecté : le code ne traite que des appels internes Python. Les risques de sécurité classiques (injection SQL, XSS, authz, exposition de secrets) sont structurellement absents par construction. Les risques réels sont de nature robustesse : comportements inattendus sur des entrées mal formées, valeur de retour hors invariant, silences trompeurs.

## Résumé exécutif

Aucun secret en clair, aucune route exposée, aucune dépendance tierce : la surface de sécurité est quasi nulle pour ce pilote dans le périmètre du dépôt inspecté (aucune surface réseau, aucune dépendance tierce déclarée). Les risques identifiés sont de robustesse : (1) `available_qty()` retourne `max(0, qty - reserved)` — l'invariant est garanti par le code et encodé par des tests présents (`inventory/warehouse.py:22-24`) ; (2) `can_fulfil()` rejette les quantités nulles/négatives mais n'effectue pas de validation de type ; `picking_list()` suppose un itérable de tuples `(str, int)` sans contrôle (`inventory/orders.py:28`) ; (3) `picking_list()` avale silencieusement les SKUs inconnus sans log ni signal (`inventory/orders.py:32-33`). Ces points sont sans impact de sécurité dans l'état actuel, mais deviendraient des vecteurs de comportement indéterminé si une couche web ou externe était ajoutée.

## Constats détaillés

**VÉRIFIÉ_CODE — Aucun secret, aucune clé, aucune donnée sensible.** Le code source ne contient aucune valeur ressemblant à un token, mot de passe, clé d'API ou donnée personnelle. La donnée de démonstration (`ITEMS`) est inventée (articles fictifs : Ancre 10kg, Bouée gonflable, etc.) (`inventory/warehouse.py:3-8`). Aucun fichier de configuration, `.env`, ni credential n'est localisé dans le dépôt (inventaire complet effectué).

**VÉRIFIÉ_CODE — Aucune route réseau, aucun binding de port.** Il n'y a ni serveur HTTP, ni WebSocket, ni listener TCP dans le code. Les fonctions sont des callables Python purs. Aucun framework web n'est importé.

**VÉRIFIÉ_CODE — `available_qty()` : invariant borné à zéro, correctif CLA-177 appliqué.** `available_qty(item)` retourne `max(0, item["qty"] - item["reserved"])` (`inventory/warehouse.py:22-24`). Pour `CX-330` (`qty=45, reserved=5`), le retour est `40`. L'invariant « disponibilité ≥ 0 » est respecté par construction. Deux tests encodent cet invariant : `test_available_qty_cx330` (cas nominal sur `CX-330`) et `test_available_qty_borne_a_zero_quand_reserved_superieur_a_qty` (cas `reserved > qty` sur article synthétique `{qty=10, reserved=15}` → retourne `0`) (`tests/test_warehouse.py:14-23`) — voir TESTING_AUDIT.md pour la confirmation d'exécution.

**VÉRIFIÉ_CODE — Validation partielle des entrées dans `can_fulfil()` et `picking_list()`.** `can_fulfil(sku, requested)` rejette `requested <= 0` (`inventory/orders.py:7-8`), mais n'effectue aucun contrôle de type sur `sku` ni de validation explicite du type de `requested`. `picking_list(lines)` déstructure chaque élément de `lines` en deux valeurs `(sku, qty)` au moment de l'itération (`inventory/orders.py:28`), sans validation préalable du format des éléments.

**HYPOTHÈSE — Exceptions non guidées sur entrées mal formées dans `can_fulfil()` et `picking_list()`.** Un `requested` de type incorrect (ex. `None`, `"3"`) provoquerait probablement une `TypeError` à la comparaison `requested <= 0` avant d'atteindre la logique métier. Pour `picking_list()`, un élément ne pouvant être déstructuré en exactement deux valeurs (ex. un `str` seul, un dict, un entier) lèverait probablement une `ValueError` ou `TypeError` au déstructurage ; en revanche, une séquence de deux éléments (ex. liste `[sku, qty]`) satisferait le déstructurage même si ce n'est pas le format attendu. Ces comportements n'ont pas été reproduits : il s'agit d'une inférence par lecture du code, pas d'une observation d'exécution.

**VÉRIFIÉ_CODE — Silence sur SKU inconnu dans `picking_list()`.** Quand `find_by_sku(sku)` retourne `None`, `picking_list()` exécute un `continue` sans log, sans compteur et sans valeur de retour enrichie (`inventory/orders.py:32-33`). L'appelant reçoit une liste silencieusement incomplète. À noter : ce silence s'applique uniquement aux SKUs inconnus et aux quantités invalides ; les articles en stock insuffisant sont eux journalisés dans `skipped`. Dans un contexte de préparation physique, la perte silencieuse d'un SKU inconnu pourrait passer inaperçue.

**VÉRIFIÉ_CODE — `find_by_sku()` retourne `None` sur SKU inconnu — gardes présentes dans les deux appelants actuels.** `warehouse.py` retourne `None` pour tout SKU non trouvé (`inventory/warehouse.py:19`). `can_fulfil()` teste ce cas (`inventory/orders.py:9-11`). `picking_list()` aussi (`inventory/orders.py:32-33`). L'invariant de sécurité du `None` n'est pas documenté au niveau de l'interface publique de `find_by_sku()`.

**HYPOTHÈSE — `TypeError` non guidée si `find_by_sku()` est chaîné sans garde.** Un futur appelant qui passerait directement `find_by_sku(sku)` dans `available_qty()` sans tester `None` obtiendrait probablement une `TypeError: 'NoneType' object is not subscriptable` — erreur technique non métier, difficile à diagnostiquer sans connaître le code source. Ce scénario n'a pas été reproduit ; il s'agit d'une inférence par lecture du code.

**VÉRIFIÉ_CODE — Aucune dépendance tierce déclarée dans le dépôt.** Pas de `requirements.txt`, `pyproject.toml`, `Pipfile` ni `setup.py` localisé dans le dépôt (inventaire complet). Aucune surface de vulnérabilité de supply chain identifiable dans le dépôt inspecté.

## Forces

- **Surface d'attaque quasi nulle dans le périmètre du dépôt inspecté, d'après le code lu.** Pas de réseau, pas de BD, pas de secrets déclarés dans le dépôt : les catégories OWASP classiques (injection, auth, exposition) sont structurellement hors périmètre pour l'état actuel du code. Cette affirmation est bornée au dépôt inspecté et ne vaut pas pour un futur environnement avec couche réseau.
- **Invariant de disponibilité garanti par le code et encodé par des tests.** `available_qty()` retourne `max(0, qty - reserved)` (`inventory/warehouse.py:22-24`), garantissant une disponibilité jamais négative. Deux tests (`test_available_qty_cx330` et `test_available_qty_borne_a_zero_quand_reserved_superieur_a_qty`, `tests/test_warehouse.py:14-23`) encodent cet invariant (voir TESTING_AUDIT.md pour la confirmation d'exécution).
- **Gestion du `None` dans les deux appelants immédiats.** `can_fulfil()` et `picking_list()` défendent tous les deux contre le retour `None` de `find_by_sku()` (`inventory/orders.py:9-11`, `inventory/orders.py:32-33`).

## Dettes techniques

- **Borne `max(0, ...)` présente mais non documentée comme contrat public.** `available_qty()` garantit une disponibilité ≥ 0 (`inventory/warehouse.py:24`), mais cette garantie n'est pas formalisée dans la signature (pas de type hint, pas de postcondition). Un futur mainteneur pourrait supprimer le `max(0, ...)` sans réaliser qu'il porte un invariant métier.
- **Aucune validation de types d'entrée.** `can_fulfil()` et `picking_list()` font confiance à leurs appelants. Sans garde, un type incorrect produit une exception non guidée ou un résultat silencieusement faux. (`inventory/orders.py:6`, `inventory/orders.py:13`)
- **Silences partiellement signalés dans `picking_list()`.** Le `continue` sur SKU inconnu ou quantité invalide (`inventory/orders.py:29-33`) est une perte d'information non gérée : ces cas n'apparaissent pas dans `skipped`. Seul le stock insuffisant est journalisé. Un log ou une liste de rejets séparée éviterait les prélèvements silencieusement incomplets sur SKU inconnu.

## Zones critiques

- **`inventory/orders.py:32-33` — silence sur SKU inconnu.** C'est le comportement le plus susceptible de produire un incident silencieux en production : le code continue sans erreur, mais le résultat est factuellement incomplet (l'article absent disparaît sans trace dans `picks` ni `skipped`).

## Risques

- **VÉRIFIÉ_CODE — Garde sur `requested ≤ 0` présente dans `can_fulfil()`.** `can_fulfil()` rejette toute quantité nulle ou négative (`inventory/orders.py:7-8`). Le vecteur d'injection via `requested` négatif (ex. `-6`) est fermé par cette garde.
- **HYPOTHÈSE — `TypeError` non guidée sur `requested` de type incorrect.** Un `requested` de type non-numérique (ex. `None`, `"3"`) provoquerait probablement une `TypeError` avant même d'atteindre la garde `requested <= 0`, car Python lèverait une erreur à la comparaison. Ce comportement n'a pas été reproduit ; il s'agit d'une inférence par lecture du code.
- **HYPOTHÈSE — Mutation de `ITEMS` par `list_items()`.** Si un appelant de `list_items()` modifie la liste retournée, l'état global de `ITEMS` est corrompu pour tous les appels suivants. Risque nul aujourd'hui, réel si une couche concurrente ou externe est introduite. (`inventory/warehouse.py:11-12`)
- **HYPOTHÈSE — `TypeError` non guidée sur `None` non gardé.** Un futur appelant qui enchaîne `available_qty(find_by_sku("INEXISTANT"))` sans garde obtiendra `TypeError: 'NoneType' object is not subscriptable` — erreur technique non métier, difficile à diagnostiquer sans connaître le code source.

## Recommandations priorisées

1. **Documenter le contrat `None` de `find_by_sku()` dans la docstring** — Préciser que le retour peut être `None` et que l'appelant doit tester avant usage, pour éviter les chaînes d'appel non gardées. (`inventory/warehouse.py:15-19`)
2. **Ajouter un signal sur SKU inconnu ignoré dans `picking_list()`** — À minima un `warnings.warn()` ou un second retour (liste des SKUs ignorés) pour éviter les prélèvements silencieusement incomplets. (`inventory/orders.py:32-33`)
3. **Ajouter des tests pour `can_fulfil()`** — La fonction porte la décision de faisabilité commerciale mais n'a aucun test. (`inventory/orders.py:6-12`, `tests/test_orders.py`)

## Questions ouvertes

- Doit-on valider le type de `requested` en entrée de `can_fulfil()`, ou la validation appartient-elle à l'orchestrateur appelant ? La garde `requested <= 0` existe déjà, mais pas le contrôle de type.
- Le signal sur SKU inconnu dans `picking_list()` doit-il être un log, une exception, ou une entrée dans un troisième retour (`invalid`) distinct de `skipped` ?
- Si une couche HTTP est ajoutée (FastAPI, Flask), des règles de sécurité supplémentaires seront nécessaires (authz, rate limiting, validation de schéma d'entrée) — hors périmètre du pilote actuel, mais à anticiper.
