"""Application-owned English/French text catalog and presentation helpers."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from string import Formatter
from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QCheckBox, QLineEdit, QComboBox, QDoubleSpinBox, QFormLayout

FRENCH = {'Home': 'Accueil',
 'Sound Library': 'Bibliothèque sonore',
 'Training': 'Entraînement',
 'Exam': 'Examen',
 'Statistics': 'Statistiques',
 'Settings': 'Paramètres',
 'About': 'À propos',
 'Add MP3 files': 'Ajouter des MP3',
 'Preview': 'Écouter',
 'Edit': 'Modifier',
 'Remove': 'Supprimer',
 'Import JSON': 'Importer JSON',
 'Export JSON': 'Exporter JSON',
 'Select shown': 'Tout sélectionner',
 'Assign category': 'Attribuer la catégorie',
 'Clear': 'Effacer',
 'Start a training round': 'Commencer un entraînement',
 'Set up an exam': 'Préparer un examen',
 'Play a new sound': 'Lire un nouveau son',
 'Replay': 'Réécouter',
 'Pause / resume': 'Pause / reprendre',
 'Reveal answer': 'Afficher la réponse',
 'I missed it': 'Je ne savais pas',
 'I was correct': "J'avais juste",
 'Start exam': "Commencer l'examen",
 'Submit answer': 'Valider la réponse',
 'Cancel': 'Annuler',
 'New exam': 'Nouvel examen',
 'Save local settings': 'Enregistrer les paramètres',
 'Language': 'Langue',
 'Volume': 'Volume',
 'Your data': 'Vos données',
 'Your audio': 'Vos audios',
 'Cloud and accounts': 'Cloud et comptes',
 'Workspace': 'Espace local',
 'Learn the sound. Trust the answer.': 'Apprenez le son. Faites confiance à votre réponse.',
 'A focused, local workspace for turning your MP3 collection into exam confidence.': 'Un espace local pour '
                                                                                     'transformer vos MP3 en '
                                                                                     'confiance pour '
                                                                                     "l'examen.",
 'Manage the source material for every practice session. Original MP3 files are never modified.': 'Gérez les '
                                                                                                  'sons de '
                                                                                                  'vos '
                                                                                                  'séances. '
                                                                                                  'Les MP3 '
                                                                                                  'originaux '
                                                                                                  'ne sont '
                                                                                                  'jamais '
                                                                                                  'modifiés.',
 'Practise deliberately. No timer, no penalty — only useful repetition.': 'Entraînez-vous sans chronomètre '
                                                                          'ni pénalité, avec des répétitions '
                                                                          'utiles.',
 'Turn practice into a clear result, then replay every sound worth revisiting.': 'Transformez vos '
                                                                                 'entraînements en résultat '
                                                                                 'clair, puis réécoutez les '
                                                                                 'sons à revoir.',
 'Use recent evidence to choose what deserves your next practice session.': 'Utilisez vos résultats récents '
                                                                            'pour choisir les sons à '
                                                                            'retravailler.',
 'Local defaults for playback and free-text answer assessment.': 'Préférences locales de lecture et '
                                                                 "d'évaluation des réponses.",
 'A focused, offline desktop tool for serious sound-recognition practice.': 'Un outil de bureau hors ligne '
                                                                            'pour un entraînement sérieux à '
                                                                            'la reconnaissance sonore.',
 'Search sound name or category': 'Rechercher un son ou une catégorie',
 'Choose or type a category': 'Choisir ou saisir une catégorie',
 'Start every playback at': 'Démarrer toutes les lectures à',
 'Default offset for new sounds': 'Décalage par défaut des nouveaux sons',
 'Correct threshold': 'Seuil de bonne réponse',
 'Almost-correct threshold': 'Seuil de réponse approchante',
 'Reveal in exam': "Afficher la réponse pendant l'examen",
 'Allow repeats': 'Autoriser les répétitions',
 'Prioritize difficult': 'Privilégier les sons difficiles',
 'All categories': 'Toutes les catégories',
 'Scope': 'Périmètre',
 'Questions': 'Questions',
 'Difficulty': 'Niveau',
 'Show missed and almost-correct only': 'Afficher seulement les erreurs et réponses approchantes',
 'Replay selected sound': 'Réécouter le son sélectionné',
 'Sound': 'Son',
 'Category': 'Catégorie',
 'Offset': 'Décalage',
 'Ready': 'Prêt',
 'File': 'Fichier',
 'Attempts': 'Tentatives',
 'Success': 'Réussite',
 'Last practiced': 'Dernier entraînement',
 'Your answer': 'Votre réponse',
 'Expected answer': 'Réponse attendue',
 'Similarity': 'Similarité',
 'Outcome': 'Résultat',
 'LOCAL WORKSPACE\nNo account. No cloud.': 'ESPACE LOCAL\nSans compte. Sans cloud.'}

FRENCH.update({
    "Enable / disable": "Activer / désactiver",
    "Shuffle": "Lecture aléatoire",
    "Play checked": "Lire les sons cochés",
    "Play category": "Lire la catégorie",
    "Prioritize difficult sounds": "Privilégier les sons difficiles",
    "Ready when you are": "Prêt quand vous l'êtes",
    "Choose a sound and identify what you hear.": "Choisissez un son et identifiez ce que vous entendez.",
    "The answer stays hidden until you reveal it.": "La réponse reste masquée jusqu'à ce que vous la révéliez.",
    "Choose the conditions. The app verifies library requirements before the exam starts.": "Choisissez les conditions. L'application vérifie la bibliothèque avant de commencer l'examen.",
    "Level 1 — Multiple choice": "Niveau 1 — Choix multiples",
    "Level 2 — Free text": "Niveau 2 — Réponse libre",
    "Allow repeated sounds": "Autoriser les répétitions",
    "Reveal answers immediately": "Afficher les réponses immédiatement",
    "A fair test, with useful evidence": "Un examen équitable, avec des résultats utiles",
    "Level 1 offers one correct answer and four alternatives. Level 2 accepts aliases, removed accents and minor typos according to Settings.": "Le niveau 1 propose une bonne réponse et quatre autres choix. Le niveau 2 accepte les alias et tolère les accents et les fautes légères selon vos paramètres.",
    "Listen carefully.": "Écoutez attentivement.",
    "Type the sound name": "Saisissez le nom du son",
    "From each sound's own offset": "Selon le décalage propre à chaque son",
    "Every preview, training round, exam question, and replay starts no earlier than this point.": "Toutes les écoutes, en bibliothèque, en entraînement et en examen, commencent au plus tôt à cet instant.",
    "Use a common start time to skip the beginning of every recording. A sound with its own later offset still starts later.": "Utilisez un décalage commun pour passer le début des enregistrements. Un son dont le décalage propre est plus grand commencera toujours plus tard.",
    "About Sound Recognition Trainer": "À propos de Sound Recognition Trainer",
    "Version 1.0.0 · Created by Michael Ruffenach": "Version 1.0.0 · Créé par Michael Ruffenach",
    "Your MP3 files, names, aliases, scores and exam history stay on this computer. No cloud service and no account are required.": "Vos MP3, noms, alias, scores et historiques d'examen restent sur cet ordinateur. Aucun service cloud ni compte n'est nécessaire.",
    "Edit sound": "Modifier le son",
    "Add sound": "Ajouter un son",
    "Display name": "Nom affiché",
    "MP3 file": "Fichier MP3",
    "Start playback at": "Démarrer la lecture à",
    "Aliases, comma-separated": "Alias, séparés par des virgules",
    "Include in training and exams": "Inclure dans les entraînements et les examens",
    "Browse": "Parcourir",
    "Choose MP3": "Choisir un MP3",
    "MP3 files (*.mp3)": "Fichiers MP3 (*.mp3)",
    "Save": "Enregistrer",
    " seconds": " secondes",
    "Missing information": "Informations manquantes",
    "A display name and MP3 file are required.": "Un nom affiché et un fichier MP3 sont obligatoires.",
    "Already in library": "Déjà dans la bibliothèque",
    "This file is already in your library. Edit its existing entry instead.": "Ce fichier est déjà dans la bibliothèque. Modifiez son entrée existante.",
    "Select a sound": "Choisir un son",
    "Select a library row first.": "Sélectionnez d'abord une ligne de la bibliothèque.",
    "Remove sounds": "Supprimer des sons",
    "Remove {count} selected sound(s) and their local history?": "Supprimer les {count} sons sélectionnés et leur historique local ?",
    "Keep exam history": "Conserver l'historique des examens",
    "Export library": "Exporter la bibliothèque",
    "Import library": "Importer la bibliothèque",
    "Export failed": "Échec de l'export",
    "Import failed": "Échec de l'import",
    "Missing paths": "Fichiers introuvables",
    "Now listening": "Lecture en cours",
    "What sound are you hearing?": "Quel son entendez-vous ?",
    "The answer is waiting when you are ready.": "Révélez la réponse quand vous êtes prêt.",
    "No sound available": "Aucun son disponible",
    "Cannot start exam": "Impossible de commencer l'examen",
    "Cancel exam": "Annuler l'examen",
    "Discard this unfinished exam?": "Abandonner cet examen inachevé ?",
    "Question {current} / {total}": "Question {current} / {total}",
    "Answer when ready": "Répondez quand vous êtes prêt",
    "Answer recorded": "Réponse enregistrée",
    "Expected: {name}\n{result} · {similarity:.0f}%": "Réponse attendue : {name}\n{result} · {similarity:.0f} %",
    "Correct": "Correcte",
    "Almost": "Presque correcte",
    "Incorrect": "Incorrecte",
    "<b>{count} active sounds, ready when you are.</b><br>Training success: {rate:.0f}% across {attempts} attempts · {exams} completed exams": "<b>{count} sons actifs, prêts quand vous l'êtes.</b><br>Réussite en entraînement : {rate:.0f} % sur {attempts} tentatives · {exams} examens terminés",
    "{active} active sounds · {shown} shown": "{active} sons actifs · {shown} affichés",
    "{correct}/{total}\n<span>correct answers</span>": "{correct}/{total}\n<span>réponses correctes</span>",
    "{percentage:.0f}% score · {incorrect} incorrect · {almost} almost correct · {minutes}:{seconds:02d} duration": "Score : {percentage:.0f} % · {incorrect} incorrectes · {almost} presque correctes · Durée : {minutes}:{seconds:02d}",
    "<b>{attempts} training attempts · {rate:.0f}% global success · {exams} completed exams</b>": "<b>{attempts} tentatives d'entraînement · {rate:.0f} % de réussite globale · {exams} examens terminés</b>",
    "Recent exams: {exams}": "Examens récents : {exams}",
    "No exams yet.": "Aucun examen pour le moment.",
    "Never": "Jamais",
    "Uncategorised": "Sans catégorie",
    "Enabled": "Activé",
    "Paused": "Désactivé",
    "One sound selected": "Un son sélectionné",
    "{count} sounds selected": "{count} sons sélectionnés",
    "Choose a category, then assign it to the checked sounds.": "Choisissez une catégorie, puis attribuez-la aux sons cochés.",
    "Organize several sounds at once": "Organisez plusieurs sons à la fois",
    "Use the checkboxes beside each sound to prepare a category assignment.": "Cochez les sons auxquels vous souhaitez attribuer une catégorie.",
    "Check thresholds": "Vérifier les seuils",
    "Almost-correct threshold cannot be higher than correct threshold.": "Le seuil de réponse approchante ne peut pas dépasser le seuil de bonne réponse.",
    "Settings saved": "Paramètres enregistrés",
    "Your local playback start and assessment defaults were updated.": "Vos préférences de lecture et d'évaluation ont été mises à jour.",
    "Choose sounds": "Choisir des sons",
    "Tick the checkbox beside one or more sounds, then choose a category.": "Cochez un ou plusieurs sons, puis choisissez une catégorie.",
    "Choose a category": "Choisir une catégorie",
    "Type a category name or choose one from the list.": "Saisissez une catégorie ou choisissez-en une dans la liste.",
    "Category “{category}” assigned to one sound": "Catégorie « {category} » attribuée à un son",
    "Category “{category}” assigned to {count} sounds": "Catégorie « {category} » attribuée à {count} sons",
    "Select more sounds whenever you are ready.": "Sélectionnez d'autres sons quand vous le souhaitez.",
    "Tick one or more sounds, then choose Play checked.": "Cochez un ou plusieurs sons, puis choisissez Lire les sons cochés.",
    "Playing one sound": "Lecture d'un son",
    "Playing {count} sounds": "Lecture de {count} sons",
    "Choose or type a category before playing it.": "Choisissez ou saisissez une catégorie avant de lancer la lecture.",
    "No enabled sounds are in {category}.": "Aucun son activé dans la catégorie {category}.",
    "Playing {count} sounds from {category}": "Lecture de {count} sons de la catégorie {category}",
    "At least one enabled sound is required.": "Au moins un son activé est nécessaire.",
    "Add and enable at least one sound first.": "Ajoutez et activez d'abord au moins un son.",
    "Question count must be positive.": "Le nombre de questions doit être supérieur à zéro.",
    "{count} questions require repeats: only {available} enabled sounds are available.": "Les {count} questions nécessitent des répétitions : seuls {available} sons activés sont disponibles.",
    "Level 1 requires at least five enabled sounds.": "Le niveau 1 nécessite au moins cinq sons activés.",
    "This sound belongs to a completed exam. Disable it instead to preserve exam history.": "Ce son appartient à un examen terminé. Désactivez-le pour conserver l'historique de l'examen.",
    "A library must be a JSON array of sounds.": "La bibliothèque doit être une liste de sons au format JSON.",
    "Sound {index} must be an object.": "Le son {index} doit être un objet JSON.",
    "Sound {index} requires a name and a valid file path.": "Le son {index} doit avoir un nom et un chemin de fichier valide.",
    "Sound {index} offset must be between 0 and 3600 seconds.": "Le décalage du son {index} doit être compris entre 0 et 3600 secondes.",
    "Sound {index} has invalid enabled, category or aliases values.": "Les valeurs d'activation, de catégorie ou d'alias du son {index} sont invalides.",
    "The JSON file is invalid. Check its contents and try again.": "Le fichier JSON est invalide. Vérifiez son contenu et réessayez.",
    "The operation could not be completed. Check the selected file and try again.": "L'opération n'a pas pu aboutir. Vérifiez le fichier sélectionné et réessayez.",
})


def translate(source: str, language: str, **values) -> str:
    text = FRENCH.get(source, source) if language == "fr" else source
    return text.format(**values) if values else text


def translated_error(error: Exception, language: str) -> str:
    message = str(error)
    if message in FRENCH:
        return translate(message, language)
    for template in FRENCH:
        parts = list(Formatter().parse(template))
        if not any(field for _, field, _, _ in parts):
            continue
        pattern = ''.join(re.escape(literal) + (f'(?P<{field}>.+?)' if field else '') for literal, field, _, _ in parts)
        match = re.fullmatch(pattern, message)
        if match:
            return translate(template, language, **match.groupdict())
    if isinstance(error, (ValueError, UnicodeError)):
        return translate("The JSON file is invalid. Check its contents and try again.", language)
    return translate("The operation could not be completed. Check the selected file and try again.", language)


def install_qt_language(language: str) -> None:
    app = QApplication.instance()
    previous = getattr(app, '_sound_translator', None)
    if previous is not None:
        app.removeTranslator(previous)
        previous.deleteLater()
    app._sound_translator = None
    QLocale.setDefault(QLocale('fr_FR' if language == 'fr' else 'en_US'))
    if language == 'fr':
        translator = QTranslator(app)
        roots = [Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[2])) / 'translations', Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))]
        if not any(translator.load(str(root / 'qtbase_fr.qm')) for root in roots):
            raise RuntimeError('French Qt translation file is missing')
        app.installTranslator(translator)
        app._sound_translator = translator


class LocalizationMixin:
    def t(self, source: str, **values) -> str:
        return translate(source, self.language, **values)

    def error_text(self, error: Exception) -> str:
        return translated_error(error, self.language)

    def set_text(self, widget, source: str, **values) -> None:
        widget.setProperty('i18n_user_text', False)
        widget.setProperty('source_text', source)
        widget.setProperty('source_values', values)
        widget.setText(self.t(source, **values))

    def set_user_text(self, widget, text: str) -> None:
        widget.setProperty('i18n_user_text', True)
        widget.setText(text)

    def translate_widgets(self) -> None:
        self.setLocale(QLocale('fr_FR' if self.language == 'fr' else 'en_US'))
        for layout in self.findChildren(QFormLayout):
            layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        for widget in self.findChildren(QWidget):
            if isinstance(widget, QLabel):
                widget.setWordWrap(True)
            if isinstance(widget, (QLabel, QPushButton, QCheckBox)) and not widget.property('i18n_user_text'):
                source = widget.property('source_text')
                if source is None:
                    source = widget.text()
                    widget.setProperty('source_text', source)
                widget.setText(self.t(source, **(widget.property('source_values') or {})))
            if isinstance(widget, (QLineEdit, QComboBox)):
                source = widget.property('source_placeholder')
                if source is None:
                    source = widget.placeholderText()
                    widget.setProperty('source_placeholder', source)
                widget.setPlaceholderText(self.t(source))
            source = widget.property('source_tooltip')
            if source is None:
                source = widget.toolTip()
                widget.setProperty('source_tooltip', source)
            widget.setToolTip(self.t(source))
            if isinstance(widget, QDoubleSpinBox):
                for field, getter, setter in [('suffix', widget.suffix, widget.setSuffix), ('special', widget.specialValueText, widget.setSpecialValueText)]:
                    source = widget.property('source_' + field)
                    if source is None:
                        source = getter()
                        widget.setProperty('source_' + field, source)
                    setter(self.t(source))
