# Suivi des délais de réponse

Les calculs excluent les week-ends et les **11 jours fériés nationaux français**,
avec un calendrier commun. La structure des pages, les noms de colonnes et
mesures, SharePoint et les besoins répétés sont conservés.

## Sauvegarde préalable

Projet complet copié hors du dossier actif avant modification :
`../Suivi_Appel_offre_Ruth_sauvegarde_20261014_171617`.
Les 91 fichiers ont été vérifiés par SHA-256 avant modification. Aucun AGENTS.md
n'a été trouvé dans le workspace ou ses répertoires parents contrôlés.

## Règles

- Départ : DATE D'EMISSION sans heure, jour d'émission exclu (J0).
- Fin : DATE DE REPONSE sans heure, incluse uniquement si ouvrée.
- Jour ouvré : lundi à vendredi et non férié national français.
- Même date valide : 0, même si ce jour est férié ou en week-end.
- De 0 à 5 jours : Dans le délai ; au-delà : Hors délai.
- Échéance : cinquième jour ouvré strictement après l'émission.
- Aucun report au lundi d'un férié tombant le week-end.
- Aucune exclusion des ponts, congés d'entreprise ou fêtes propres à
  l'Alsace-Moselle et à l'outre-mer.

Les règles existantes de qualité des dates sont préservées : émission absente ou
non valide, conversion impossible, année incohérente ou réponse antérieure donnent
Dates à vérifier. Une réponse absente avec émission valide donne Sans date de
réponse. Ces lignes sont exclues du taux et de la moyenne.

Le contrôle M des années reste **2000 à l'année UTC d'actualisation + 1**.
Le calendrier ne modifie pas ce seuil préexistant. Valeurs brutes et motifs sont
conservés ; une année 206 n'est jamais corrigée silencieusement en 2026.
Les anomalies ont priorité sur l'absence de réponse. Le compteur de réponses
absentes peut donc recouper celui des dates à vérifier.

Une absence de réponse ne désigne pas automatiquement un besoin ouvert. Aucun
indicateur de retard de besoin ouvert n'est créé. No Go reste une décision de ne
pas répondre favorablement ; ce statut ne prouve pas une réponse envoyée aux achats.

## Calendrier centralisé

`Calendrier ouvré France` est une table calculée DAX masquée, **sans relation**.
Elle contient une date unique par jour, les colonnes Férié national, Fête
nationale et Est jour ouvré. Les deux calculs utilisent ce dernier drapeau.

Les bornes utilisent uniquement les dates importées déjà contrôlées, sans
dépendre du délai ou de l'échéance :

- Début : 1er janvier de la plus ancienne année valide, émission ou réponse.
- Fin : 31 décembre de l'année suivant la plus récente année valide.
- Source vide ou sans date valide : année d'actualisation et année suivante.

Ce calendrier couvre les changements d'année et les échéances au-delà de la
dernière émission. Il n'est pas limité à 2026. Aucune API n'est appelée à
l'actualisation pour générer les jours fériés.

Pâques suit le comput grégorien Meeus/Jones/Butcher. Les fêtes mobiles sont
Pâques + 1, + 39 et + 50. Les huit fêtes fixes complètent les 11 fêtes nationales.
Deux fêtes peuvent coïncider : leurs libellés sont conservés, mais une date
n'est exclue qu'une fois.

## Calculs adaptés

| Objet existant | Adaptation |
| --- | --- |
| Date émission jour / Date réponse jour | Inchangées, sans heure |
| Anomalie dates | Inchangée |
| Délai réponse jours ouvrés | Nombre de jours du calendrier avec Est jour ouvré, strictement après émission et jusqu'à réponse incluse |
| Échéance réponse | Date maximale parmi les cinq premières dates ouvrées après émission |
| Qualification délai | Inchangée ; dépend du nouveau délai |
| Les sept mesures Délais de réponse | Expressions inchangées ; agrègent les colonnes existantes |

Le délai vaut zéro si les dates sont évaluables et aucun jour ouvré n'est compté ;
sinon BLANK si non évaluable. L'échéance exige une émission valide indépendamment
de la présence ou de la validité de la réponse. Les mesures gardent leur contexte
de filtres et COUNTROWS. Aucune déduplication des DAH n'est ajoutée.
ID ligne besoin reste présent dans le modèle et les tableaux.

## Mentions visibles

Trois zones de texte sur Délais de réponse et Détail des besoins indiquent :

> Jours ouvrés : hors week-ends et jours fériés nationaux français. Jour d’émission exclu.

Titres, couleurs, segments, infobulles, navigation et signets sont conservés.
Le filtre du graphique reste Nb réponses évaluables > 0, sans filtrer le modèle.

## Fichiers et diff

Modifiés :

- `Suivi_Appel_offre.SemanticModel/definition/tables/Données.tmdl` : deux expressions et leurs descriptions.
- `Suivi_Appel_offre.SemanticModel/definition/model.tmdl` : référence à la table ajoutée.
- `Suivi_Appel_offre.Report/definition/pages/d31a1500000000000001/visuals/d31a1500000000000002/visual.json`
- `Suivi_Appel_offre.Report/definition/pages/d31a1500000000000001/visuals/d31a150000000000000a/visual.json`
- `Suivi_Appel_offre.Report/definition/pages/9d01f4bf588b204a2bf9/visuals/07934e2207002df50354/visual.json`
- `scripts/verifier_delais_reponse.py` : contrôles et comparaison avant/après.
- `docs/Delais_de_reponse.md` : cette documentation.

