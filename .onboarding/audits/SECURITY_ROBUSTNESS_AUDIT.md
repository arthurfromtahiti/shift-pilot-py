# Sécurité & Robustesse — Audit

> Confiance : high

## Compréhension globale

`shift-pilot-py` est une bibliothèque Python sans surface réseau, sans authentification, sans base de données et sans secrets. La surface d'attaque est donc très réduite : le code ne traite que des appels internes Python. Les risques de sécurité classiques (injection SQL, XSS, authz, exposition de secrets) sont structurellement absents par construction. Les risques réels sont de nature robustesse : comportements inattendus sur des entrées mal formées, valeur de retour hors invariant, silences trompeurs.

## Résumé exécutif

Aucun secret en clair, aucune route exposée, aucune dépendance tierce : la surface de sécurité est quasi nulle pour ce pilote. Les risques identifiés sont de robustesse : (1) `available_qty()` retourne une valeur négative sur `CX-330` — comportement volontaire documenté mais non borné (`inventory/warehouse.py:29`) ; (2) `can_fulfil()` et `picking_list()` n'effectuent aucune validation des paramètres d'entrée ; (3) `picking_list()` avale silencieusement les SKUs inconnus sans log ni signal (`inventory/orders.py:18-19`). Ces trois points sont sans impact de sécurité dans l'état actuel, mais deviendraient des vecteurs de comportement indéterminé si une couche web ou externe était ajoutée.

## Constats détaillés

**VÉRIFIÉ_CODE — Aucun secret, aucune clé, aucune donnée sensible.** Le code source ne contient aucune valeur ressemblant à un token, mot de passe, clé d'API ou donnée personnelle. La donnée de démonstration (`ITEMS`) est inventée (articles fictifs : Ancre 10kg, Bouée gonflable, etc.) (`inventory/warehouse.py:3-8`). Aucun fichier de configuration, `.env`, ni credential n'est localisé dans le dépôt (inventaire complet effectué).

**VÉRIFIÉ_CODE — Aucune route réseau, aucun binding de port.** Il n'y a ni serveur HTTP, ni WebSocket, ni listener TCP dans le code. Les fonctions sont des callables Python purs. Aucun framework web n'est importé.

**VÉRIFIÉ_CODE — Bug volontaire : `available_qty()` retourne une valeur négative.** `available_qty(item)` retourne `item["qty"] - item["reserved"]` sans borne inférieure (`inventory/warehouse.py:29`). Pour `CX-330` (`qty=45, reserved=50`), le retour est `-5`. Ce comportement est documenté dans la docstring (`inventory/warehouse.py:23-28`) et dans `README.md`. L'invariant « disponibilité ≥ 0 » est violé de façon intentionnelle. Ce n'est pas un risque de sécurité, mais une robustesse défaillante : un appelant qui stokerait, afficherait ou additionnerait cette valeur sans garde obtiendrait un résultat sémantiquement faux.

**VÉRIFIÉ_CODE — Absence de validation des entrées dans `can_fulfil()` et `picking_list()`.** `can_fulfil(sku, requested)` n'effectue aucun contrôle de type sur `sku` ni sur `requested` (`inventory/orders.py:6-10`). Un `requested` négatif ou non-entier produirait un comportement indéfini silencieux plutôt qu'une erreur explicite. `picking_list(lines)` suppose que `lines` est un itérable de tuples `(str, int)` ; un format incorrect (dict, str seul, liste de listes) lèverait une `ValueError` ou `TypeError` non guidée (`inventory/orders.py:16`).

**VÉRIFIÉ_CODE — Silence sur SKU inconnu dans `picking_list()`.** Quand `find_by_sku(sku)` retourne `None`, `picking_list()` exécute un `continue` sans log, sans compteur et sans valeur de retour enrichie (`inventory/orders.py:18-19`). L'appelant reçoit une liste silencieusement incomplète. Dans un contexte de préparation physique, ce silence pourrait passer inaperçu et produire un prélèvement partiel.

**VÉRIFIÉ_CODE — `find_by_sku()` retourne `None` sur SKU inconnu — documenté, mais sans garde systématique chez l'appelant.** `warehouse.py` retourne `None` pour tout SKU non trouvé (`inventory/warehouse.py:19`). `can_fulfil()` teste ce cas (`inventory/orders.py:8-9`). `picking_list()` aussi (`inventory/orders.py:18-19`). En revanche, un futur appelant qui passerait directement `find_by_sku(sku)` dans `available_qty()` sans tester `None` provoquerait une `TypeError: 'NoneType' object is not subscriptable` — l'invariant de sécurité du `None` n'est pas documenté au niveau de l'interface publique.

