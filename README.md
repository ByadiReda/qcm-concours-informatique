# qcm-concours-informatique

QCM pour concours en **génie logiciel**, **développement informatique** et **base de données**, avec génération d'un PDF prêt à télécharger.

## Contenu

Le dépôt contient :

- `questions.py` : base structurée de **108 QCM**
- `generate_qcm.py` : script Python qui génère le PDF
- `QCM_Concours.pdf` : PDF final avec questions et corrigés
- `requirements.txt` : dépendances Python

## Couverture du QCM

Le PDF couvre les catégories suivantes, avec les niveaux **Basique**, **Intermédiaire** et **Avancé** :

- Génie logiciel
- Java
- Spring / Spring Boot
- SQL / Bases de données
- Développement Web
- Algorithmes et structures de données

## Régénérer le PDF

```bash
pip install -r requirements.txt
python generate_qcm.py
```

Le script recherche automatiquement les polices `DejaVuSans.ttf` et `DejaVuSans-Bold.ttf` :

- dans `./fonts/` si vous souhaitez les fournir avec le projet ;
- dans les emplacements système courants ;
- ou dans le dossier pointé par la variable d'environnement `QCM_FONT_DIR`.

Le fichier généré sera disponible à la racine du dépôt sous le nom `QCM_Concours.pdf`.
