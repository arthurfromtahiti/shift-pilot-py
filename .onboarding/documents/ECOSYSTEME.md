# ECOSYSTEME — T-PORTE1b (Shift Pilot multi-stack)

> **Confiance** : medium (dépendances inter-workspaces non trouvées dans le périmètre de vérification explicité ci-après)
>
> Synthèse transverse du projet T-PORTE1b : description des deux workspaces `shift-pilot-cli` (Node.js) et `shift-pilot-py` (Python 3), leurs rôles documentés et l'absence d'intégration observée dans les artefacts consultés.
> 
> **Portée du document** :
> - Rôles locaux de chaque workspace, issus de leurs documents de référence (PROJECT_CONTEXT, CDC, CARTOGRAPHIE).
> - Dépendances inter-workspaces : absence de preuve d'intégration directe dans les surfaces consultées (CDC, CARTOGRAPHIE, PROJECT_CONTEXT, documents d'audit).
> - Différences de patterns d'exposition observées entre les deux workspaces.
> - Questions et incertitudes qui justifient un réinspection si l'intégration est envisagée.
> - **Non inclus** : audit exhaustif du code source ou des fichiers partagés au-delà du périmètre documentaire.

---

## Workspaces et rôles documentés

### shift-pilot-cli (Node.js 18+)

