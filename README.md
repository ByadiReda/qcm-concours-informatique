# qcm-concours-informatique

QCM de préparation au concours d'informatique, avec génération d'un PDF structuré et prêt à télécharger.

## Contenu

Le dépôt contient :

- `questions.py` : banque structurée de **648 QCM**
- `generate_qcm.py` : script Python qui génère le PDF
- `QCM_Concours.pdf` : PDF final régénéré avec questions et corrigés
- `requirements.txt` : dépendances Python

## Couverture du QCM

Le PDF couvre les catégories suivantes, avec les niveaux **Basique**, **Intermédiaire** et **Avancé** :

- Génie logiciel
- Java
- Spring / Spring Boot
- SQL / Bases de données
- Développement Web
- Algorithmes et structures de données

### Répartition actuelle

- **108 questions par catégorie**
- **648 questions au total**
- **Par catégorie** : 38 Basique • 43 Intermédiaire • 27 Avancé

## Structure du PDF

Le document généré inclut :

- une **table des matières cliquable** au début ;
- une **section par catégorie** ;
- des **sous-sections par niveau** dans chaque catégorie ;
- une **numérotation continue** de `Q1` à `Q648` ;
- un **identifiant local par catégorie** (ex. `JAVA-042`, `SQL-017`, `ALGO-103`) ;
- un **corrigé détaillé à la fin de chaque catégorie**.

## Régénérer le PDF

Prérequis : disposer des polices `DejaVuSans.ttf` et `DejaVuSans-Bold.ttf`, soit déjà installées sur la machine, soit copiées dans le dossier `./fonts/`, soit accessibles via la variable d'environnement `QCM_FONT_DIR`.

```bash
pip install -r requirements.txt
python generate_qcm.py
```

Le script recherche automatiquement les polices `DejaVuSans.ttf` et `DejaVuSans-Bold.ttf` :

- dans `./fonts/` si vous souhaitez les fournir avec le projet ;
- dans les emplacements système courants ;
- ou dans le dossier pointé par la variable d'environnement `QCM_FONT_DIR`.

Le fichier généré sera disponible à la racine du dépôt sous le nom `QCM_Concours.pdf`.
