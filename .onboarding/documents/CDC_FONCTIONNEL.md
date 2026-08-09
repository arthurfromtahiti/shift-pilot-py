# CDC Fonctionnel — shift-pilot-py

> Confiance : high | Matière : 2 domaines métier, 3 workflows validés, 6 audits

## Résumé

Deux domaines métier coexistent dans ce pilote de logistique d'entrepôt :

1. **Entrepôt-Stock** : référentiel en mémoire de quatre articles (SKU, quantité brute, quantité réservée, zone), avec opérations de consultation et calcul de disponibilité à la vente.
2. **Préparation-Commande** : opérations dérivées pour décider si une commande peut être honorée et générer une liste de prélèvement, avec allocation cross-article pour éviter la surallocation.

La disponibilité à la vente est toujours non négative (bornée à zéro via `max(0, ...)`), et la génération de liste de prélèvement respècte l'allocation cumulée par article en vérifiant la disponibilité et en signalant les pénuries.

---

## Contexte métier

**Scenario** : Dans un scenario pédagogique de logistique d'entrepôt, une entreprise de distribution doit gérer un stock en mémoire et préparer des commandes.  
**Objectif** : gérer un stock d'entrepôt et préparer des commandes.  
**Contrainte** : vérifier avant chaque prélèvement qu'on dispose de la quantité demandée ; traiter les commandes multi-lignes du même SKU sans surallocation.

Le modèle simplifié en mémoire porte quatre articles distincts, chacun une zone, une quantité, et une quantité réservée par des commandes précédentes. **Invariant fonctionnel respecté** : la disponibilité à la vente (stock moins réservé) ne descend jamais en-dessous de zéro. `available_qty()` la borne via `max(0, item["qty"] - item["reserved"])`. Pour les commandes multi-lignes, `picking_list()` alloue séquentiellement par article et signale les pénuries.

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
2. La fonction calcule `item["qty"] - item["reserved"]` et la borne à zéro via `max(0, ...)`.
3. Retourne un entier positif ou zéro.

**Données** :
- Entrée : dict article (supposé porter `qty` et `reserved` en tant que clés entières).
- Sortie : int ≥ 0 (jamais négatif).

**État actuel des quatre articles** :
| SKU | qty | reserved | available |
|-----|-----|----------|-----------|
| AX-100 | 12 | 2 | 10 |
| BX-220 | 0 | 0 | 0 |
| CX-330 | 45 | 5 | 40 |
| DX-440 | 7 | 1 | 6 |

**Règle métier** :
- Disponibilité ≥ 0 toujours. On ne peut pas vendre ce qu'on n'a pas.
- Implémentation : `max(0, item["qty"] - item["reserved"])` garantit le non-negativité structurelle.

**Propriété assurée** :
- La fonction est une pure fonction de ses entrées : même item → même disponibilité, indépendamment du moment de l'appel.

---

### Domaine « Préparation-Commande »

#### Parcours 5 : Vérification de faisabilité d'une commande

**Objectif** : décider si on peut honorer une demande de quantité pour un SKU donné.  
**Réponse** : booléen (`True` = oui, `False` = non).

**Flux** :
1. L'appelant invoque `can_fulfil(sku, requested)` avec un SKU et une quantité entière.
2. Si `requested <= 0` : retourne `False` immédiatement (pas de demande nulle ou négative).
3. `find_by_sku(sku)` récupère l'article.
4. Si article inexistant (`None`) : retourne `False` immédiatement.
5. Sinon : appelle `available_qty(item)` et compare `available_qty(item) >= requested`.
6. Retourne le booléen du résultat.

**Données** :
- Entrée : `sku` (str), `requested` (int).
- Sortie : booléen.

**Comportement observé** :
- `can_fulfil("AX-100", 5)` → `True` (disponible 10, demande 5).
- `can_fulfil("AX-100", 15)` → `False` (disponible 10, demande 15 — rupture).
- `can_fulfil("AX-100", 0)` → `False` (demande nulle refusée).
- `can_fulfil("AX-100", -5)` → `False` (demande négative refusée).
- `can_fulfil("INEXISTANT", 1)` → `False` (article inexistant).

**Validation** :
- La faisabilité repose sur la disponibilité nette (`qty - reserved`), pas sur le stock brut.
- Les demandes nulles et négatives sont rejetées avant vérification d'article (`requested <= 0` → `False`).

---

#### Parcours 6 : Génération de liste de prélèvement avec signalement des pénuries

**Objectif** : transformer des lignes de commande en feuille de prélèvement triée par zone, tout en signalant les pénuries et en respectant l'allocation cumulée par article.  
**Entrée** : liste de tuples `(sku, qty)`.  
**Sortie** : dict `{picks: [...], skipped: [...]}` où `picks` est triée par zone et `skipped` liste les lignes non servies.

