# Guide de reprise du projet Power BI

État documenté le **14 octobre 2026**. Ce guide décrit les fichiers présents dans
le projet et les contrôles réalisés. Il ne vaut pas validation du rendu ni des
calculs exécutés dans Power BI Desktop.

## 1. Comprendre le projet

Le rapport suit les besoins associés aux appels d'offres, leur statut commercial
et le délai de réponse envoyée aux achats. Le délai cible est de **5 jours ouvrés**.

**Une ligne de Données représente un besoin.** Plusieurs besoins peuvent porter
le même DAH : ces répétitions sont normales et doivent rester comptées.
Les libellés historiques « consultations » ne changent pas ce grain de données.

Le projet utilise le format **PBIP**, avec un modèle sémantique en **TMDL** et des
pages/visuels en **PBIR**. Le rapport et le modèle doivent être transmis ensemble.

## 2. Démarrage pour la personne qui reprend

1. Lire ce guide et les éventuels `AGENTS.md` présents au moment de la reprise.
2. Faire une copie horodatée du projet complet dans un dossier voisin, hors du
   dossier actif. Vérifier la copie avant toute modification du modèle ou du rapport.
3. Ouvrir [Suivi_Appel_offre.pbip](../Suivi_Appel_offre.pbip) dans Power BI Desktop.
   La version Desktop observée lors des derniers contrôles était 2.158.1304.0.
4. Vérifier l'accès au site SharePoint avec le compte professionnel approprié.
5. Actualiser dans Desktop, puis contrôler le modèle et les pages. Les contrôles
   hors moteur décrits plus bas ne remplacent pas cette étape.

Si Desktop affiche un rapport vide après une erreur d'ouverture, fermer cette
instance **sans enregistrer le rapport vide**. Corriger la définition ou restaurer
une sauvegarde cohérente avant de rouvrir le PBIP.

## 3. Où trouver chaque élément

| Emplacement depuis la racine | Contenu / rôle |
| --- | --- |
| `Suivi_Appel_offre.pbip` | Point d'entrée du projet |
| `Suivi_Appel_offre.Report/definition.pbir` | Référence relative au modèle sémantique |
| `Suivi_Appel_offre.Report/definition/report.json` | Configuration générale et références aux thèmes |
| `Suivi_Appel_offre.Report/definition/pages/pages.json` | Ordre, page active et page d'accueil |
| `Suivi_Appel_offre.Report/definition/pages/<id>/page.json` | Nom, dimensions et propriétés d'une page |
| `Suivi_Appel_offre.Report/definition/pages/<id>/visuals/<id>/visual.json` | Champs, filtres et présentation d'un visuel |
| `Suivi_Appel_offre.Report/StaticResources` | Thèmes et ressources du rapport |
| `Suivi_Appel_offre.SemanticModel/definition` | Modèle TMDL, tables, relations et culture |
| `data/REPORTING_2026.xlsx` | Copie locale utilisée pour les contrôles hors moteur |
| `scripts/verifier_delais_reponse.py` | Vérifications Python, sans exécution DAX/M |
| `docs` | Documentation et diff de l'évolution des jours fériés |

Ne pas déplacer seulement le dossier Report : `definition.pbir` pointe vers
`../Suivi_Appel_offre.SemanticModel`.

## 4. Source réelle et préparation des données

La source du modèle est **le fichier Excel REPORTING_2026.xlsx sur SharePoint**,
dans le site `BPCEEquipetendue`, feuille **SUIVI**. L'adresse complète et le chemin
de référence sont dans la partition M de
[Données.tmdl](../Suivi_Appel_offre.SemanticModel/definition/tables/Données.tmdl).

La copie du dossier `data` n'alimente pas le modèle : elle sert aux vérifications
Python. Elle peut différer du fichier SharePoint actuel. Ne pas remplacer la
connexion SharePoint par cette copie pour résoudre un problème d'actualisation.

La requête M effectue notamment :

- Lecture du classeur et promotion/nettoyage des en-têtes.
- Contrôle des dates avant typage, avec conversion en culture `fr-FR`.
- Conservation des valeurs brutes et des états de contrôle.
- Typage des colonnes, puis filtre existant sur STATUT : exclusion de `null`,
  de la chaîne vide et de `Supprimé`.
- Nettoyage des textes d'entité, de lieu et de statut.
- Extraction de Fonction / Rôle à partir de POSTE.
- Ajout de l'index technique ID ligne besoin, sans déduplication.

L'ordre de ces étapes fait partie de l'implémentation actuelle. Ne pas modifier
le périmètre ou corriger les dates dans l'Excel sans décision métier explicite.

