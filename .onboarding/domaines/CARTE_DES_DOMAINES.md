# Carte des domaines — shift-pilot-py

> **Verdict : carte à 2 domaines métier, assumée.** Le code a été lu en intégralité (4 fichiers source, dépôt minuscule) — chaque affirmation ci-dessous est `VÉRIFIÉ_CODE`. Ce dépôt porte objectivement **deux** périmètres qu'un chef de projet nommerait : `entrepot-stock` (cœur) et `preparation-commande` (support). Sous le plancher indicatif de 4, mais c'est un **choix assumé** et non un oubli : gonfler confondrait domaines et fonctions (règle de la compétence — *matière pauvre → moins de domaines en confiance honnête, jamais une carte inventée*). Confiance **par domaine** ci-dessous (les deux en `high`) ; il n'y a pas de confiance « globale » dégradée à signaler, seulement un périmètre volontairement réduit.
>
> **Recentrage post-relecture :** le harnais de test `unittest` a été retiré de la liste des domaines. Ce n'est pas un domaine au sens de la méthode (pas de capacité produit autonome, pas de donnée métier propre, pas de workflow métier distinct — juste la vérification du domaine stock) : il est traité en section **Hors-domaines — outillage** ci-dessous.
>
> **Mode d'onboarding : complet** (rien sur le distant — pas de branche `onboarding/artifacts`, pas de `.onboarding/` dans le checkout). SHA de tête analysé : `fb5440af2859b33c5c3a44f5f07625f698d40426`.

## Nature du projet

`shift-pilot-py` est un **pilote de démonstration** d'une logistique d'entrepôt écrit en **Python 3 pur** (stdlib uniquement, tests `unittest`). Le `README.md` l'énonce : c'est volontairement une stack **non-JavaScript**, distincte des pilotes Node `shift-pilot-back` / `shift-pilot-front`, pour vérifier que l'outillage d'onboarding et de production ne présuppose pas un écosystème JS.

Fonctionnellement, il modélise un **stock d'entrepôt en mémoire** (articles avec SKU, quantité, quantité réservée, zone) et une **préparation de commande** dérivée (disponibilité à la vente, liste de prélèvement triée par zone). Il n'y a **ni route HTTP, ni base de données, ni persistance** : les données vivent dans une liste Python en dur (`inventory/warehouse.py:3`). Le dépôt embarque de plus un **bug volontaire** documenté (`available_qty` ne borne pas la disponibilité à zéro) et un **test rouge volontaire** qui l'attrape — signaux clairs que l'objet est pédagogique/de validation de chaîne, pas un produit livrable.

**Faits de stack `VÉRIFIÉ_CODE`** (à ne pas re-supposer en aval) : Python 3.12 (`inventory/__pycache__/*.cpython-312.pyc`) · tests via `python3 -m unittest discover -s tests -t .` (`README.md:10`) · **aucun** manifeste de dépendances (`requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile` non localisés malgré inventaire complet du dépôt) → aucune dépendance tierce · package importable `inventory` (`inventory/__init__.py`, vide) et `tests` (`tests/__init__.py`, vide).

## Domaines