**Flux** :
1. L'appelant invoque `picking_list(lines)` avec une liste de tuples `(sku, qty)`.
2. Initialise deux accumulateurs : `picks = []` et `skipped = []`, et un dico `allocated = {}` pour tracer l'allocation par article (clé = SKU canonique).
3. Pour chaque tuple `(sku, qty)` à l'index `idx` :
   a. Si `qty <= 0` : ignore la ligne sans signal (n'ajoute pas à `skipped`).
   b. Récupère l'article via `find_by_sku(sku)`.
   c. Si article inexistant (`None`) : ignore la ligne sans signal.
   d. Sinon, normalise le SKU sur `item["sku"]` (canonical).
   e. Calcule le reste disponible : `remaining = available_qty(item) - allocated[canonical]` (ou 0 si non encore alloué).
   f. Si `qty > remaining` : ajoute l'entrée à `skipped` avec `qty_missing = qty - remaining`.
   g. Sinon : ajoute `qty` à `allocated[canonical]`, puis ajoute l'entrée à `picks`.
4. Trie `picks` par zone en ordre alphabétique croissant.
5. Retourne `{picks: picks_triés, skipped: skipped}`.

**Données** :
- Entrée : liste de tuples informelle `(str sku, int qty)` (pas de classe `OrderLine`).
- Sortie : dict `{picks: [dict], skipped: [dict]}`.
  - Chaque pick : `{sku: str, zone: str, qty: int}`.
  - Chaque skip : `{order_id: int, sku: str, qty_requested: int, qty_missing: int}`.

**Exemple** :
```
Entrée : [("CX-330", 30), ("CX-330", 30), ("AX-100", 5), ("INEXISTANT", 1), ("CX-330", -5)]

Traitement (CX-330 available=40, AX-100 available=10) :
- idx=0, CX-330, qty=30 → remaining=40, qty <= remaining → picks.append, allocated[CX-330]=30
- idx=1, CX-330, qty=30 → remaining=10, qty > remaining → skipped.append(order_id=1, qty_missing=20)
- idx=2, AX-100, qty=5 → remaining=10, qty <= remaining → picks.append, allocated[AX-100]=5
- idx=3, INEXISTANT → item None → ignoré
- idx=4, CX-330, qty=-5 → qty <= 0 → ignoré

Après tri par zone : [{zone: "A", sku: "CX-330", qty: 30}, {zone: "A", sku: "AX-100", qty: 5}]

Retour : {
  "picks": [...],
  "skipped": [{order_id: 1, sku: "CX-330", qty_requested: 30, qty_missing: 20}]
}
```

**Comportement observé** :
- Demandes nulles ou négatives : ignorées silencieusement, n'ajoutent pas à `skipped`.
- SKU inconnu : ignoré silencieusement, n'ajoute pas à `skipped`.
- SKU en casse différente (ex. "AX-100" puis "ax-100") : allocation cumulative respectée (même canonical).
- La sortie `picks` est triée par zone en ordre alphabétique croissant.
- Les pénuries sont signalées explicitement dans `skipped` avec la quantité manquante calculée.

**Propriétés de robustesse** :
- **Surallocation impossible** : l'allocation est cumulée par article ; deux lignes du même SKU ne peuvent pas dépasser sa disponibilité.
- **Isolation de l'allocation** : si une première ligne épuise le stock, les suivantes sont rejetées avec pénurie, pas ignorées.
- **Normalisation du SKU** : les variantes de casse sont traitées comme le même article pour l'allocation.

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

**Invariants métier respectés** :
- ✓ Disponibilité ≥ 0 : garantie par `max(0, item["qty"] - item["reserved"])` dans `available_qty()`.
- ✓ Pas de surallocation : garantie par le suivi cumulé `allocated[canonical]` dans `picking_list()`.
- ✓ Demandes invalides rejetées : `can_fulfil()` rejette `requested <= 0` avant de vérifier l'article.

**Limitations structurelles non défendues par le code** :
- **SKU non unique au schéma** : le code ne vérifie ni ne garantit l'unicité. Si deux articles avaient le même SKU, `find_by_sku()` retournerait le premier seulement (comportement implicite, pas garanti). Toutefois, `picking_list()` normalise sur `item["sku"]` (canonical) pour l'allocation, donc une dupliquée verrait son stock partagé.
- **Pas de validation de format de zone** : actuellement A/B/C, mais aucune contrainte n'existe au niveau du code.
- **Pas de défense contre la mutation de `ITEMS`** : `list_items()` retourne une référence directe à `ITEMS`, pas une copie défensive. Un appelant non discipliné pourrait muter les dicts, affectant l'état interne. Le code n'a aucun verrou ni mécanisme de protection. Risque documenté dans les audits, non garanti par le contrat de l'API.
- **Pas de validation de type de quantité** : les champs `qty`, `reserved`, et demandes acceptent implicitement tout ce qui peut être comparé numériquement. Aucun contrôle de type explicite.

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

## Propriétés opérationnelles garanties

### Disponibilité positive
- `available_qty()` retourne toujours ≥ 0 via `max(0, ...)`.
- Aucun article ne peut remporter une disponibilité négative.

### Allocation sans surallocation
- `picking_list()` suit l'allocation cumulée par article.
- Deux lignes du même SKU ne peuvent pas ensemble dépasser la disponibilité.
- Les pénuries sont signalées dans `skipped` avec la quantité manquante.

### Demandes invalides
- `can_fulfil()` rejette les demandes nulles ou négatives avant vérification d'article.
- `picking_list()` ignore les demandes nulles ou négatives sans signal.

---

## Preuves et documentation

- **Workflows** : `WORKFLOW_CONSULTATION_STOCK.md`, `WORKFLOW_FAISABILITE_COMMANDE.md`, `WORKFLOW_PRELEVEMENT_COMMANDE.md` (lus en intégralité).
- **Code source courant** :
  - `inventory/warehouse.py` (29 lignes) : `list_items()`, `find_by_sku()`, `items_in_zone()`, `available_qty()` avec `max(0, ...)`.
  - `inventory/orders.py` (47 lignes) : `can_fulfil()` avec validation `requested <= 0`, `picking_list()` avec allocation cumulée et signalement des pénuries.
- **Tests courants** :
  - `tests/test_warehouse.py` (6 tests, couvre partiellement warehouse).
  - `tests/test_orders.py` (10 tests, couvre picking_list explicitement incluant multi-lignes, casse, surallocation ; can_fulfil n'est ni testé directement ni indirectement).
- **Audits réconciliés** : fonctionnel, données, architecture, testing, sécurité, code hotspots (tous alignés avec le code courant, relecture approuvée).