## 5. Modèle sémantique

| Table | Rôle |
| --- | --- |
| Données | Besoins importés, dimensions, audit des dates et colonnes de délai |
| _Mesures | Mesures de synthèse et mesures des délais |
| Calendrier ouvré France | Calendrier masqué commun au délai et à l'échéance |
| Dynamic Slicer | Paramètre de champs existant pour les visuels de synthèse |

Le calendrier des délais n'a **aucune relation** avec les autres tables.
Le modèle livré contient ces quatre tables. Les tables de dates automatiques,
leurs deux relations, les variations des colonnes et les métadonnées linguistiques
associées ont été retirées. Aucun visuel, filtre ou signet n'utilisait leur
hiérarchie : les dates explicites existantes sont conservées.
Le réglage enregistré est `__PBI_TimeIntelligenceEnabled = 0`.
Ne pas ajouter une relation au calendrier des délais sans analyser ses effets.

La culture du modèle et des requêtes est `fr-FR`. Les noms, `lineageTag` et
identifiants PBIR doivent être préservés lors d'une modification ciblée.

## 6. Règles des délais à conserver

- Départ : DATE D'EMISSION, ramenée à une date sans heure ; ce jour est exclu (J0).
- Fin : DATE DE REPONSE, réponse envoyée aux achats ; date incluse si elle est ouvrée.
- Jour ouvré : lundi à vendredi **et** non férié national français.
- Exclusion des 11 fêtes nationales : 1er janvier, lundi de Pâques, 1er mai,
  8 mai, Ascension, lundi de Pentecôte, 14 juillet, 15 août, 1er novembre,
  11 novembre et 25 décembre.
- Aucun report au lundi d'une fête tombant en week-end ; aucune double déduction.
- Particularités Alsace-Moselle et outre-mer, ponts et congés d'entreprise exclus
  du périmètre des jours non ouvrés.
- Même date valide : 0 jour.
- Délai ≤ 5 : Dans le délai ; délai > 5 : Hors délai.
- Échéance : cinquième jour ouvré strictement après l'émission.

Le calendrier est généré localement en DAX. Les fêtes mobiles utilisent le comput
grégorien de Pâques : + 1 jour, + 39 jours et + 50 jours. Il couvre les années des
dates importées valides et une année supplémentaire pour les échéances. Sans
date valide, il couvre l'année d'actualisation et la suivante.

### Dates absentes ou invalides

Une date absente ne vaut jamais zéro. Les valeurs impossibles ne sont pas
corrigées silencieusement : valeur brute et motif sont conservés, et la date
typée est null.

Le contrôle des années accepte actuellement **2000 à l'année UTC d'actualisation
+ 1**. Ce seuil préexistant reste à confirmer si le périmètre historique évolue.

| Situation | Qualification / traitement |
| --- | --- |
| Émission invalide ou absente, conversion impossible, année incohérente, réponse antérieure | Dates à vérifier ; délai BLANK, hors moyenne et taux |
| Émission valide et réponse absente | Sans date de réponse ; délai BLANK, hors moyenne et taux |
| Dates évaluables, délai de 0 à 5 | Dans le délai |
| Dates évaluables, délai supérieur à 5 | Hors délai |

Les anomalies ont priorité sur l'absence de réponse. Le compteur des lignes sans
date de réponse et celui des dates à vérifier peuvent donc se recouper.
Une émission valide suffit pour calculer l'échéance, même si la réponse est absente.

### Colonnes et mesures utiles

Dans Données : Date émission jour, Date réponse jour, Anomalie dates,
Délai réponse jours ouvrés, Échéance réponse et Qualification délai.
Les deux dates brutes, les deux états de contrôle et ID ligne besoin restent
disponibles dans le modèle.

Dans _Mesures, dossier Délais de réponse :

- Nb réponses évaluables.
- Délai moyen réponses évaluables.
- Nb réponses dans le délai.
- Nb réponses hors délai.
- % réponses dans le délai : dans le délai / évaluables.
- Nb lignes sans date de réponse.
- Nb lignes dates à vérifier.

La moyenne inclut les zéros valides et exclut les BLANK. Le taux et la moyenne
restent BLANK lorsqu'il n'y a aucune réponse évaluable. Le comptage reste un
comptage de lignes ; les filtres date, lieu et entité doivent affecter les mesures
de façon cohérente.

No Go signifie une décision de ne pas répondre favorablement au besoin. Une
absence de date de réponse ne prouve pas qu'un besoin est ouvert. **Les statuts
des besoins ouverts restent à confirmer** avant tout indicateur de retard.

