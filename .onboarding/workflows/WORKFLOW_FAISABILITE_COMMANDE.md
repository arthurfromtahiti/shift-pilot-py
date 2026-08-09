# WORKFLOW_FAISABILITE_COMMANDE — Vérification qu'une commande peut être honorée pour un SKU

> **RÉCONCILIÉ le 2026-08-09.** SHA de référence : `511104b`. Écarts vs version initiale : (1) `can_fulfil` rejette désormais `requested <= 0` en entrée (garde explicite, lignes 7-8) ; (2) `available_qty` est corrigée — plus de valeur négative possible, donc le « bug hérité » n'existe plus ; (3) la référence de ligne `available_qty` mise à jour (`:22-24` pas `:22-29`) ; (4) tests `orders` désormais présents (10 tests dans `test_orders.py`), mais aucun ne couvre `can_fulfil` — le risque d'absence de test reste valide.

## Classification
- **Type** : `business_process`
- **Sous-type** : contrôle de faisabilité d'une ligne de commande
- **Visibilité** : `technical` — appelé par du code, pas par une interface utilisateur
- **Acteur principal** : module appelant (ex. orchestrateur de commandes)
- **Acteurs** : code appelant uniquement — aucun humain direct
- **Criticité** : Haute — une erreur autorise une commande infaisable ou refuse une commande réalisable
- **Confiance** : high
- **Justification** : Fonction `can_fulfil` lue en intégralité (`inventory/orders.py:6-12`). Sa dépendance vers `find_by_sku` et `available_qty` a été lue (`inventory/warehouse.py`). La garde `requested <= 0` est visible en ligne 7. `available_qty` retourne désormais `max(0, ...)` — aucune propagation de valeur négative dans la chaîne.

## Objectif
Permettre à un orchestrateur de commandes de savoir, avant d'engager une préparation, si l'entrepôt dispose d'une quantité disponible suffisante pour un article donné (SKU + quantité demandée). La décision est binaire : oui ou non. Ce workflow est la garde-barrière logistique : s'il répond oui à tort, des commandes impossibles seront lancées en préparation.

## Acteurs
- Module Python appelant (ex. orchestrateur de commandes, futur contrôleur HTTP)

## Points d'entrée
- `inventory.orders.can_fulfil(sku, requested)` — prend un SKU (str, précondition non validée en type) et une quantité demandée (int, précondition non validée en type) ; retourne un booléen (`inventory/orders.py:6`)

## Étapes principales
1. L'appelant invoque `can_fulfil(sku, requested)` avec un SKU et une quantité entière (`inventory/orders.py:6`).
2. **Garde quantité :** si `requested <= 0`, retourne `False` immédiatement — quantité nulle ou négative est toujours refusée (`inventory/orders.py:7-8`).
3. `find_by_sku(sku)` est appelée pour récupérer l'article dans le stock (`inventory/orders.py:9`, `inventory/warehouse.py:15-19`).
4. Si l'article n'existe pas (`item is None`) : retourne `False` immédiatement — la commande ne peut pas être honorée (`inventory/orders.py:10-11`).
5. `available_qty(item)` est appelée pour obtenir la disponibilité nette (`inventory/orders.py:12`, `inventory/warehouse.py:22-24`).
6. Comparaison `available_qty(item) >= requested` : retourne `True` si la disponibilité couvre la demande, `False` sinon (`inventory/orders.py:12`).

## Règles métier
- **Quantité nulle ou négative → commande refusée.** Si `requested <= 0`, `can_fulfil` retourne `False` sans consulter le stock (`inventory/orders.py:7-8`). Aucun test ne couvre ce cas directement dans `test_orders.py` (qui n'importe pas `can_fulfil`).
- **Un SKU inconnu rend la commande infaisable.** Si `find_by_sku` retourne `None`, `can_fulfil` retourne `False` sans lever d'exception (`inventory/orders.py:10-11`).
- **La faisabilité repose sur la disponibilité nette** (`max(0, qty - reserved)`), pas sur le stock brut. L'invariant est `available_qty(item) >= requested` (`inventory/orders.py:12`). `available_qty` est bornée à zéro — une donnée corrompue (`reserved > qty`) ne peut pas produire de fausse autorisation.
- **`find_by_sku` est insensible à la casse.** Un SKU en minuscules ou casse mixte retrouve l'article canonique (`inventory/warehouse.py:17`).

## Données
- `ITEMS` (via `find_by_sku`) : référentiel stock en mémoire, non persisté (`inventory/warehouse.py:3-8`)
- Paramètres d'entrée : `sku` (str, précondition non validée en type) et `requested` (int, précondition non validée en type) — `requested <= 0` est rejeté par la garde, mais aucun contrôle de type n'est effectué ni sur `sku` ni sur `requested` : un `requested` non comparable à zéro (ex. `None`) lèverait `TypeError` à la ligne 7 avant toute consultation du stock

## Intégrations
Aucune intégration externe explicite visible. Dépendance interne : `inventory.warehouse` (`inventory/orders.py:3`).

## Risques
- **Absence de validation de type sur `sku`.** `sku` n'est pas contrôlé en type. Un `sku` de type incorrect (ex. `None`) n'est pas rejeté : `find_by_sku` effectuerait `None.upper()` et lèverait `AttributeError`. Aucun test ne couvre ce chemin.
- **Aucun test couvrant `can_fulfil`.** `tests/test_orders.py` n'importe que `picking_list`, pas `can_fulfil` (`tests/test_orders.py:3`). Le comportement en cas de SKU inconnu, de quantité nulle, ou de type incorrect n'est pas vérifié automatiquement.
- **`picking_list` et `can_fulfil` sont indépendantes et non composées.** `picking_list` fait sa propre vérification de disponibilité (cumulative) sans appeler `can_fulfil`. Un orchestrateur qui appelle `can_fulfil` puis `picking_list` sans tenir compte de l'allocation cumulative peut obtenir un refus partiel dans `picking_list` malgré un feu vert de `can_fulfil` (ex. plusieurs lignes du même SKU). Cette divergence est intentionnelle mais non documentée dans le code.

## Questions ouvertes
- Le cas `requested = 0` est rejeté par la garde `requested <= 0`. Est-ce le comportement attendu pour « vérifier si un article est simplement en stock, quelle que soit la quantité » ? Si oui, il faudrait un `can_fulfil(sku, 0)` qui retourne `True` uniquement si le stock existe.
- Pourquoi `can_fulfil` n'a-t-il aucun test dans `test_orders.py` ? Omission volontaire (exercice laissé aux apprenants) ou dette à combler ?

## Preuves
- `inventory/orders.py` — lu en intégralité
- `inventory/warehouse.py` — lu en intégralité (chaîne d'appel `find_by_sku`, `available_qty`)
- `tests/test_orders.py` — lu en intégralité (absence de test sur `can_fulfil` confirmée — seul `picking_list` est importé et testé)
- `.onboarding/domaines/CARTE_DES_DOMAINES.md` — domaine `preparation-commande` (réconcilié)
