# WORKFLOW_FAISABILITE_COMMANDE — Vérification qu'une commande peut être honorée pour un SKU

## Classification
- **Type** : `business_process`
- **Sous-type** : contrôle de faisabilité d'une ligne de commande
- **Visibilité** : `technical` — appelé par du code, pas par une interface utilisateur
- **Acteur principal** : module appelant (ex. orchestrateur de commandes)
- **Acteurs** : code appelant uniquement — aucun humain direct
- **Criticité** : Haute — une erreur autorise une commande infaisable ou refuse une commande réalisable
- **Confiance** : high
- **Justification** : Fonction `can_fulfil` lue en intégralité (`inventory/orders.py:6-10`). Sa dépendance vers `find_by_sku` et `available_qty` a été lue (`inventory/warehouse.py`). Le cas de propagation du bug est directement visible dans la chaîne d'appel.

## Objectif
Permettre à un orchestrateur de commandes de savoir, avant d'engager une préparation, si l'entrepôt dispose d'une quantité disponible suffisante pour un article donné (SKU + quantité demandée). La décision est binaire : oui ou non. Ce workflow est la garde-barrière logistique : s'il répond oui à tort, des commandes impossibles seront lancées en préparation.

## Acteurs
- Module Python appelant (ex. orchestrateur de commandes, futur contrôleur HTTP)

## Points d'entrée
- `inventory.orders.can_fulfil(sku, requested)` — prend un SKU (chaîne) et une quantité demandée (entier) ; retourne un booléen (`inventory/orders.py:6`)

## Étapes principales
1. L'appelant invoque `can_fulfil(sku, requested)` avec un SKU et une quantité entière (`inventory/orders.py:6`).
2. `find_by_sku(sku)` est appelée pour récupérer l'article dans le stock (`inventory/orders.py:7`, `inventory/warehouse.py:15-19`).
3. Si l'article n'existe pas (`item is None`) : retourne `False` immédiatement — la commande ne peut pas être honorée (`inventory/orders.py:8-9`).
4. `available_qty(item)` est appelée pour obtenir la disponibilité nette (`inventory/orders.py:10`, `inventory/warehouse.py:22-29`).
5. Comparaison `available_qty(item) >= requested` : retourne `True` si la disponibilité couvre la demande, `False` sinon (`inventory/orders.py:10`).

## Règles métier
- **Un SKU inconnu rend la commande infaisable.** Si `find_by_sku` retourne `None`, `can_fulfil` retourne `False` sans lever d'exception (`inventory/orders.py:8-9`).
- **La faisabilité repose sur la disponibilité nette** (`qty - reserved`), pas sur le stock brut. L'invariant attendu est `available_qty(item) >= requested` (`inventory/orders.py:10`).
- **Bug hérité :** si `reserved > qty`, `available_qty` retourne une valeur négative (`inventory/warehouse.py:29`). Exemple : `CX-330` → disponible = `-5`. Pour tout `requested >= 0`, l'expression `-5 >= requested` vaut `False` — la commande est refusée, ce qui correspond au comportement attendu en rupture réelle. Ce résultat correct est produit par accident arithmétique, non par une garde explicite. Le seul cas où ce bug autoriserait une commande à tort est un `requested` inférieur à la disponibilité négative (ex. `requested = -6` : `-5 >= -6` vaut `True`). Ce scénario requiert une valeur d'entrée anormale, non défendue par le code (`inventory/orders.py:6`).

## Données
- `ITEMS` (via `find_by_sku`) : référentiel stock en mémoire, non persisté (`inventory/warehouse.py:3-8`)
- Paramètres d'entrée : `sku` (str), `requested` (int) — non validés par la fonction (pas de contrôle de type, pas de garde `requested > 0`)

## Intégrations
Aucune intégration externe explicite visible. Dépendance interne : `inventory.warehouse` (`inventory/orders.py:3`).

## Risques
- **Invariant `available_qty` violé.** Pour `CX-330` (`qty=45, reserved=50`), `available_qty` retourne `-5` (`inventory/warehouse.py:29`). L'invariant attendu est qu'une disponibilité nette ne soit jamais négative. Ce retour négatif se propage jusqu'à `can_fulfil`, où la comparaison devient `-5 >= requested`. Pour tout `requested >= 0`, la commande est refusée : résultat observable correct, mais obtenu par accident arithmétique et non par logique explicite.
- **Absence de validation de `requested`.** `requested` n'est pas contrôlé à l'entrée de `can_fulfil` (`inventory/orders.py:6`). Aucune garde ne rejette une valeur nulle, négative ou d'un type incorrect. Dans l'état actuel du code, passer `requested=0` retourne `False` (`-5 >= 0` est faux) et passer `requested=-1` retourne également `False` (`-5 >= -1` est faux) : le comportement est refus, non autorisation. Le risque réel serait une valeur `requested` inférieure à la disponibilité négative (ex. -6 pour `CX-330`), scénario qui suppose un bug dans l'appelant — possible faute de garde.
- **`sku` de type incorrect — silence.** Un `sku` de type incorrect (ex. `None`) n'est pas rejeté. `find_by_sku` effectuerait une comparaison `None == "AX-100"` qui retourne `False` pour tous les articles ; `can_fulfil` retournerait alors `False` sans crash, mais silencieusement (`inventory/orders.py:7`).
- **Aucun test couvrant `can_fulfil`.** `inventory/orders.py` n'a aucune suite de test (`tests/test_warehouse.py` ne l'importe pas). Le comportement en cas de SKU inconnu, de quantité nulle, ou de bug `available_qty` n'est pas vérifié automatiquement.

## Questions ouvertes
- Doit-on valider que `requested > 0` en entrée de `can_fulfil`, ou la validation est-elle censée être faite par l'appelant ?
- Le cas `requested = 0` est-il un appel légitime (vérifier si un article est en stock, quelle que soit la quantité) ou une erreur à rejeter ?
- Pourquoi `inventory/orders.py` n'a-t-il aucun test ? Est-ce un oubli du seed ou une omission volontaire (ex. pour laisser cet exercice aux apprenants) ?

## Preuves
- `inventory/orders.py` — lu en intégralité
- `inventory/warehouse.py` — lu en intégralité (chaîne d'appel `find_by_sku`, `available_qty`)
- `tests/test_warehouse.py` — lu en intégralité (absence de test sur `can_fulfil` confirmée)
- `CARTE_DES_DOMAINES.md` — domaine `preparation-commande`
