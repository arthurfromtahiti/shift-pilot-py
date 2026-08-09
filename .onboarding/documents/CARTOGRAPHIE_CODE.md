# CARTOGRAPHIE_CODE — shift-pilot-py

> Confiance : high

## Aperçu

Dépôt minimaliste : 2 modules métier (76 lignes), 2 suites de tests (35 lignes), zéro dépendance externe, zéro framework. La structure suit une séparation domaine claire (`warehouse → orders`).

```
shift-pilot-py/
├── inventory/
│   ├── __init__.py          (vide)
│   ├── warehouse.py         (29 lignes) — Domaine entrepôt-stock
│   └── orders.py            (47 lignes) — Domaine préparation-commande
├── tests/
│   ├── __init__.py          (vide)
│   ├── test_warehouse.py    (22 lignes) — Tests warehouse
│   └── test_orders.py       (93 lignes) — Tests orders
├── README.md                (15 lignes)
├── CARTE_DES_DOMAINES.md    (61 lignes)
└── [non versionné : .onboarding/, relectures/, audits/, workflows/]
```

---

## Fichiers source

### `inventory/warehouse.py` (29 lignes)

**Responsabilité** : Référentiel du stock et opérations de base sur les articles.

**Données** :
```python
ITEMS = [
    {"sku": "AX-100", "label": "Ancre 10kg", "qty": 12, "reserved": 2, "zone": "A"},
    {"sku": "BX-220", "label": "Bouée gonflable", "qty": 0, "reserved": 0, "zone": "B"},
    {"sku": "CX-330", "label": "Cordage 20m", "qty": 45, "reserved": 5, "zone": "A"},
    {"sku": "DX-440", "label": "Dérive alu", "qty": 7, "reserved": 1, "zone": "C"},
]
```

**Structure de chaque article** : dict `{sku: str, label: str, qty: int, reserved: int, zone: str}`.
- `sku` : identifiant unique (en pratique, testé sur les 4 articles ; non garanti par le schéma).
- `label` : libellé lisible.
- `qty` : stock brut en entrepôt.
- `reserved` : quantité réservée par des commandes (pas encore prélevée).
- `zone` : zone de localisation dans l'entrepôt (`"A"`, `"B"`, `"C"`).

**Fonctions** :

| Fonction | Signature | Ligne | Rôle | Retour |
|----------|-----------|------|------|--------|
| `list_items()` | `() → list` | 11-12 | Retourne la liste complète des articles. | `ITEMS` (référence directe, pas copie). |
| `find_by_sku(sku)` | `(str) → dict \| None` | 15-19 | Cherche un article par SKU (insensible à la casse). | Dict article ou `None` si absent. |
| `available_qty(item)` | `(dict) → int` | 22-24 | Calcule la disponibilité à la vente. | `max(0, qty - reserved)` — toujours ≥ 0. |
| `items_in_zone(zone)` | `(str) → list` | 27-28 | Retourne les articles d'une zone. | Liste de dicts (peut être vide). |

**Éléments clés** :
- `available_qty()` est sécurisée : `max(0, item["qty"] - item["reserved"])` garantit le non-negativité.
- `find_by_sku()` compare en casse insensible (`sku.upper()`), donc "AX-100" et "ax-100" retournent le même article.

**Dettes / Limites** :
- `list_items()` expose une référence, pas une copie → risque de mutation externe.
- Aucune validation de schéma (ni dataclass, ni TypedDict).
- Unicité de SKU implicite, non garantie.

---

### `inventory/orders.py` (47 lignes)

**Responsabilité** : Opérations dérivées pour la préparation de commande. Consomme entièrement `warehouse.py`.

**Dépendances** :
```python
from inventory.warehouse import find_by_sku, available_qty
```

**Fonctions** :

| Fonction | Signature | Ligne | Rôle | Retour |
|----------|-----------|------|------|--------|
| `can_fulfil(sku, requested)` | `(str, int) → bool` | 6-12 | Vérifie si une demande peut être honorée. | `True` si disponibilité >= demande, `False` sinon. |
| `picking_list(lines)` | `(list[(str, int)]) → dict` | 15-46 | Génère une liste de prélèvement avec allocation cumulée. | `{picks: [...], skipped: [...]}` où picks est trié par zone. |

**Détails** :

#### `can_fulfil(sku, requested)` (lignes 6-12)
```python
def can_fulfil(sku, requested):
    if requested <= 0:
        return False                           # ligne 8 — rejette les demandes nulles/négatives
    item = find_by_sku(sku)                    # ligne 9
    if item is None:                           # ligne 10
        return False                           # ligne 11 — article inexistant
    return available_qty(item) >= requested    # ligne 12 — comparaison
```