Ajoutés :

- `Suivi_Appel_offre.SemanticModel/definition/tables/Calendrier ouvré France.tmdl`
- [Diff complet](Delais_jours_feries.diff), par rapport à la sauvegarde préalable.

Les autres fichiers sont inchangés : notamment _Mesures.tmdl, la requête M,
relationships.tmdl, les Synthèses, la navigation, les signets, l'Excel, les
caches et paramètres locaux.

Ce constat décrit l'évolution des jours fériés. La finalisation de livraison a
ensuite retiré les tables de dates automatiques et leurs dépendances, y compris
le fichier de relations devenu inutile. Le calendrier ouvré et ses calculs sont
restés identiques. Le modèle final possède quatre tables et aucune relation,
avec le réglage Date/heure automatique enregistré à 0.

## Contrôles du 14 octobre 2026

Commande : `python -B scripts/verifier_delais_reponse.py`.

**Hors moteur Power BI :**

- Cas ci-dessous validés par une référence Python indépendante.
- Expressions arithmétiques du comput lues dans le TMDL et évaluées par un
  évaluateur AST limité ; le DAX complet n'est pas exécuté.
- Comparaison au comput indépendant de Gauss sur 1900 à 2399 (500 années).
- Les 11 dates de 2026 et 2027 correspondent au cas général de
  [Service-Public](https://www.service-public.gouv.fr/particuliers/vosdroits/F2405),
  consulté le 14 octobre 2026.
- 10 955 cas de délai de 2025 à 2030 comparés à un calendrier matérialisé ;
  échéances vérifiées pour chaque date de départ de cette plage.
- Source vide/sans date valide, années multiples, même jour, invalidité,
  fête en week-end, fêtes locales exclues et fêtes coïncidentes contrôlés.
- 576 combinaisons date/lieu/entité : dans + hors = évaluables ; taux cohérent.
- Références PBIR, descriptions TMDL en ///, absence de relation et d'API contrôlées.
- Trois zones de texte validées avec le schéma public PBIR 2.9 ; la version
  2.13 du projet est conservée. Il s'agit d'un contrôle de compatibilité.

Le **sérialiseur Microsoft TMDL** de Power BI Desktop 2.158.1304.0 a lu le modèle
complet sans erreur : 7 tables. C'est une désérialisation réelle des métadonnées,
pas une compilation ou exécution des expressions DAX.

| Départ → réponse ou échéance | Résultat |
| --- | --- |
| 03/04/2026 → 07/04/2026 | 1 jour |
| Émission 03/04/2026 | Échéance 13/04/2026 |
| 30/04/2026 → 04/05/2026 | 1 jour |
| 13/07/2026 → 15/07/2026 | 1 jour |
| Émission 13/07/2026 | Échéance 21/07/2026 |
| 14/08/2026 → 17/08/2026 | 1 jour, sans double déduction ni report |
| 24/12/2026 → 04/01/2027 | 5 jours, conforme |
| Émission 24/12/2026 | Échéance 04/01/2027 |
| Même date valide | 0 jour |
| Date absente ou réponse antérieure | Non évaluable |

Comparaison sur **la même copie Excel locale**, en lecture seule, sans interroger
SharePoint ni ajouter de données fictives au modèle :

| Indicateur | Avant, hors week-ends | Après, hors week-ends et fériés |
| --- | ---: | ---: |
| Lignes | 117 | 117 |
| Réponses évaluables | 48 | 48 |
| Dans le délai | 34 | 35 |
| Hors délai | 14 | 13 |
| Sans date de réponse | 66 | 66 |
| Dates à vérifier | 3 | 3 |
| Délai moyen | 4,9791667 | 4,7916667 |
| Dans le délai (%) | 70,8333333 % | 72,9166667 % |

Les trois références DAH répétées sont conservées. Neuf délais diminuent et
17 échéances reculent. Aucun délai valide n'augmente, aucune échéance n'avance
et aucun besoin auparavant conforme ne devient hors délai.

## À vérifier dans Desktop

1. Fermer sans enregistrer une éventuelle instance sur l'ancienne version,
   rouvrir Suivi_Appel_offre.pbip et actualiser SharePoint.
2. Confirmer la compilation et l'exécution DAX du calendrier, du délai et de
   l'échéance ; vérifier la table masquée et les fêtes de 2026/2027.
3. Vérifier les cas métier ci-dessus dans le moteur, notamment émission/réponse
   fériée, fin décembre et source vide/sans dates valides.
4. Comparer sur SharePoint actuel : la copie locale peut différer. Contrôler
   les segments, le graphique, les infobulles et les besoins répétés.
5. Confirmer le rendu et la lisibilité des mentions dans les deux pages.

Aucune expression DAX/M ni aucun rendu n'a été exécuté dans Desktop pendant
cette intervention. Le calendrier est recalculé à l'actualisation ; délai et
échéance restent des colonnes et ne varient pas selon un segment.
Une modification future de la liste des fêtes nationales nécessiterait
l'adaptation du générateur.

La correction précédente UnknownKeyword description est conservée :
les descriptions utilisent /// devant les objets, jamais description:.
