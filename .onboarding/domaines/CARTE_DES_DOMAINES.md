# Carte des domaines — shift-pilot-py

> **Verdict : carte à 2 domaines métier, assumée — RÉCONCILIÉE le 2026-08-09.** Le code a été relu en intégralité (4 fichiers source + 2 fichiers de test, dépôt minuscule) — chaque affirmation ci-dessous est `VÉRIFIÉ_CODE`. Ce dépôt porte objectivement **deux** périmètres qu'un chef de projet nommerait : `entrepot-stock` (cœur) et `preparation-commande` (support). Sous le plancher indicatif de 4, mais c'est un **choix assumé** et non un oubli : gonfler confondrait domaines et fonctions (règle de la compétence — *matière pauvre → moins de domaines en confiance honnête, jamais une carte inventée*). Confiance **par domaine** ci-dessous (les deux en `high`) ; il n'y a pas de confiance « globale » dégradée à signaler, seulement un périmètre volontairement réduit.
>
> **Réconciliation (mode : `.onboarding/` présent).** Carte initiale produite au SHA `d0097aad`. **SHA de tête réconcilié : `511104b96ed8bafce0d5a44bed5a08c0b2550974`** (`main`). La **structure à 2 domaines n'a pas changé** ; ce qui a changé, ce sont les internes, qui ont muri via une série de correctifs (voir « Delta depuis la carte initiale » en fin de document). En conséquence, le récit central de la carte initiale — un « bug volontaire » dans `available_qty` attrapé par un « test rouge volontaire » — **ne décrit plus le code** : ce bug est corrigé et tous les tests passent. Ce document remplace cette narration périmée par l'état réel du code.
>
> **Recentrage post-relecture (conservé) :** le harnais de test `unittest` n'est pas un domaine (pas de capacité produit autonome, pas de donnée métier propre, pas de workflow métier distinct) : il reste traité en section **Hors-domaines — outillage**.

## Nature du projet

`shift-pilot-py` est un **pilote de démonstration** d'une logistique d'entrepôt écrit en **Python 3 pur** (stdlib uniquement, tests `unittest`). Le `README.md` l'énonce : c'est volontairement une stack **non-JavaScript**, distincte des pilotes Node `shift-pilot-back` / `shift-pilot-front`, pour vérifier que l'outillage d'onboarding et de production ne présuppose pas un écosystème JS.

Fonctionnellement, il modélise un **stock d'entrepôt en mémoire** (articles avec SKU, quantité, quantité réservée, zone) et une **préparation de commande** dérivée (disponibilité à la vente, faisabilité, liste de prélèvement triée par zone avec journalisation des lignes non servies). Il n'y a **ni route HTTP, ni base de données, ni persistance** : les données vivent dans une liste Python en dur (`inventory/warehouse.py:3`).

Contrairement à l'état capturé par la carte initiale, le dépôt **ne porte plus de bug volontaire non corrigé** : la série de commits `SHIAAA-*` / `CLA-*` a durci le comportement (bornage à zéro de la disponibilité, insensibilité à la casse des SKU, allocation cumulative dans la liste de prélèvement) et **tous les tests sont verts**. L'objet reste pédagogique/de validation de chaîne, mais il illustre désormais un cycle *test rouge → correctif → vert* **abouti** plutôt qu'un défaut latent.

**Faits de stack `VÉRIFIÉ_CODE`** (à ne pas re-supposer en aval) : Python 3.12 (`inventory/__pycache__/*.cpython-312.pyc`) · tests via `python3 -m unittest discover -s tests -t .` (`README.md:10`) → **16 tests, tous OK** (relancé le 2026-08-09) · **aucun** manifeste de dépendances (`requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile` non localisés malgré inventaire complet du dépôt) → aucune dépendance tierce · packages importables `inventory` (`inventory/__init__.py`, vide) et `tests` (`tests/__init__.py`, vide).

## Domaines

