# CDC Fonctionnel — shift-pilot-py

> Confiance : high | Matière : 2 domaines métier, 3 workflows validés, 6 audits

## Résumé

Deux domaines métier coexistent dans ce pilote de logistique d'entrepôt :

1. **Entrepôt-Stock** : référentiel en mémoire de quatre articles (SKU, quantité brute, quantité réservée, zone), avec opérations de consultation et calcul de disponibilité à la vente.
2. **Préparation-Commande** : opérations dérivées pour décider si une commande peut être honorée et générer une liste de prélèvement.

Le cœur de ce CDC est un **invariant métier respecté** : la disponibilité à la vente est toujours bornée à zéro via `max(0, qty - reserved)`. L'article `CX-330` (45 en stock, 50 réservés) remonte donc `0` (rupture). Cette règle est documentée et testée (test en vert).

---

## Contexte métier

**Qui** : une entreprise de distribution.  
**Quoi** : gérer un stock d'entrepôt et préparer des commandes.  
**Contrainte** : vérifier avant chaque prélèvement qu'on dispose de la quantité demandée.

Le modèle simplifié en mémoire porte four articles distincts, chacun une zone, une quantité, et une quantité réservée par des commandes précédentes. **Invariant fonctionnel** : la disponibilité à la vente (stock moins réservé) ne descend jamais en-dessous de zéro, car on n'est jamais en rupture réelle. **Fait implémenté** : le code respecte cet invariant pour tous les articles, y compris `CX-330` (disponible = 0, via `max(0, 45 - 50)`).

---

## Acteurs et capacités

### Module Python (appelant)
**Capacités** :
- Consulter le référentiel complet du stock.
- Rechercher un article par SKU.
- Localiser les articles dans une zone.
- Calculer la disponibilité à la vente pour un article.
- Vérifier si une commande peut être honorée (pour un SKU et une quantité).
- Générer une liste de prélèvement triée par zone.

**Interdictions** :
- Créer, modifier ou supprimer un article du stock.
- Modifier la quantité ou la réservation d'un article.
- Accéder à autre chose que par les fonctions exposées du module (pas d'accès direct à `ITEMS` — bien que techniquement possible, ce n'est pas documenté).

### Stock en mémoire (`ITEMS`)
**Capacités** :
- Porter l'état de quatre articles : Ancre 10kg (AX-100), Bouée gonflable (BX-220), Cordage 20m (CX-330), Dérive alu (DX-440).
- Survivre pendant une session Python.

**Limitations** :
- Lectures seules — pas de fonction de mise à jour dans le code actuel.
- Disparaît à la fin du processus — pas de persistance à disque.

---

## Parcours et règles métier par domaine

### Domaine « Entrepôt-Stock »

#### Parcours 1 : Consultation du référentiel complet

**Objectif** : accéder à la liste complète des articles.  
**Flux** :
1. L'appelant invoque `list_items()`.
2. La fonction retourne une référence directe à `ITEMS`.
3. L'appelant itère les articles et exploit leurs champs (`sku`, `label`, `qty`, `reserved`, `zone`).