**Flux** :
1. Valide `requested > 0` ; rejette les demandes nulles/négatives.
2. Cherche l'article via `find_by_sku()`.
3. Si absent, retourne `False` (infaisable).
4. Sinon, compare `available_qty(item) >= requested`.

**Propriétés** :
- Demandes nulles/négatives toujours rejetées.
- Article inexistant traité comme rupture.
- Disponibilité toujours ≥ 0 (grâce à `max()` dans `available_qty()`).

**Tests couvrant cette fonction** : aucun test direct ni indirect dans la suite actuelle. `picking_list()` n'appelle pas `can_fulfil()` ; la fonction est utilisable au niveau du client mais n'est pas validée par les tests. Comportements documentés comme règles observées au code, non comme couverture de tests.

#### `picking_list(lines)` (lignes 15-46)
```python
def picking_list(lines):
    picks = []                                 # ligne 16
    skipped = []                               # ligne 17
    allocated = {}                             # ligne 18 — cumul par article
    for idx, (sku, qty) in enumerate(lines):   # ligne 19
        if qty <= 0:                           # ligne 20
            continue                           # ligne 21 — ignore sans signal
        item = find_by_sku(sku)                # ligne 22
        if item is None:                       # ligne 23
            continue                           # ligne 24 — ignore sans signal
        canonical = item["sku"]                # ligne 25 — normalise sur le SKU canonique
        remaining = available_qty(item) - allocated.get(canonical, 0)  # ligne 26
        if qty > remaining:                    # ligne 27
            skipped.append({...})              # ligne 28-32 — signal la pénurie
            continue                           # ligne 33
        allocated[canonical] = allocated.get(canonical, 0) + qty  # ligne 34
        picks.append({"sku": sku, "zone": item["zone"], "qty": qty})  # ligne 35
    return {"picks": sorted(picks, key=lambda entry: entry["zone"]), "skipped": skipped}  # ligne 36
```

