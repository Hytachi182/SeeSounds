from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import *
from src.database import Repository
from src.models import Sound
from src.ui.localization import LocalizationMixin, install_qt_language
from src.services.audio import AudioPlayer
from src.services.selection import exam_questions, multiple_choice_options, training_choice
from src.utils.answers import compare_answer, MatchResult, normalize_answer


def button(text: str, kind: str = "primary") -> QPushButton:
    w = QPushButton(text); w.setObjectName(f"button_{kind}"); w.setProperty("i18n_user_text", kind == "choice"); return w

class SoundDialog(LocalizationMixin, QDialog):
    def __init__(self, parent: QWidget, repo: Repository, sound: Sound | None = None):
        super().__init__(parent); self.language=parent.language; self.repo, self.sound = repo, sound; self.setWindowTitle(self.t("Edit sound" if sound else "Add sound")); self.setMinimumWidth(500)
        form = QFormLayout(self); self.name, self.path, self.category, self.aliases = QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit(); self.offset = QDoubleSpinBox(); self.offset.setRange(0,3600); self.offset.setDecimals(2); self.offset.setSuffix(" seconds"); self.enabled=QCheckBox("Include in training and exams"); self.enabled.setChecked(True)
        browse=button("Browse", "secondary"); browse.clicked.connect(self.browse); row=QHBoxLayout(); row.addWidget(self.path); row.addWidget(browse)
        for label,field in (("Display name",self.name),("MP3 file",row),("Start playback at",self.offset),("Category",self.category),("Aliases, comma-separated",self.aliases),("",self.enabled)): form.addRow(label,field)
        b=QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save); b.accepted.connect(self.accept); b.rejected.connect(self.reject); form.addRow(b)
        if sound: self.name.setText(sound.name); self.path.setText(str(sound.filepath)); self.offset.setValue(sound.start_offset); self.category.setText(sound.category or ""); self.aliases.setText(", ".join(repo.aliases(sound.id))); self.enabled.setChecked(sound.enabled)
        else: self.offset.setValue(repo.settings()["default_offset"])
        for standard, text in ((QDialogButtonBox.StandardButton.Save,"Save"),(QDialogButtonBox.StandardButton.Cancel,"Cancel")):
            b.button(standard).setProperty("source_text",text)
        self.translate_widgets()
    def browse(self):
        p,_=QFileDialog.getOpenFileName(self,self.t("Choose MP3"),filter=self.t("MP3 files (*.mp3)"),options=QFileDialog.Option.DontUseNativeDialog)
        if p: self.path.setText(p); self.name.setText(self.name.text() or Path(p).stem)
    def accept(self):
        if not self.name.text().strip() or not self.path.text().strip(): QMessageBox.warning(self,self.t("Missing information"),self.t("A display name and MP3 file are required.")); return
        try:
            self.repo.save_sound(self.name.text().strip(),self.path.text().strip(),self.offset.value(),self.enabled.isChecked(),self.category.text().strip() or None,self.aliases.text().split(","),self.sound.id if self.sound else None)
        except sqlite3.IntegrityError:
            QMessageBox.warning(self,self.t("Already in library"),self.t("This file is already in your library. Edit its existing entry instead.")); return
        super().accept()

