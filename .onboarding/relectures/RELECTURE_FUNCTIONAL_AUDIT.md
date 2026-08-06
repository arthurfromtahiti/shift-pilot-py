# Relecture — FUNCTIONAL_AUDIT.md

## Verdict global
Acceptable avec réserves — l'audit est cohérent avec le code et avec les trois workflows relus. Les principaux écarts sont bien identifiés, mais une partie de la synthèse va un peu trop vite sur la portée réelle de l'impact du bug volontaire.

## Problèmes bloquants
Aucun.

## Problèmes mineurs
- La formule "le bug volontaire ... son impact fonctionnel est limité et connu" dans le résumé exécutif est plausible mais pas entièrement prouvée comme fait général. Le caractère "connu" est documenté par [README.md](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/README.md:13), les workflows et le test rouge ; en revanche "limité" est un jugement de portée qui devrait rester plus conditionnel.

## Points vérifiés et corrects
- La correspondance code/workflows est correctement démontrée contre [.onboarding/workflows/WORKFLOW_CONSULTATION_STOCK.md](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/.onboarding/workflows/WORKFLOW_CONSULTATION_STOCK.md:1), [.onboarding/workflows/WORKFLOW_FAISABILITE_COMMANDE.md](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/.onboarding/workflows/WORKFLOW_FAISABILITE_COMMANDE.md:1) et [.onboarding/workflows/WORKFLOW_PRELEVEMENT_COMMANDE.md](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/.onboarding/workflows/WORKFLOW_PRELEVEMENT_COMMANDE.md:1).
- Le constat "pas d'orchestrateur de commande" est bien prouvé par lecture de [inventory/orders.py](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/inventory/orders.py:1), qui n'expose que `can_fulfil()` et `picking_list()`.
- Après le correctif SHIAAAAAAAAAAAAAAAAAAAAAAAA-316, `picking_list()` vérifie la disponibilité via un dict cumulatif `allocated` pour gérer les lignes multiples du même SKU dans une commande ([inventory/orders.py:30-33](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/inventory/orders.py:30)). `can_fulfil()` et `picking_list()` sont maintenant complètement indépendantes, ce qui est une séparation intentionnelle.
- L'absence de mutation métier du stock est correctement démontrée à la lecture complète de [inventory/warehouse.py](/paperclip/instances/default/projects/be2f6065-a710-4a1d-8bb7-531efdbc6f23/4ec0dde5-c953-42bb-987a-33680bc426ea/shift-pilot-py/inventory/warehouse.py:1).
- La vérification de disponibilité intégrée à `picking_list()` (sans appel à `can_fulfil()`) est correctement documentée dans le workflow mis à jour et le test `test_plusieurs_lignes_meme_sku_depassement_exclu` en valide le cumul intra-commande.

## Recommandations de correction
- Aucune ; l'audit et les workflows sont maintenant cohérents avec le code après le correctif 316.
