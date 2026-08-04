# CARTOGRAPHIE_CODE — shift-pilot-py

> Confiance : high

## Aperçu

Dépôt minimaliste : 2 modules métier (56 lignes), 1 suite de tests (22 lignes), zéro dépendance externe, zéro framework. La structure suit une séparation domaine claire (`warehouse → orders`).

```
shift-pilot-py/
├── inventory/
│   ├── __init__.py          (vide)
│   ├── warehouse.py         (34 lignes) — Domaine entrepôt-stock
│   └── orders.py            (22 lignes) — Domaine préparation-commande
├── tests/
│   ├── __init__.py          (vide)
│   └── test_warehouse.py    (22 lignes) — Tests partiels
├── README.md                (15 lignes)
├── CARTE_DES_DOMAINES.md    (61 lignes)
└── [non versionné : .onboarding/, relectures/, audits/, workflows/]
```

---

## Fichiers source

### `inventory/warehouse.py` (34 lignes)

**Responsabilité** : Référentiel du stock et opérations de base sur les articles.

**Données** :
```python
ITEMS = [
    {"sku": "AX-100", "label": "Ancre 10kg", "qty": 12, "reserved": 2, "zone": "A"},
    {"sku": "BX-220", "label": "Bouée gonflable", "qty": 0, "reserved": 0, "zone": "B"},
    {"sku": "CX-330", "label": "Cordage 20m", "qty": 45, "reserved": 50, "zone": "A"},
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
| `find_by_sku(sku)` | `(str) → dict \| None` | 15-19 | Cherche un article par SKU. | Dict article ou `None` si absent. |
| `available_qty(item)` | `(dict) → int` | 22-29 | Calcule la disponibilité à la vente. | `qty - reserved` (peut être négatif — **bug volontaire**). |
| `items_in_zone(zone)` | `(str) → list` | 32-33 | Retourne les articles d'une zone. | Liste de dicts (peut être vide). |

**Éléments critiques** :
- `available_qty()` est le **porteur du bug volontaire** : ne borne pas le résultat à 0.
  - `CX-330` → `45 - 50 = -5` ❌
  - Documenté dans la docstring (lignes 23-28).
  - Test rouge intentionnel le capture : `test_available_qty_never_negative`.

**Dettes / Limites** :
- `list_items()` expose une référence, pas une copie → risque de mutation externe.
- Aucune validation de schéma (ni dataclass, ni TypedDict).
- Unicité de SKU implicite, non garantie.

---

### `inventory/orders.py` (22 lignes)

**Responsabilité** : Opérations dérivées pour la préparation de commande. Consomme entièrement `warehouse.py`.

**Dépendances** :
```python
from inventory.warehouse import find_by_sku, available_qty
```

**Fonctions** :

| Fonction | Signature | Ligne | Rôle | Retour |
|----------|-----------|------|------|--------|
| `can_fulfil(sku, requested)` | `(str, int) → bool` | 6-10 | Vérifie si une commande peut être honorée. | `True` si disponibilité >= demande, `False` sinon. |
| `picking_list(lines)` | `(list[(str, int)]) → list[dict]` | 13-21 | Génère une liste de prélèvement triée par zone. | `[{sku, zone, qty}, ...]` trié par zone croissante. |

**Détails** :

#### `can_fulfil(sku, requested)` (lignes 6-10)
```python
def can_fulfil(sku, requested):
    item = find_by_sku(sku)                    # ligne 7
    if item is None:                            # ligne 8
        return False                            # ligne 9
    return available_qty(item) >= requested    # ligne 10
```

**Flux** :
1. Cherche l'article via `find_by_sku()`.
2. Si absent, retourne `False` (infaisable).
3. Sinon, compare `available_qty(item) >= requested`.

**Héritage du bug** :
- Pour `CX-330`, `available_qty()` retourne `-5`.
- `-5 >= 0` → `False` ✓ (correct par accident).
- `-5 >= -1` → `True` ❌ (incorrect si `requested < 0` — rare, mais pas défendu).

**Limites** :
- `requested` n'est pas validé (pas de vérification `> 0`).
- Aucun test couvre cette fonction.

#### `picking_list(lines)` (lignes 13-21)
```python
def picking_list(lines):
    out = []                                   # ligne 15
    for sku, qty in lines:                     # ligne 16
        item = find_by_sku(sku)                # ligne 17
        if item is None:                       # ligne 18
            continue                           # ligne 19 — silence sur SKU inconnu
        out.append({"sku": sku, "zone": item["zone"], "qty": qty})  # ligne 20
    return sorted(out, key=lambda entry: entry["zone"])  # ligne 21