## 7. Pages et navigation actuelles

| Page | Identifiant PBIR | État observé |
| --- | --- | --- |
| Synthèse Reporting | `796e866cbcd987abc828` | Masquée en mode lecture |
| Page 2 | `5745ae7983024da31b62` | Masquée en mode lecture |
| Synthèse Commerciale | `5b804ba8646b7816a59f` | Visible, page d'accueil |
| Détail des besoins | `9d01f4bf588b204a2bf9` | Visible |
| Délais de réponse | `d31a1500000000000001` | Visible |

Les noms ci-dessus proviennent des fichiers actuels ; l'ordre est défini dans
pages.json. Préserver les identifiants pour conserver les références de navigation.
Ne pas supprimer les pages masquées, boutons ou signets comme s'ils étaient inutiles.

La page Délais de réponse comporte les segments date d'émission, lieu et entité,
les cartes de performance, les compteurs de qualité et le graphique à 100 %.
Le graphique « Respect du délai de 5 jours par lieu » affiche seulement les lieux
ayant des réponses évaluables, via un filtre **au niveau du visuel** : évaluables > 0.
Bleu = Dans le délai ; orange = Hors délai ; pourcentages à une décimale.
Les infobulles contiennent les nombres évaluables, dans et hors délai, ainsi que le taux.

Dans les tableaux, garder l'identifiant technique s'il est nécessaire pour
empêcher le regroupement de besoins identiques. Il peut apparaître discrètement
sous N°. Cet index peut changer à l'actualisation ; ce n'est pas une clé métier
durable. Les dates brutes peuvent être retirées du visuel, tout en restant dans
le modèle. Le motif de contrôle des dates doit rester accessible.

La mention affichée sur les pages concernées est :

> Jours ouvrés : hors week-ends et jours fériés nationaux français. Jour d’émission exclu.

## 8. Contrôles reproductibles

Depuis la racine du projet, avec Python (version 3.12 utilisée lors des contrôles) :

```powershell
python -B scripts/verifier_delais_reponse.py
```

Le script utilise la bibliothèque standard et lit l'Excel local en lecture seule.
L'option `-B` évite la création de fichiers Python de cache. Un rapport JSON peut
être écrit avec l'option `--output`, dans un emplacement choisi.

Il contrôle les références de champs, certaines structures PBIR/TMDL, la règle
de calcul par une référence Python et les invariants avant/après jours fériés.
Le comput lu dans le TMDL est comparé à une méthode indépendante sur 500 années.
**Il n'exécute ni le DAX, ni Power Query, ni le rendu du rapport.**

Cas à conserver pour toute évolution :

| Cas | Attendu |
| --- | --- |
| 03/04/2026 → 07/04/2026 | 1 jour |
| Émission 03/04/2026 | Échéance 13/04/2026 |
| 30/04/2026 → 04/05/2026 | 1 jour |
| 13/07/2026 → 15/07/2026 | 1 jour |
| Émission 13/07/2026 | Échéance 21/07/2026 |
| 14/08/2026 → 17/08/2026 | 1 jour, aucun report du 15 août |
| 24/12/2026 → 04/01/2027 | 5 jours, conforme ; échéance 04/01/2027 |
| Même date valide | 0 jour |
| Date absente ou réponse antérieure | Non évaluable |

Le détail des contrôles est dans [Delais_de_reponse.md](Delais_de_reponse.md).
Le [diff des jours fériés](Delais_jours_feries.diff) est une trace historique :
il n'est pas à réappliquer sur le projet actuel.

Pour contrôler les quatre tables finales, les références des champs et la
navigation, lancer également :

```powershell
python -B scripts/verifier_structure_rapport.py
```

L'option `--backup` permet une comparaison en lecture seule avec une sauvegarde
complète. Les différences éventuelles des fichiers locaux sont signalées,
sans être corrigées ou réécrites par le script.

## 9. État de validation et travail restant

Les contrôles du 14 octobre 2026 ont réussi hors moteur : cas métier, 10 955 cas
complémentaires de délai, comput sur 500 années et 576 combinaisons de filtres.
Le sérialiseur Microsoft TMDL fourni avec Desktop a réellement lu le modèle
final à quatre tables sans erreur. Cette lecture valide la syntaxe des
métadonnées, pas l'exécution DAX.

Sur la copie Excel locale de contrôle : 117 lignes, 48 réponses évaluables,
35 dans le délai, 13 hors délai, 66 sans date de réponse et 3 dates à vérifier.
Ces nombres sont un **instantané de référence**, pas des valeurs attendues après
toute future actualisation SharePoint.

