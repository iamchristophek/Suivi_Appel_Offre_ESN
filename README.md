# Suivi_Appel_Offre_ESN

Projet Power BI au format PBIP : suivi commercial des besoins, détail des lignes
et respect du délai de réponse de cinq jours ouvrés.
Le rapport suit la réponse envoyée aux achats. Une ligne représente un besoin ;
les références DAH répétées sont normales et conservées.

## Reprendre le développement

1. Cloner le dépôt et conserver les dossiers Report et SemanticModel à côté du PBIP.
2. Lire le [guide de reprise](docs/Reprise_du_projet.md).
3. Ouvrir [Suivi_Appel_offre.pbip](Suivi_Appel_offre.pbip) dans Power BI Desktop.
4. S'authentifier auprès de SharePoint avec un compte professionnel autorisé.
5. Actualiser, vérifier les résultats, puis enregistrer.

La source réelle est le classeur Excel sur SharePoint, référencé dans la requête
M de Données. Le dépôt ne donne pas de droits d'accès à cette source.

## Structure

| Emplacement | Contenu |
| --- | --- |
| `Suivi_Appel_offre.pbip` | Point d'entrée dans Desktop |
| `Suivi_Appel_offre.Report/` | Pages, visuels, navigation, signets et thèmes PBIR |
| `Suivi_Appel_offre.SemanticModel/` | Tables, mesures et requêtes TMDL |
| `scripts/` | Contrôles hors moteur |
| `docs/` | Guides et vérifications documentées |

Le dépôt versionne le code source PBIP. Les fichiers locaux, caches, PBIX et
copies Excel sont exclus par `.gitignore` et restent disponibles sur le poste.

## Règles essentielles

- Une ligne représente un besoin : conserver les références DAH répétées.
- No Go est la décision de ne pas répondre favorablement au besoin.
- Délai : jour d'émission exclu ; réponse incluse si ouvrée ; lundi à vendredi,
  hors jours fériés nationaux français. À cinq jours ouvrés, la réponse est conforme.
- Dates absentes ou invalides : exclues des réponses évaluables, du taux et de la moyenne.
- Une absence de réponse ne signifie pas automatiquement un besoin en retard.
- Préserver le calendrier partagé des jours ouvrés, les calculs, les identifiants
  techniques, la connexion SharePoint et les trois pages finales.

## Contrôles

Depuis la racine, avec Python 3.12 utilisé lors des vérifications précédentes :

```powershell
python -B scripts/verifier_structure_rapport.py
python -B scripts/verifier_delais_reponse.py
```

Les scripts utilisent la bibliothèque standard. Le contrôle des délais nécessite
la copie Excel locale `data/REPORTING_2026.xlsx`. Si elle n'est pas versionnée,
obtenir une copie autorisée et la placer à cet emplacement sans changer la source
SharePoint du modèle. Les résultats dépendent de cette copie.

Ces contrôles n'exécutent pas Power BI Desktop, DAX ou Power Query. Tester aussi
l'actualisation, le rendu, les filtres, la navigation et les boutons dans Desktop.

## Documentation

- [Guide d'utilisation pour Ruth](docs/Guide_utilisation_Ruth.md)
- [Guide de reprise technique](docs/Reprise_du_projet.md)
- [Règles et contrôles des délais](docs/Delais_de_reponse.md)
- [Vérification de livraison et limites connues](docs/Verification_livraison.md)

Avant un changement fonctionnel, créer et vérifier une sauvegarde complète hors
du dossier actif. Éviter d'éditer les fichiers pendant qu'une instance Desktop
enregistre les mêmes définitions. Les caches et paramètres locaux ne servent pas
à corriger une erreur du modèle.