### Gestion du stock d'entrepôt (`entrepot-stock`)
- **Catégorie** : métier
- **Priorité** : cœur
- **Confiance** : high
- **Description** : Référentiel des articles en entrepôt et calculs qui s'y rattachent — recherche par SKU, filtrage par zone, et **disponibilité réelle à la vente** (stock moins réservé). C'est le domaine fondateur : il porte la donnée que tout le reste consomme, et c'est là que réside le **bug volontaire** central du pilote (`available_qty` renvoie une quantité négative quand le réservé dépasse le stock, `inventory/warehouse.py:22-29`).
- **Entités** : `ITEMS` — collection en mémoire d'articles, chacun `{sku, label, qty, reserved, zone}` (`inventory/warehouse.py:3-8`). Pas d'entité ORM : structure de données Python, non persistée.
- **Routes / points d'entrée** : aucune route (pas de couche web). Points d'entrée = fonctions du module : `list_items()`, `find_by_sku(sku)`, `available_qty(item)`, `items_in_zone(zone)` (`inventory/warehouse.py:11-33`).
- **Indices de rattachement** : module `inventory/warehouse.py` ; symboles `ITEMS`, `available_qty`, `find_by_sku`, `items_in_zone`, `zone`, `reserved`, `qty`, `sku`.
- **Types de workflows attendus** : consultation du stock (par SKU, par zone), calcul de disponibilité vendable. Pas de mutation du stock dans le code actuel (aucune fonction n'écrit dans `ITEMS`).
- **Preuves** : `inventory/warehouse.py`, `tests/test_warehouse.py`, `README.md:13-15`.
- **Dépend de la base** : non. *(Aucun accès base fourni à cette étape ; par ailleurs aucun signal schéma/entité-étendue/code-exécutable de contenu piloté par la base — données en dur, pas de structure arborescente décodée à l'exécution.)*

### Préparation de commande (`preparation-commande`)
- **Catégorie** : métier
- **Priorité** : support
- **Confiance** : high
- **Description** : Opérations dérivées du stock côté exécution logistique — décider si une commande **peut être honorée** pour une quantité demandée, et transformer des **lignes de commande** en **liste de prélèvement** triée par zone (ordre de parcours de l'entrepôt). Domaine consommateur : il ne détient aucune donnée propre, il s'appuie entièrement sur `entrepot-stock` (`from inventory.warehouse import find_by_sku, available_qty`, `inventory/orders.py:3`). D'où sa priorité `support` plutôt que `cœur`.
- **Entités** : aucune entité propre. Manipule des **lignes de commande** — tuples `(sku, qty)` en entrée (`inventory/orders.py:16`) — et produit des **entrées de prélèvement** `{sku, zone, qty}` (`inventory/orders.py:20`).
- **Routes / points d'entrée** : aucune route. Fonctions : `can_fulfil(sku, requested)`, `picking_list(lines)` (`inventory/orders.py:6-35`).
- **Indices de rattachement** : module `inventory/orders.py` ; symboles `can_fulfil`, `picking_list`, `lines`, `requested`, `picking`.
- **Types de workflows attendus** : contrôle de faisabilité d'une commande, génération d'une feuille de prélèvement ordonnée par zone. Hérite mécaniquement du bug de `available_qty` : `can_fulfil` peut se tromper quand le réservé dépasse le stock (à confronter en étape workflows/audit).
- **Preuves** : `inventory/orders.py`.
- **Dépend de la base** : non.

## Hors-domaines — outillage

### Harnais de test `unittest`
Ce n'est **pas un domaine** au sens de la méthode : pas de capacité produit autonome, pas de donnée métier propre, pas de workflow métier distinct. C'est l'**outillage qualité** du pilote, qui ne fait que vérifier le comportement du domaine `entrepot-stock`. Il est documenté ici plutôt que promu en domaine, pour ne pas gonfler la carte.

- **Ce que c'est** : suite `unittest` de la bibliothèque standard, classe `TestWarehouse` (`tests/test_warehouse.py:6`), lancée par `python3 -m unittest discover -s tests -t .` (`README.md:10`).
- **Portée** : couvre uniquement `inventory/warehouse.py` (disponibilité, recherche par SKU, comptage par zone). `inventory/orders.py` n'a aucun test.
- **Fait structurant** : contient un **test rouge volontaire** `test_available_qty_never_negative` — il encode en exécutable l'invariant « la disponibilité ne descend jamais sous zéro » que le code métier viole exprès. C'est le porteur de l'intention pédagogique du seed, mais l'invariant qu'il défend appartient au domaine `entrepot-stock`, pas à un domaine « tests ».
- **Vérification exécutable** : `python3 -m unittest discover -s tests -t .` → `3 tests`, `1 failure` sur `test_available_qty_never_negative` (`-5 != 0`).
- **CI** : aucune localisée dans le dépôt (pas de `.github/`, `.gitlab-ci.yml`, etc. — inventaire complet effectué).

## Incertitudes

- **Périmètre volontairement réduit — carte à 2 domaines métier, sous le plancher de 4.** C'est un choix assumé, pas un oubli : le dépôt ne contient objectivement que deux périmètres métier nommables (`entrepot-stock`, `preparation-commande`). Gonfler à 4+ reviendrait à confondre domaines et fonctions, ou à promouvoir de l'outillage (le harnais de test) en domaine — d'où son passage en section *Hors-domaines*. À réévaluer si le pilote gagne des modules.
- **`entrepot-stock` vs `preparation-commande` : un seul module `inventory/` les héberge tous deux.** Le découpage repose sur les fichiers (`warehouse.py` / `orders.py`) et la dépendance directionnelle (orders → warehouse), pas sur des frontières de package. Un relecteur pourrait légitimement les fusionner en un seul domaine « logistique entrepôt » : je les garde séparés parce qu'ils correspondent à deux capacités métier distinctes (tenir le stock vs préparer une commande) qu'un chef de projet nommerait séparément.
- **`preparation-commande` en `support` plutôt que `cœur`** : appuyé sur sa dépendance unidirectionnelle au stock et son absence de donnée propre. Défendable dans l'autre sens (c'est l'opération métier finale) — point d'arbitrage possible en relecture.
- **Aucun accès base de données à cette étape**, et le pilote n'en utilise pas : la détection « contenu piloté par la base » a tourné sur deux de ses trois signaux (entité étendue, code exécutable) et n'a rien trouvé. Conclusion `Dépend de la base : non` sur tous les domaines, avec la réserve habituelle qu'un signal schéma ne peut être écarté qu'avec un accès base — ici sans objet, puisqu'il n'y a pas de base du tout.
- **Aucune couche d'exposition** (HTTP, CLI, tâche planifiée) : les domaines métier n'ont pas de route au sens de la méthode. Normal pour une bibliothèque de démonstration ; à surveiller si une interface est ajoutée.