**VÉRIFIÉ_CODE — Aucune dépendance tierce.** Pas de `requirements.txt`, `pyproject.toml`, `Pipfile` ni `setup.py` localisé dans le dépôt (inventaire complet). Pas de surface de vulnérabilité de supply chain.

## Forces

- **Surface d'attaque structurellement nulle.** Pas de réseau, pas de BD, pas de secrets : les catégories OWASP classiques (injection, auth, exposition) sont hors périmètre.
- **Bug volontaire documenté et encapsulé.** La docstring de `available_qty()` décrit explicitement le comportement (`inventory/warehouse.py:23-28`), et un test rouge en fait une assertion contrôlée (`tests/test_warehouse.py:14-18`). Le risque est connu et tracé.
- **Gestion du `None` dans les deux appelants immédiats.** `can_fulfil()` et `picking_list()` défendent tous les deux contre le retour `None` de `find_by_sku()` (`inventory/orders.py:8-9`, `inventory/orders.py:18-19`).

## Dettes techniques

- **`available_qty()` ne borne pas à zéro.** L'invariant sémantique « disponibilité ≥ 0 » est absent du code (`inventory/warehouse.py:29`). Si ce comportement doit rester volontaire, la docstring suffit ; si le bug doit être corrigé, la borne est `max(0, item["qty"] - item["reserved"])`.
- **Aucune validation de types d'entrée.** `can_fulfil()` et `picking_list()` font confiance à leurs appelants. Sans garde, un type incorrect produit une exception non guidée ou un résultat silencieusement faux. (`inventory/orders.py:6`, `inventory/orders.py:13`)
- **Silences non signalés dans `picking_list()`.** Le `continue` sur SKU inconnu (`inventory/orders.py:18-19`) est une perte d'information non gérée. Un log, un second paramètre de retour, ou une liste de rejets enrichirait la robustesse sans alourdir l'interface.

## Zones critiques

- **`inventory/orders.py:18-19` — silence sur SKU inconnu.** C'est le comportement le plus susceptible de produire un incident silencieux en production : le code continue sans erreur, mais le résultat est factuellement incomplet.
- **`inventory/warehouse.py:29` — valeur négative propagée.** Point d'origine du bug documenté ; toute future chaîne appelante en aval de `available_qty()` doit tester ou borner explicitement.

## Risques

- **HYPOTHÈSE — Injection de comportement par `requested` négatif.** Si `can_fulfil(sku, -6)` est appelé pour un article dont `available_qty` vaut `-5`, l'expression `-5 >= -6` retourne `True` et autoriserait la commande. Ce scénario requiert un bug dans l'appelant, mais aucune garde ne l'intercepte. (`inventory/orders.py:10`)
- **HYPOTHÈSE — Mutation de `ITEMS` par `list_items()`.** Si un appelant de `list_items()` modifie la liste retournée, l'état global de `ITEMS` est corrompu pour tous les appels suivants. Risque nul aujourd'hui, réel si une couche concurrente ou externe est introduite. (`inventory/warehouse.py:11-12`)
- **HYPOTHÈSE — `TypeError` non guidée sur `None` non gardé.** Un futur appelant qui enchaîne `available_qty(find_by_sku("INEXISTANT"))` sans garde obtiendra `TypeError: 'NoneType' object is not subscriptable` — erreur technique non métier, difficile à diagnostiquer sans connaître le code source.

## Recommandations priorisées

1. **Documenter le contrat `None` de `find_by_sku()` dans la docstring** — Préciser que le retour peut être `None` et que l'appelant doit tester avant usage, pour éviter les chaînes d'appel non gardées. (`inventory/warehouse.py:15-19`)
2. **Ajouter un signal sur SKU ignoré dans `picking_list()`** — À minima un `warnings.warn()` ou un second retour (liste des SKUs ignorés) pour éviter les prélèvements silencieusement incomplets. (`inventory/orders.py:18-19`)
3. **Borne `max(0, ...)` dans `available_qty()` si le bug est à corriger** — Si l'objectif pédagogique est atteint, restaurer l'invariant en une ligne. Si le bug doit rester, ajouter une assertion explicite dans les tests verts qu'il documente le comportement voulu, pas seulement qu'il échoue. (`inventory/warehouse.py:29`)

## Questions ouvertes

- Le bug `available_qty` est-il prévu pour être corrigé dans ce pilote (borne à zéro), ou rester volontairement cassé jusqu'à la fin de l'exercice ?
- Doit-on valider `requested > 0` en entrée de `can_fulfil()`, ou la validation appartient-elle à l'orchestrateur appelant ?
- Si une couche HTTP est ajoutée (FastAPI, Flask), des règles de sécurité supplémentaires seront nécessaires (authz, rate limiting, validation de schéma d'entrée) — hors périmètre du pilote actuel, mais à anticiper.
