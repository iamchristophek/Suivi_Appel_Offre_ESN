# Guide d'utilisation — suivi des appels d'offres

## Les trois pages

| Page | Utilisation |
| --- | --- |
| **Synthèse Commerciale** | Vue d'ensemble des volumes de besoins, statuts et répartitions par lieu, entité ou fonction. |
| **Délais de réponse** | Délai moyen, respect de l'objectif de cinq jours ouvrés, répartition par lieu et qualité des dates. |
| **Détail des besoins** | Consultation des besoins ligne par ligne, de leurs dates, échéances, délais et motifs de contrôle. |

## Filtrer et naviguer

Utilisez les segments visibles pour sélectionner une date d'émission, un lieu,
une entité ou les autres critères proposés sur la page. Les indicateurs et les
tableaux se recalculent selon vos sélections. Vérifiez les filtres de la page
après un changement de page.

Les boutons permettent de passer de la synthèse aux délais ou au détail et de
revenir à la synthèse. **Dans Power BI Desktop, maintenez Ctrl et cliquez** pour
activer les boutons de navigation et **Réinitialiser**.

Utilisez **Réinitialiser** pour revenir aux sélections enregistrées pour la page.
Vous pouvez aussi effacer une sélection dans son segment. Survolez les barres
du graphique des délais pour consulter les nombres de réponses évaluables,
dans le délai et hors délai.

## Actualiser les données

1. Ouvrez `Suivi_Appel_offre.pbip` dans Power BI Desktop, en conservant les dossiers
   Report et SemanticModel à côté du fichier.
2. Si une authentification SharePoint est demandée, choisissez **Compte
   organisationnel** et connectez-vous avec votre **compte professionnel autorisé**
   à accéder au fichier source.
3. Cliquez sur **Accueil > Actualiser** et attendez la fin de l'actualisation.
4. Vérifiez les indicateurs et les éventuels messages d'erreur, puis **enregistrez**.

La source est le classeur Excel sur SharePoint. La copie Excel du dossier `data`
sert aux contrôles techniques et ne remplace pas cette source.

## Lire les indicateurs

- **Une ligne = un besoin.** Des références DAH répétées sont normales et conservées.
- **No Go** : décision de l'équipe de ne pas répondre favorablement au besoin.
- Le délai part de la **date d'émission**, dont le jour est exclu, et s'arrête à
  la **date de réponse envoyée aux achats**, incluse si elle est ouvrée.
- Les jours ouvrés sont les **lundis à vendredis, hors jours fériés nationaux
  français**. Les heures des dates n'entrent pas dans la comparaison.
- Une réponse à **J+5 ouvrés est conforme** ; au-delà, elle est hors délai.
  Une réponse le jour même vaut zéro jour.
- L'échéance est le cinquième jour ouvré après l'émission.
- Les dates absentes ou invalides, ainsi qu'une réponse antérieure à l'émission,
  sont exclues des réponses évaluables, du taux et de la moyenne.
- **Sans date de réponse ne signifie pas automatiquement en retard.**
- **Dates à vérifier** signale un problème de date : consultez le motif dans le détail.

Le taux dans le délai compare les réponses conformes aux seules réponses
évaluables. Le graphique affiche les lieux ayant au moins une réponse évaluable.
Le bleu désigne les réponses dans le délai et l'orange celles hors délai.

Pour une modification du modèle ou un diagnostic technique, consultez le
[guide de reprise](Reprise_du_projet.md).