### Gestion du stock d'entrepôt (`entrepot-stock`)
- **Catégorie** : métier
- **Priorité** : cœur
- **Confiance** : high
- **Description** : Référentiel des articles en entrepôt et calculs qui s'y rattachent — recherche par SKU (**insensible à la casse**), filtrage par zone, et **disponibilité réelle à la vente** (stock moins réservé, **bornée à zéro**). C'est le domaine fondateur : il porte la donnée que tout le reste consomme.
- **Entités** : `ITEMS` — collection en mémoire d'articles, chacun `{sku, label, qty, reserved, zone}` (`inventory/warehouse.py:3-8`). Pas d'entité ORM : structure de données Python, non persistée. Invariant désormais respecté dans les données seed : `reserved <= qty` pour chaque article (vérifié par test).
- **Routes / points d'entrée** : aucune route (pas de couche web). Points d'entrée = fonctions du module : `list_items()`, `find_by_sku(sku)` (comparaison `.upper()`, `inventory/warehouse.py:15-19`), `available_qty(item)` (`max(0, qty - reserved)`, `inventory/warehouse.py:22-24`), `items_in_zone(zone)` (`inventory/warehouse.py:27-28`).
- **Indices de rattachement** : module `inventory/warehouse.py` ; symboles `ITEMS`, `available_qty`, `find_by_sku`, `items_in_zone`, `zone`, `reserved`, `qty`, `sku`.
- **Types de workflows attendus** : consultation du stock (par SKU, par zone), calcul de disponibilité vendable. Pas de mutation du stock dans le code actuel (aucune fonction n'écrit dans `ITEMS`).
- **Preuves** : `inventory/warehouse.py`, `tests/test_warehouse.py` (6 tests : recherche par SKU, casse, comptage par zone, disponibilité CX-330, garde `max(0,...)`, invariant `reserved <= qty`), `README.md:13-15`.
- **Dépend de la base** : non. *(Aucun accès base fourni à cette étape ; par ailleurs aucun signal schéma/entité-étendue/code-exécutable de contenu piloté par la base — données en dur, pas de structure arborescente décodée à l'exécution.)*

### Préparation de commande (`preparation-commande`)
- **Catégorie** : métier
- **Priorité** : support
- **Confiance** : high
- **Description** : Opérations dérivées du stock côté exécution logistique — décider si une commande **peut être honorée** pour une quantité demandée (`can_fulfil`, qui **rejette les quantités nulles ou négatives**), et transformer des **lignes de commande** en **liste de prélèvement** triée par zone. La liste de prélèvement gère désormais l'**allocation cumulative par article** (plusieurs lignes du même SKU ne peuvent dépasser la disponibilité totale, la clé d'allocation étant normalisée sur le SKU canonique `item["sku"]` pour couvrir les casses différentes) et **journalise les lignes non servies** pour stock insuffisant (`skipped`, avec `order_id`, `sku`, `qty_requested`, `qty_missing`). Domaine consommateur : il ne détient aucune donnée propre, il s'appuie entièrement sur `entrepot-stock` (`from inventory.warehouse import find_by_sku, available_qty`, `inventory/orders.py:3`). D'où sa priorité `support` plutôt que `cœur`.
- **Entités** : aucune entité propre. Manipule des **lignes de commande** — tuples `(sku, qty)` en entrée (`inventory/orders.py:28`) — et produit un dictionnaire `{"picks": [...], "skipped": [...]}` où `picks` contient des entrées `{sku, zone, qty}` triées par zone et `skipped` des entrées `{order_id, sku, qty_requested, qty_missing}` (`inventory/orders.py:37-46`).
- **Routes / points d'entrée** : aucune route. Fonctions : `can_fulfil(sku, requested)` (`inventory/orders.py:6-12`), `picking_list(lines)` (`inventory/orders.py:15-46`).
- **Indices de rattachement** : module `inventory/orders.py` ; symboles `can_fulfil`, `picking_list`, `lines`, `requested`, `picks`, `skipped`, `allocated`, `qty_missing`, `order_id`.
- **Types de workflows attendus** : contrôle de faisabilité d'une commande, génération d'une feuille de prélèvement ordonnée par zone avec traçabilité des lignes non servies. Les lignes invalides (qty <= 0, SKU inconnu) sont ignorées **sans trace** dans `skipped` ; seul le stock insuffisant y est journalisé.
- **Preuves** : `inventory/orders.py`, `tests/test_orders.py` (10 tests : exclusion/journalisation hors-stock, inclusion en stock, quantités invalides, dépassement multi-lignes, allocation cumulative, cumul insensible à la casse).
- **Dépend de la base** : non.

## Hors-domaines — outillage

### Harnais de test `unittest`
Ce n'est **pas un domaine** au sens de la méthode : pas de capacité produit autonome, pas de donnée métier propre, pas de workflow métier distinct. C'est l'**outillage qualité** du pilote, qui vérifie le comportement des deux domaines. Il est documenté ici plutôt que promu en domaine, pour ne pas gonfler la carte.

- **Ce que c'est** : suite `unittest` de la bibliothèque standard — `TestWarehouse` (`tests/test_warehouse.py:6`) et `TestPickingList` (`tests/test_orders.py:6`), lancées par `python3 -m unittest discover -s tests -t .` (`README.md:10`).
- **Portée** : `inventory/warehouse.py` **et** `inventory/orders.py` sont désormais couverts (le second ne l'était pas au moment de la carte initiale).
- **Fait structurant réconcilié** : le « test rouge volontaire » `test_available_qty_never_negative` décrit par la carte initiale **n'existe plus sous cette forme rouge** ; l'invariant qu'il défendait est maintenant encodé par des tests **verts** (`test_available_qty_borne_a_zero_quand_reserved_superieur_a_qty`, `test_invariant_reserved_ne_depasse_pas_qty_dans_items`, `tests/test_warehouse.py:20-31`), le code métier respectant l'invariant. Le dépôt illustre donc un cycle rouge→vert **abouti**, pas un défaut latent.
- **Vérification exécutable (2026-08-09)** : `python3 -m unittest discover -s tests -t .` → **`Ran 16 tests`, `OK`** (0 échec).
- **CI** : aucune localisée dans le dépôt (pas de `.github/`, `.gitlab-ci.yml`, etc. — inventaire complet effectué).

## Delta depuis la carte initiale (`d0097aad` → `511104b`)

Résumé des écarts entre l'état capturé par la carte du 2026-08-03 et le code courant (traçable par `git log d0097aad..HEAD -- inventory tests`). La **structure des domaines est inchangée** ; seuls les internes ont évolué :

| Élément | Carte initiale (`d0097aad`) | Code courant (`511104b`) | Commits |
|---|---|---|---|
| `available_qty` | bug volontaire — renvoie du négatif si `reserved > qty` | corrigé — `max(0, qty - reserved)` | `f3d4233` (CLA-177) |
| `find_by_sku` | sensible à la casse | **insensible** à la casse (`.upper()`) | `56a38e6` (SHIAAA-452) |
| Données `ITEMS` (CX-330) | `reserved=50` (> qty, article indisponible) | `reserved=5` (disponible, `available=40`) | `742b458` (SHIAAA-231) |
| `can_fulfil` | pas de garde sur la quantité | rejette `requested <= 0` | `b2e0108` (SHIAAA-291) |
| `picking_list` | produit de simples entrées `{sku, zone, qty}` | retourne `{"picks", "skipped"}`, allocation cumulative par SKU canonique, journalisation `qty_missing`/`order_id` | `1618fee`, `1cc705f` (316), `bf59867`/`c5a69cb` (442), `fa597ba`/`bbe524c` (507) |
| Tests `orders` | inexistants (« orders.py n'a aucun test ») | `tests/test_orders.py`, 10 tests | 442, 507, 316 |
| Bilan tests | « 3 tests, 1 échec » (test rouge) | **16 tests, tous OK** | — |

## Incertitudes

- **Périmètre volontairement réduit — carte à 2 domaines métier, sous le plancher de 4.** Choix assumé, pas un oubli : le dépôt ne contient objectivement que deux périmètres métier nommables (`entrepot-stock`, `preparation-commande`). Gonfler à 4+ confondrait domaines et fonctions, ou promouvrait de l'outillage (harnais de test) en domaine. À réévaluer si le pilote gagne des modules.
- **`entrepot-stock` vs `preparation-commande` : un seul module `inventory/` les héberge.** Le découpage repose sur les fichiers (`warehouse.py` / `orders.py`) et la dépendance directionnelle (orders → warehouse), pas sur des frontières de package. Un relecteur pourrait légitimement les fusionner en un seul domaine « logistique entrepôt » : je les garde séparés parce qu'ils correspondent à deux capacités métier distinctes (tenir le stock vs préparer une commande).
- **`preparation-commande` en `support` plutôt que `cœur`** : appuyé sur sa dépendance unidirectionnelle au stock et son absence de donnée propre. Défendable dans l'autre sens (c'est l'opération métier finale) — point d'arbitrage possible en relecture.
- **Aucun accès base de données à cette étape**, et le pilote n'en utilise pas : la détection « contenu piloté par la base » a tourné sur deux de ses trois signaux (entité étendue, code exécutable) et n'a rien trouvé. Conclusion `Dépend de la base : non` sur tous les domaines.
- **Aucune couche d'exposition** (HTTP, CLI, tâche planifiée) : les domaines métier n'ont pas de route au sens de la méthode. Normal pour une bibliothèque de démonstration ; à surveiller si une interface est ajoutée.
- **Aval à réconcilier** : la carte étant à jour, les artefacts en aval qui reposent sur le récit « bug volontaire non corrigé » (audit fonctionnel, cahier de recette, workflow prélèvement décrivant l'ancien format de sortie) sont probablement périmés eux aussi — à confronter au code courant dans leurs étapes respectives.
