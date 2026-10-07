<p align="center">
  <img src="assets/sound-recognition-trainer.svg" width="112" alt="Icône Sound Recognition Trainer">
</p>

<h1 align="center">Sound Recognition Trainer</h1>

<p align="center"><a href="README.md">English</a> · <strong>Français</strong></p>

<p align="center">
  Apprenez le son. Faites confiance à votre réponse.<br>
  Une application de bureau hors ligne pour s'entraîner sérieusement à reconnaître des MP3.
</p>

<p align="center">
  <a href="https://www.buymeacoffee.com/hytachi182"><img src="https://img.shields.io/badge/Buy%20me%20a%20coffee-soutenir%20le%20projet-FFDD00?style=flat-square&logo=buymeacoffee&logoColor=black" alt="Offrir un café à Michael"></a>
</p>

<p align="center">
  <a href="https://github.com/Hytachi182/SeeSounds"><img src="https://img.shields.io/badge/plateforme-Windows%20%7C%20macOS-167277?style=flat-square" alt="Windows et macOS"></a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-102D38?style=flat-square&logo=python&logoColor=white" alt="Python 3.11 ou plus récent">
  <img src="https://img.shields.io/badge/donn%C3%A9es-SQLite%20local-167277?style=flat-square&logo=sqlite&logoColor=white" alt="Données SQLite locales">
  <img src="https://img.shields.io/badge/cloud-non%20requis-102D38?style=flat-square" alt="Aucun cloud requis">
</p>

<p align="center">
  <a href="#bien-démarrer">Bien démarrer</a> ·
  <a href="#fonctionnalités">Fonctionnalités</a> ·
  <a href="#utilisation">Utilisation</a> ·
  <a href="#développement">Développement</a> ·
  <a href="https://github.com/Hytachi182/SeeSounds/issues">Signaler un problème</a>
</p>

---

## Bien démarrer

Sound Recognition Trainer transforme votre collection personnelle de MP3 en séances d'entraînement ciblées et en résultats d'examen détaillés. Tout reste sur votre ordinateur : les fichiers audio sont lus à leur emplacement, tandis que la bibliothèque, les scores, les réglages et l'historique des examens sont conservés dans une base SQLite locale.

| Plateforme | Méthode recommandée | Pour commencer |
| --- | --- | --- |
| **Windows** | PowerShell | Exécutez le script d'installation, puis le lanceur. |
| **macOS** | Terminal | Lancez un seul script ; il installe les dépendances si nécessaire. |

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

Le premier lancement crée `.venv`, installe les dépendances, les vérifie, puis ouvre l'application. Les lancements suivants ouvrent directement l'application. Définissez `PYTHON` si vous devez utiliser un exécutable Python 3.11+ particulier, par exemple `PYTHON=python3.12 bash run_mac.sh`.

Prérequis : **Python 3.11 ou plus récent**. La lecture audio utilise le moteur multimédia Qt fourni avec PySide6 ; assurez-vous que votre système peut lire les fichiers MP3 concernés.

> Votre espace de travail local est enregistré dans `~/.sound-recognition-trainer/`, notamment le fichier `sound_trainer.db`. Les fichiers MP3 originaux ne sont jamais modifiés.

## Fonctionnalités

| Disponible aujourd'hui | Description |
| --- | --- |
| **Bibliothèque MP3** | Importez plusieurs fichiers, recherchez par nom ou catégorie, modifiez les noms affichés, activez ou désactivez les sons et gérez les catégories. |
| **Décalages de lecture** | Démarrez chaque son après une introduction parlée sans modifier son fichier MP3. |
| **Alias** | Acceptez plusieurs noms pour un même son lors des examens à réponse libre. |
| **Entraînement ciblé** | Écoutez, réécoutez, révélez la réponse et indiquez si vous aviez juste, sans chronomètre ni pénalité. |
| **Priorité aux sons difficiles** | Consacrez davantage d'entraînement aux sons dont les résultats sont les plus faibles. |
| **Deux niveaux d'examen** | Le niveau 1 propose cinq choix dans un ordre aléatoire. Le niveau 2 accepte les réponses libres. |
| **Évaluation tolérante des réponses** | Ignore les différences de casse, les espaces superflus, les accents et la ponctuation simple ; des seuils configurables prennent en compte les fautes légères. |
| **Résultats détaillés** | Consultez chaque réponse, son score de similarité et son évaluation, puis réécoutez les sons à retravailler. |
| **Statistiques locales** | Suivez les tentatives, le taux de réussite, l'historique par son et les examens récents. |
| **Portabilité de la bibliothèque** | Exportez et importez les métadonnées de la bibliothèque au format JSON ; les chemins audio introuvables sont signalés après l'import. |

## Utilisation

1. Dans **Bibliothèque sonore**, choisissez **Ajouter des MP3**. Les noms proviennent initialement des noms de fichiers et peuvent ensuite être modifiés.
2. Configurez si nécessaire un décalage **Démarrer la lecture à** (par exemple `4.0` ou `5.25` secondes), des catégories et des alias séparés par des virgules.
3. Dans **Entraînement**, sélectionnez une catégorie si utile, écoutez un son, révélez la réponse quand vous êtes prêt, puis indiquez si vous l'aviez reconnue.
4. Dans **Examen**, choisissez le nombre de questions, le niveau et si les répétitions sont autorisées. L'application vérifie la bibliothèque avant de commencer.
5. Consultez les résultats, réécoutez les sons manqués et utilisez les **Statistiques** pour choisir quoi travailler ensuite.

<details>
<summary><strong>Règles des examens et évaluation des réponses</strong></summary>