**Rôle déclaré** : Banc d'essai pour la chaîne d'intégration SHIFT/Paperclip.  
**Domaines** (d'après `CDC_FONCTIONNEL.md`) : calcul statistique (moyenne, médiane) ; orchestration CLI.  
**Entrée/Sortie** : fichier texte (un nombre par ligne) → stdout (`n=<compte> moyenne=<valeur> mediane=<valeur>`).  
**Exposition réseau** : aucune (outil CLI sans serveur HTTP).

**Référence source** : `shift-pilot-cli/.onboarding/documents/PROJECT_CONTEXT.md`, section « Nature du projet » et « Périmètre ».

### shift-pilot-py (Python 3, stdlib)

**Rôle déclaré** : Pilote pédagogique démontrant la logistique d'entrepôt (exemple multi-stack non-JavaScript).  
**Domaines** (d'après `CDC_FONCTIONNEL.md`) : gestion du stock en entrepôt ; vérification et préparation de commande.  
**Entrée/Sortie** : appels de fonctions Python → structures Python natives (dicts, listes).  
**Exposition réseau** : aucune ; pas de CLI. Module Python pur, données en mémoire.

**Référence source** : `shift-pilot-py/.onboarding/documents/PROJECT_CONTEXT.md`, sections « Résumé exécutif » et « Stack technique ».

---

## Dépendances inter-workspaces : absence de preuve dans le périmètre consulté

**Synthèse** : Aucune dépendance inter-workspace n'est mentionnée dans les sections d'orchestration, de domaines métier, et de parcours transactionnels des documents d'onboarding consultés. Le périmètre de cette vérification est délimité précisément pour chaque workspace et type de document.

### Périmètre de vérification consulté

**Documents inspectés** :
- `shift-pilot-cli/.onboarding/documents/` : PROJECT_CONTEXT.md, CDC_FONCTIONNEL.md, CARTOGRAPHIE_CODE.md, CAHIER_RECETTE.md, audits FUNCTIONAL/ARCHITECTURE/SECURITY/CODE_HOTSPOTS/DATA_MODEL/TESTING.
- `shift-pilot-py/.onboarding/documents/` : PROJECT_CONTEXT.md, CDC_FONCTIONNEL.md, CARTOGRAPHIE_CODE.md, CAHIER_RECETTE.md, audits FUNCTIONAL/ARCHITECTURE/DATA_MODEL/TESTING.

**Résultats du périmètre consulté** :

**shift-pilot-cli** — Domaines et parcours :
- `shift-pilot-cli/.onboarding/documents/CDC_FONCTIONNEL.md` § « Domaines métier » énumère deux domaines locaux : `calcul-statistique`, `application-cli`.
- `shift-pilot-cli/.onboarding/documents/CDC_FONCTIONNEL.md` § « Parcours golden path » décrit un seul parcours transactionnel : fichier valide → parsing numérique → calcul statistique → stdout. Aucune mention de shift-pilot-py ni d'orchestration transverse.
- `shift-pilot-cli/.onboarding/documents/CARTOGRAPHIE_CODE.md` § « Structure des fichiers » énumère 6 fichiers locaux (bin/, src/, test/). Aucune référence croisée vers shift-pilot-py.

**shift-pilot-py** — Domaines et parcours :
- `shift-pilot-py/.onboarding/documents/CDC_FONCTIONNEL.md` § « Domaines métier » énumère deux domaines locaux : `entrepôt-stock`, `préparation-commande`.
- `shift-pilot-py/.onboarding/documents/CDC_FONCTIONNEL.md` § « Parcours principaux » décrit trois flux transactionnels fermés : consultation stock, vérification faisabilité commande, génération prélèvement. Aucune mention de shift-pilot-cli ni d'orchestration transverse.
- `shift-pilot-py/.onboarding/documents/CARTOGRAPHIE_CODE.md` § « Structure du code » énumère 4 modules locaux (inventory/, orders/). Aucune référence croisée vers shift-pilot-cli.

**Exposition et interfaces** :
- **shift-pilot-cli** : `shift-pilot-cli/.onboarding/documents/PROJECT_CONTEXT.md` § « Périmètre » énonce clairement que l'outil n'expose pas d'API REST (constat fondé : CLI autonome sans serveur réseau).
- **shift-pilot-py** : `shift-pilot-py/.onboarding/documents/PROJECT_CONTEXT.md` § « Stack technique » énonce que le module n'expose aucune API (REST, gRPC) ni CLI (constat fondé : module Python pur, invocation par import local).

### Limites explicites du périmètre

**Cette vérification se limite à** :
- Lectures des documents d'onboarding listés ci-avant (PROJECT_CONTEXT, CDC_FONCTIONNEL, CARTOGRAPHIE_CODE, CAHIER_RECETTE, audits).

**Non inclus** :
- Grep du code source complet (recherche multi-workspace de `import shift-pilot-py`, `subprocess.call`, hostname, URL d'API, ou chaînes de dépendance).
- Inspection de fichiers potentiellement partagés au niveau du dépôt git (`.gitignore`, variables d'environnement, configuration shared, données de test partagées).
- Traces de workflows d'orchestration transverses (queues, événements, webhooks, cron jobs, communications réseau).

**Conséquence** : Une dépendance cachée au niveau du code source, des fichiers partagés, ou de l'infrastructure ne peut être exclue au-delà du périmètre documentaire consultés. Si l'intégration est envisagée, une inspection exhaustive est recommandée.

### Différences de patterns d'exposition observées

| Aspect | shift-pilot-cli | shift-pilot-py | Source |
|--------|---|---|---|
| **Invocation** | Processus CLI (`node bin/index.js`) | Import Python + appel de fonction | PROJECT_CONTEXT.md chaque workspace |
| **Entrée** | Argument : chemin fichier | Argument de fonction | CDC_FONCTIONNEL.md chaque workspace |
| **Sortie** | Texte sur stdout : `n=<compte> moyenne=<valeur> mediane=<valeur>` | Structures Python natives : dicts, listes | PROJECT_CONTEXT.md, CDC_FONCTIONNEL.md |
| **Gestion d'erreur** | Exit code + stderr | Exceptions Python | PROJECT_CONTEXT.md chaque workspace |
| **État** | Aucun (processus terminé après invocation) | En mémoire (session Python persistante) | PROJECT_CONTEXT.md chaque workspace |

**Observation** : Les interfaces d'invocation diffèrent (processus externe vs. import local). 

**HYPOTHÈSE** (point de conception non résolu) : Une intégration directe entre les deux impliquerait soit une orchestration par subprocess, soit un wrapper Python autour du CLI — ces options ne sont pas validées par un flux réel et restent des extrapolations architecturales.

Références : `PROJECT_CONTEXT.md` et `CDC_FONCTIONNEL.md` de chaque workspace.

---

## Domaines métier par workspace (workflows séparés et fermés)

**shift-pilot-cli** : 
- Domaines : `calcul-statistique`, `application-cli` (lecture fichier → parsing → calcul → sortie texte).
- Référence source : `shift-pilot-cli/.onboarding/documents/CDC_FONCTIONNEL.md` § « Domaines métier ».

**shift-pilot-py** :
- Domaines : `entrepôt-stock`, `préparation-commande` (consultation faisabilité commande, allocation stock, liste de prélèvement).
- Référence source : `shift-pilot-py/.onboarding/documents/CDC_FONCTIONNEL.md` § « Domaines métier ».

**Observation** : 
- `shift-pilot-cli/.onboarding/documents/CDC_FONCTIONNEL.md` § « Parcours golden path » décrit un workflow fermé transactionnel (fichier valide → calcul → stdout), sans mention de shift-pilot-py.
- `shift-pilot-py/.onboarding/documents/CDC_FONCTIONNEL.md` § « Parcours principaux » décrit trois workflows fermés transactionnels (stock, faisabilité, prélèvement), sans mention de shift-pilot-cli.
- Aucun flux documenté ne relie les deux workspaces au sein de leurs CDC respectifs.

---

## Interfaces détaillées

### shift-pilot-cli

**Contrat d'invocation** (d'après `CDC_FONCTIONNEL.md`) :
- **Entrée** : argument CLI contenant chemin fichier ; fichier texte avec un nombre par ligne (UTF-8).
- **Sortie** : une seule ligne sur stdout : `n=<compte> moyenne=<valeur> mediane=<valeur>`.
- **Gestion d'erreur** : message sur stderr, exit code 1.
- **État** : sans état (chaque invocation traite et termine).
- **Runtime** : Node.js ≥ 18.

**Référence** : `shift-pilot-cli/.onboarding/documents/PROJECT_CONTEXT.md` § Périmètre, CDC_FONCTIONNEL.md § Parcours 1.

### shift-pilot-py

**Contrat d'invocation** (d'après `CDC_FONCTIONNEL.md`) :
- **Entrée** : appels de fonction Python (ex. `Warehouse.can_fulfil(order)`, `Warehouse.picking_list(order)`).
- **Sortie** : structures Python natives (booléens, dicts, listes de dicts).
- **Gestion d'erreur** : exceptions Python (pas de serveur réseau, pas de timeout externe).
- **État** : en mémoire (données stock résident pour la session Python courante).
- **Runtime** : interpréteur Python 3, session persistante.

**Référence** : `shift-pilot-py/.onboarding/documents/PROJECT_CONTEXT.md` § Stack technique, CDC_FONCTIONNEL.md.

### Compatibilité transverse

Les patterns d'invocation et de sérialisation diffèrent : subprocess vs. import local, texte vs. structures Python en mémoire. Une intégration impliquerait une couche d'adaptation explicite (ex. subprocess Python appelant le CLI, ou wrapper CLI autour du module Python).

---

## Absence de contrat inter-workspace documenté

**shift-pilot-cli** :
- `shift-pilot-cli/.onboarding/documents/PROJECT_CONTEXT.md` § « Périmètre » énonce que l'outil n'expose pas d'API REST (fondement : CLI autonome sans serveur réseau).
- `shift-pilot-cli/.onboarding/documents/CDC_FONCTIONNEL.md` § « Parcours golden path » décrit une sortie texte libre sur stdout, sans mention d'orchestration transverse.
- `shift-pilot-cli/.onboarding/documents/CDC_FONCTIONNEL.md` § « Parcours golden path » énumère un flux transactionnel fermé (fichier valide → calcul → stdout), sans consommation de données d'un autre workspace.

**shift-pilot-py** :
- `shift-pilot-py/.onboarding/documents/PROJECT_CONTEXT.md` § « Stack technique » énonce que le module n'expose aucune API (fondement : module Python pur, pas de serveur HTTP/gRPC).
- `shift-pilot-py/.onboarding/documents/CDC_FONCTIONNEL.md` décrit des structures Python en mémoire (dicts, listes) comme sortie d'invocation, sans mention d'harmonisation avec d'autres workspaces.
- `shift-pilot-py/.onboarding/documents/CDC_FONCTIONNEL.md` § « Parcours principaux » énumère trois flux transactionnels fermés (stock, faisabilité, prélèvement), sans consommation de données d'un autre workspace.

**Absence de protocole d'harmonisation** :
- Aucun schéma d'échange ou protocole ne relie les formats de sortie (texte CLI vs. structures Python en mémoire) dans les sections pertinentes des CDC_FONCTIONNEL.md ou PROJECT_CONTEXT.md respectifs.

**Absence de mécanismes d'intégration documentés** :
- `shift-pilot-cli/.onboarding/documents/CARTOGRAPHIE_CODE.md` § « Dépendances externes » n'énumère aucune queue, webhook, ou bus d'événement.
- `shift-pilot-py/.onboarding/documents/CARTOGRAPHIE_CODE.md` § « Dépendances externes » n'énumère aucune queue, webhook, ou bus d'événement.
- *Limite du périmètre* : cette vérification porte sur les listes de dépendances externes documentées, pas sur une inspection exhaustive du code ou de l'infrastructure.

---

## Questions et hypothèses non résolues

### 1. Intégration future : absence de plan documenté

**Observation** : Aucun plan d'intégration n'est documenté entre les deux workspaces.

**Données amont** :
- `shift-pilot-cli/.onboarding/documents/PROJECT_CONTEXT.md` § « Résumé exécutif » décrit ce workspace comme un « banc d'essai pour la chaîne SHIFT/Paperclip ».
- `shift-pilot-py/.onboarding/documents/PROJECT_CONTEXT.md` § « Résumé exécutif » décrit ce workspace comme un « pilote pédagogique » démontrant la logistique d'entrepôt.
- Aucune relation ou orchestration commune n'est mentionnée au sein des PROJECT_CONTEXT.md § Résumé exécutif, CDC_FONCTIONNEL.md § Domaines métier / Parcours, ou CARTOGRAPHIE_CODE.md § Structure fichiers/modules consultés.
- `shift-pilot-cli/.onboarding/documents/PROJECT_CONTEXT.md` § « Questions ouvertes » énumère des pistes d'évolution (extensibilité CLI) sans mention de shift-pilot-py.
- `shift-pilot-py/.onboarding/documents/PROJECT_CONTEXT.md` § « Questions ouvertes » énumère des pistes d'évolution (orchestrateur) sans mention de shift-pilot-cli.

**Constat documentaire** : Sur la base du périmètre consulté, aucun document ne décrit une relation, un flux orchestré, ou un contrat partagé entre les deux workspaces. Cette absence est distincte d'une propriété d'« indépendance » — elle énonce simplement que le matériel consulté ne relève aucune liaison.

**Question ouverte** : T-PORTE1b envisage-t-il une intégration transverse, ou restera-t-il deux workspaces fermés ?

**Impact si intégration future** : Ce document ECOSYSTEME.md devra être révisé pour décrire les contrats transverses réels et les points de friction (formats, gestion d'erreur, orchestration) découverts lors d'une inspection plus exhaustive.

### 2. Périmètre de vérification des dépendances

**Limitation du périmètre consulté** : la vérification d'absence de dépendance s'appuie sur les documents d'onboarding (contexte, CDC, cartographie) ; un audit exhaustif du code source (grep multi-workspace, inspection de fichiers partagés, traces de communication runtime) n'a pas été réalisé.

**Conséquence** : Une dépendance pourrait exister au-delà du périmètre documentaire. Si l'intégration est envisagée, une inspection plus exhaustive est recommandée.

### 3. Exposition future de shift-pilot-py

**Observation** : shift-pilot-py n'expose actuellement aucune API (HTTP, gRPC, CLI).

**Données amont** : Le PROJECT_CONTEXT.md (shift-pilot-py) énumère comme « piste d'évolution non décidée » la création d'une « couche d'exposition (API Flask/FastAPI, CLI Python wrapper) ».

Référence : PROJECT_CONTEXT.md (shift-pilot-py), section « Questions ouvertes récurrentes ».

**Question ouverte** : Une couche d'exposition sera-t-elle créée pour shift-pilot-py ? Si oui, cela modifierait les patterns d'intégration possibles.

---

## Risques d'intégration identifiés (HYPOTHÈSE — non validés par flux réel)

**HYPOTHÈSE** : Si une intégration transverse était envisagée ultérieurement, les éléments suivants pourraient constituer des points de friction. Cette analyse est une extrapolation — non validée par une intégration réelle :

| Point | Description | Source |
|-------|-------------|--------|
| **Incompatibilité de transport** | Invocation par processus (CLI) vs. import local (Python) : à concevoir (adapter via subprocess ou wrapper). | Interfaces observées aux sections précédentes |
| **Différence de sérialisation** | Texte libre (stdout) vs. structures Python en mémoire : harmonisation à concevoir. | `CDC_FONCTIONNEL.md` de chaque workspace |
| **Gestion d'erreur disparate** | Exit codes (CLI) vs. exceptions Python (module) : contrat d'erreur transverse à concevoir. | `PROJECT_CONTEXT.md` de chaque workspace |
| **État et persistance** | Processus sans état vs. session Python avec état mémoire : implications pour réutilisation de données à concevoir. | `PROJECT_CONTEXT.md` de chaque workspace |
| **Absence de test d'intégration** | Aucun scénario de test ne valide une chaîne CLI → Python dans le périmètre consulté. | `CDC_FONCTIONNEL.md`, `CAHIER_RECETTE.md` de chaque workspace |

**Remarque** : Cette liste énumère les points de friction observables dans l'absence de contrat documenté ; un réinspection plus exhaustive (grep multi-workspace, audit des fichiers partagés) et un test d'intégration réel découvriraient d'autres enjeux non anticipés ici.

---

## Documents de référence : accès par workspace

### shift-pilot-cli — `.onboarding/documents/`

**Présentation générale** :
- `PROJECT_CONTEXT.md` — rôle (banc d'essai SHIFT/Paperclip), domaines (calcul statistique, CLI), points d'attention (débordement numérique, divergence terminologique CSV).

**Spécification fonctionnelle** :
- `CDC_FONCTIONNEL.md` — parcours golden path (fichier valide → calcul → stdout), cas d'erreur, règles de validation.

**Code** :
- `CARTOGRAPHIE_CODE.md` — structure fichiers (bin/, src/, test/), zones critiques, dépendances externes.

**Test** :
- `CAHIER_RECETTE.md` — scénarios de recette manuelle et automatisée.

**Audits** : FUNCTIONAL_AUDIT, ARCHITECTURE_AUDIT, SECURITY_ROBUSTNESS_AUDIT, CODE_HOTSPOTS_AUDIT, DATA_MODEL_AUDIT, TESTING_AUDIT (en `.onboarding/audits/`).

### shift-pilot-py — `.onboarding/documents/`

**Présentation générale** :
- `PROJECT_CONTEXT.md` — rôle (pilote pédagogique logistique d'entrepôt), domaines (stock, préparation de commande), points d'attention (pas d'API/CLI exposée, unicité SKU).

**Spécification fonctionnelle** :
- `CDC_FONCTIONNEL.md` — parcours : consultation stock, vérification faisabilité commande, génération prélèvement. Règles d'allocation et disponibilité.

**Code** :
- `CARTOGRAPHIE_CODE.md` — structure Python (inventory/warehouse.py, orders.py), fonctions exposées, dépendances externes.

**Test** :
- `CAHIER_RECETTE.md` — scénarios : stock nominal, surallocation, pénuries, commandes multi-zones.

**Audits** : FUNCTIONAL_AUDIT, ARCHITECTURE_AUDIT, DATA_MODEL_AUDIT, TESTING_AUDIT (en `.onboarding/audits/`).

---

## Synthèse et niveaux de confiance

| Aspect | Niveau | Raison et limite |
|--------|--------|----------|
| **Rôles locaux (chaque workspace)** | high | PROJECT_CONTEXT.md de chaque workspace énonce clairement son domaine et son rôle. |
| **Absence d'intégration (périmètre documentaire)** | medium | Aucune dépendance croisée n'est mentionnée dans PROJECT_CONTEXT, CDC, CARTOGRAPHIE de chaque workspace. *Limite* : périmètre limité aux documents d'onboarding ; audit exhaustif du code source non réalisé. |
| **Interfaces et patterns observés** | high | Les CDC et PROJECT_CONTEXT décrivent avec précision les modèles d'invocation (CLI vs. import) et de sérialisation (texte vs. structures Python). |
| **Absence de contrat transverse** | high | Aucun projet, workflow ou test documenté ne définit une interaction inter-workspace. |
| **Risques d'intégration future** | medium | Les points de friction (transport, sérialisation, gestion d'erreur, état) sont identifiables mais non validés par expérience réelle. |

### Conclusion : traçabilité des absences documentées

**Constat strictement documentaire** : Sur la base du périmètre consulté (voir section « Périmètre de vérification »), les sections suivantes ne mentionnent aucune relation, orchestration, ou dépendance inter-workspace :

| Workspace | Fichier | Section | Constat |
|-----------|---------|---------|---------|
| **shift-pilot-cli** | PROJECT_CONTEXT.md | Résumé exécutif | Rôle déclaré : banc d'essai SHIFT/Paperclip ; aucune mention de shift-pilot-py. |
| **shift-pilot-cli** | PROJECT_CONTEXT.md | Périmètre | Exposition : CLI autonome, pas d'API REST ; aucune dépendance transverse. |
| **shift-pilot-cli** | CDC_FONCTIONNEL.md | Domaines métier | Énumération : calcul-statistique, application-cli (locaux). |
| **shift-pilot-cli** | CDC_FONCTIONNEL.md | Parcours golden path | Flux fermé : fichier → parsing → calcul → stdout ; sans orchestration transverse. |
| **shift-pilot-cli** | CARTOGRAPHIE_CODE.md | Structure des fichiers | 6 fichiers locaux ; aucune référence croisée vers shift-pilot-py. |
| **shift-pilot-py** | PROJECT_CONTEXT.md | Résumé exécutif | Rôle déclaré : pilote pédagogique logistique d'entrepôt ; aucune mention de shift-pilot-cli. |
| **shift-pilot-py** | PROJECT_CONTEXT.md | Stack technique | Exposition : module Python pur, pas d'API (REST, gRPC) ni CLI ; aucune dépendance transverse. |
| **shift-pilot-py** | CDC_FONCTIONNEL.md | Domaines métier | Énumération : entrepôt-stock, préparation-commande (locaux). |
| **shift-pilot-py** | CDC_FONCTIONNEL.md | Parcours principaux | Trois flux fermés (stock, faisabilité, prélèvement) ; sans orchestration transverse. |
| **shift-pilot-py** | CARTOGRAPHIE_CODE.md | Structure du code | 4 modules locaux ; aucune référence croisée vers shift-pilot-cli. |

Chaque workspace énumère ses domaines, rôles, et interfaces de manière fermée, sans mention croisée de l'autre, dans les sections clés consultées.

**Limites explicites de cette analyse** :
- **Périmètre consulté** : documents d'onboarding uniquement (PROJECT_CONTEXT.md, CDC_FONCTIONNEL.md, CARTOGRAPHIE_CODE.md, audits). 
- **Non inclus** : audit exhaustif du code source (grep multi-workspace), inspection de fichiers partagés au niveau du dépôt git (`.gitignore`, variables d'environnement, config shared), traces de communication runtime ou d'infrastructure d'orchestration (queues, webhooks, workflows transverses).
- **Conséquence** : Une dépendance cachée (au niveau du code source, des fichiers partagés, ou de l'infrastructure) ne peut être exclue au-delà du périmètre documentaire consulté.

**Si intégration ultérieure envisagée** : Une réinspection plus exhaustive (grep multi-workspace pour imports/calls, audit des fichiers partagés `.gitignore`/`.env`/config, traces de workflows d'orchestration) est recommandée avant de concevoir les contrats transverses. Ce document ECOSYSTEME.md devra être révisé pour documenter les flux et les points de friction réels découverts.

---

---

## Validité et mise à jour

**Date de production** : 2026-08-09

**SHAs de code inspectés** :
- **shift-pilot-cli** : `55a63bb` (fix: gestion d'erreur et validation d'entrée complètes)
- **shift-pilot-py** : `bbe524c` (fix: normaliser la clé allocated)

**Artefacts consultés** : 
- Chaque workspace : PROJECT_CONTEXT.md, CDC_FONCTIONNEL.md, CARTOGRAPHIE_CODE.md, CAHIER_RECETTE.md, audits FUNCTIONAL/ARCHITECTURE/DATA_MODEL/TESTING.
- Pas d'audit exhaustif du code source, des fichiers partagés, ou des configurations d'infrastructure.

**Révision recommandée si** :
1. Une dépendance inter-workspace est découverte ultérieurement.
2. Une couche d'exposition (API, CLI) est ajoutée à shift-pilot-py.
3. Une orchestration transverse (workflow, intégration) est décidée pour T-PORTE1b.
4. Les domaines métier de chaque workspace évoluent.

**Rédacteur — Étape 4, synthèse transverse**  
2026-08-09 (révisé suite à relecture SHIAAAAAAAAAAAAAAAAAAAAAAAA-555)

