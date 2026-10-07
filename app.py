from __future__ import annotations

import logging
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from src.database import Repository
from src.ui.main_window import MainWindow

STYLE = """
* { font-family: 'Segoe UI Variable', 'Segoe UI', sans-serif; font-size: 14px; color:#172B36; }
QMainWindow { background:#F4F7F6; } #sidebar { background:#102D38; } #brand {color:#F7FBFA;font-size:23px;font-weight:700;line-height:1.2;} #sidebar_footer {color:#9BB2B9;font-size:11px;font-weight:600;letter-spacing:1px;line-height:1.5;}
#navigation {background:transparent;border:0;outline:0;color:#C5D8DB;} #navigation::item {padding:12px;border-radius:9px;margin:2px 0;} #navigation::item:hover {background:#1C4652;color:white;} #navigation::item:selected {background:#2B6970;color:white;font-weight:700;}
#page_title {font-size:31px;font-weight:700;letter-spacing:-0.5px;color:#102D38;} #page_description {font-size:15px;color:#58707A;margin-bottom:4px;} #panel {background:#FFFFFF;border:1px solid #DDE8E5;border-radius:14px;} #home_hero {background:#DCECE8;border:1px solid #BDD8D1;} #home_summary {font-size:17px;line-height:1.65;color:#21434A;} #home_summary b {font-size:21px;color:#102D38;} #status_line {color:#527078;font-weight:600;} #note_title {font-size:19px;font-weight:700;color:#163842;}
QPushButton {border:0;border-radius:8px;padding:10px 16px;font-weight:700;min-height:18px;} QPushButton#button_primary {background:#167277;color:white;} QPushButton#button_primary:hover {background:#0D5B62;} QPushButton#button_secondary {background:#E6F0EE;color:#15545A;} QPushButton#button_secondary:hover {background:#D5E7E3;} QPushButton#button_quiet {background:transparent;color:#31646B;border:1px solid #C8DCDA;} QPushButton#button_quiet:hover {background:#F0F6F4;} QPushButton#button_danger {background:#A94442;color:white;} QPushButton#button_danger:hover {background:#873431;} QPushButton#button_choice {background:white;color:#173A43;border:1px solid #C8DCDA;text-align:left;padding:12px;} QPushButton#button_choice:hover {background:#F0F8F6;border-color:#167277;} QPushButton:focus,QLineEdit:focus,QComboBox:focus {outline:0;border:2px solid #167277;}
QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox {background:white;border:1px solid #C7D8D5;border-radius:8px;padding:8px;min-height:19px;} QCheckBox {spacing:8px;color:#31535D;font-weight:600;} QCheckBox::indicator {width:17px;height:17px;border:1px solid #8EACA8;border-radius:5px;background:#FFFFFF;} QCheckBox::indicator:hover {border-color:#167277;background:#F0F8F6;} QCheckBox::indicator:checked {background:#167277;border-color:#167277;} QTableWidget {background:white;border:1px solid #D8E4E1;border-radius:12px;gridline-color:#EDF2F1;selection-background-color:#DCECE8;selection-color:#102D38;} QTableWidget::indicator {width:17px;height:17px;border:1px solid #8EACA8;border-radius:5px;background:#FFFFFF;} QTableWidget::indicator:hover {border-color:#167277;background:#F0F8F6;} QTableWidget::indicator:checked {background:#167277;border-color:#167277;} QHeaderView::section {background:#EDF4F2;border:0;padding:10px;color:#49656C;font-weight:700;} #bulk_assign {background:#E6F0EE;border:1px solid #C8DCDA;border-radius:12px;} #bulk_assign_title {font-size:14px;font-weight:700;color:#15545A;} #bulk_assign_help {font-size:12px;color:#527078;} #listening_stage,#exam_stage {background:#FFFFFF;border:1px solid #D7E7E3;border-radius:18px;} #stage_status {color:#167277;font-weight:700;} #stage_question {font-size:25px;font-weight:700;color:#112F39;padding:20px;} #stage_answer {font-size:16px;color:#587078;padding:10px;} #result_banner {background:#102D38;border:0;} #result_score {color:#F5FBFA;font-size:29px;font-weight:700;} #result_score span {font-size:13px;color:#BBD6D6;} #result_detail {color:#D0E4E1;font-size:15px;} 
"""

def main() -> int:
    if "--self-test" in sys.argv:
        from src.utils.self_test import run_self_test
        return run_self_test(STYLE)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = QApplication(sys.argv); app.setStyleSheet(STYLE)
    data_dir = Path.home() / ".sound-recognition-trainer"
    window = MainWindow(Repository(data_dir / "sound_trainer.db")); window.showMaximized()
    return app.exec()

if __name__ == "__main__": raise SystemExit(main())
