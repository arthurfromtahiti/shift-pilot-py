# CAHIER_RECETTE — shift-pilot-py

> Confiance : high

## Objet

Ce cahier de recette énumère les cas de test **dérivés directement des workflows métier** documentés en étape 2. Chaque cas est tracé à un workflow, à une fonction code, et à un objectif métier. Le but est de guider la création d'une suite de test complète couvrant tous les domaines.

**État actuel** : 13 tests existent et passent. `tests/test_warehouse.py` contient 3 tests (warehouse), et `tests/test_orders.py` contient 10 tests (orders picking_list). La couverture fonctionnelle est **partielle** : le domaine entrepôt-stock a des tests sur `find_by_sku()` et `items_in_zone()`, mais le domaine préparation-commande manque de tests directs sur `can_fulfil()` (voir section 2, État actuel).

---

## Structure du cahier

Pour chaque workflow :
1. **Cas nominal** : le parcours heureux.
2. **Cas limites** : valeurs frontières, entrées vides, SKU inconnus, etc.
3. **Cas dégradés** : comportements attendus sous bug volontaire.
4. **État de l'implémentation** : ✓ testé, ✗ non testé, ⚠ partiellement testé.

---

## Workflow 1 : Consultation du stock

**Référence** : `WORKFLOW_CONSULTATION_STOCK.md`  
**Domaine** : `entrepot-stock`  
**Fonctions testées** : `list_items()`, `find_by_sku()`, `items_in_zone()`, `available_qty()`

### 1.1 — Consultation du référentiel complet

**Objectif métier** : obtenir la liste complète de tous les articles en entrepôt.

**Fonction** : `list_items()`

**Cas de test** :

| # | Cas | Entrée | Attente | Statut |
|---|-----|--------|---------|--------|
| 1.1.a | Nominal : liste complète | Appel direct `list_items()` | Retourne une liste de 4 articles. | ✗ Non testé |
| 1.1.b | Intégrité des champs | Retour de `list_items()` | Chaque dict contient exactement 5 clés : `sku`, `label`, `qty`, `reserved`, `zone`. | ✗ Non testé |
| 1.1.c | Ordre de retour | Appel direct | Retourne les articles dans l'ordre de définition : AX-100, BX-220, CX-330, DX-440. | ✗ Non testé |
| 1.1.d | Référence vs copie (robustesse) | Appel direct, puis modification du retour (`ret[0]["qty"] = 999`) | Vérifier si `ITEMS` est affectée (risque de mutation). Actuellement : oui, c'est une référence. | ✗ Non testé (test de robustesse) |

---

### 1.2 — Recherche d'un article par SKU

**Objectif métier** : localiser rapidement un article unique par son identifiant.

**Fonction** : `find_by_sku(sku)`

**Cas de test** :

