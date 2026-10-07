<p align="center">
  <img src="assets/sound-recognition-trainer.svg" width="112" alt="Icône Sound Recognition Trainer">
</p>

<h1 align="center">Sound Recognition Trainer</h1>

<p align="center"><a href="README.md">English</a> · <strong>Français</strong></p>

<p align="center">Apprenez le son. Faites confiance à votre réponse.<br>Une application de bureau hors ligne pour s'entraîner sérieusement à reconnaître des MP3.</p>

<p align="center">
  <a href="https://www.buymeacoffee.com/hytachi182"><img src="https://img.shields.io/badge/Buy%20me%20a%20coffee-soutenir%20le%20projet-FFDD00?style=flat-square&logo=buymeacoffee&logoColor=black" alt="Offrir un café à Michael"></a>
</p>

## Démarrage rapide

Tout reste sur votre ordinateur : les fichiers MP3 sont lus à leur emplacement, tandis que la bibliothèque, les résultats et les réglages sont enregistrés localement.

### Windows

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
.\run_windows.ps1
```

### macOS

```bash
bash run_mac.sh
```

Python 3.11 ou plus récent est requis. Au premier lancement sur macOS, le script crée l'environnement Python, installe les dépendances puis ouvre l'application.

## Fonctionnalités

- Bibliothèque MP3, catégories, alias, import et export JSON.
- Décalage de lecture par son et heure de démarrage commune à toutes les écoutes.
- Entraînement sans pression, priorisation des sons difficiles et statistiques locales.
- Examen à choix multiples ou réponse libre avec tolérance aux accents et fautes légères.
- Lecture d'un son, des sons cochés ou d'une catégorie, avec mode aléatoire.
- Aucune modification des MP3 originaux, aucun compte et aucun cloud requis.

## Développement

```bash
git clone https://github.com/Hytachi182/SeeSounds.git
cd SeeSounds
```

Sous Windows : `.\.venv\Scripts\python.exe -m pytest`.

Sous macOS : `.venv/bin/python -m pytest`.

Créé par Michael Ruffenach.