class MainWindow(LocalizationMixin, QMainWindow):
    def __init__(self, repo: Repository):
        super().__init__(); self.repo=repo; self.language=repo.settings().get("language","en"); self.audio=AudioPlayer(repo.settings()["volume"]); self.training_sound=None; self.exam=None; self.last_exam_id=None; self.checked_sound_ids:set[int]=set(); self.setWindowTitle("Sound Recognition Trainer"); self.setWindowIcon(QIcon(str(Path(__file__).resolve().parents[2] / "assets" / "sound-recognition-trainer.svg"))); self.resize(1240,780); self.setMinimumSize(1000,680); self.build(); self.apply_language()
    def page(self,title,subtitle):
        p=QWidget(); l=QVBoxLayout(p); l.setContentsMargins(42,34,42,34); h=QLabel(title); h.setObjectName("page_title"); h.setWordWrap(True); s=QLabel(subtitle); s.setObjectName("page_description"); s.setWordWrap(True); l.addWidget(h);l.addWidget(s);return p,l
    def panel(self): w=QFrame();w.setObjectName("panel");return w
    def build(self):
        root=QWidget(); r=QHBoxLayout(root);r.setContentsMargins(0,0,0,0);r.setSpacing(0);self.setCentralWidget(root); side=QFrame();side.setObjectName("sidebar");side.setFixedWidth(244);sl=QVBoxLayout(side);sl.setContentsMargins(22,28,18,22);brand=QLabel("Sound\nRecognition\nTrainer");brand.setObjectName("brand");sl.addWidget(brand);sl.addSpacing(28);self.nav=QListWidget();self.nav.setObjectName("navigation");self.nav.setIconSize(QSize(18,18));self.nav.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);self.nav.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents);nav_items=(("Home",QStyle.StandardPixmap.SP_ComputerIcon),("Sound Library",QStyle.StandardPixmap.SP_DirOpenIcon),("Training",QStyle.StandardPixmap.SP_MediaPlay),("Exam",QStyle.StandardPixmap.SP_DialogApplyButton),("Statistics",QStyle.StandardPixmap.SP_FileDialogDetailedView),("Settings",QStyle.StandardPixmap.SP_FileDialogContentsView),("About",QStyle.StandardPixmap.SP_MessageBoxInformation));[self.nav.addItem(QListWidgetItem(self.style().standardIcon(icon),label)) for label,icon in nav_items];self.nav.currentRowChanged.connect(self.change);sl.addWidget(self.nav);sl.addStretch();f=QLabel("LOCAL WORKSPACE\nNo account. No cloud.");f.setObjectName("sidebar_footer");sl.addWidget(f);r.addWidget(side);self.pages=QStackedWidget();r.addWidget(self.pages,1)
        for page in (self.home(),self.library(),self.training(),self.exam_page(),self.statistics(),self.settings(),self.about()):
            scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.Shape.NoFrame);scroll.viewport().setAutoFillBackground(False);scroll.setWidget(page);self.pages.addWidget(scroll)
        self.nav.setCurrentRow(0)
    def home(self):
        p,l=self.page("Learn the sound. Trust the answer.","A focused, local workspace for turning your MP3 collection into exam confidence.");hero=self.panel();hero.setObjectName("home_hero");hl=QVBoxLayout(hero);self.home_summary=QLabel();self.home_summary.setObjectName("home_summary");self.home_summary.setWordWrap(True);hl.addWidget(self.home_summary);a=QHBoxLayout();b=button("Start a training round");b.clicked.connect(lambda:self.nav.setCurrentRow(2));e=button("Set up an exam","secondary");e.clicked.connect(lambda:self.nav.setCurrentRow(3));a.addWidget(b);a.addWidget(e);a.addStretch();hl.addLayout(a);l.addWidget(hero);l.addStretch();return p
    def library(self):
        p,l=self.page("Sound Library","Manage the source material for every practice session. Original MP3 files are never modified.");bar=QVBoxLayout();self.search=QLineEdit();self.search.setPlaceholderText("Search sound name or category");self.search.textChanged.connect(self.refresh_library);bar.addWidget(self.search)
        actions=QGridLayout();bar.addLayout(actions)
        for index,(label,fn,kind) in enumerate((("Add MP3 files",self.add_sounds,"primary"),("Preview",self.preview,"secondary"),("Edit",self.edit,"secondary"),("Enable / disable",self.toggle,"secondary"),("Remove",self.remove,"danger"))):
            b=button(label,kind);b.clicked.connect(fn);actions.addWidget(b,index//3,index%3)
        l.addLayout(bar);meta=QHBoxLayout();self.library_status=QLabel();self.library_status.setObjectName("status_line");meta.addWidget(self.library_status);meta.addStretch();imp=button("Import JSON","quiet");imp.clicked.connect(self.import_library);exp=button("Export JSON","quiet");exp.clicked.connect(self.export_library);meta.addWidget(imp);meta.addWidget(exp);l.addLayout(meta)
        self.bulk_assign=QFrame();self.bulk_assign.setObjectName("bulk_assign");bulk=QVBoxLayout(self.bulk_assign);bulk.setContentsMargins(16,10,16,10);bulk.setSpacing(10)
        selection=QHBoxLayout();bulk.addLayout(selection)
        self.select_visible=QCheckBox("Select shown");self.select_visible.toggled.connect(self.toggle_visible_checked);selection.addWidget(self.select_visible)
        copy=QVBoxLayout();copy.setSpacing(1);self.bulk_assign_title=QLabel();self.bulk_assign_title.setObjectName("bulk_assign_title");self.bulk_assign_title.setWordWrap(True);self.bulk_assign_help=QLabel();self.bulk_assign_help.setObjectName("bulk_assign_help");self.bulk_assign_help.setWordWrap(True);copy.addWidget(self.bulk_assign_title);copy.addWidget(self.bulk_assign_help);selection.addLayout(copy,1)
        clear=button("Clear","quiet");clear.clicked.connect(self.clear_checked_sounds);selection.addWidget(clear)
        playback=QHBoxLayout();bulk.addLayout(playback);self.library_shuffle=QCheckBox("Shuffle");playback.addWidget(self.library_shuffle)
        play=button("Play checked","secondary");play.clicked.connect(self.play_checked);playback.addWidget(play)
        play_category=button("Play category","secondary");play_category.clicked.connect(self.play_category);playback.addWidget(play_category)
        categories=QHBoxLayout();bulk.addLayout(categories);self.category_assign=QComboBox();self.category_assign.setEditable(True);self.category_assign.setMinimumWidth(160);self.category_assign.setPlaceholderText("Choose or type a category");categories.addWidget(self.category_assign,1)
        assign=button("Assign category");assign.clicked.connect(self.assign_category);categories.addWidget(assign);l.addWidget(self.bulk_assign)
        self.table=QTableWidget(0,6);self.table.setObjectName("data_table");self.table.setHorizontalHeaderLabels(("","Sound","Category","Offset","Ready","File"));self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection);self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);self.table.verticalHeader().setVisible(False);self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Fixed);self.table.setColumnWidth(0,42);self.table.horizontalHeader().setStretchLastSection(True);self.table.itemChanged.connect(self.library_item_changed);self.table.doubleClicked.connect(self.edit);l.addWidget(self.table,1);return p
    def training(self):
        p,l=self.page("Training","Practise deliberately. No timer, no penalty — only useful repetition.");bar=QHBoxLayout();self.training_category=QComboBox();self.training_category.addItem("All categories",None);self.priority=QCheckBox("Prioritize difficult sounds");self.priority.setChecked(self.repo.settings()["prioritize_difficult"]);new=button("Play a new sound");new.clicked.connect(self.next_training);bar.addWidget(QLabel("Scope"));bar.addWidget(self.training_category);bar.addWidget(self.priority);bar.addStretch();bar.addWidget(new);l.addLayout(bar);stage=self.panel();stage.setObjectName("listening_stage");st=QVBoxLayout(stage);self.training_status=QLabel("Ready when you are");self.training_status.setObjectName("stage_status");self.training_question=QLabel("Choose a sound and identify what you hear.");self.training_question.setObjectName("stage_question");self.reveal=QLabel("The answer stays hidden until you reveal it.");self.reveal.setObjectName("stage_answer");[x.setAlignment(Qt.AlignmentFlag.AlignCenter) for x in (self.training_status,self.training_question,self.reveal)];[st.addWidget(x) for x in (self.training_status,self.training_question,self.reveal)];l.addWidget(stage,1);a=QGridLayout();
        for index,(label,fn,kind) in enumerate((("Replay",self.replay_training,"secondary"),("Pause / resume",self.audio.pause_or_resume,"quiet"),("Reveal answer",self.reveal_training,"quiet"),("I missed it",lambda:self.score(False),"danger"),("I was correct",lambda:self.score(True),"primary"))):
            b=button(label,kind);b.clicked.connect(fn);a.addWidget(b,index//3,index%3)
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
        w=QWidget();l=QVBoxLayout(w);banner=self.panel();banner.setObjectName("result_banner");bl=QHBoxLayout(banner);self.result_score=QLabel();self.result_score.setObjectName("result_score");self.result_detail=QLabel();self.result_detail.setObjectName("result_detail");self.result_detail.setWordWrap(True);bl.addWidget(self.result_score);bl.addWidget(self.result_detail,1);l.addWidget(banner);a=QHBoxLayout();self.missed=QCheckBox("Show missed and almost-correct only");self.missed.toggled.connect(self.populate_results);a.addWidget(self.missed);a.addStretch();b=button("Replay selected sound","secondary");b.clicked.connect(self.replay_result);a.addWidget(b);n=button("New exam");n.clicked.connect(lambda:self.exam_stack.setCurrentIndex(0));a.addWidget(n);l.addLayout(a);self.results=QTableWidget(0,5);self.results.setObjectName("data_table");self.results.setHorizontalHeaderLabels(("Sound","Your answer","Expected answer","Similarity","Outcome"));self.results.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);self.results.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);self.results.verticalHeader().setVisible(False);self.results.horizontalHeader().setStretchLastSection(True);self.results.doubleClicked.connect(self.replay_result);l.addWidget(self.results,1);return w
    def statistics(self):
        p,l=self.page("Statistics","Use recent evidence to choose what deserves your next practice session.");self.stats=QLabel();self.stats.setObjectName("home_summary");self.stats.setWordWrap(True);l.addWidget(self.stats);self.stats_table=QTableWidget(0,4);self.stats_table.setObjectName("data_table");self.stats_table.setHorizontalHeaderLabels(("Sound","Attempts","Success","Last practiced"));self.stats_table.verticalHeader().setVisible(False);self.stats_table.horizontalHeader().setStretchLastSection(True);l.addWidget(self.stats_table,1);self.history=QLabel();l.addWidget(self.history);return p
    def change(self,i):
        self.pages.setCurrentIndex(i)
        if i==0:self.refresh_home()
        elif i==1:self.refresh_library()
        elif i==2:self.refresh_filters()
        elif i==4:self.refresh_stats()
    def refresh_home(self):
        stats = self.repo.statistics()
        self.set_text(self.home_summary, "<b>{count} active sounds, ready when you are.</b><br>Training success: {rate:.0f}% across {attempts} attempts · {exams} completed exams", count=len(self.repo.sounds(enabled_only=True)), rate=stats['rate']*100, attempts=stats['attempts'], exams=stats['exams'])
    def add_sounds(self):
        files,_=QFileDialog.getOpenFileNames(self,self.t("Add MP3 files"),filter=self.t("MP3 files (*.mp3)"),options=QFileDialog.Option.DontUseNativeDialog)
        existing={str(sound.filepath) for sound in self.repo.sounds()}
        for file in files:
            if file not in existing:
                self.repo.save_sound(Path(file).stem,file,self.repo.settings()["default_offset"],True,None,[]);existing.add(file)
        self.refresh_library()
    def preview(self):
        x=self.selected(); self.play_sound(x[0]) if x else QMessageBox.information(self,self.t("Select a sound"),self.t("Select a library row first."))
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

    def remove(self):
        x=self.selected()
        if x and QMessageBox.question(self,self.t("Remove sounds"),self.t("Remove {count} selected sound(s) and their local history?",count=len(x)),QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes:
            try:
                for sound in x:self.repo.delete_sound(sound.id)
            except ValueError as error:
                QMessageBox.warning(self,self.t("Keep exam history"),self.error_text(error))
            self.refresh_library()
    def export_library(self):
        p,_=QFileDialog.getSaveFileName(self,self.t("Export library"),"sound-library.json","JSON (*.json)",options=QFileDialog.Option.DontUseNativeDialog)
        if p:
            try:self.repo.export_library(Path(p))
            except OSError as error:QMessageBox.warning(self,self.t("Export failed"),self.error_text(error))
    def import_library(self):
        p,_=QFileDialog.getOpenFileName(self,self.t("Import library"),filter=self.t("JSON (*.json)"),options=QFileDialog.Option.DontUseNativeDialog)
        if p:
            try:missing=self.repo.import_library(Path(p))
            except (OSError, ValueError, sqlite3.Error) as error:
                QMessageBox.warning(self,self.t("Import failed"),self.error_text(error));return
            self.refresh_library();QMessageBox.warning(self,self.t("Missing paths"),"\n".join(missing)) if missing else None
    def refresh_filters(self):
        current = self.training_category.currentData()
        self.training_category.clear()
        self.training_category.addItem(self.t("All categories"), None)
        self.training_category.setItemData(0, "All categories", Qt.ItemDataRole.UserRole+1)
        for category in sorted({sound.category for sound in self.repo.sounds(enabled_only=True) if sound.category}):
            self.training_category.addItem(category, category)
        self.training_category.setCurrentIndex(max(0, self.training_category.findData(current)))
    def next_training(self):
        try:
            self.training_sound=training_choice(self.repo.sounds(enabled_only=True,category=self.training_category.currentData()),self.repo.success_rates(),self.priority.isChecked());self.set_text(self.training_status,"Now listening");self.set_text(self.training_question,"What sound are you hearing?");self.set_text(self.reveal,"The answer is waiting when you are ready.");self.play_sound(self.training_sound)
        except ValueError as e:QMessageBox.warning(self,self.t("No sound available"),self.error_text(e))
    def replay_training(self):
        if self.training_sound:self.play_sound(self.training_sound)
    def reveal_training(self):
        if self.training_sound:self.set_user_text(self.reveal,self.training_sound.name)
    def score(self,ok):
        if self.training_sound:self.repo.record_training(self.training_sound.id,ok);self.next_training()
    def start_exam(self):
        try:
            sounds=self.repo.sounds(enabled_only=True);q=exam_questions(sounds,int(self.exam_count.currentText()),self.repeats.isChecked())
            if self.level.currentData()==1 and len(sounds)<5:raise ValueError("Level 1 requires at least five enabled sounds.")
            self.exam={"questions":q,"index":0,"answers":[],"difficulty":self.level.currentData(),"reveal":self.reveal_now.isChecked(),"started":datetime.now(timezone.utc).isoformat()};self.exam_stack.setCurrentIndex(1);self.show_question()
        except ValueError as e:QMessageBox.warning(self,self.t("Cannot start exam"),self.error_text(e))
    def cancel_exam(self):
        if self.exam and QMessageBox.question(self,self.t("Cancel exam"),self.t("Discard this unfinished exam?"),QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes:self.audio.stop();self.exam=None;self.exam_stack.setCurrentIndex(0)
    def show_question(self):
        s=self.exam["questions"][self.exam["index"]];self.set_text(self.exam_progress,"Question {current} / {total}",current=self.exam["index"]+1,total=len(self.exam["questions"]));self.set_text(self.exam_feedback,"Answer when ready");self.exam_answer.clear();free=self.exam["difficulty"]==2;self.exam_answer.setVisible(free);self.submit.setVisible(free)
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
        if self.exam["reveal"]:QMessageBox.information(self,self.t("Answer recorded"),self.t("Expected: {name}\n{result} · {similarity:.0f}%",name=s.name,result=self.t(m.result.title()),similarity=m.similarity))
        self.exam["index"]+=1;self.show_question() if self.exam["index"]<len(self.exam["questions"]) else self.finish_exam()
    def finish_exam(self):
        answers = self.exam["answers"]
        self.last_exam_id = self.repo.record_exam(self.exam["difficulty"], self.exam["started"], answers)
        correct = sum(answer["result"] == "correct" for answer in answers)
        almost = sum(answer["result"] == "almost" for answer in answers)
        elapsed = datetime.now(timezone.utc) - datetime.fromisoformat(self.exam["started"])
        minutes, seconds = divmod(int(elapsed.total_seconds()), 60)
        self.set_text(self.result_score, "{correct}/{total}\n<span>correct answers</span>", correct=correct, total=len(answers))
        self.set_text(self.result_detail, "{percentage:.0f}% score · {incorrect} incorrect · {almost} almost correct · {minutes}:{seconds:02d} duration", percentage=correct/len(answers)*100, incorrect=len(answers)-correct-almost, almost=almost, minutes=minutes, seconds=seconds)
        self.exam = None
        self.missed.setChecked(False)
        self.populate_results()
        self.exam_stack.setCurrentIndex(2)
    def populate_results(self):
        rows=self.repo.exam_answers(self.last_exam_id);rows=[x for x in rows if x["result"]!="correct"] if self.missed.isChecked() else rows;self.results.setRowCount(len(rows))
        for r,x in enumerate(rows):
            for c,v in enumerate((x["expected_answer"],x["user_answer"] or "—",x["expected_answer"],f"{x['similarity']:.0f}%",self.t(x["result"].title()))):i=QTableWidgetItem(v);i.setData(Qt.ItemDataRole.UserRole,x["sound_id"]);self.results.setItem(r,c,i)
    def replay_result(self):
        r=self.results.selectionModel().selectedRows()
        if r:self.play_sound(self.repo.sound(self.results.item(r[0].row(),0).data(Qt.ItemDataRole.UserRole)))
    def refresh_stats(self):
        stats = self.repo.statistics()
        self.set_text(self.stats, "<b>{attempts} training attempts · {rate:.0f}% global success · {exams} completed exams</b>", attempts=stats['attempts'], rate=stats['rate']*100, exams=stats['exams'])
        sounds = self.repo.sounds()
        self.stats_table.setRowCount(len(sounds))
        for row, sound in enumerate(sounds):
            data = self.repo.connection.execute("SELECT COUNT(*) count,COALESCE(AVG(correct),0) rate,MAX(created_at) latest FROM training_results WHERE sound_id=?", (sound.id,)).fetchone()
            values = (sound.name, str(data['count']), f"{data['rate']*100:.0f}%", data['latest'][:10] if data['latest'] else self.t("Never"))
            for column, value in enumerate(values):
                self.stats_table.setItem(row, column, QTableWidgetItem(value))
        exams = " · ".join(f"{exam['score']}/{exam['question_count']} ({exam['percentage']:.0f}%)" for exam in self.repo.recent_exams())
        # Keep the empty-state translation live when the language changes.
        self.set_text(self.history, "Recent exams: {exams}", exams=exams or self.t("No exams yet."))
    def refresh_library(self):
        sounds=self.repo.sounds(self.search.text());visible_ids={sound.id for sound in sounds};self.checked_sound_ids.intersection_update({sound.id for sound in self.repo.sounds()});self.table.blockSignals(True);self.table.setRowCount(len(sounds));self.set_text(self.library_status,"{active} active sounds · {shown} shown",active=len(self.repo.sounds(enabled_only=True)),shown=len(sounds))
        current=self.category_assign.currentText();self.category_assign.blockSignals(True);self.category_assign.clear();self.category_assign.addItem("");[self.category_assign.addItem(category) for category in sorted({sound.category for sound in self.repo.sounds() if sound.category})];self.category_assign.setEditText(current);self.category_assign.blockSignals(False)
        for row,sound in enumerate(sounds):
            checked=QTableWidgetItem();checked.setData(Qt.ItemDataRole.UserRole,sound.id);checked.setFlags(Qt.ItemFlag.ItemIsEnabled|Qt.ItemFlag.ItemIsUserCheckable);checked.setCheckState(Qt.CheckState.Checked if sound.id in self.checked_sound_ids else Qt.CheckState.Unchecked);self.table.setItem(row,0,checked)
            for column,value in enumerate((sound.name,sound.category or self.t("Uncategorised"),f"{sound.start_offset:.2f} s",self.t("Enabled" if sound.enabled else "Paused"),str(sound.filepath)),1): item=QTableWidgetItem(value);item.setData(Qt.ItemDataRole.UserRole,sound.id);self.table.setItem(row,column,item)
        self.table.blockSignals(False);self.update_bulk_assign(visible_ids)

    def library_item_changed(self,item):
        if item.column()!=0:return
        sound_id=item.data(Qt.ItemDataRole.UserRole)
        if item.checkState()==Qt.CheckState.Checked:self.checked_sound_ids.add(sound_id)
        else:self.checked_sound_ids.discard(sound_id)
        self.update_bulk_assign()

    def update_bulk_assign(self, visible_ids=None):
        visible_ids = visible_ids if visible_ids is not None else {self.table.item(row,0).data(Qt.ItemDataRole.UserRole) for row in range(self.table.rowCount())}
        count = len(self.checked_sound_ids)
        self.select_visible.blockSignals(True)
        self.select_visible.setChecked(bool(visible_ids) and visible_ids.issubset(self.checked_sound_ids))
        self.select_visible.blockSignals(False)
        if count:
            self.set_text(self.bulk_assign_title, "One sound selected" if count == 1 else "{count} sounds selected", **({} if count == 1 else {'count': count}))
            self.set_text(self.bulk_assign_help, "Choose a category, then assign it to the checked sounds.")
        else:
            self.set_text(self.bulk_assign_title, "Organize several sounds at once")
            self.set_text(self.bulk_assign_help, "Use the checkboxes beside each sound to prepare a category assignment.")

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
        install_qt_language(self.language)
        self.translate_widgets()
        for index in range(self.nav.count()):
            item = self.nav.item(index)
            source = item.data(Qt.ItemDataRole.UserRole+1) or item.text()
            item.setData(Qt.ItemDataRole.UserRole+1, source)
            item.setText(self.t(source))
        for table in self.findChildren(QTableWidget):
            for index in range(table.columnCount()):
                item = table.horizontalHeaderItem(index)
                if item:
                    source = item.data(Qt.ItemDataRole.UserRole+1) or item.text()
                    item.setData(Qt.ItemDataRole.UserRole+1, source)
                    item.setText(self.t(source))
        # Translate only application-owned options, never user categories or names.
        for combo, indexes in ((self.level, range(self.level.count())), (self.training_category, range(min(1, self.training_category.count())))):
            for index in indexes:
                source = combo.itemData(index, Qt.ItemDataRole.UserRole+1) or combo.itemText(index)
                combo.setItemData(index, source, Qt.ItemDataRole.UserRole+1)
                combo.setItemText(index, self.t(source))
        self.language_choice.blockSignals(True)
        self.language_choice.setCurrentIndex(max(0, self.language_choice.findData(self.language)))
        self.language_choice.blockSignals(False)
        self.refresh_home()
        self.refresh_library()
        self.refresh_filters()
        self.refresh_stats()
        if self.last_exam_id is not None:
            self.populate_results()

    def about(self):
        p,l=self.page("About Sound Recognition Trainer","A focused, offline desktop tool for serious sound-recognition practice.");card=self.panel();card.setObjectName("home_hero");cl=QVBoxLayout(card);name=QLabel("Sound Recognition Trainer");name.setObjectName("page_title");by=QLabel("Version 1.0.0 · Created by Michael Ruffenach");by.setObjectName("home_summary");copy=QLabel("Your MP3 files, names, aliases, scores and exam history stay on this computer. No cloud service and no account are required.");copy.setWordWrap(True);language=QComboBox();language.addItem("English","en");language.addItem("Français","fr");language.setCurrentIndex(max(0,language.findData(self.language)));language.currentIndexChanged.connect(self.change_language);self.language_choice=language;cl.addWidget(name);cl.addWidget(by);cl.addSpacing(10);cl.addWidget(copy);cl.addSpacing(12);cl.addWidget(QLabel("Language"));cl.addWidget(language);l.addWidget(card);l.addStretch();return p

    def save_settings(self):
        if self.almost.value()>self.correct.value():QMessageBox.warning(self,self.t("Check thresholds"),self.t("Almost-correct threshold cannot be higher than correct threshold."));return
        d={"volume":self.volume.value(),"default_offset":self.offset.value(),"global_playback_offset":self.global_playback_offset.value(),"correct_threshold":self.correct.value(),"almost_threshold":self.almost.value(),"reveal_immediately":self.default_reveal.isChecked(),"allow_repeats":self.default_repeat.isChecked(),"prioritize_difficult":self.default_priority.isChecked()};self.repo.set_settings(d);self.audio.output.setVolume(d["volume"]/100);QMessageBox.information(self,self.t("Settings saved"),self.t("Your local playback start and assessment defaults were updated."))

    def assign_category(self):
        sounds=[self.repo.sound(sound_id) for sound_id in self.checked_sound_ids];category=self.category_assign.currentText().strip()
        if not sounds:QMessageBox.information(self,self.t("Choose sounds"),self.t("Tick the checkbox beside one or more sounds, then choose a category."));return
        if not category:QMessageBox.information(self,self.t("Choose a category"),self.t("Type a category name or choose one from the list."));return
        for sound in sounds:self.repo.save_sound(sound.name,str(sound.filepath),sound.start_offset,sound.enabled,category,self.repo.aliases(sound.id),sound.id)
        self.checked_sound_ids.clear();self.refresh_library();self.set_text(self.bulk_assign_title,"Category “{category}” assigned to one sound" if len(sounds)==1 else "Category “{category}” assigned to {count} sounds",category=category,**({} if len(sounds)==1 else {"count":len(sounds)}));self.set_text(self.bulk_assign_help,"Select more sounds whenever you are ready.")

    def play_checked(self):
        sounds=[self.repo.sound(sound_id) for sound_id in self.checked_sound_ids]
        if not sounds:sounds=self.selected()
        if not sounds:QMessageBox.information(self,self.t("Choose sounds"),self.t("Tick one or more sounds, then choose Play checked."));return
        self.audio.play_queue(sounds,self.global_playback_offset.value(),self.library_shuffle.isChecked());self.set_text(self.bulk_assign_title,"Playing one sound" if len(sounds)==1 else "Playing {count} sounds",**({} if len(sounds)==1 else {"count":len(sounds)}))

    def play_category(self):
        category=self.category_assign.currentText().strip()
        if not category:QMessageBox.information(self,self.t("Choose a category"),self.t("Choose or type a category before playing it."));return
        sounds=self.repo.sounds(enabled_only=True,category=category)
        if not sounds:QMessageBox.information(self,self.t("No sound available"),self.t("No enabled sounds are in {category}.",category=category));return
        self.audio.play_queue(sounds,self.global_playback_offset.value(),self.library_shuffle.isChecked());self.set_text(self.bulk_assign_title,"Playing {count} sounds from {category}",count=len(sounds),category=category)
