# Relecture — audits réconciliés

## Verdict global

Bon — les six audits sont exploitables sans réserve bloquante. Les faits issus du source sont marqués `VÉRIFIÉ_CODE`, l'exécution réelle des tests est marquée `OBSERVÉ`, et les scénarios conditionnels/non reproduits restent `HYPOTHÈSE` ou `INCONNU`.

## Problèmes bloquants

Aucun.

Preuves contrôlées : `inventory/warehouse.py:22-24` confirme la borne `max(0, ...)`; `inventory/orders.py:6-12,28-46` confirme les chemins décrits; `python3 -m unittest discover -s tests -t .` a produit `Ran 16 tests ... OK` et cette sortie est portée comme `OBSERVÉ` dans `TESTING_AUDIT.md:17`.

## Problèmes mineurs

Aucun défaut nécessitant un retour au producteur. Les absences sont bornées au dépôt inspecté et les risques futurs sont explicitement conditionnels, notamment `CODE_HOTSPOTS_AUDIT.md:44-47`, `DATA_MODEL_AUDIT.md:47-49` et `SECURITY_ROBUSTNESS_AUDIT.md:52-54`.

## Points vérifiés et corrects

- Les métriques et inventaires concordent avec le dépôt : `warehouse.py` fait 28 lignes, `orders.py` 46 lignes, et la suite contient 6 + 10 tests (`ARCHITECTURE_AUDIT.md:15`, `TESTING_AUDIT.md:15`).
- La mutabilité de `ITEMS` et les retours directs sont correctement sourcés (`inventory/warehouse.py:3,11-18`; `ARCHITECTURE_AUDIT.md:23`; `DATA_MODEL_AUDIT.md:25`).
- L'absence de `can_fulfil()` dans les tests et le silence sur SKU inconnu sont des faits de code, séparés de leurs impacts hypothétiques (`CODE_HOTSPOTS_AUDIT.md:15,43-46`).
- Les vérifications d'absence sont bornées à l'inventaire du dépôt et aucun secret n'est recopié (`ARCHITECTURE_AUDIT.md:19,28`; `SECURITY_ROBUSTNESS_AUDIT.md:7,15-17`).

## Recommandations de correction

Aucune correction obligatoire. Les recommandations présentes dans les audits sont actionnables et reliées aux fichiers concernés, notamment l'ajout de tests pour `can_fulfil()` (`TESTING_AUDIT.md:65`) et la protection/signalisaton des retours de `picking_list()` (`SECURITY_ROBUSTNESS_AUDIT.md:58`).