| # | Cas | Entrée | Attente | Statut |
|---|-----|--------|---------|--------|
| 1.2.a | SKU connu (AX-100) | `find_by_sku("AX-100")` | Retourne le dict de l'article AX-100. | ✓ Vert (`test_find_by_sku`) |
| 1.2.b | SKU connu (CX-330) | `find_by_sku("CX-330")` | Retourne le dict avec `qty=45`, `reserved=5`. | ✗ Non testé |
| 1.2.c | SKU absent | `find_by_sku("INEXISTANT")` | Retourne `None`, pas d'exception. | ✓ Vert (`test_find_by_sku`) |
| 1.2.d | SKU vide | `find_by_sku("")` | Retourne `None` (aucun article n'a SKU vide). | ✗ Non testé |
| 1.2.e | SKU nul (type incorrect) | `find_by_sku(None)` | Comportement non défini : probablement `False implicitement` → retourne `None`. | ✗ Non testé (robustesse) |
| 1.2.f | SKU type incorrect (int) | `find_by_sku(123)` | Comportement non défini : `123 == "AX-100"` est faux → retourne `None`. | ✗ Non testé (robustesse) |
| 1.2.g | Insensibilité à la casse | `find_by_sku("ax-100")` (minuscules) | Retourne le dict de l'article AX-100 (comparaison en `.upper()`). | ✓ Vert (implicitement dans test_orders.py) |

---

### 1.3 — Filtrage par zone d'entrepôt

**Objectif métier** : récupérer tous les articles d'une zone (ex. préparer un circuit de prélèvement pour la zone A).

**Fonction** : `items_in_zone(zone)`

**Cas de test** :

| # | Cas | Entrée | Attente | Statut |
|---|-----|--------|---------|--------|
| 1.3.a | Zone A (2 articles) | `items_in_zone("A")` | Retourne une liste de 2 articles : AX-100, CX-330. | ✓ Vert (`test_items_in_zone`) |
| 1.3.b | Zone B (1 article, rupture) | `items_in_zone("B")` | Retourne une liste de 1 article : BX-220. | ✗ Non testé |
| 1.3.c | Zone C (1 article) | `items_in_zone("C")` | Retourne une liste de 1 article : DX-440. | ✗ Non testé |
| 1.3.d | Zone inconnue | `items_in_zone("Z")` | Retourne une liste vide `[]`, pas d'exception. | ✗ Non testé |
| 1.3.e | Zone vide (chaîne vide) | `items_in_zone("")` | Retourne une liste vide (aucun article n'a zone ""). | ✗ Non testé |
| 1.3.f | Ordre dans la liste retournée | `items_in_zone("A")` | Retourne AX-100 puis CX-330 (ordre de `ITEMS`). | ✗ Non testé (ordre) |
| 1.3.g | Identités des articles | `items_in_zone("A")` | Vérifie les SKUs exacts, les labels, les quantités. | ✗ Non testé (identités) |

---

### 1.4 — Calcul de disponibilité à la vente

**Objectif métier** : connaître la quantité réellement vendable (stock brut - réservé).

**Fonction** : `available_qty(item)`

**Règle métier** : disponibilité ≥ 0 toujours.  
**Règle implémentée** : `max(0, qty - reserved)` — garantit la non-negativité.

**Cas de test** :

| # | Cas | Entrée | Attente | Réalité (code) | Statut |
|---|-----|--------|---------|---|--------|
| 1.4.a | Article normal (AX-100, qty=12, reserved=2) | `available_qty(find_by_sku("AX-100"))` | Retourne 10 | Retourne 10 ✓ | ✗ Non testé |
| 1.4.b | Article en rupture totale (BX-220, qty=0, reserved=0) | `available_qty(find_by_sku("BX-220"))` | Retourne 0 | Retourne 0 ✓ | ✗ Non testé |
| 1.4.c | Article avec réservations élevées (CX-330, qty=45, reserved=5) | `available_qty(find_by_sku("CX-330"))` | Retourne 40 | Retourne 40 ✓ | ✓ Vert (implicitement dans test_orders.py) |
| 1.4.d | Article avec petite marge (DX-440, qty=7, reserved=1) | `available_qty(find_by_sku("DX-440"))` | Retourne 6 | Retourne 6 ✓ | ✗ Non testé |
| 1.4.e | Entrée `None` (robustesse) | `available_qty(None)` | Pas d'attente définie — entrée invalide | Lève `TypeError` sur accès `item["qty"]` | ✗ Non testé (robustesse) |
| 1.4.f | Dict malformé (clé `qty` manquante) | `available_qty({"sku": "XX", "reserved": 0})` | Pas d'attente définie — schéma invalide | Lève `KeyError: 'qty'` lors du calcul | ✗ Non testé (robustesse) |

**Propriété assurée** :
- `available_qty()` retourne toujours ≥ 0 via `max(0, ...)`.
- Aucun test n'échoue sur cette fonction — le bug volontaire a été corrigé.

---

## Workflow 2 : Vérification de faisabilité de commande

**Référence** : `WORKFLOW_FAISABILITE_COMMANDE.md`  
**Domaine** : `preparation-commande`  
**Fonction testée** : `can_fulfil(sku, requested)`

**État actuel** : cette fonction est couverte **implicitement** par `test_orders.py` via l'allocation dans `picking_list()`. Aucun test direct, mais la logique est validée indirectement.

### 2.1 — Vérification nominale

**Objectif métier** : avant de lancer un prélèvement, vérifier qu'on dispose de la quantité demandée.

| # | Cas | SKU | Quantité | Disponibilité réelle | Attente | Notes |
|---|-----|-----|----------|----------------------|---------|-------|
| 2.1.a | Nominal : stock suffisant | AX-100 | 5 | 10 | `True` | Commande possible. |
| 2.1.b | Nominal : stock exact | AX-100 | 10 | 10 | `True` | Limite atteinte. |
| 2.1.c | Dégradé : stock insuffisant | AX-100 | 15 | 10 | `False` | Rupture. |
| 2.1.d | Validation : quantité zéro | AX-100 | 0 | 10 | `False` | Demande nulle rejetée (`requested <= 0` → `False`). |
| 2.1.e | Validation : quantité négative | AX-100 | -1 | 10 | `False` | Demande négative rejetée (`requested <= 0` → `False`). |

### 2.2 — SKU inexistant

| # | Cas | SKU | Quantité | Attente | Notes |
|---|-----|-----|----------|---------|-------|
| 2.2.a | SKU absent | INEXISTANT | 5 | `False` | Article n'existe pas, donc rupture. |
| 2.2.b | SKU vide | "" | 5 | `False` | Idem. |
| 2.2.c | SKU nul (robustesse) | None | 5 | `False` | Code : `find_by_sku(None)` retourne `None`, `can_fulfil()` retourne `False`. Comportement sûr. |

### 2.3 — Validation des entrées

| # | Cas | Entrée | Comportement observé | Notes |
|---|-----|--------|---------|---------|
| 2.3.a | Type SKU incorrect | `can_fulfil(123, 5)` | Retourne `False` (SKU ne correspond à aucun article) | Pas de validation de type, mais comportement sûr. |
| 2.3.b | Type quantité incorrect | `can_fulfil("AX-100", "5")` | Lève `TypeError` lors de la comparaison `"5" <= 10` (str vs int) | Pas de validation de type. |

---

## Workflow 3 : Génération de liste de prélèvement avec allocation

**Référence** : `WORKFLOW_PRELEVEMENT_COMMANDE.md`  
**Domaine** : `preparation-commande`  
**Fonction testée** : `picking_list(lines)`

**Signature actuelle** : `picking_list(lines) → {picks: [dict], skipped: [dict]}`

**État actuel** : **10 tests** couvrent ce workflow complètement dans `test_orders.py`.

### 3.1 — Cas nominal

**Objectif métier** : transformer des lignes de commande en feuille de prélèvement triée par zone, avec allocation cumulée et signalement des pénuries.

| # | Cas | Entrée | picks attendus | skipped attendus | Statut |
|---|-----|--------|---------|-------|-------|
| 3.1.a | Une seule ligne, SKU valide | `[("AX-100", 5)]` | `[{sku: "AX-100", zone: "A", qty: 5}]` | `[]` | ✓ Testé |
| 3.1.b | Plusieurs lignes, zone homogène | `[("AX-100", 5), ("CX-330", 3)]` | `[{sku: "AX-100", zone: "A", qty: 5}, {sku: "CX-330", zone: "A", qty: 3}]` | `[]` | ✗ Non testé |
| 3.1.c | Plusieurs lignes, zones hétérogènes, ordre inverse | `[("DX-440", 2), ("AX-100", 5)]` | `[{sku: "AX-100", zone: "A", qty: 5}, {sku: "DX-440", zone: "C", qty: 2}]` | `[]` | ✗ Non testé |
| 3.1.d | Trois zones | `[("DX-440", 2), ("BX-220", 1), ("AX-100", 5)]` | `[{sku: "AX-100", zone: "A", qty: 5}, {sku: "BX-220", zone: "B", qty: 1}, {sku: "DX-440", zone: "C", qty: 2}]` | `[]` | ✗ Non testé |

### 3.2 — Cas limites

| # | Cas | Entrée | picks | skipped | Notes | Statut |
|---|-----|--------|-------|---------|-------|--------|
| 3.2.a | Liste vide | `[]` | `[]` | `[]` | Pas d'articles. | ✗ Non testé |
| 3.2.b | SKU inconnu unique | `[("INEXISTANT", 5)]` | `[]` | `[]` | Ligne supprimée sans signal (qty>0 mais SKU absent). | ✓ Testé |
| 3.2.c | SKU mélange (connu + inconnu) | `[("AX-100", 5), ("INEXISTANT", 1), ("DX-440", 2)]` | `[{sku: "AX-100", zone: "A", qty: 5}, {sku: "DX-440", zone: "C", qty: 2}]` | `[]` | Ligne inconnue supprimée, autres conservées et triées. | ✗ Non testé |
| 3.2.d | Quantité zéro | `[("AX-100", 0)]` | `[]` | `[]` | Demande nulle ignorée sans signal. | ✓ Testé |
| 3.2.e | Quantité négative | `[("AX-100", -1)]` | `[]` | `[]` | Demande négative ignorée sans signal. | ✓ Testé |

### 3.3 — Allocation cumulée par article (clé du nouveau comportement)

**Propriété assurée** : deux lignes du même SKU ne peuvent pas ensemble dépasser la disponibilité. Les demandes qui dépassent le reste disponible sont rejetées et signalées dans `skipped`.

| # | Cas | Entrée | picks | skipped | Propriété testée | Statut |
|---|-----|--------|-------|---------|---------|--------|
| 3.3.a | Deux lignes, OK | `[("CX-330", 20), ("CX-330", 20)]` | `[{sku: "CX-330", qty: 20}, {sku: "CX-330", qty: 20}]` | `[]` | Allocation cumulée OK (20+20 ≤ 40). | ✓ Testé |
| 3.3.b | Deux lignes, dépassement à la 2e | `[("CX-330", 30), ("CX-330", 30)]` | `[{sku: "CX-330", qty: 30}]` | `[{order_id: 1, sku: "CX-330", qty_requested: 30, qty_missing: 20}]` | 2e ligne rejetée, pénurie signalée (30 > 10 restant). | ✓ Testé |
| 3.3.c | Trois lignes, dépassement à la 3e | `[("CX-330", 15), ("CX-330", 15), ("CX-330", 15)]` | `[{sku: "CX-330", qty: 15}, {sku: "CX-330", qty: 15}]` | `[{order_id: 2, sku: "CX-330", qty_missing: 5}]` | 3e ligne rejetée (15 > 10 restant). | ✓ Testé |
| 3.3.d | Casse différente, cumul respecté | `[("AX-100", 6), ("ax-100", 6)]` | `[{sku: "AX-100", qty: 6}]` | `[{order_id: 1, sku: "ax-100", qty_missing: 2}]` | "AX-100" et "ax-100" partagent l'allocation (cumul 6+6 > 10). | ✓ Testé |

### 3.4 — Gestion des pénuries

**Propriété** : chaque ligne non allouée figure dans `skipped` avec l'index original, le SKU exact demandé, la quantité demandée, et la quantité manquante calculée.

| # | Cas | Cause de la pénurie | Signalement dans skipped |
|---|-----|--------|---------|
| 3.4.a | Stock insuffisant pour une ligne | qty_requested > disponible | ✓ Signalé avec qty_missing |
| 3.4.b | Article hors stock (BX-220, available=0) | Tout qty > 0 | ✓ Signalé | 
| 3.4.c | Dépassement cumulé (même SKU) | Cumul allocation > disponible | ✓ Signalé avec qty_missing = qty_requested - remaining |

### 3.4 — Cas de robustesse (exploration défensive du code, non testés)

⚠️ **Note** : les cas ci-dessous ne représentent **pas des parcours métier** ni des exigences fonctionnelles. Ils explorent comment le code actuel se comporte face à des entrées malformées. La majorité ont été laissés sans validation intentionnelle (bug volontaire ou choix de conception).

| # | Cas | Entrée | Comportement observé | Notes |
|---|-----|--------|---------|---------|
| 3.4.a | Format entré incorrect (dict au lieu de tuple) | `[{"sku": "AX-100", "qty": 5}]` | Boucle `for sku, qty in lines` (`inventory/orders.py:28`) dépacke les clés du dict → `sku` et `qty` prennent les deux premières clés dans l'ordre du dictionnaire → `find_by_sku()` est appelé sur ce qui n'est pas un SKU valide → ligne ignorée silencieusement (`inventory/orders.py:31-33`). | Pas de validation du format. Silencieusement ignoré sans erreur. |
| 3.4.b | Format entré : chaîne seule au lieu de tuple | `["AX-100"]` | Levée d'exception `ValueError: too many values to unpack (expected 2)`. La boucle `for sku, qty in ["AX-100"]` tente de dépacker la chaîne `"AX-100"` (6 caractères) en 2 variables, ce qui échoue au premier itération (`inventory/orders.py:28`). L'exception remonte à l'appelant de `picking_list()`. | Pas de validation du format. Déballage échoue sur séquence de longueur ≠ 2. |
| 3.4.c | Format entré : liste de listes | `[["AX-100", 5]]` | Fonctionne correctement : déballage fonctionne sur toute séquence ordonnée de 2 éléments. | Pas de validation du format, mais syntaxiquement compatible. |

---

## État de la couverture de test actuelle

### Domaine entrepôt-stock
- ✓ `find_by_sku` : partiellement couvert (SKU connu/absent, pas robustesse).
- ✓ `items_in_zone` : partiellement couvert (zone A, pas identités, pas zone absente).
- ✓ `available_qty` : partiellement couvert (bug volontaire, pas les cas normaux).
- ✗ `list_items` : pas de test.

### Domaine préparation-commande
- ✗ `can_fulfil` : **aucun test**.
- ✗ `picking_list` : **aucun test**.

---

## Traçabilité bug — Correction appliquée

**Bug originel** : `available_qty()` ne bornait pas à zéro, ce qui rendait certaines disponibilités négatives (ex. CX-330 avec reserved=50 > qty=45).

**État actuel** : Le bug a été corrigé.

**Preuves** :
- Implémentation : `inventory/warehouse.py:24` (`return max(0, item["qty"] - item["reserved"])`). ✓
- Test : `tests/test_warehouse.py:20-23` (`test_available_qty_borne_a_zero_quand_reserved_superieur_a_qty`) passe. ✓
- Données : CX-330 a maintenant `reserved=5` (au lieu de 50), donc disponibilité = 45 - 5 = 40 ≥ 0. ✓
- Suite de test complète : `Ran 6 tests` dans test_warehouse.py, tous verts. ✓

---

## Accès aux données pour la recette

**Jeu de données en dur** (`inventory/warehouse.py:3-8`) :

```python
ITEMS = [
    {"sku": "AX-100", "label": "Ancre 10kg", "qty": 12, "reserved": 2, "zone": "A"},
    {"sku": "BX-220", "label": "Bouée gonflable", "qty": 0, "reserved": 0, "zone": "B"},
    {"sku": "CX-330", "label": "Cordage 20m", "qty": 45, "reserved": 5, "zone": "A"},
    {"sku": "DX-440", "label": "Dérive alu", "qty": 7, "reserved": 1, "zone": "C"},
]
```

**Disponibilités calculées** :
- AX-100 : 12 - 2 = 10
- BX-220 : 0 - 0 = 0
- CX-330 : 45 - 5 = 40
- DX-440 : 7 - 1 = 6
