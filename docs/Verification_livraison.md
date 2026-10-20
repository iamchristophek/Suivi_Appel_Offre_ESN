# Vérification de livraison — 14 octobre 2026

Le projet conserve ses trois pages finales visibles : Synthèse Commerciale,
Délais de réponse et Détail des besoins. Les deux pages masquées et les signets
existants sont conservés.

## Sauvegarde et état initial

- Sauvegarde complète hors du projet :
  `../Suivi_Appel_offre_Ruth_sauvegarde_20261014_175510`.
- 94 fichiers vérifiés par SHA-256 avant modification.
- Aucun AGENTS.md applicable trouvé dans le workspace et ses parents contrôlés.
- Le dossier actif n'est pas un dépôt Git : inspection Git impossible. Aucun
  reset, clean, changement d'historique, commit ou push effectué.

## Nettoyage des dates automatiques

Le réglage enregistré était encore à 1 dans model.tmdl, avec trois tables
automatiques. Il est désormais à **0**.

Retraits cohérents :

- Deux tables locales et leur modèle de table de dates automatique.
- Trois références de tables dans model.tmdl.
- Deux variations des colonnes importées de dates.
- Deux relations automatiques ; le fichier de relations est supprimé car vide.
- Dix entités et seize relations linguistiques associées aux hiérarchies retirées.

Le contrôle des visuels, filtres et signets n'a trouvé aucun usage d'année,
trimestre ou mois par ces hiérarchies. Aucune migration de visuel ni création
de calendrier supplémentaire n'a donc été nécessaire. Les colonnes de dates
explicites sont conservées. Il ne subsiste aucune référence active aux objets
retirés dans les définitions du modèle et du rapport.

## Fichiers de cette finalisation

Modifiés :

- `Suivi_Appel_offre.SemanticModel/definition/model.tmdl`
- `Suivi_Appel_offre.SemanticModel/definition/tables/Données.tmdl`
- `Suivi_Appel_offre.SemanticModel/definition/cultures/fr-FR.tmdl`
- `scripts/verifier_delais_reponse.py` : prise en charge du modèle sans relations.
- `docs/Reprise_du_projet.md` : structure actuelle et formulation neutre.
- `docs/Delais_de_reponse.md` : distinction entre évolution des fériés et finalisation.

Ajoutés :

- [Guide_utilisation_Ruth.md](Guide_utilisation_Ruth.md)
- `scripts/verifier_structure_rapport.py`
- `docs/Verification_livraison.md`

Supprimés : les trois fichiers TMDL des tables de dates automatiques et
`Suivi_Appel_offre.SemanticModel/definition/relationships.tmdl` devenu inutile.

Aucun renommage nécessaire : les noms des scripts et documents sont explicites.
Les identifiants des pages, visuels, signets et objets métier sont conservés.
Les métadonnées techniques générées par Power BI et les références aux
instructions de travail ne sont pas assimilées à une mention d'assistance.

## Contrôles réussis hors moteur

```powershell
python -B scripts/verifier_structure_rapport.py
python -B scripts/verifier_delais_reponse.py
```

- Modèle TMDL réellement désérialisé par le sérialiseur Microsoft installé
  avec Desktop : **4 tables, 0 relation, Date/heure automatique = 0**.
- Comparaison des modèles courant et sauvegardé : mêmes noms, types et lineageTag
  des colonnes métier ; mêmes sources M, calendrier, expressions de colonnes et
  mesures, hors indentation et présentation du texte.
- Structure PBIR : **65 JSON lus, 54 visuels, 161 références de champs,
  7 liens de navigation/signets** ; aucune erreur de référence de champ ou de page.
- Tests de délais et fériés réussis : cas métier, 500 années du comput,
  10 955 cas de délai et 576 combinaisons de filtres.
- Copie Excel locale inchangée : 117 besoins, 48 réponses évaluables, 35 conformes
  et 13 hors délai. Ces valeurs ne valident pas les données SharePoint actuelles.
- Recherche des mentions d'assistance dans les contenus livrables : aucune
  mention restante ; la documentation utilise une formulation neutre.

Les opérations de finalisation n'ont pas écrit dans les caches ni les paramètres
locaux. Des écritures supplémentaires ont été constatées pendant la session sur
ces fichiers, la page active et la présentation du calendrier. Elles ont été
conservées. Les trois textes PBIR concernés sont identiques en contenu à la
sauvegarde ; le calendrier conserve exactement son expression.

## Limites du contrôle PBIR et points de livraison

Les 65 JSON ont été comparés aux schémas publics disponibles. Les 54 visuels
déclarent la version 2.13, contrôlée en compatibilité avec la version publique
2.9, sans modifier les versions dans les fichiers.

Huit fichiers préexistants présentent des écarts aux schémas publics utilisés :
deux signets avec `preserveNewVisualVisibility`, et six visuels de synthèse avec
des options d'infobulle telles que `sentenceTemplate`, `showTooltipFieldsOnly`
ou `showChartSpecificTooltips`. Ces huit fichiers sont identiques à la
sauvegarde. Les propriétés sont conservées pour préserver le comportement.
Ce contrôle ne constitue donc pas une validation intégrale de la version Desktop.

Un point préexistant reste à vérifier : **Reset_Synthese** contient la cible
technique `7fc7cd1be58ba1a85081`, absente des visuels actuels. Les états de visuels
enregistrés sont valides et le signet est préservé. Vérifier son effet réel dans
Desktop. Le bouton Réinitialiser du détail utilise Reset_Delais : vérifier qu'il
efface les sélections souhaitées sur la page de détail.

## Vérifications restantes dans Desktop

1. Rouvrir le PBIP, confirmer le réglage Date/heure automatique désactivé et
   l'absence de réapparition des tables automatiques après enregistrement.
2. Actualiser avec le compte professionnel autorisé sur SharePoint, contrôler
   les éventuelles erreurs, puis enregistrer.
3. Confirmer l'exécution DAX des délais, échéances et indicateurs sur les données
   actuelles, ainsi que les filtres des trois pages.
4. Tester tous les boutons par Ctrl + clic, en particulier Réinitialiser sur
   Synthèse Commerciale, Délais de réponse et Détail des besoins.
5. Vérifier le rendu, les décimales, les infobulles et la lisibilité des tableaux.

Aucune ouverture de l'interface Desktop ni aucune exécution DAX/M n'a été
effectuée par les opérations de vérification décrites ici. La désérialisation
TMDL et les tests Python sont des contrôles hors moteur. Aucun PBIX n'a été
généré par script.