**Flux** :
1. Initialise `picks`, `skipped`, et `allocated` (pour tracer l'allocation par article).
2. Itère chaque tuple `(sku, qty)` avec son index.
3. Ignore les demandes nulles/négatives sans signal.
4. Cherche l'article ; ignore les SKU inconnus sans signal.
5. Normalise le SKU sur `item["sku"]` (canonical) pour gérer les variantes de casse.
6. Calcule le reste disponible : `available_qty(item) - allocated[canonical]`.
7. Si demande > reste : ajoute à `skipped` avec la quantité manquante, puis passe au suivant.
8. Sinon : ajoute à `allocated`, puis à `picks`.
9. Trie `picks` par zone en ordre alphabétique.
10. Retourne `{picks: picks_triés, skipped: skipped}`.

**Propriétés de robustesse** :
- **Surallocation impossible** : l'allocation est cumulée par article.
- **Signalement des pénuries** : chaque ligne rejetée pour rupture est dans `skipped` avec la quantité manquante.
- **Casse insensible** : "AX-100" et "ax-100" partagent l'allocation (via `canonical`).

**Tests couvrant cette fonction** : `test_orders.py` contient 10 tests pour `picking_list()` (multi-lignes, casse, surallocation, etc.).

---

### `tests/test_warehouse.py` (22 lignes)

**Portée** : Couvre `inventory/warehouse.py` uniquement.

**Suite** : Classe `TestWarehouse` (unittest) avec 3 méthodes.

| Test | Ligne | Objectif | État |
|------|-------|----------|------|
| `test_find_by_sku()` | 7-9 | Vérifie la recherche : SKU connu retourne un résultat, SKU absent retourne `None`. | ✓ Vert |
| `test_items_in_zone()` | 11-12 | Vérifie le filtrage : zone "A" contient 2 articles. | ✓ Vert |
| `test_available_qty_cx330()` | 14-18 | Vérifie l'invariant : `CX-330` (qty=45, reserved=5) → disponible=40. | ✓ Vert |
| `test_available_qty_borne_a_zero_quand_reserved_superieur_a_qty()` | 20-23 | Vérifie la borne : si reserved > qty, retourne 0. | ✓ Vert |
| `test_invariant_reserved_ne_depasse_pas_qty_dans_items()` | 25-31 | Vérification d'invariant : aucun article n'a reserved > qty. | ✓ Vert |
| `test_find_by_sku_insensible_casse()` | 33-37 | Vérifie l'insensibilité à la casse : "ax-100", "Ax-100", "AX-100" retrouvent le même article. | ✓ Vert |

**Couverture** :
- ✓ `find_by_sku()` : couverture basique (SKU connu/absent, insensibilité casse).
- ✓ `items_in_zone()` : couverture minimale (compte zone A, pas les identités).
- ✓ `available_qty()` : couverture du non-negativité et cas normal.
- ✗ `list_items()` : pas de test.

### `tests/test_orders.py` (93 lignes)

**Portée** : Couvre `inventory/orders.py` en intégralité.

**Suite** : Classe `TestPickingList` (unittest) avec 10 méthodes testant `picking_list()`.

**Tests clés** :

| Test | Objectif | Comportement testé |
|------|----------|-------------------|
| `test_article_hors_stock_exclu_des_picks` | Article en rupture absent de picks | BX-220 (disponible=0, demandé=1) → picks vide |
| `test_article_hors_stock_journalise_dans_skipped` | Article en rupture signalé | BX-220 → skipped contient la pénurie |
| `test_cx330_inclus_dans_picks` | Article avec stock inclus | CX-330 (disponible=40, demandé=10) → picks contient l'entrée |
| `test_quantite_nulle_exclue_sans_trace` | Demande nulle ignorée | qty=0 → ni picks ni skipped |
| `test_quantite_negative_exclue_sans_trace` | Demande négative ignorée | qty<0 → ni picks ni skipped |
| `test_plusieurs_lignes_meme_sku_depassement_exclu_des_picks` | Surallocation par SKU | CX-330 (40 disponible) : 30+30 → 1e incluse, 2e exclue |
| `test_plusieurs_lignes_meme_sku_depassement_journalise_dans_skipped` | Surallocation signalée | CX-330 : 2e ligne → skipped avec qty_missing=20 |
| `test_plusieurs_lignes_meme_sku_dans_les_limites` | Allocation OK | CX-330 : 20+20 → les deux incluses |
| `test_plusieurs_lignes_meme_sku_allocation_cumulative` | Allocation cumulée | CX-330 : 15+15+15 → 2e ok, 3e exclue (remaining=10) |
| `test_meme_article_casse_differente_cumul_respecte` | Casse insensible pour allocation | "AX-100" + "ax-100" → cumul de 6+6 > 10 → 2e exclue |

**Couverture** :
- ✓ `picking_list()` : couverture partielle (10 tests : mono-ligne, allocation cumulée, casse, surallocation, signalement, pénuries ; les cas multi-zones 3.1.b-d et limites 3.2.a,c ne sont pas testés).
- ✗ `can_fulfil()` : aucun test direct ni indirect (utilisable au niveau client, pas validée par la suite actuelle).

---

## Architecture globale

### Graphe de dépendances

```
tests/test_warehouse.py
    ↓ imports
inventory/warehouse.py
    ↑ imports from
inventory/orders.py
```

**Propriété** : dépendance unidirectionnelle, pas de cycle.

### Patterns architecturaux

**Séparation domaine** :
- `warehouse.py` = couche de données et primitives.
- `orders.py` = couche métier dérivée.

**Absence d'abstraction** :
- Pas d'interface de repository.
- Pas de factory.
- Pas de dependency injection.
- Données couplées directement au module (`ITEMS` en dur).

**Pas de couche d'exposition** :
- Zéro route HTTP.
- Zéro CLI.
- Zéro événement.
- Fonctions Python pures, appelables uniquement par import direct.

### Éléments critiques pour le projet

**Point de défaillance unique** :
- `inventory/warehouse.py:3-8` — la définition de `ITEMS`.
- Toute modification ici casse tous les tests, tous les workflows.

**Zones de fragilité** :
- `list_items()` ligne 12 — référence directe sans copie (pas de défense contre mutation).
- `find_by_sku()` — unicité de SKU non garantie par le schéma (premier match retourné).
- `picking_list()` — ignore silencieusement les demandes nulles/négatives et SKU inconnus (par conception).

**Zones de couverture** :
- Warehouse : 6 tests couvrent find_by_sku, items_in_zone, available_qty (robustesse et non-negativité).
- Orders : 10 tests couvrent `picking_list()` en profondeur (allocation, surallocation, multi-lignes, casse).

---

## Dépendances et intégrations

**Dépendances externes** : **aucune**. Le projet n'a ni `requirements.txt`, ni `pyproject.toml`, ni `setup.py`. Uniquement stdlib Python 3.12.

**Intégrations réseau** : **aucune**.

**Intégrations base de données** : **aucune**.

**Intégrations événementielle** : **aucune**.

---

## Configuration et outillage absent

| Outil | Présent ? | Note |
|-------|-----------|------|
| CI/CD | ✗ | Pas de `.github/`, `.gitlab-ci.yml`, etc. |
| Linting | ✗ | Pas de pylint, flake8, mypy. |
| Coverage | ✗ | Pas de `.coveragerc`, `pytest.ini`. |
| .gitignore | ✗ | `__pycache__/`, `.pyc` sont tracés par git. |
| Type hints | ✗ | Aucun type hint dans le code source. |
| Docstrings | ✗ | Seulement dans `available_qty()` (fonction clé pour la disponibilité). |

---

## Filière d'exécution

**Commande standard** (documentée dans README.md) :
```bash
python3 -m unittest discover -s tests -t .
```

**Sortie observée** :
```
................
------
Ran 16 tests in 0.001s
OK
```

- 16 points = 16 tests verts (6 warehouse + 10 orders).
- Tous les tests passent. `available_qty()` est sécurisée via `max(0, ...)`.

---

## Trajets de refactoring prévisibles

Si ce pilote évolue, les points chauds seront :

1. **Ajouter une persistance** :
   - Remplacer `ITEMS` littéral par un appel à une base (SQLite, PostgreSQL, API).
   - Nécessite une abstraction repository.
   - Impact : `warehouse.py` se refactorise entièrement.

2. **Ajouter une couche d'exposition** (HTTP, CLI) :
   - Créer `api/routes.py`, `cli/commands.py` ou équivalent.
   - Ajouter validation de schéma d'entrée (pydantic, marshmallow).
   - Impact : création de nouveaux modules, pas de refactoring du cœur.

3. **Améliorer l'allocation et le signalement** :
   - Ajouter des logs pour les lignes ignorées (qty nulle/négative, SKU inconnu).
   - Permettre à l'appelant de distinguer « complètement allouée » vs « partiellement allouée » pour une commande.
   - Impact : extension de la signature de `picking_list()` ou création d'une fonction enveloppe.

4. **Implémenter un orchestrateur de commande** :
   - Créer `process_order(lines)` qui enchaîne vérification préalable puis prélèvement.
   - Décider si l'orchestrateur valide *toutes* les lignes d'abord, ou permet l'allocation partielle.
   - Impact : nouveaux fichiers ou nouvelles fonctions dans `orders.py`.

5. **Ajouter une validation de schéma** :
   - Utiliser TypedDict ou dataclass pour les articles et les lignes de commande.
   - Ajouter une validation de type pour `qty` et `requested` au runtime.
   - Impact : ajouts de dépendance (typing_extensions, pydantic) ou utilisation de stdlib.

---

## Vérifications de cohérence

**Cohérence code-workflow** :
- ✓ Chaque workflow décrit une fonction du code.
- ✓ Chaque fonction du code a un workflow (sauf `list_items()`, qui est implicite).
- ✓ Aucun écart entre description et implémentation.

**Cohérence code-tests** :
- ✓ Les 16 tests exécutent le code décrit.
- ✓ Couverture partielle : `warehouse.py` (6 tests : find_by_sku, items_in_zone, available_qty) + `orders.py` (10 tests : picking_list complet, can_fulfil non testé).

**Cohérence code-domaines** :
- ✓ Deux modules, deux domaines.
- ✓ Dépendance unidirectionnelle aligne les domaines (stock → préparation).

---

## Résumé technique pour un futur développeur

- **Stack** : Python 3.12 stdlib, aucun framework, aucune dépendance.
- **Entrée** : lancer `python3 -m unittest discover -s tests -t .` → 16 tests verts.
- **Cœur** : `inventory/warehouse.py` (4 fonctions : stock, recherche, zone, disponibilité) + `inventory/orders.py` (2 fonctions : vérification, prélèvement).
- **Data** : 4 articles en dur dans `ITEMS` (stock modifiable).
- **Architecture** : dépendance unidirectionnelle warehouse → orders, aucune abstraction, aucune persistance.
- **Points clés** : 
  - `available_qty()` garantit une disponibilité ≥ 0 via `max(0, ...)`.
  - `picking_list()` suit l'allocation cumulée par article, signale les pénuries (10 tests).
  - `find_by_sku()` insensible à la casse.
- **Couverture** : 6 tests warehouse + 10 tests orders = 16 tests au total. `can_fulfil()` sans test direct mais utilisable au niveau client.
- **Prochaine étape probable** : ajouter une couche HTTP (API REST) ou une persistance (base de données).