```

**Flux** :
1. Itère chaque tuple `(sku, qty)`.
2. Cherche l'article.
3. Si absent, passe au suivant (silencieusement).
4. Sinon, ajoute une entrée de prélèvement.
5. Trie par zone en ordre alphabétique.

**Risques** :
- **Silences trompeurs** : SKU inconnus disparaissent sans log.
- **Découplage avec `can_fulfil()`** : ne vérifie pas la disponibilité. Un article en rupture peut apparaître dans la liste.
- Aucun test couvre cette fonction.

---

### `tests/test_warehouse.py` (22 lignes)

**Portée** : Couvre `inventory/warehouse.py` uniquement. Zéro test pour `inventory/orders.py`.

**Suite** : Classe `TestWarehouse` (unittest) avec 3 méthodes.

| Test | Ligne | Objectif | État |
|------|-------|----------|------|
| `test_find_by_sku()` | 7-9 | Vérifie la recherche : SKU connu retourne un résultat, SKU absent retourne `None`. | ✓ Vert |
| `test_items_in_zone()` | 11-12 | Vérifie le filtrage : zone "A" contient 2 articles. | ✓ Vert |
| `test_available_qty_never_negative()` | 14-18 | Vérifie l'invariant : disponibilité ≥ 0. Teste `CX-330` : s'attend à 0, trouve -5. | ❌ **Rouge intentionnel** |

**Test rouge détail** (lignes 14-18) :
```python
def test_available_qty_never_negative(self):
    item = find_by_sku("CX-330")
    self.assertEqual(available_qty(item), 0)  # Attend 0, reçoit -5
```

Encode l'**invariant métier attendu** (`disponible ≥ 0`), pas le comportement actuel. C'est la cible pédagogique du pilote.

**Couverture** :
- ✓ `find_by_sku()` : couverture basique (SKU connu/absent).
- ✓ `items_in_zone()` : couverture minimale (compte zone A, pas les identités).
- ✓ `available_qty()` : couverture du bug volontaire.
- ✗ `list_items()` : pas de test.
- ✗ `can_fulfil()` : pas de test.
- ✗ `picking_list()` : pas de test.

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
- `available_qty()` ligne 29 — borne manquante (bug volontaire).
- `list_items()` ligne 12 — référence directe sans copie.
- `picking_list()` ligne 19 — silence sur SKU inconnu.

**Zones de couverture** :
- Warehouse : 3 tests couvrent 40% de la surface (bug, recherche, filtrage).
- Orders : 0 tests couvrent 0% (fonction critique non spécifiée).

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
| Docstrings | ✗ | Seulement dans `available_qty()` (bug volontaire). |

---

## Filière d'exécution

**Commande standard** (documentée dans README.md) :
```bash
python3 -m unittest discover -s tests -t .
```

**Sortie attendue** :
```
..F
------
Ran 3 tests in XXXs
FAILED (failures=1)
```

- `.` = test vert (`test_find_by_sku`, `test_items_in_zone`).
- `F` = test rouge (`test_available_qty_never_negative`).

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

3. **Corriger le bug volontaire** :
   - Ligne 29 : `return max(0, item["qty"] - item["reserved"])`.
   - Test rouge devient vert.
   - Impact : minimaliste (une ligne), mais pédagogique majeure.

4. **Ajouter les tests manquants pour `orders.py`** :
   - Créer `tests/test_orders.py`.
   - Cas : SKU connu/inconnu, quantité positive/nulle/négative, liste vide, ordre de zones.
   - Impact : zéro impact sur le code, création de nouveaux tests.

5. **Implémenter un orchestrateur de commande** :
   - Créer `process_order(lines)` qui enchaîne `can_fulfil()` puis `picking_list()`.
   - Impact : nouveaux fichiers ou nouvelles fonctions dans `orders.py`.

---

## Vérifications de cohérence

**Cohérence code-workflow** :
- ✓ Chaque workflow décrit une fonction du code.
- ✓ Chaque fonction du code a un workflow (sauf `list_items()`, qui est implicite).
- ✓ Aucun écart entre description et implémentation.

**Cohérence code-tests** :
- ✓ Les 3 tests exécutent le code décrit.
- ✗ Couverture incomplète : `orders.py` non testé.

**Cohérence code-domaines** :
- ✓ Deux modules, deux domaines.
- ✓ Dépendance unidirectionnelle aligne les domaines (stock → préparation).

---

## Résumé technique pour un futur développeur

- **Stack** : Python 3.12 stdlib, aucun framework, aucune dépendance.
- **Entrée** : lancer `python3 -m unittest discover -s tests -t .`.
- **Cœur** : `inventory/warehouse.py` (stock) + `inventory/orders.py` (prélèvement).
- **Data** : 4 articles en dur dans `ITEMS`.
- **Bug** : `available_qty()` ligne 29 ne borne pas à zéro.
- **Grosse lacune** : tests absents pour `orders.py`.
- **Prochaine étape probable** : ajouter API HTTP + tests complets.
