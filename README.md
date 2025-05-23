# HTMLConverter

## Description

HTMLConverter est une application permettant de convertir du texte brut en HTML structuré. Il prend en charge le traitement des titres, la génération d'un panneau de navigation, et la gestion des assets statiques.

## Fonctionnalités

- Lecture et traitement de fichiers texte.
- Conversion automatique des titres en balises HTML avec des identifiants uniques.
- Génération d'un panneau de navigation basé sur les titres détectés.
- Vérification et intégration des favicons.
- Gestion des templates avec Jinja2.
- Copie et validation des assets CSS, JS et images.
- Journalisation des erreurs et des processus via un logger configurable.

## Installation

### Prérequis

- Python 3.7+
- Virtualenv (optionnel mais recommandé)

### Étapes

1. Cloner le dépôt :

   ```sh
   git clone https://github.com/BAYRYO/plaintext-interpreter.git
   cd plaintext-interpreter
   ```

2. Installer les dépendances :

   ```sh
   pip install -r requirements.txt
   ```

## Utilisation

### Exécution de la conversion

```sh
python -m main.py <input_file> <output_file>
```

Exemple :

```sh
python -m main.py input.txt output.html
```

### Configuration

Le fichier `config.yml` permet de personnaliser les options suivantes :
    - Modes de débogage (`debug_mode`)
    - Encodage des fichiers (`encoding`)
    - Modèles Jinja2 et assets (`templates.paths`)
    - Expressions régulières pour le traitement des titres (`patterns.title`)

### Structure du projet

```bash
htmlconverter/
│── configs/
│   ├── config.yml
│   ├── logging_config.yml
│── input/
│── logs/
│   ├── converter.log
│   ├── error.log
│── output/
│   ├── assets/
│   │   ├── css/
│   │   │   ├── style.css
│   │   │   ├── icons.css
│   │   ├── js/
│   │   │   ├── script.js
│   │   ├── images/
│   │   │   ├── favicon.ico
│   │   │   ├── ...
│── src/
│   ├── html_converter.py
│   ├── interfaces.py
│   ├── live_editor.py
│   ├── processors.py
│   ├── validators.py
├── templates/
│   ├── assets/
│   │   ├── css/
│   │   │   ├── style.css
│   │   │   ├── icons.css
│   │   ├── js/
│   │   │   ├── script.js
│   │   ├── images/
│   │   │   ├── favicon.ico
│   │   │   ├── ...
│   ├── base.html
│   ├── footer.html
│   ├── header.html
│   ├── macro.html
│   ├── components/
│   │   ├── navigation.html
│   │   ├── nav_button.html
│── .gitignore
│── LICENSE
│── main.py
│── README.md
│── requirements.txt
```

## Journalisation

Les logs sont configurés pour afficher des messages en fonction du niveau de journalisation défini dans `config.yml`. Par défaut, les logs sont affichés dans la console.

## Contributions

Les contributions sont les bienvenues ! Merci de respecter les bonnes pratiques de développement et d'effectuer une revue de code avant de proposer un pull request.

## Licence

Ce projet est sous licence MIT.