À confirmer dans Desktop avant de considérer le rapport comme validé :

1. Ouverture du PBIP, actualisation SharePoint et compilation/exécution DAX/M.
2. Résultats des cas métier, calendrier masqué et changements d'année.
3. Conservation des besoins répétés et exclusion des dates non évaluables du taux/moyenne.
4. Segments, filtre du graphique, infobulles, boutons et navigation.
5. Rendu en Ajuster à la page, décimales et lisibilité des mentions/tableaux.

À la date de ce guide, aucune exécution DAX/M ni validation visuelle dans Desktop
n'a été réalisée pendant les interventions documentées.

Lors de la finalisation, le signet Reset_Synthese conservait une cible technique
vers un ancien visuel absent, tandis que ses états de visuels enregistrés
correspondent aux visuels actuels. Les signets ont été préservés : vérifier
l'effet réel de Réinitialiser dans Desktop sur les trois pages. Le bouton de
réinitialisation du détail utilise le signet Reset_Delais ; contrôler également
qu'il réinitialise les segments souhaités sur cette page.

## 10. Modifier et transmettre le projet sans perdre l'existant

- Sauvegarder et vérifier le projet complet avant les changements fonctionnels.
- Éviter une modification simultanée des fichiers et de la même instance Desktop :
  une sauvegarde Desktop pourrait écraser les modifications externes.
- Adapter les objets existants, leurs noms et conventions ; ne pas reconstruire
  les pages ou le modèle pour une évolution ciblée.
- Ne pas modifier les caches, paramètres locaux, connexion SharePoint ou Excel source.
- Après un changement des jours ouvrés, modifier le calendrier commun et contrôler
  à la fois délai et échéance ; ne pas créer deux définitions concurrentes.
- Comparer sur les mêmes données : lignes/évaluables inchangés ; lors de l'ajout
  de jours exclus, aucun délai ne doit augmenter, aucune échéance avancer et
  aucun besoin conforme devenir hors délai.
- Mettre à jour la documentation, les mentions visibles et les contrôles concernés.
- Transmettre le PBIP et ses deux dossiers, la documentation et le script.

La sauvegarde de référence des jours fériés se trouve dans le dossier voisin
`Suivi_Appel_offre_Ruth_sauvegarde_20261014_171617` : ses 91 fichiers ont été
vérifiés par SHA-256. Pour revenir en arrière, privilégier une copie complète
cohérente et conserver le projet courant pour comparaison ; ne pas mélanger des
tables, pages et références issus de versions différentes.

La sauvegarde préalable à la livraison est
`Suivi_Appel_offre_Ruth_sauvegarde_20261014_175510` : 94 fichiers vérifiés par
SHA-256. Lors du contrôle de livraison du 14 octobre 2026, le dossier n'était
pas un dépôt Git ; les fichiers avaient été comparés à cette sauvegarde.
Le dépôt local a été initialisé le 20 octobre 2026 sur la branche main.

Le [guide d'utilisation pour Ruth](Guide_utilisation_Ruth.md) présente les trois
pages, les filtres, la navigation et l'actualisation en langage utilisateur.
Le [contrôle de livraison](Verification_livraison.md) recense les modifications,
les contrôles réalisés et les points restant à valider dans Desktop.

Le `.gitignore` exclut les dossiers `.pbi` (paramètres et caches locaux) ainsi
que les fichiers de cache et environnements locaux Python.
Cela ne garantit pas à lui seul que toutes les autres informations locales sont
exclues d'une transmission : vérifier son contenu avant un partage ou un dépôt.

### Erreur TMDL déjà rencontrée

L'erreur `UnknownKeyword : description` provenait de lignes `description:` sous
des colonnes. La correction consiste à placer une description `///` immédiatement
au-dessus de la déclaration, avec la même indentation :

```tmdl
	/// Description de la colonne.
	column 'Nom de colonne'
		dataType: string
```

Cette correction est déjà appliquée dans le projet. Ne pas réintroduire la
propriété `description:` à cet emplacement.

## 11. Points à faire confirmer par le métier

- Quels statuts représentent réellement les besoins ouverts ?
- La plage de contrôle des années convient-elle à l'historique futur ?
- Quel est le circuit de correction des dates signalées dans l'Excel source ?
- Qui valide le rapport dans Desktop, puis son éventuelle diffusion ?

Ces décisions ne doivent pas être déduites silencieusement des données actuelles.
