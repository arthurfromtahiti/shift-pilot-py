# Relecture — audits réconciliés

## Verdict global

À corriger — les quatre corrections précédentes sont confirmées, mais la discipline de preuve n'est pas encore homogène dans les six audits.

## Problèmes bloquants

- `TESTING_AUDIT.md:11` affirme « tous verts » dans le résumé sans statut `OBSERVÉ`. La sortie est bien observée fraîchement (`python3 -m unittest discover -s tests -t .` → `Ran 16 tests ... OK`), mais cette preuve doit être portée explicitement dans le résumé ou celui-ci doit dire seulement « six tests présents ».
- `SECURITY_ROBUSTNESS_AUDIT.md:21,25,47` étiquette `VÉRIFIÉ_CODE` des résultats non exécutés (« provoquerait une TypeError », erreur au déstructurage, erreur lors d'un chaînage `None`). La lecture établit les gardes et les chemins de code (`inventory/orders.py:7-12,28-33`, `inventory/warehouse.py:15-24`) ; les comportements avec ces entrées doivent être `HYPOTHÈSE` tant qu'ils ne sont pas reproduits, ou être accompagnés d'une preuve `OBSERVÉE`.

## Problèmes mineurs

- `SECURITY_ROBUSTNESS_AUDIT.md:21` généralise les erreurs de `picking_list()` sur « dict, str seul, liste de listes » : une liste de listes peut satisfaire le déstructurage. Reformuler le fait observé (`lines` est déstructuré en deux valeurs, `inventory/orders.py:28`) et laisser le résultat précis pour chaque entrée en `HYPOTHÈSE`/`INCONNU`.
- `TESTING_AUDIT.md:33` rapporte la présence des `.pyc` dans `git status` sans statut d'observation. Le fait est vérifiable par une sortie Git fraîche, mais ne pas le présenter comme une propriété purement `VÉRIFIÉ_CODE`; distinguer absence de `.gitignore` (code/arborescence) et état Git observé.
- Les formulations « se comportent comme documenté », « obtiendra une liste garantie faisable » et « surface d'attaque nulle » (`FUNCTIONAL_AUDIT.md:15,47`, `SECURITY_ROBUSTNESS_AUDIT.md:7,31`) doivent rester bornées à la lecture du code et au dépôt inspecté ; elles ne valent pas preuve d'exécution ni garantie d'un futur environnement.

## Points vérifiés et corrects

- Le code courant confirme `available_qty() == max(0, qty - reserved)` (`inventory/warehouse.py:22-24`) et les audits ne le présentent plus comme un bug actif (`FUNCTIONAL_AUDIT.md:11,15,17`).
- Les métriques et la structure sont maintenant exactes : `warehouse.py` 28 lignes, `orders.py` 46 lignes, 74 au total, et deux fichiers de tests (`ARCHITECTURE_AUDIT.md:15,19,39`, `CODE_HOTSPOTS_AUDIT.md:7`).
- La mutabilité de `ITEMS` et les références retournées sont correctement sourcées (`inventory/warehouse.py:3,11-18`; `ARCHITECTURE_AUDIT.md:11,23`; `DATA_MODEL_AUDIT.md:25`).
- Les risques conditionnels sur SKU inconnu, mutation et absence de tests sont désormais marqués `HYPOTHÈSE` là où l'impact n'est pas directement observé (`CODE_HOTSPOTS_AUDIT.md:44,46-47`, `TESTING_AUDIT.md:55,57-58`).
- Vérification runtime fraîche : la suite réelle passe avec 16 tests (`python3 -m unittest discover -s tests -t .` → `OK`). Cela confirme la sortie d'exécution, pas l'absence de couverture de `can_fulfil()` (`tests/test_orders.py:3`, `inventory/orders.py:6-12`).

## Recommandations de correction

1. Corriger les statuts de preuve aux emplacements signalés, en séparant systématiquement `VÉRIFIÉ_CODE` (source lu), `OBSERVÉ` (commande réellement exécutée), `HYPOTHÈSE` (scénario conditionnel) et `INCONNU` (non vérifié).
2. Corriger la formulation des entrées mal formées de `picking_list()` et borner les affirmations de sécurité à l'état du dépôt inspecté.
3. Après correction, relancer la suite et conserver la sortie `OBSERVÉE` dans `TESTING_AUDIT.md`; soumettre ensuite les six audits à une dernière passe.
