# Corrections appliquées — CAHIER_RECETTE.md

**Date** : 2026-08-09  
**Contexte** : Relecture Paperclip (issue SHIAAAAAAAAAAAAAAAAAAAAAAAA-554) — 4 contradictions bloquantes identifiées et corrigées.

## Synthèse des changements

### 1. Couverture annoncée à la fois complète et inexistante (ligne 9)

**Avant** : "La couverture fonctionnelle est **complète** pour les workflows métier principaux."

**Après** : "La couverture fonctionnelle est **partielle** : le domaine entrepôt-stock a des tests sur `find_by_sku()` et `items_in_zone()`, mais le domaine préparation-commande manque de tests directs sur `can_fulfil()` (voir section 2, État actuel)."

**Justification** : Le document lui-même énumère à la section 2 que `can_fulfil()` n'a **aucun test** (`✗ Aucun test`). La première affirmation était factuellement inexacte.

---

### 2. Ligne parasite `3.3.b` en section 3.4 (ligne 200)

**Avant** : Une ligne de tableau intitulée `3.3.b` parlait d'orchestrateur et d'articles bugués.

```
| 3.3.b | Article bugué, avec `can_fulfil` validant | ... | -5 | Aucune liste générée | N/A | L'orchestrateur doit enchaîner les deux (pas implémenté). |
```

**Après** : Ligne supprimée.

**Justification** :
- Cette ligne était en conflit de numérotation avec le cas 3.3.b existant (allocation cumulée, 2 lignes OK).
- Elle décrivait un scénario d'orchestration inexistant dans le code.
- La relecture l'a flaggée comme "ligne parasite".

---

### 3. Cas 3.4.b — Traçabilité du comportement incorrect (ligne 209)

**Avant** : "Boucle `for sku, qty in lines` ... dépacke la chaîne `"AX-100"` ... → `find_by_sku("qty")` retourne `None` → ligne **ignorée silencieusement** sans erreur."

**Après** : "Levée d'exception `ValueError: too many values to unpack (expected 2)`. La boucle `for sku, qty in ["AX-100"]` tente de dépacker la chaîne `"AX-100"` (6 caractères) en 2 variables, ce qui échoue **au premier itération** (`inventory/orders.py:28`). L'exception **remonte à l'appelant de** `picking_list()`."

**Justification** :
- Code réel (`inventory/orders.py:28`) : `for idx, (sku, qty) in enumerate(lines):`
- Avec `lines = ["AX-100"]`, l'itération tente de dépacker la chaîne `"AX-100"` en 2 variables → `ValueError`.
- **Pas de déballage en caractères**, pas d'appel à `find_by_sku()`, pas d'ignorance silencieuse.
- Lignes de code référencées mises à jour de 16 → 28, 18-19 → 31-33.

---

### 4. Jeu de données erroné pour CX-330 (lignes 249, 257)

**Avant** :
```python
{"sku": "CX-330", "label": "Cordage 20m", "qty": 45, "reserved": 50, "zone": "A"},
```
Disponibilité calculée : `45 - 50 = -5 (bug)`

**Après** :
```python
{"sku": "CX-330", "label": "Cordage 20m", "qty": 45, "reserved": 5, "zone": "A"},
```
Disponibilité calculée : `45 - 5 = 40`

**Justification** :
- Le code réel (`inventory/warehouse.py:6`) a `"reserved": 5`, pas 50.
- Le document avait introduit un jeu de données fictif incompatible.
- Tous les cas de recette utilisant CX-330 (1.4.c, 3.3.a/b/c) sont maintenant cohérents.

---

### 5. Section "Traçabilité bug volontaire" — État obsolète (lignes 229-237)

**Avant** :
```markdown
**Bug** : `available_qty()` ne borne pas à zéro.
**Traces** : ... Test rouge : `tests/test_warehouse.py:14-18` ...
**Correction attendue** : l'implémentation qui corrige le bug fera passer le test rouge au vert.
```

**Après** :
```markdown
**Bug originel** : `available_qty()` ne bornait pas à zéro, ce qui rendait certaines disponibilités négatives...
**État actuel** : Le bug a été corrigé.

**Preuves** :
- Implémentation : `inventory/warehouse.py:24` (`return max(0, ...)`). ✓
- Test : `tests/test_warehouse.py:20-23` (`test_available_qty_borne_a_zero_quand_reserved_superieur_a_qty`) passe. ✓
- Données : CX-330 a maintenant `reserved=5` (au lieu de 50), donc disponibilité = 45 - 5 = 40 ≥ 0. ✓
- Suite de test complète : `Ran 6 tests` dans test_warehouse.py, tous verts. ✓
```

**Justification** :
- Le test 3 n'est pas "rouge" : `test_available_qty_cx330` (ligne 14-18) demande 40 unités pour CX-330 et le code retourne effectivement 40.
- Le test 4 (`test_available_qty_borne_a_zero_quand_reserved_superieur_a_qty`, ligne 20-23) **passe** ✓ et prouve que la borne fonctionne.
- Le bug a effectivement été **corrigé** (data + code + tests).

---

## Vérification croisée

Tous les changements ont été vérifiés contre :
- ✓ Code réel (`inventory/warehouse.py`, `inventory/orders.py`)
- ✓ Tests réels (`tests/test_warehouse.py`, `tests/test_orders.py`)
- ✓ Cas de recette internes (cohérence CX-330 partout)
- ✓ Relecture Paperclip (tous les points d'alerte adressés)

Le document **CAHIER_RECETTE.md** est maintenant **factuellement exact** et **traçable au code**.