<br>

- **Niveau 1 — Choix multiples :** nécessite au moins cinq sons activés et présente une bonne réponse ainsi que quatre autres propositions.
- **Niveau 2 — Réponse libre :** accepte le nom principal du son ou l'un de ses alias configurés.
- Lorsque les répétitions sont désactivées, un examen ne peut pas comporter plus de questions que de sons activés.
- Par défaut, une réponse est évaluée **correcte** à partir de 90 % de similarité et **presque correcte** à partir de 75 %. Les deux seuils sont réglables dans **Paramètres**.
- Chaque réponse saisie, sa version normalisée, son score de similarité et son évaluation sont conservés localement avec l'examen.

</details>

<details>
<summary><strong>Confidentialité et données</strong></summary>

<br>

Aucun compte ni service cloud n'est nécessaire. Après l'installation, l'application fonctionne sans connexion réseau. La base de données contient les métadonnées de la bibliothèque, les alias, les résultats d'entraînement et d'examen ainsi que les réglages. Elle conserve les chemins vers vos fichiers MP3 ; elle ne modifie ni ne copie les fichiers audio sources.

</details>

## Développement

Clonez le dépôt, créez l'environnement virtuel avec le script correspondant à votre plateforme, puis lancez la suite de tests :

```bash
git clone https://github.com/Hytachi182/SeeSounds.git
cd SeeSounds
```

```powershell
# Windows
.\.venv\Scripts\python.exe -m pytest
```

```bash
# macOS
.venv/bin/python -m pytest
```

Les tests couvrent la normalisation des réponses, la suppression des accents, les alias, la comparaison tolérante, la sélection de questions sans répétition, la construction des choix multiples, la pondération des sons difficiles et la persistance des données de correction des examens.

### Construire une application de bureau

Effectuez la compilation sur chaque système d'exploitation cible : ne compilez pas la version macOS sur Windows, ni l'inverse.

```bash
.venv/bin/pyinstaller --noconfirm sound_recognition_trainer.spec
```

Sous Windows, utilisez :

```powershell
.\.venv\Scripts\pyinstaller.exe --noconfirm sound_recognition_trainer.spec
```

L'application générée est placée dans `dist/`.

Sur macOS, la compilation crée `dist/SoundRecognitionTrainer.app`. Les versions natives Apple Silicon et Intel sont vérifiées séparément. Le workflow de validation macOS vérifie aussi une installation vierge depuis un chemin contenant des espaces, la récupération d'un environnement incomplet, le redémarrage hors ligne, la réparation des dépendances et le lancement du `.app` déplacé avec un MP3 synthétique.

Pour lancer un contrôle d'intégration isolé (PySide6 6.8+), utilisez :

```bash
python app.py --self-test --audio tests/fixtures/tone.mp3 --report build/self-test.json
```

Ce contrôle crée une base temporaire et produit un rapport JSON ainsi qu'une capture d'écran sans toucher à votre espace d'apprentissage. Le son est coupé, mais les données audio décodées, les décalages, la pause/reprise et la fin de la lecture enchaînée sont vérifiés. La CI ne peut pas confirmer le son dans des haut-parleurs physiques ni l'approbation des applications téléchargées par Apple.

### Organisation du projet

| Élément | Rôle |
| --- | --- |
| `app.py` | Assemblage de l'application, espace de travail local et thème visuel. |
| `src/database` | Schéma SQLite, persistance, import/export et statistiques locales. |
| `src/models` | Modèle de données des sons. |
| `src/services` | Lecture audio et règles de sélection pour l'entraînement et les examens. |
| `src/utils` | Normalisation et comparaison des réponses libres. |
| `src/ui` | Interface de bureau PySide6. |
| `tests` | Tests de comportement des règles d'entraînement et d'évaluation. |

## Contribuer

Une amélioration, un problème ou une méthode d'apprentissage à proposer ? [Ouvrez une issue](https://github.com/Hytachi182/SeeSounds/issues). Privilégiez le fonctionnement local, préservez les fichiers audio sources et gardez les règles d'évaluation testables.

## Préversion publique et licence

Le code est disponible sous [licence MIT](LICENSE). Il s'agit d'une préversion publique ; la lecture sur des périphériques audio physiques et la distribution d'applications autonomes restent à valider. L'installation native macOS, le lancement de l'application et le décodage d'un MP3 synthétique sont couverts par le workflow de validation. Consultez le [bilan de publication](PUBLIC_RELEASE_REVIEW.md) pour connaître les contrôles effectués et les étapes restantes.

Les imports JSON fusionnent les entrées selon le chemin du fichier : les métadonnées des sons existants sont mises à jour, tout en conservant l'historique d'entraînement et d'examen. Les bibliothèques invalides sont rejetées sans écriture partielle. Les sons utilisés dans des examens terminés doivent être désactivés plutôt que supprimés pour préserver leur historique de correction.

Les exports de bibliothèque contiennent les chemins locaux des fichiers, les noms, les catégories et les alias. Vérifiez-les avant de les partager. Aucun fichier audio n'est fourni : utilisez des enregistrements que vous avez le droit d'utiliser ou de distribuer.

Les dépendances tierces conservent leurs propres licences. PySide6/Qt propose des licences LGPL/GPL ainsi que des licences commerciales ; la licence MIT de l'application ne remplace pas ces conditions. Avant de distribuer des exécutables autonomes, consultez les [conditions de licence Qt](https://doc.qt.io/qt-6/licensing.html) et joignez les notices applicables ainsi que les informations requises sur les sources des dépendances.

## Créateur

Conçu et créé par Michael Ruffenach.
