from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import *
from src.database import Repository
from src.models import Sound
from src.services.audio import AudioPlayer
from src.services.selection import exam_questions, multiple_choice_options, training_choice
from src.utils.answers import compare_answer, MatchResult, normalize_answer

FRENCH = {"Home":"Accueil","Sound Library":"Bibliothèque sonore","Training":"Entraînement","Exam":"Examen","Statistics":"Statistiques","Settings":"Paramètres","About":"À propos","Add MP3 files":"Ajouter des MP3","Preview":"Écouter","Edit":"Modifier","Remove":"Supprimer","Import JSON":"Importer JSON","Export JSON":"Exporter JSON","Select shown":"Tout sélectionner","Assign category":"Attribuer la catégorie","Clear":"Effacer","Start a training round":"Commencer un entraînement","Set up an exam":"Préparer un examen","Play a new sound":"Lire un nouveau son","Replay":"Réécouter","Pause / resume":"Pause / reprendre","Reveal answer":"Afficher la réponse","I missed it":"Je ne savais pas","I was correct":"J'avais juste","Start exam":"Commencer l'examen","Submit answer":"Valider la réponse","Cancel":"Annuler","New exam":"Nouvel examen","Save local settings":"Enregistrer les paramètres","Language":"Langue","Volume":"Volume","Your data":"Vos données","Your audio":"Vos audios","Cloud and accounts":"Cloud et comptes","Workspace":"Espace local"}
FRENCH.update({"Learn the sound. Trust the answer.":"Apprenez le son. Faites confiance à votre réponse.","A focused, local workspace for turning your MP3 collection into exam confidence.":"Un espace local pour transformer vos MP3 en confiance pour l'examen.","Manage the source material for every practice session. Original MP3 files are never modified.":"Gérez les sons de vos séances. Les MP3 originaux ne sont jamais modifiés.","Practise deliberately. No timer, no penalty — only useful repetition.":"Entraînez-vous sans chronomètre ni pénalité, avec des répétitions utiles.","Turn practice into a clear result, then replay every sound worth revisiting.":"Transformez vos entraînements en résultat clair, puis réécoutez les sons à revoir.","Use recent evidence to choose what deserves your next practice session.":"Utilisez vos résultats récents pour choisir les sons à retravailler.","Local defaults for playback and free-text answer assessment.":"Préférences locales de lecture et d'évaluation des réponses.","A focused, offline desktop tool for serious sound-recognition practice.":"Un outil de bureau hors ligne pour un entraînement sérieux à la reconnaissance sonore.","Search sound name or category":"Rechercher un son ou une catégorie","Choose or type a category":"Choisir ou saisir une catégorie","Start every playback at":"Démarrer toutes les lectures à","Default offset for new sounds":"Décalage par défaut des nouveaux sons","Correct threshold":"Seuil de bonne réponse","Almost-correct threshold":"Seuil de réponse approchante","Reveal in exam":"Afficher la réponse pendant l'examen","Allow repeats":"Autoriser les répétitions","Prioritize difficult":"Privilégier les sons difficiles","All categories":"Toutes les catégories","Scope":"Périmètre","Questions":"Questions","Difficulty":"Niveau","Show missed and almost-correct only":"Afficher seulement les erreurs et réponses approchantes","Replay selected sound":"Réécouter le son sélectionné","Sound":"Son","Category":"Catégorie","Offset":"Décalage","Ready":"Prêt","File":"Fichier","Attempts":"Tentatives","Success":"Réussite","Last practiced":"Dernier entraînement","Your answer":"Votre réponse","Expected answer":"Réponse attendue","Similarity":"Similarité","Outcome":"Résultat","LOCAL WORKSPACE\nNo account. No cloud.":"ESPACE LOCAL\nSans compte. Sans cloud."})

def button(text: str, kind: str = "primary") -> QPushButton:
    w = QPushButton(text); w.setObjectName(f"button_{kind}"); return w

class SoundDialog(QDialog):
    def __init__(self, parent: QWidget, repo: Repository, sound: Sound | None = None):
        super().__init__(parent); self.repo, self.sound = repo, sound; self.setWindowTitle("Edit sound" if sound else "Add sound"); self.setMinimumWidth(500)
        form = QFormLayout(self); self.name, self.path, self.category, self.aliases = QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(); self.offset = QDoubleSpinBox(); self.offset.setRange(0,3600); self.offset.setDecimals(2); self.offset.setSuffix(" seconds"); self.enabled=QCheckBox("Include in training and exams"); self.enabled.setChecked(True)
        browse=button("Browse", "secondary"); browse.clicked.connect(self.browse); row=QHBoxLayout(); row.addWidget(self.path); row.addWidget(browse)
        for label,field in (("Display name",self.name),("MP3 file",row),("Start playback at",self.offset),("Category",self.category),("Aliases, comma-separated",self.aliases),("",self.enabled)): form.addRow(label,field)
        b=QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save); b.accepted.connect(self.accept); b.rejected.connect(self.reject); form.addRow(b)
        if sound: self.name.setText(sound.name); self.path.setText(str(sound.filepath)); self.offset.setValue(sound.start_offset); self.category.setText(sound.category or ""); self.aliases.setText(", ".join(repo.aliases(sound.id))); self.enabled.setChecked(sound.enabled)
        else: self.offset.setValue(repo.settings()["default_offset"])
    def browse(self):
        p,_=QFileDialog.getOpenFileName(self,"Choose MP3",filter="MP3 files (*.mp3)")
        if p: self.path.setText(p); self.name.setText(self.name.text() or Path(p).stem)
    def accept(self):
        if not self.name.text().strip() or not self.path.text().strip(): QMessageBox.warning(self,"Missing information","A display name and MP3 file are required."); return
        try:
            self.repo.save_sound(self.name.text().strip(),self.path.text().strip(),self.offset.value(),self.enabled.isChecked(),self.category.text().strip() or None,self.aliases.text().split(","),self.sound.id if self.sound else None)
        except sqlite3.IntegrityError:
            QMessageBox.warning(self,"Already in library","This file is already in your library. Edit its existing entry instead."); return
        super().accept()

