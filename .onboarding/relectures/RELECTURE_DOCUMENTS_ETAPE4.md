# Relecture — documents de référence, étape 4

## Verdict global

**À corriger.** Le comptage des tests est désormais exact et la suite réelle passe, mais le lot documentaire contient encore des affirmations contradictoires avec le code courant. Le lot ne peut pas certifier l’absence de contradiction tant que ces traces historiques et cette couverture fictive ne sont pas retirées.

## Problèmes bloquants

### 1. `PROJECT_CONTEXT.md` conserve un état historique contredit

Les sections « Questions non tranchées » et « Livrables d’onboarding » indiquent encore que le bug `available_qty` est à décider et qu’un « test rouge » est en place. Le code courant borne bien la valeur par `max(0, ...)`, et `tests/test_warehouse.py` contient le test de borne qui passe. Ces formulations ne sont donc plus l’état actuel et contredisent les preuves directes du code et de la suite exécutée.

À corriger : qualifier ces éléments comme historique si leur conservation est nécessaire, sinon les supprimer ; décrire l’état courant comme corrigé et testé.

### 2. `can_fulfil()` est présenté comme couvert indirectement alors qu’il ne l’est pas

`PROJECT_CONTEXT.md` (piste d’évolution), `CDC_FONCTIONNEL.md` (preuves/tests) et `CARTOGRAPHIE_CODE.md` affirment que `can_fulfil()` est « couvert indirectement » ou qu’elle est appelée par `picking_list()`. La preuve directe `inventory/orders.py` montre pourtant que `picking_list()` appelle seulement `find_by_sku()` et `available_qty()` ; aucun test de `tests/test_orders.py` n’importe ou n’appelle `can_fulfil()`.

À corriger : dire « aucun test direct ni indirect dans la suite actuelle », puis conserver les exemples de comportement comme règles observées au code, non comme couverture de tests. Si une couverture est requise, le rédacteur doit ajouter des tests directs et actualiser les compteurs.

### 3. `VERDICT_FINAL.md` certifie prématurément l’absence de contradiction

Le verdict final affirme « aucune contradiction résiduelle », « chaque affirmation ... sourcée » et « prêts pour production », alors que les deux écarts ci-dessus sont toujours présents. Cette certification est réfutée par la comparaison des documents entre eux et avec `inventory/orders.py`, `inventory/warehouse.py` et les tests.

À corriger : réviser le certificat après correction effective et vérification globale ; ne pas présenter la simple correction des compteurs comme une réconciliation exhaustive.

## Points vérifiés

- `tests/test_warehouse.py` contient 6 tests et `tests/test_orders.py` 10 tests ; `python3 -m unittest discover -v` établit 16 tests verts.
- Le jeu de données `CX-330` (`reserved=5`) et la borne `max(0, ...)` sont cohérents.
- Le cas `picking_list(["AX-100"])` est correctement décrit comme une `ValueError` au déballage.
- Les workflows et la majorité des règles fonctionnelles restent traçables à l’amont.

## Disposition

**Demande de changements.** Le rédacteur doit supprimer/qualifier l’état historique du `PROJECT_CONTEXT.md`, corriger partout la prétendue couverture indirecte de `can_fulfil()`, puis resoumettre le lot et son verdict final pour relecture.
