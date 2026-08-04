# CAHIER_RECETTE — shift-pilot-py

> Confiance : high

## Objet

Ce cahier de recette énumère les cas de test **dérivés directement des workflows métier** documentés en étape 2. Chaque cas est tracé à un workflow, à une fonction code, et à un objectif métier. Le but est de guider la création d'une suite de test complète couvrant tous les domaines.

**État actuel** : 3 tests existent dans `tests/test_warehouse.py` (2 verts, 1 rouge intentionnel). Tous les cas du domaine `préparation-commande` sont **non testés**.

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
| 1.2.b | SKU connu (CX-330, le bugué) | `find_by_sku("CX-330")` | Retourne le dict avec `qty=45`, `reserved=50`. | ✗ Non testé |
| 1.2.c | SKU absent | `find_by_sku("INEXISTANT")` | Retourne `None`, pas d'exception. | ✓ Vert (`test_find_by_sku`) |
| 1.2.d | SKU vide | `find_by_sku("")` | Retourne `None` (aucun article n'a SKU vide). | ✗ Non testé |
| 1.2.e | SKU nul (type incorrect) | `find_by_sku(None)` | Comportement non défini : probablement `False implicitement` → retourne `None`. | ✗ Non testé (robustesse) |
| 1.2.f | SKU type incorrect (int) | `find_by_sku(123)` | Comportement non défini : `123 == "AX-100"` est faux → retourne `None`. | ✗ Non testé (robustesse) |
| 1.2.g | Sensibilité à la casse | `find_by_sku("ax-100")` (minuscules) | Retourne `None` (pas de SKU en minuscules). | ✗ Non testé |

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

### 1.4 — Calcul de disponibilité à la vente (porteur du bug volontaire)

**Objectif métier** : connaître la quantité réellement vendable (stock brut - réservé).

**Fonction** : `available_qty(item)`

**Règle métier attendue** : disponibilité ≥ 0 toujours.  
**Règle implémentée** : disponibilité = qty - reserved (pas de borne).

**Cas de test** :

| # | Cas | Entrée | Attente (métier) | Réalité (code) | Statut |
|---|-----|--------|------------------|---|--------|
| 1.4.a | Article normal (AX-100, qty=12, reserved=2) | `available_qty(find_by_sku("AX-100"))` | Retourne 10 | Retourne 10 ✓ | ✗ Non testé |
| 1.4.b | Article en rupture totale (BX-220, qty=0, reserved=0) | `available_qty(find_by_sku("BX-220"))` | Retourne 0 | Retourne 0 ✓ | ✗ Non testé |
| 1.4.c | Article bugué (CX-330, qty=45, reserved=50) | `available_qty(find_by_sku("CX-330"))` | **Devrait retourner 0** (rupture) | **Retourne -5** ❌ | ❌ **Rouge intentionnel** (`test_available_qty_never_negative`) |
| 1.4.d | Article avec petite marge (DX-440, qty=7, reserved=1) | `available_qty(find_by_sku("DX-440"))` | Retourne 6 | Retourne 6 ✓ | ✗ Non testé |
| 1.4.e | Entrée `None` (robustesse) | `available_qty(None)` | Pas d'attente définie — entrée invalide | Lève `TypeError: 'NoneType' object is not subscriptable` sur accès `item["qty"]` | ✗ Non testé (robustesse) |
| 1.4.f | Dict malformé (clé `qty` manquante) | `available_qty({"sku": "XX", "reserved": 0})` | Pas d'attente définie — schéma invalide | Lève `KeyError: 'qty'` lors du calcul | ✗ Non testé (robustesse) |

**Résumé du bug** :
- Test rouge existant encode l'invariant attendu (`disponible >= 0`).
- Le bug est volontaire, documenté, et pédagogique.

---

## Workflow 2 : Vérification de faisabilité de commande

**Référence** : `WORKFLOW_FAISABILITE_COMMANDE.md`  
**Domaine** : `preparation-commande`  
**Fonction testée** : `can_fulfil(sku, requested)`

**État actuel** : **Zéro test** pour ce workflow.

### 2.1 — Vérification nominale

**Objectif métier** : avant de lancer un prélèvement, vérifier qu'on dispose de la quantité demandée.

| # | Cas | SKU | Quantité | Disponibilité réelle | Attente | Notes |
|---|-----|-----|----------|----------------------|---------|-------|
| 2.1.a | Nominal : stock suffisant | AX-100 | 5 | 10 | `True` | Commande possible. |
| 2.1.b | Nominal : stock exact | AX-100 | 10 | 10 | `True` | Limite atteinte. |
| 2.1.c | Dégradé : stock insuffisant | AX-100 | 15 | 10 | `False` | Rupture. |
| 2.1.d | Nominal : quantité zéro | AX-100 | 0 | 10 | `True` ou `False` ? | **Question ouverte** : est-ce une demande valide ? Code : `10 >= 0` → `True`. |
| 2.1.e | Dégradé : quantité négative | AX-100 | -1 | 10 | `False` | **Entrée invalide** : code : `10 >= -1` → `True` ❌ (mauvais). Pas défendu. |

### 2.2 — SKU inexistant

| # | Cas | SKU | Quantité | Attente | Notes |
|---|-----|-----|----------|---------|-------|
| 2.2.a | SKU absent | INEXISTANT | 5 | `False` | Article n'existe pas, donc rupture. |
| 2.2.b | SKU vide | "" | 5 | `False` | Idem. |
| 2.2.c | SKU nul (robustesse) | None | 5 | Pas d'attente définie | Code : `find_by_sku(None)` retourne `None`, `can_fulfil()` teste `if item is None` et retourne `False` (`inventory/orders.py:8-9`). Entrée invalide, comportement sûr. |

### 2.3 — Héritage du bug (disponibilité négative)

| # | Cas | SKU | Quantité | Disponibilité | Attente métier | Réalité code | Problème |
|---|-----|-----|----------|---|---|---|---|
| 2.3.a | Article bugué, demande valide | CX-330 | 0 | -5 | `False` (rupture) | `-5 >= 0` → `False` ✓ | Aucun (correct par accident). |
| 2.3.b | Article bugué, demande invalide | CX-330 | -6 | -5 | `False` (refus ou rupture) | `-5 >= -6` → `True` ❌ | **Incorrect** : accepte une demande invalide. |

### 2.4 — Cas de robustesse (non testés)

| # | Cas | Entrée | Comportement observé | Notes |
|---|-----|--------|---------|---------|
| 2.4.a | Type SKU incorrect | `can_fulfil(123, 5)` | Retourne `False` (SKU ne correspond à aucun article) | Pas de validation de type. |
| 2.4.b | Type quantité incorrect | `can_fulfil("AX-100", "5")` | Lève `TypeError` lors de la comparaison `"5" <= 10` (str vs int) | Pas de validation de type. |

---

## Workflow 3 : Génération de liste de prélèvement

**Référence** : `WORKFLOW_PRELEVEMENT_COMMANDE.md`  
**Domaine** : `preparation-commande`  
**Fonction testée** : `picking_list(lines)`

**État actuel** : **Zéro test** pour ce workflow.

### 3.1 — Cas nominal

**Objectif métier** : transformer des lignes de commande en feuille de prélèvement triée par zone d'entrepôt.

| # | Cas | Entrée | Attente | Notes |
|---|-----|--------|---------|-------|
| 3.1.a | Une seule ligne, SKU valide | `[("AX-100", 5)]` | `[{sku: "AX-100", zone: "A", qty: 5}]` | Liste à 1 entrée, non triée (1 seul élément). |
| 3.1.b | Plusieurs lignes, zone homogène | `[("AX-100", 5), ("CX-330", 3)]` | `[{sku: "AX-100", zone: "A", qty: 5}, {sku: "CX-330", zone: "A", qty: 3}]` | Deux articles de zone A, déjà triés. |
| 3.1.c | Plusieurs lignes, zones hétérogènes, ordre inverse | `[("DX-440", 2), ("AX-100", 5)]` | `[{sku: "AX-100", zone: "A", qty: 5}, {sku: "DX-440", zone: "C", qty: 2}]` | Après tri : A avant C (lexicographique). |
| 3.1.d | Trois zones | `[("DX-440", 2), ("BX-220", 1), ("AX-100", 5)]` | `[{sku: "AX-100", zone: "A", qty: 5}, {sku: "BX-220", zone: "B", qty: 1}, {sku: "DX-440", zone: "C", qty: 2}]` | Tri : A, B, C. |

### 3.2 — Cas limites

| # | Cas | Entrée | Attente | Notes |
|---|-----|--------|---------|-------|
| 3.2.a | Liste vide | `[]` | `[]` | Pas d'articles à prélever. |
| 3.2.b | SKU inconnu unique | `[("INEXISTANT", 5)]` | `[]` | Ligne supprimée silencieusement. **Risque** : préparateur reçoit liste vide sans signal. |
| 3.2.c | SKU mélange (connu + inconnu) | `[("AX-100", 5), ("INEXISTANT", 1), ("DX-440", 2)]` | `[{sku: "AX-100", zone: "A", qty: 5}, {sku: "DX-440", zone: "C", qty: 2}]` | Ligne inconnue supprimée, autres conservées et triées. **Risque** : silences trompeurs. |
| 3.2.d | Quantité zéro | `[("AX-100", 0)]` | `[{sku: "AX-100", zone: "A", qty: 0}]` | Pas de validation : inclut la quantité, même si zéro. |
| 3.2.e | Quantité négative | `[("AX-100", -1)]` | `[{sku: "AX-100", zone: "A", qty: -1}]` | Pas de validation : inclut la quantité, même si négative. |

### 3.3 — Interaction avec le bug (disponibilité négative)

| # | Cas | Entrée | Disponibilité réelle | Attente métier | Réalité code | Problème |
|---|-----|--------|---|---|---|---|
| 3.3.a | Article bugué, sans `can_fulfil` préalable | `[("CX-330", 10)]` | -5 | Devrait refuser ou signaler | `{sku: "CX-330", zone: "A", qty: 10}` | ❌ **Grave** : prélèvement sur rupture, silencieux. |
| 3.3.b | Article bugué, avec `can_fulfil` validant | `can_fulfil("CX-330", 0)` retourne `False`, donc pas d'appel à `picking_list` | -5 | Aucune liste générée | N/A | L'orchestrateur doit enchaîner les deux (pas implémenté). |

### 3.4 — Cas de robustesse (exploration défensive du code, non testés)

⚠️ **Note** : les cas ci-dessous ne représentent **pas des parcours métier** ni des exigences fonctionnelles. Ils explorent comment le code actuel se comporte face à des entrées malformées. La majorité ont été laissés sans validation intentionnelle (bug volontaire ou choix de conception).

| # | Cas | Entrée | Comportement observé | Notes |
|---|-----|--------|---------|---------|
| 3.4.a | Format entré incorrect (dict au lieu de tuple) | `[{"sku": "AX-100", "qty": 5}]` | Boucle `for sku, qty in lines` (`inventory/orders.py:16`) dépacke les clés du dict → `sku="qty"`, `qty="sku"` (ordre des clés) → `find_by_sku("qty")` retourne `None` → ligne ignorée (`inventory/orders.py:18-19`). | Pas de validation du format. Silencieusement ignoré sans erreur. |
| 3.4.b | Format entré : chaîne seule au lieu de tuple | `["AX-100"]` | Levée d'exception `ValueError: too many values to unpack (expected 2)`. La boucle `for sku, qty in ["AX-100"]` tente de dépacker la chaîne `"AX-100"` (6 caractères) en 2 variables, ce qui échoue (`inventory/orders.py:16`). | Pas de validation du format. Dépaquage échoue sur chaîne de longueur ≠ 2. |
| 3.4.c | Format entré : liste de listes | `[["AX-100", 5]]` | Fonctionne correctement : déballage fonctionne sur toute séquence ordonnée de 2 éléments. | Pas de validation du format, mais par chance syntaxiquement compatible. |

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

## Traçabilité bug volontaire

**Bug** : `available_qty()` ne borne pas à zéro.

**Traces** :
- Implémentation : `inventory/warehouse.py:29` (`return item["qty"] - item["reserved"]`).
- Documentation : docstring lignes 23-28.
- Test rouge : `tests/test_warehouse.py:14-18` (`test_available_qty_never_negative`).
- Cahier de recette : cas 1.4.c, 2.3.a, 2.3.b, 3.3.a.
- README : ligne 13-14.
- Carte des domaines : mentionné.

**Correction attendue** : l'implémentation qui corrige le bug fera passer le test rouge au vert.

---

## Accès aux données pour la recette

**Jeu de données en dur** (`inventory/warehouse.py:3-8`) :

```python
ITEMS = [
    {"sku": "AX-100", "label": "Ancre 10kg", "qty": 12, "reserved": 2, "zone": "A"},
    {"sku": "BX-220", "label": "Bouée gonflable", "qty": 0, "reserved": 0, "zone": "B"},
    {"sku": "CX-330", "label": "Cordage 20m", "qty": 45, "reserved": 50, "zone": "A"},
    {"sku": "DX-440", "label": "Dérive alu", "qty": 7, "reserved": 1, "zone": "C"},
]
```

**Disponibilités calculées** :
- AX-100 : 12 - 2 = 10
- BX-220 : 0 - 0 = 0
- CX-330 : 45 - 50 = -5 (bug)
- DX-440 : 7 - 1 = 6