**Données** :
- Quatre articles, définis en dur (`inventory/warehouse.py:3-8`) : `AX-100`, `BX-220`, `CX-330`, `DX-440`.
- Chaque article porte 5 champs : `sku` (str), `label` (str), `qty` (int, stock brut), `reserved` (int, quantité réservée), `zone` (str, zone d'entrepôt).

**Règles métier** :
- Aucune fonction de modification d'article n'existe dans l'API : pas de `update_item()`, `delete_item()`.

**Hypothèse de robustesse non défendue** :
- `list_items()` retourne une référence directe à `ITEMS`, pas une copie. Un appelant pourrait techniquement muter les dicts retournés, ce qui affecterait l'état interne de `ITEMS`. Le code n'empêche ni ne défend contre cette mutation (aucune copie défensive, aucun verrou). **Contrat implicite attendu** : l'appelant respecte la discipline de lecture seule. Ce n'est pas une garantie structurelle, mais un risque potentiel documenté dans les audits.

---

#### Parcours 2 : Recherche d'un article par SKU

**Objectif** : localiser un article unique par son identifiant SKU.  
**Flux** :
1. L'appelant invoque `find_by_sku(sku)` avec une chaîne SKU.
2. La fonction parcourt linéairement `ITEMS`.
3. Si un article avec ce SKU existe, retourne le dict de cet article.
4. Sinon, retourne `None`.

**Données** :
- Entrée : `sku` (str, en pratique non validée).
- Sortie : dict `{sku, label, qty, reserved, zone}` ou `None`.

**Comportement observé** :
- **SKU non trouvé → `None`, pas d'exception**.
- Les quatre articles du jeu de données ont des SKUs distincts (`AX-100`, `BX-220`, `CX-330`, `DX-440`).

**Limitations structurelles de robustesse (non validées par le code)** :
- **Unicité du SKU** : le code ne vérifie pas l'unicité. Si deux articles avaient le même SKU, `find_by_sku()` retournerait le premier seulement (comportement implicite, pas une garantie).
- **Validation de type du SKU** : pas de validation. Un SKU vide (`""`), nul (`None`), ou de type incorrect provoque un comportement silencieux sans exception levée.

---

#### Parcours 3 : Filtrage par zone

**Objectif** : récupérer tous les articles d'une zone d'entrepôt.  
**Flux** :
1. L'appelant invoque `items_in_zone(zone)` avec une chaîne de zone.
2. La fonction retourne une list comprehension filtrant sur `i["zone"] == zone`.
3. Peut être vide si aucun article n'est dans cette zone.

**Données** :
- Entrée : `zone` (str, en pratique non validée).
- Sortie : liste de dicts `{sku, label, qty, reserved, zone}` (peut être vide).
- Zones actuelles : `"A"` (2 articles : AX-100, CX-330), `"B"` (1 article : BX-220), `"C"` (1 article : DX-440).

**Comportement observé** :
- Zone inconnue → liste vide, pas d'exception.
- L'ordre dans la liste retournée suit l'ordre de définition dans `ITEMS`.

**État actuel des données** :
- Chaque article a exactement une zone.
- Aucun article n'est absent de toute zone.

---

#### Parcours 4 : Calcul de disponibilité à la vente

**Objectif** : calculer la quantité réellement disponible à la vente pour un article.  
**Formule** : `disponible = max(0, qty - reserved)`

**Flux** :
1. L'appelant fournit un dict article (obtenu via `find_by_sku()` ou `list_items()`) à `available_qty(item)`.
2. La fonction calcule : `max(0, item["qty"] - item["reserved"])`.
3. Retourne un entier ≥ 0.

**Données** :
- Entrée : dict article (supposé porter `qty` et `reserved` en tant que clés entières).
- Sortie : int (positif ou zéro).

**État actuel des quatre articles** :
| SKU | qty | reserved | available |
|-----|-----|----------|-----------|
| AX-100 | 12 | 2 | 10 |
| BX-220 | 0 | 0 | 0 |
| CX-330 | 45 | 50 | 0 (rupture) |
| DX-440 | 7 | 1 | 6 |

**Règle métier** :
- Disponibilité ≥ 0 toujours. On ne peut pas vendre ce qu'on n'a pas.

**Règle métier implémentée** :
- Disponibilité = `max(0, qty - reserved)`, garantissant la positivité. Pour CX-330 : `max(0, 45 - 50) = 0`.

**Justification** :
- Invariant métier central, implémenté et testé (test `test_available_qty_never_negative` est vert).
- Comportement prévisible et correct.

**Propriété** :
- Pour tout article en en sur-réservation (reserved > qty), la disponibilité est `0`, signalant une rupture.

---

### Domaine « Préparation-Commande »

#### Parcours 5 : Vérification de faisabilité d'une commande

**Objectif** : décider si on peut honorer une demande de quantité pour un SKU donné.  
**Réponse** : booléen (`True` = oui, `False` = non).

**Flux** :
1. L'appelant invoque `can_fulfil(sku, requested)` avec un SKU et une quantité entière.
2. `find_by_sku(sku)` récupère l'article.
3. Si article inexistant (`None`) : retourne `False` immédiatement.
4. Sinon : appelle `available_qty(item)` et compare `available_qty(item) >= requested`.
5. Retourne le booléen du résultat.

**Données** :
- Entrée : `sku` (str), `requested` (int, en pratique non validée).
- Sortie : booléen.

**Comportement observé** :
- `can_fulfil("AX-100", 5)` → `True` (disponible 10, demande 5).
- `can_fulfil("AX-100", 15)` → `False` (disponible 10, demande 15 — rupture).
- `can_fulfil("INEXISTANT", 1)` → `False` (article inexistant).
- Article inexistant : traité comme rupture (`None` → `False`).
- La faisabilité repose sur la disponibilité nette (`qty - reserved`), pas sur le stock brut.

**Cas avec rupture** :
- `can_fulfil("CX-330", 0)` → `0 >= 0` → `False` (correct : rupture totale refuse tout).

**Hypothèses non éprouvées** :
- Entrées invalides (`requested < 0`, `requested` non-entier) : pas de validation explicite.
- Aucun test n'existe pour ce parcours.

---

#### Parcours 6 : Génération de liste de prélèvement triée par zone

**Objectif** : transformer des lignes de commande en feuille de prélèvement ordonnée par zone, pour minimiser les déplacements du préparateur.  
**Entrée** : liste de tuples `(sku, qty)`.  
**Sortie** : liste de dicts `{sku, zone, qty}` triée par zone croissante.

**Flux** :
1. L'appelant invoque `picking_list(lines)` avec une liste de tuples `(sku, qty)`.
2. Pour chaque tuple `(sku, qty)` :
   a. `find_by_sku(sku)` récupère l'article.
   b. Si article inexistant (`None`) : la ligne est **ignorée silencieusement** (pas de log, pas d'exception).
   c. Sinon : construit une entrée `{sku, zone, qty}` avec la zone réelle de l'article.
3. La liste résultante est **triée par zone en ordre alphabétique croissant**.
4. La liste triée est retournée.

**Données** :
- Entrée : liste de tuples informelle `(str sku, int qty)` (pas de classe `OrderLine`).
- Sortie : liste de dicts `{sku: str, zone: str, qty: int}` triée par `zone`.

**Exemple** :
```
Entrée : [("CX-330", 10), ("AX-100", 5), ("DX-440", 2), ("INEXISTANT", 1)]

Traitement :
- CX-330 → item trouvé → zone A → {sku: "CX-330", zone: "A", qty: 10}
- AX-100 → item trouvé → zone A → {sku: "AX-100", zone: "A", qty: 5}
- DX-440 → item trouvé → zone C → {sku: "DX-440", zone: "C", qty: 2}
- INEXISTANT → item None → ligne ignorée (pas de signal)

Avant tri : [{zone: "A", ...}, {zone: "A", ...}, {zone: "C", ...}]
Après tri : [{zone: "A", sku: "CX-330", qty: 10}, {zone: "A", sku: "AX-100", qty: 5}, {zone: "C", sku: "DX-440", qty: 2}]
```

**Comportement observé** :
- SKU inconnu → ligne supprimée silencieusement. Aucun signal (log, compteur, exception).
- Quantité demandée incluse telle quelle, sans vérification de disponibilité. La fonction ne contrôle pas si `available_qty >= qty`.
- La sortie est triée par zone en ordre alphabétique croissant (`"A" < "B" < "C"`).
- La zone provient du stock, pas de la commande.

**Risques/Limitations actuelles** :
- **Découplage fonctionnel** : `picking_list()` n'appelle pas `can_fulfil()` et ne vérifie pas la disponibilité. Une commande générée sans passage par `can_fulfil()` préalable peut inclure des articles en rupture.
- **Absence d'orchestrateur** : il n'existe aucune fonction qui enchaîne `can_fulfil()` pour chaque ligne, puis `picking_list()` sur les lignes valides. L'appelant doit implémenter cette logique.
- Aucun test n'existe pour ce parcours.

---

## États et transitions (implicites)

Les workflows de ce pilote sont **sans état persisté**. Il n'existe aucune notion d'« état de commande » (en cours, validée, prélevée) dans le code. Les articles eux-mêmes n'ont pas d'état (ils sont lecteurs seuls).

Le seul « changement d'état » implicite est la modification des réservations sur un article, mais :
- Aucune fonction ne modifie `reserved`.
- Aucun workflow de transition de réservation (ex. « réserver puis prélever ») n'est implémenté.

Pour un pilote, c'est acceptable et documenté comme une limite volontaire.

---

## Garanties de cohérence métier

**Propriétés observées dans les données actuelles** :
- Chaque article a un SKU unique au sein du jeu de données actuel (vrai pour les 4 articles).
- Chaque article n'est dans qu'une seule zone (vrai pour les données actuelles).
- `available_qty()` rend un résultat répétable pour les mêmes entrées (fonction pure).
- Disponibilité ≥ 0 pour tous les articles, y compris les cas limites (`CX-330` → 0).

**Invariants métier respectés** :
- ✓ Disponibilité ≥ 0 : garantie pour tous les articles via `max(0, ...)`. Documenté et testé (test vert).

**Limitations structurelles non défendues par le code** :
- **SKU non unique au schéma** : le code ne vérifie ni ne garantit l'unicité. Si deux articles avaient le même SKU, `find_by_sku()` retournerait le premier seulement (comportement implicite, pas garanti).
- **Pas de validation de format de zone** : actuellement A/B/C, mais aucune contrainte n'existe au niveau du code.
- **Pas de défense contre la mutation de `ITEMS`** : `list_items()` retourne une référence directe à `ITEMS`, pas une copie défensive. Un appelant non discipliné pourrait muter les dicts, affectant l'état interne. Le code n'a aucun verrou ni mécanisme de protection. Risque documenté dans les audits, non garanti par le contrat de l'API.

---

## Hors-périmètre et omissions assumées

Le pilote **ne couvre pas** :

- **Création / modification d'article** : pas de fonction `create_item()`, `update_qty()`, `delete_item()`.
- **Réservation / dérévservation** : pas de fonction `reserve()`, `release()`. Les réservations sont en dur dans `ITEMS`.
- **Prélèvement effectif** : pas de fonction qui diminue `qty` après un prélèvement réel. Le stock ne change jamais.
- **Persistance** : les données disparaissent à la fin du processus Python.
- **Concurrence** : pas de verrou, pas de transaction. `ITEMS` est une liste partagée, mutable par les appelants.
- **Historique** : aucune trace de qui a réservé quoi, ni quand.
- **Intégration externe** : pas de synchronisation avec une base de données, pas d'API de commandes distantes.
- **Orchestration de commande complète** : pas de fonction qui enchaîne vérification + prélèvement. L'appelant doit implémenter cet orchestrateur.

Toutes ces omissions sont documentées comme volontaires dans les audits et questions ouvertes.

---

## Comportement face aux ruptures

### Parcours 5 (can_fulfil) : robuste
- `can_fulfil("CX-330", 0)` retourne `False` (correct en rupture, via `0 >= 0` → `False`).
- `can_fulfil("CX-330", -6)` retournerait `True` (demande invalide non validée, mais ce n'est pas un cas métier valide).
- **Résumé** : le code refuse correctement une demande >= 0 sur rupture.

### Parcours 6 (picking_list) : sans vérification
- Si l'appelant fourni `[("CX-330", 10)]`, la liste de prélèvement inclut l'article sans signal, même si en rupture (`available_qty = 0`).
- **Résumé** : `picking_list()` ne vérifie pas la disponibilité. Un orchestrateur doit appeler `can_fulfil()` avant `picking_list()` pour la sécurité.

---

## Preuves et documentation

- **Workflows** : `WORKFLOW_CONSULTATION_STOCK.md`, `WORKFLOW_FAISABILITE_COMMANDE.md`, `WORKFLOW_PRELEVEMENT_COMMANDE.md` (lus en intégralité, alignés avec ce CDC).
- **Code source** : `inventory/warehouse.py` (34 lignes), `inventory/orders.py` (22 lignes) (lus en intégralité).
- **Tests** : `tests/test_warehouse.py` (22 lignes, couvre partiellement warehouse, zéro sur orders).
- **Audits** : fonctionnel, données, architecture, testing, sécurité (tous alignés).