class MainWindow(QMainWindow):
    def __init__(self, repo: Repository):
        super().__init__(); self.repo=repo; self.language=repo.settings().get("language","en"); self.audio=AudioPlayer(repo.settings()["volume"]); self.training_sound=None; self.exam=None; self.last_exam_id=None; self.checked_sound_ids:set[int]=set(); self.setWindowTitle("Sound Recognition Trainer"); self.setWindowIcon(QIcon(str(Path(__file__).resolve().parents[2] / "assets" / "sound-recognition-trainer.svg"))); self.resize(1240,780); self.setMinimumSize(1000,680); self.build(); self.apply_language()
    def page(self,title,subtitle):
        p=QWidget(); l=QVBoxLayout(p); l.setContentsMargins(42,34,42,34); h=QLabel(title); h.setObjectName("page_title"); s=QLabel(subtitle); s.setObjectName("page_description"); l.addWidget(h);l.addWidget(s);return p,l
    def panel(self): w=QFrame();w.setObjectName("panel");return w
    def build(self):
        root=QWidget(); r=QHBoxLayout(root);r.setContentsMargins(0,0,0,0);r.setSpacing(0);self.setCentralWidget(root); side=QFrame();side.setObjectName("sidebar");side.setFixedWidth(244);sl=QVBoxLayout(side);sl.setContentsMargins(22,28,18,22);brand=QLabel("Sound\nRecognition\nTrainer");brand.setObjectName("brand");sl.addWidget(brand);sl.addSpacing(28);self.nav=QListWidget();self.nav.setObjectName("navigation");self.nav.setIconSize(QSize(18,18));self.nav.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);self.nav.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents);nav_items=(("Home",QStyle.StandardPixmap.SP_ComputerIcon),("Sound Library",QStyle.StandardPixmap.SP_DirOpenIcon),("Training",QStyle.StandardPixmap.SP_MediaPlay),("Exam",QStyle.StandardPixmap.SP_DialogApplyButton),("Statistics",QStyle.StandardPixmap.SP_FileDialogDetailedView),("Settings",QStyle.StandardPixmap.SP_FileDialogContentsView),("About",QStyle.StandardPixmap.SP_MessageBoxInformation));[self.nav.addItem(QListWidgetItem(self.style().standardIcon(icon),label)) for label,icon in nav_items];self.nav.currentRowChanged.connect(self.change);sl.addWidget(self.nav);sl.addStretch();f=QLabel("LOCAL WORKSPACE\nNo account. No cloud.");f.setObjectName("sidebar_footer");sl.addWidget(f);r.addWidget(side);self.pages=QStackedWidget();r.addWidget(self.pages,1)
        for p in (self.home(),self.library(),self.training(),self.exam_page(),self.statistics(),self.settings(),self.about()):self.pages.addWidget(p)
        self.nav.setCurrentRow(0)
    def home(self):
        p,l=self.page("Learn the sound. Trust the answer.","A focused, local workspace for turning your MP3 collection into exam confidence.");hero=self.panel();hero.setObjectName("home_hero");hl=QVBoxLayout(hero);self.home_summary=QLabel();self.home_summary.setObjectName("home_summary");hl.addWidget(self.home_summary);a=QHBoxLayout();b=button("Start a training round");b.clicked.connect(lambda:self.nav.setCurrentRow(2));e=button("Set up an exam","secondary");e.clicked.connect(lambda:self.nav.setCurrentRow(3));a.addWidget(b);a.addWidget(e);a.addStretch();hl.addLayout(a);l.addWidget(hero);l.addStretch();return p
    def library(self):
        p,l=self.page("Sound Library","Manage the source material for every practice session. Original MP3 files are never modified.");bar=QHBoxLayout();self.search=QLineEdit();self.search.setPlaceholderText("Search sound name or category");self.search.textChanged.connect(self.refresh_library);bar.addWidget(self.search,1)
        for label,fn,kind in (("Add MP3 files",self.add_sounds,"primary"),("Preview",self.preview,"secondary"),("Edit",self.edit,"secondary"),("Enable / disable",self.toggle,"secondary"),("Remove",self.remove,"danger")):
            b=button(label,kind);b.clicked.connect(fn);bar.addWidget(b)
        l.addLayout(bar);meta=QHBoxLayout();self.library_status=QLabel();self.library_status.setObjectName("status_line");meta.addWidget(self.library_status);meta.addStretch();imp=button("Import JSON","quiet");imp.clicked.connect(self.import_library);exp=button("Export JSON","quiet");exp.clicked.connect(self.export_library);meta.addWidget(imp);meta.addWidget(exp);l.addLayout(meta)
        self.bulk_assign=QFrame();self.bulk_assign.setObjectName("bulk_assign");bulk=QHBoxLayout(self.bulk_assign);bulk.setContentsMargins(16,10,16,10);bulk.setSpacing(10);self.select_visible=QCheckBox("Select shown");self.select_visible.toggled.connect(self.toggle_visible_checked);bulk.addWidget(self.select_visible);copy=QVBoxLayout();copy.setSpacing(1);self.bulk_assign_title=QLabel();self.bulk_assign_title.setObjectName("bulk_assign_title");self.bulk_assign_help=QLabel();self.bulk_assign_help.setObjectName("bulk_assign_help");copy.addWidget(self.bulk_assign_title);copy.addWidget(self.bulk_assign_help);bulk.addLayout(copy,1);shuffle=QCheckBox("Shuffle");self.library_shuffle=shuffle;bulk.addWidget(shuffle);play=button("Play checked","secondary");play.clicked.connect(self.play_checked);bulk.addWidget(play);self.category_assign=QComboBox();self.category_assign.setEditable(True);self.category_assign.setMinimumWidth(160);self.category_assign.setPlaceholderText("Choose or type a category");bulk.addWidget(self.category_assign);play_category=button("Play category","secondary");play_category.clicked.connect(self.play_category);bulk.addWidget(play_category);assign=button("Assign category");assign.clicked.connect(self.assign_category);bulk.addWidget(assign);clear=button("Clear","quiet");clear.clicked.connect(self.clear_checked_sounds);bulk.addWidget(clear);l.addWidget(self.bulk_assign)
        self.table=QTableWidget(0,6);self.table.setObjectName("data_table");self.table.setHorizontalHeaderLabels(("","Sound","Category","Offset","Ready","File"));self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection);self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);self.table.verticalHeader().setVisible(False);self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Fixed);self.table.setColumnWidth(0,42);self.table.horizontalHeader().setStretchLastSection(True);self.table.itemChanged.connect(self.library_item_changed);self.table.doubleClicked.connect(self.edit);l.addWidget(self.table,1);return p
    def training(self):
        p,l=self.page("Training","Practise deliberately. No timer, no penalty — only useful repetition.");bar=QHBoxLayout();self.training_category=QComboBox();self.training_category.addItem("All categories",None);self.priority=QCheckBox("Prioritize difficult sounds");self.priority.setChecked(self.repo.settings()["prioritize_difficult"]);new=button("Play a new sound");new.clicked.connect(self.next_training);bar.addWidget(QLabel("Scope"));bar.addWidget(self.training_category);bar.addWidget(self.priority);bar.addStretch();bar.addWidget(new);l.addLayout(bar);stage=self.panel();stage.setObjectName("listening_stage");st=QVBoxLayout(stage);self.training_status=QLabel("Ready when you are");self.training_status.setObjectName("stage_status");self.training_question=QLabel("Choose a sound and identify what you hear.");self.training_question.setObjectName("stage_question");self.reveal=QLabel("The answer stays hidden until you reveal it.");self.reveal.setObjectName("stage_answer");[x.setAlignment(Qt.AlignmentFlag.AlignCenter) for x in (self.training_status,self.training_question,self.reveal)];[st.addWidget(x) for x in (self.training_status,self.training_question,self.reveal)];l.addWidget(stage,1);a=QHBoxLayout();
        for label,fn,kind in (("Replay",self.replay_training,"secondary"),("Pause / resume",self.audio.pause_or_resume,"quiet"),("Reveal answer",self.reveal_training,"quiet"),("I missed it",lambda:self.score(False),"danger"),("I was correct",lambda:self.score(True),"primary")):
            b=button(label,kind);b.clicked.connect(fn);a.addWidget(b)
        l.addLayout(a);return p
    def exam_page(self):
        p,l=self.page("Exam","Turn practice into a clear result, then replay every sound worth revisiting.");self.exam_stack=QStackedWidget();self.exam_stack.addWidget(self.exam_setup());self.exam_stack.addWidget(self.exam_session());self.exam_stack.addWidget(self.exam_results());l.addWidget(self.exam_stack,1);return p
    def exam_setup(self):
        w=QWidget();r=QHBoxLayout(w);card=self.panel();f=QFormLayout(card);intro=QLabel("Choose the conditions. The app verifies library requirements before the exam starts.");intro.setWordWrap(True);f.addRow(intro);self.exam_count=QComboBox();self.exam_count.addItems(("5","10","20","30"));self.level=QComboBox();self.level.addItem("Level 1 — Multiple choice",1);self.level.addItem("Level 2 — Free text",2);self.repeats=QCheckBox("Allow repeated sounds");self.repeats.setChecked(self.repo.settings()["allow_repeats"]);self.reveal_now=QCheckBox("Reveal answers immediately");self.reveal_now.setChecked(self.repo.settings()["reveal_immediately"]);start=button("Start exam");start.clicked.connect(self.start_exam);[f.addRow(k,v) for k,v in (("Questions",self.exam_count),("Difficulty",self.level),("",self.repeats),("",self.reveal_now),("",start))];note=self.panel();nl=QVBoxLayout(note);t=QLabel("A fair test, with useful evidence");t.setObjectName("note_title");c=QLabel("Level 1 offers one correct answer and four alternatives. Level 2 accepts aliases, removed accents and minor typos according to Settings.");c.setWordWrap(True);nl.addWidget(t);nl.addWidget(c);nl.addStretch();r.addWidget(card,2);r.addWidget(note,1);return w
    def exam_session(self):
        w=QWidget();l=QVBoxLayout(w);top=QHBoxLayout();self.exam_progress=QLabel();self.exam_feedback=QLabel();top.addWidget(self.exam_progress);top.addStretch();top.addWidget(self.exam_feedback);l.addLayout(top);stage=self.panel();stage.setObjectName("exam_stage");sl=QVBoxLayout(stage);self.exam_prompt=QLabel("Listen carefully.");self.exam_prompt.setObjectName("stage_question");self.exam_prompt.setAlignment(Qt.AlignmentFlag.AlignCenter);self.exam_answer=QLineEdit();self.exam_answer.setPlaceholderText("Type the sound name");self.options=QVBoxLayout();sl.addWidget(self.exam_prompt);sl.addWidget(self.exam_answer);sl.addLayout(self.options);l.addWidget(stage,1);a=QHBoxLayout();
        for label,fn,kind in (("Replay",self.replay_exam,"secondary"),("Pause / resume",self.audio.pause_or_resume,"quiet"),("Cancel",self.cancel_exam,"quiet")):
            b=button(label,kind);b.clicked.connect(fn);a.addWidget(b)
        a.addStretch();self.submit=button("Submit answer");self.submit.clicked.connect(lambda checked=False:self.submit_answer());a.addWidget(self.submit);l.addLayout(a);return w
    def exam_results(self):
        w=QWidget();l=QVBoxLayout(w);banner=self.panel();banner.setObjectName("result_banner");bl=QHBoxLayout(banner);self.result_score=QLabel();self.result_score.setObjectName("result_score");self.result_detail=QLabel();self.result_detail.setObjectName("result_detail");bl.addWidget(self.result_score);bl.addWidget(self.result_detail,1);l.addWidget(banner);a=QHBoxLayout();self.missed=QCheckBox("Show missed and almost-correct only");self.missed.toggled.connect(self.populate_results);a.addWidget(self.missed);a.addStretch();b=button("Replay selected sound","secondary");b.clicked.connect(self.replay_result);a.addWidget(b);n=button("New exam");n.clicked.connect(lambda:self.exam_stack.setCurrentIndex(0));a.addWidget(n);l.addLayout(a);self.results=QTableWidget(0,5);self.results.setObjectName("data_table");self.results.setHorizontalHeaderLabels(("Sound","Your answer","Expected answer","Similarity","Outcome"));self.results.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);self.results.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);self.results.verticalHeader().setVisible(False);self.results.horizontalHeader().setStretchLastSection(True);self.results.doubleClicked.connect(self.replay_result);l.addWidget(self.results,1);return w
    def statistics(self):
        p,l=self.page("Statistics","Use recent evidence to choose what deserves your next practice session.");self.stats=QLabel();self.stats.setObjectName("home_summary");l.addWidget(self.stats);self.stats_table=QTableWidget(0,4);self.stats_table.setObjectName("data_table");self.stats_table.setHorizontalHeaderLabels(("Sound","Attempts","Success","Last practiced"));self.stats_table.verticalHeader().setVisible(False);self.stats_table.horizontalHeader().setStretchLastSection(True);l.addWidget(self.stats_table,1);self.history=QLabel();l.addWidget(self.history);return p
    def about(self):
        p,l=self.page("About Sound Recognition Trainer","A focused, offline desktop tool for serious sound-recognition practice.");intro=self.panel();intro.setObjectName("home_hero");il=QVBoxLayout(intro);name=QLabel("Sound Recognition Trainer");name.setObjectName("page_title");by=QLabel("Version 1.0.0 · Created by Michael Ruffenach");by.setObjectName("home_summary");copy=QLabel("Turn a personal MP3 collection into purposeful practice, then use clear exam evidence to decide what to learn next.");copy.setWordWrap(True);il.addWidget(name);il.addWidget(by);il.addSpacing(8);il.addWidget(copy);l.addWidget(intro);details=self.panel();form=QFormLayout(details);form.setContentsMargins(20,18,20,18);form.addRow("Your data",QLabel("Stored locally in a SQLite workspace"));form.addRow("Your audio",QLabel("Read in place; original MP3 files are never changed"));form.addRow("Cloud and accounts",QLabel("Not required"));form.addRow("Workspace",QLabel("~/.sound-recognition-trainer/"));l.addWidget(details);help=QLabel("Need a change or found a problem? Share the workflow that led to it so the next version can improve the right learning moment.");help.setWordWrap(True);help.setObjectName("page_description");l.addWidget(help);l.addStretch();return p
    def change(self,i):
        self.pages.setCurrentIndex(i)
        if i==0:self.refresh_home()
        elif i==1:self.refresh_library()
        elif i==2:self.refresh_filters()
        elif i==4:self.refresh_stats()
    def refresh_home(self):
        s=self.repo.statistics();self.home_summary.setText(f"<b>{len(self.repo.sounds(enabled_only=True))} active sounds, ready when you are.</b><br>Training success: {s['rate']*100:.0f}% across {s['attempts']} attempts · {s['exams']} completed exams")
    def refresh_library(self):
        sounds=self.repo.sounds(self.search.text());self.table.setRowCount(len(sounds));self.library_status.setText(f"{len(self.repo.sounds(enabled_only=True))} active sounds · {len(sounds)} shown")
        current=self.category_assign.currentText();self.category_assign.blockSignals(True);self.category_assign.clear();self.category_assign.addItem("");[self.category_assign.addItem(category) for category in sorted({sound.category for sound in self.repo.sounds() if sound.category})];self.category_assign.setEditText(current);self.category_assign.blockSignals(False)
        for r,s in enumerate(sounds):
            for c,v in enumerate((s.name,s.category or "Uncategorised",f"{s.start_offset:.2f} s","Enabled" if s.enabled else "Paused",str(s.filepath))): it=QTableWidgetItem(v);it.setData(Qt.ItemDataRole.UserRole,s.id);self.table.setItem(r,c,it)
    def selected(self): return [self.repo.sound(self.table.item(x.row(),0).data(Qt.ItemDataRole.UserRole)) for x in self.table.selectionModel().selectedRows()]
    def add_sounds(self):
        files,_=QFileDialog.getOpenFileNames(self,"Add MP3 files",filter="MP3 files (*.mp3)")
        existing={str(sound.filepath) for sound in self.repo.sounds()}
        for file in files:
            if file not in existing:
                self.repo.save_sound(Path(file).stem,file,self.repo.settings()["default_offset"],True,None,[]);existing.add(file)
        self.refresh_library()
    def preview(self):
        x=self.selected(); self.play_sound(x[0]) if x else QMessageBox.information(self,"Select a sound","Select a library row first.")
    def edit(self):
        x=self.selected();
        if x and SoundDialog(self,self.repo,x[0]).exec():self.refresh_library()
    def toggle(self):
        for s in self.selected():self.repo.save_sound(s.name,str(s.filepath),s.start_offset,not s.enabled,s.category,self.repo.aliases(s.id),s.id)
        self.refresh_library()
    def play_sound(self, sound: Sound):
        """Apply the learner's common listening start without losing a sound-specific skip."""
        self.audio.play(sound, self.global_playback_offset.value())

    def settings(self):
        p,l=self.page("Settings","Local defaults for playback and free-text answer assessment.");card=self.panel();f=QFormLayout(card);s=self.repo.settings();self.volume=QSpinBox();self.volume.setRange(0,100);self.volume.setValue(s["volume"]);self.offset=QDoubleSpinBox();self.offset.setRange(0,3600);self.offset.setValue(s["default_offset"]);self.global_playback_offset=QDoubleSpinBox();self.global_playback_offset.setRange(0,3600);self.global_playback_offset.setDecimals(2);self.global_playback_offset.setSuffix(" seconds");self.global_playback_offset.setSpecialValueText("From each sound's own offset");self.global_playback_offset.setValue(s["global_playback_offset"]);self.global_playback_offset.setToolTip("Every preview, training round, exam question, and replay starts no earlier than this point.");self.correct=QSpinBox();self.correct.setRange(1,100);self.correct.setValue(s["correct_threshold"]);self.almost=QSpinBox();self.almost.setRange(1,100);self.almost.setValue(s["almost_threshold"]);self.default_reveal=QCheckBox();self.default_reveal.setChecked(s["reveal_immediately"]);self.default_repeat=QCheckBox();self.default_repeat.setChecked(s["allow_repeats"]);self.default_priority=QCheckBox();self.default_priority.setChecked(s["prioritize_difficult"]);help=QLabel("Use a common start time to skip the beginning of every recording. A sound with its own later offset still starts later.");help.setWordWrap(True);help.setObjectName("page_description");f.addRow(help);[f.addRow(k,v) for k,v in (("Volume",self.volume),("Default offset for new sounds",self.offset),("Start every playback at",self.global_playback_offset),("Correct threshold",self.correct),("Almost-correct threshold",self.almost),("Reveal in exam",self.default_reveal),("Allow repeats",self.default_repeat),("Prioritize difficult",self.default_priority))];b=button("Save local settings");b.clicked.connect(self.save_settings);f.addRow("",b);l.addWidget(card);l.addStretch();return p

    def assign_category(self):
        sounds=self.selected(); category=self.category_assign.currentText().strip()
        if not sounds: QMessageBox.information(self,"Select sounds","Select one or more sound rows before applying a category."); return
        if not category: QMessageBox.information(self,"Choose a category","Type a category name or choose one from the list."); return
        for sound in sounds:self.repo.save_sound(sound.name,str(sound.filepath),sound.start_offset,sound.enabled,category,self.repo.aliases(sound.id),sound.id)
        self.refresh_library()
    def remove(self):
        x=self.selected()
        if x and QMessageBox.question(self,"Remove sounds",f"Remove {len(x)} selected sound(s) and their local history?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes:
            try:
                for sound in x:self.repo.delete_sound(sound.id)
            except ValueError as error:
                QMessageBox.warning(self,"Keep exam history",str(error))
            self.refresh_library()
    def export_library(self):
        p,_=QFileDialog.getSaveFileName(self,"Export library","sound-library.json","JSON (*.json)")
        if p:
            try:self.repo.export_library(Path(p))
            except OSError as error:QMessageBox.warning(self,"Export failed",str(error))
    def import_library(self):
        p,_=QFileDialog.getOpenFileName(self,"Import library",filter="JSON (*.json)")
        if p:
            try:missing=self.repo.import_library(Path(p))
            except (OSError, ValueError, sqlite3.Error) as error:
                QMessageBox.warning(self,"Import failed",str(error));return
            self.refresh_library();QMessageBox.warning(self,"Missing paths","\n".join(missing)) if missing else None
    def refresh_filters(self):
        current=self.training_category.currentData();self.training_category.clear();self.training_category.addItem("All categories",None);[self.training_category.addItem(c,c) for c in sorted({x.category for x in self.repo.sounds(enabled_only=True) if x.category})];self.training_category.setCurrentIndex(max(0,self.training_category.findData(current)))
    def next_training(self):
        try:
            self.training_sound=training_choice(self.repo.sounds(enabled_only=True,category=self.training_category.currentData()),self.repo.success_rates(),self.priority.isChecked());self.training_status.setText("Now listening");self.training_question.setText("What sound are you hearing?");self.reveal.setText("The answer is waiting when you are ready.");self.play_sound(self.training_sound)
        except ValueError as e:QMessageBox.warning(self,"No sound available",str(e))
    def replay_training(self):
        if self.training_sound:self.play_sound(self.training_sound)
    def reveal_training(self):
        if self.training_sound:self.reveal.setText(self.training_sound.name)
    def score(self,ok):
        if self.training_sound:self.repo.record_training(self.training_sound.id,ok);self.next_training()
    def start_exam(self):
        try:
            sounds=self.repo.sounds(enabled_only=True);q=exam_questions(sounds,int(self.exam_count.currentText()),self.repeats.isChecked())
            if self.level.currentData()==1 and len(sounds)<5:raise ValueError("Level 1 requires at least five enabled sounds.")
            self.exam={"questions":q,"index":0,"answers":[],"difficulty":self.level.currentData(),"reveal":self.reveal_now.isChecked(),"started":datetime.now(timezone.utc).isoformat()};self.exam_stack.setCurrentIndex(1);self.show_question()
        except ValueError as e:QMessageBox.warning(self,"Cannot start exam",str(e))
    def cancel_exam(self):
        if self.exam and QMessageBox.question(self,"Cancel exam","Discard this unfinished exam?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes:self.audio.stop();self.exam=None;self.exam_stack.setCurrentIndex(0)
    def show_question(self):
        s=self.exam["questions"][self.exam["index"]];self.exam_progress.setText(f"Question {self.exam['index']+1} / {len(self.exam['questions'])}");self.exam_feedback.setText("Answer when ready");self.exam_answer.clear();free=self.exam["difficulty"]==2;self.exam_answer.setVisible(free);self.submit.setVisible(free)
        while self.options.count():i=self.options.takeAt(0);i.widget().deleteLater() if i.widget() else None
        if not free:
            for o in multiple_choice_options(s,self.repo.sounds(enabled_only=True)):
                b=button(o.name,"choice");b.clicked.connect(lambda checked=False,choice=o:self.submit_answer(choice.name,choice.id));self.options.addWidget(b)
        self.play_sound(s)
    def replay_exam(self):
        if self.exam:self.play_sound(self.exam["questions"][self.exam["index"]])
    def submit_answer(self,answer=None,choice_id=None):
        if not self.exam:return
        s=self.exam["questions"][self.exam["index"]];answer=self.exam_answer.text() if answer is None else answer
        if self.exam["difficulty"]==1:
            correct=choice_id==s.id;m=MatchResult(normalize_answer(answer),100.0 if correct else 0.0,"correct" if correct else "incorrect",s.name)
        else:
            m=compare_answer(answer,s.name,self.repo.aliases(s.id),self.repo.settings()["correct_threshold"],self.repo.settings()["almost_threshold"])
        self.exam["answers"].append({"sound":s,"answer":answer,"normalized":m.normalized,"similarity":m.similarity,"result":m.result})
        if self.exam["reveal"]:QMessageBox.information(self,"Answer recorded",f"Expected: {s.name}\n{m.result.title()} · {m.similarity:.0f}%")
        self.exam["index"]+=1;self.show_question() if self.exam["index"]<len(self.exam["questions"]) else self.finish_exam()
    def finish_exam(self):
        a=self.exam["answers"];self.last_exam_id=self.repo.record_exam(self.exam["difficulty"],self.exam["started"],a);correct=sum(x["result"]=="correct" for x in a);almost=sum(x["result"]=="almost" for x in a);elapsed=datetime.now(timezone.utc)-datetime.fromisoformat(self.exam["started"]);m,s=divmod(int(elapsed.total_seconds()),60);self.result_score.setText(f"{correct}/{len(a)}\n<span>correct answers</span>");self.result_detail.setText(f"{correct/len(a)*100:.0f}% score · {len(a)-correct-almost} incorrect · {almost} almost correct · {m}:{s:02d} duration");self.exam=None;self.missed.setChecked(False);self.populate_results();self.exam_stack.setCurrentIndex(2)
    def populate_results(self):
        rows=self.repo.exam_answers(self.last_exam_id);rows=[x for x in rows if x["result"]!="correct"] if self.missed.isChecked() else rows;self.results.setRowCount(len(rows))
        for r,x in enumerate(rows):
            for c,v in enumerate((x["expected_answer"],x["user_answer"] or "—",x["expected_answer"],f"{x['similarity']:.0f}%",x["result"].title())):i=QTableWidgetItem(v);i.setData(Qt.ItemDataRole.UserRole,x["sound_id"]);self.results.setItem(r,c,i)
    def replay_result(self):
        r=self.results.selectionModel().selectedRows()
        if r:self.play_sound(self.repo.sound(self.results.item(r[0].row(),0).data(Qt.ItemDataRole.UserRole)))
    def refresh_stats(self):
        s=self.repo.statistics();self.stats.setText(f"<b>{s['attempts']} training attempts · {s['rate']*100:.0f}% global success · {s['exams']} completed exams</b>");sounds=self.repo.sounds();self.stats_table.setRowCount(len(sounds))
        for r,x in enumerate(sounds):
            d=self.repo.connection.execute("SELECT COUNT(*) count,COALESCE(AVG(correct),0) rate,MAX(created_at) latest FROM training_results WHERE sound_id=?",(x.id,)).fetchone();[self.stats_table.setItem(r,c,QTableWidgetItem(v)) for c,v in enumerate((x.name,str(d['count']),f"{d['rate']*100:.0f}%",d['latest'][:10] if d['latest'] else "Never"))]
        self.history.setText("Recent exams: "+(" · ".join(f"{e['score']}/{e['question_count']} ({e['percentage']:.0f}%)" for e in self.repo.recent_exams()) or "No exams yet."))
    def refresh_library(self):
        sounds=self.repo.sounds(self.search.text());visible_ids={sound.id for sound in sounds};self.checked_sound_ids.intersection_update({sound.id for sound in self.repo.sounds()});self.table.blockSignals(True);self.table.setRowCount(len(sounds));self.library_status.setText(f"{len(self.repo.sounds(enabled_only=True))} active sounds · {len(sounds)} shown")
        current=self.category_assign.currentText();self.category_assign.blockSignals(True);self.category_assign.clear();self.category_assign.addItem("");[self.category_assign.addItem(category) for category in sorted({sound.category for sound in self.repo.sounds() if sound.category})];self.category_assign.setEditText(current);self.category_assign.blockSignals(False)
        for row,sound in enumerate(sounds):
            checked=QTableWidgetItem();checked.setData(Qt.ItemDataRole.UserRole,sound.id);checked.setFlags(Qt.ItemFlag.ItemIsEnabled|Qt.ItemFlag.ItemIsUserCheckable);checked.setCheckState(Qt.CheckState.Checked if sound.id in self.checked_sound_ids else Qt.CheckState.Unchecked);self.table.setItem(row,0,checked)
            for column,value in enumerate((sound.name,sound.category or "Uncategorised",f"{sound.start_offset:.2f} s","Enabled" if sound.enabled else "Paused",str(sound.filepath)),1): item=QTableWidgetItem(value);item.setData(Qt.ItemDataRole.UserRole,sound.id);self.table.setItem(row,column,item)
        self.table.blockSignals(False);self.update_bulk_assign(visible_ids)

    def library_item_changed(self,item):
        if item.column()!=0:return
        sound_id=item.data(Qt.ItemDataRole.UserRole)
        if item.checkState()==Qt.CheckState.Checked:self.checked_sound_ids.add(sound_id)
        else:self.checked_sound_ids.discard(sound_id)
        self.update_bulk_assign()

    def update_bulk_assign(self,visible_ids=None):
        visible_ids=visible_ids if visible_ids is not None else {self.table.item(row,0).data(Qt.ItemDataRole.UserRole) for row in range(self.table.rowCount())};count=len(self.checked_sound_ids);self.select_visible.blockSignals(True);self.select_visible.setChecked(bool(visible_ids) and visible_ids.issubset(self.checked_sound_ids));self.select_visible.blockSignals(False)
        if count:self.bulk_assign_title.setText(f"{count} sound{'s' if count!=1 else ''} selected");self.bulk_assign_help.setText("Choose a category, then assign it to the checked sounds.")
        else:self.bulk_assign_title.setText("Organize several sounds at once");self.bulk_assign_help.setText("Use the checkboxes beside each sound to prepare a category assignment.")

    def toggle_visible_checked(self,checked):
        visible_ids={self.table.item(row,0).data(Qt.ItemDataRole.UserRole) for row in range(self.table.rowCount())}
        if checked:self.checked_sound_ids.update(visible_ids)
        else:self.checked_sound_ids.difference_update(visible_ids)
        self.refresh_library()

    def clear_checked_sounds(self):
        self.checked_sound_ids.clear();self.refresh_library()

    def selected(self):
        return [self.repo.sound(row_item.data(Qt.ItemDataRole.UserRole)) for row_item in self.table.selectionModel().selectedRows()]

    def change_language(self):
        self.language=self.language_choice.currentData();self.repo.set_settings({"language":self.language});self.apply_language()

    def apply_language(self):
        for widget in self.findChildren(QWidget):
            if isinstance(widget,(QLabel,QPushButton,QCheckBox)):
                source=widget.property("source_text") or widget.text();widget.setProperty("source_text",source);widget.setText(FRENCH.get(source,source) if self.language=="fr" else source)
            elif isinstance(widget,QLineEdit):
                source=widget.property("source_placeholder") or widget.placeholderText();widget.setProperty("source_placeholder",source);widget.setPlaceholderText(FRENCH.get(source,source) if self.language=="fr" else source)
        for index in range(self.nav.count()):
            item=self.nav.item(index);source=item.data(Qt.ItemDataRole.UserRole+1) or item.text();item.setData(Qt.ItemDataRole.UserRole+1,source);item.setText(FRENCH.get(source,source) if self.language=="fr" else source)
        for table in self.findChildren(QTableWidget):
            for index in range(table.columnCount()):
                item=table.horizontalHeaderItem(index)
                if item:
                    source=item.data(Qt.ItemDataRole.UserRole+1) or item.text();item.setData(Qt.ItemDataRole.UserRole+1,source);item.setText(FRENCH.get(source,source) if self.language=="fr" else source)
        for combo in self.findChildren(QComboBox):
            for index in range(combo.count()):
                if combo.itemData(index,Qt.ItemDataRole.UserRole) in {"en","fr"}:continue
                source=combo.itemData(index,Qt.ItemDataRole.UserRole+1) or combo.itemText(index);combo.setItemData(index,source,Qt.ItemDataRole.UserRole+1);combo.setItemText(index,FRENCH.get(source,source) if self.language=="fr" else source)

    def about(self):
        p,l=self.page("About Sound Recognition Trainer","A focused, offline desktop tool for serious sound-recognition practice.");card=self.panel();card.setObjectName("home_hero");cl=QVBoxLayout(card);name=QLabel("Sound Recognition Trainer");name.setObjectName("page_title");by=QLabel("Version 1.0.0 · Created by Michael Ruffenach");by.setObjectName("home_summary");copy=QLabel("Your MP3 files, names, aliases, scores and exam history stay on this computer. No cloud service and no account are required.");copy.setWordWrap(True);language=QComboBox();language.addItem("English","en");language.addItem("Français","fr");language.setCurrentIndex(max(0,language.findData(self.language)));language.currentIndexChanged.connect(self.change_language);self.language_choice=language;cl.addWidget(name);cl.addWidget(by);cl.addSpacing(10);cl.addWidget(copy);cl.addSpacing(12);cl.addWidget(QLabel("Language"));cl.addWidget(language);l.addWidget(card);l.addStretch();return p

    def save_settings(self):
        if self.almost.value()>self.correct.value():QMessageBox.warning(self,"Check thresholds","Almost-correct threshold cannot be higher than correct threshold.");return
        d={"volume":self.volume.value(),"default_offset":self.offset.value(),"global_playback_offset":self.global_playback_offset.value(),"correct_threshold":self.correct.value(),"almost_threshold":self.almost.value(),"reveal_immediately":self.default_reveal.isChecked(),"allow_repeats":self.default_repeat.isChecked(),"prioritize_difficult":self.default_priority.isChecked()};self.repo.set_settings(d);self.audio.output.setVolume(d["volume"]/100);QMessageBox.information(self,"Settings saved","Your local playback start and assessment defaults were updated.")

    def assign_category(self):
        sounds=[self.repo.sound(sound_id) for sound_id in self.checked_sound_ids];category=self.category_assign.currentText().strip()
        if not sounds:QMessageBox.information(self,"Choose sounds","Tick the checkbox beside one or more sounds, then choose a category.");return
        if not category:QMessageBox.information(self,"Choose a category","Type a category name or choose one from the list.");return
        for sound in sounds:self.repo.save_sound(sound.name,str(sound.filepath),sound.start_offset,sound.enabled,category,self.repo.aliases(sound.id),sound.id)
        self.checked_sound_ids.clear();self.refresh_library();self.bulk_assign_title.setText(f"Category “{category}” assigned to {len(sounds)} sound{'s' if len(sounds)!=1 else ''}");self.bulk_assign_help.setText("Select more sounds whenever you are ready.")

    def play_checked(self):
        sounds=[self.repo.sound(sound_id) for sound_id in self.checked_sound_ids]
        if not sounds:sounds=self.selected()
        if not sounds:QMessageBox.information(self,"Choose sounds","Tick one or more sounds, then choose Play checked.");return
        self.audio.play_queue(sounds,self.global_playback_offset.value(),self.library_shuffle.isChecked());self.bulk_assign_title.setText(f"Playing {len(sounds)} sound{'s' if len(sounds)!=1 else ''}")

    def play_category(self):
        category=self.category_assign.currentText().strip()
        if not category:QMessageBox.information(self,"Choose a category","Choose or type a category before playing it.");return
        sounds=self.repo.sounds(enabled_only=True,category=category)
        if not sounds:QMessageBox.information(self,"No sound available",f"No enabled sounds are in {category}.");return
        self.audio.play_queue(sounds,self.global_playback_offset.value(),self.library_shuffle.isChecked());self.bulk_assign_title.setText(f"Playing {len(sounds)} sounds from {category}")
