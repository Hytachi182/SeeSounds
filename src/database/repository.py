"""SQLite schema and persistence boundary."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from src.models import Sound


DEFAULT_SETTINGS = {"volume": 70, "default_offset": 0.0, "global_playback_offset": 0.0, "correct_threshold": 90,
                    "almost_threshold": 75, "reveal_immediately": False,
                    "allow_repeats": False, "prioritize_difficult": True}


class Repository:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    def _migrate(self) -> None:
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS sounds (id INTEGER PRIMARY KEY, name TEXT NOT NULL, filepath TEXT NOT NULL UNIQUE,
          start_offset REAL NOT NULL DEFAULT 0, enabled INTEGER NOT NULL DEFAULT 1, category TEXT,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sound_aliases (id INTEGER PRIMARY KEY, sound_id INTEGER NOT NULL REFERENCES sounds(id) ON DELETE CASCADE, alias TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS training_results (id INTEGER PRIMARY KEY, sound_id INTEGER NOT NULL REFERENCES sounds(id) ON DELETE CASCADE, correct INTEGER NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS exams (id INTEGER PRIMARY KEY, difficulty INTEGER NOT NULL, question_count INTEGER NOT NULL,
          score INTEGER NOT NULL, percentage REAL NOT NULL, started_at TEXT NOT NULL, completed_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS exam_answers (id INTEGER PRIMARY KEY, exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
          sound_id INTEGER NOT NULL REFERENCES sounds(id), user_answer TEXT, normalized_answer TEXT, expected_answer TEXT NOT NULL,
          similarity REAL, result TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        for key, value in DEFAULT_SETTINGS.items():
            self.connection.execute("INSERT OR IGNORE INTO settings(key,value) VALUES (?,?)", (key, json.dumps(value)))
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    @staticmethod
    def _sound(row: sqlite3.Row) -> Sound:
        return Sound(row["id"], row["name"], Path(row["filepath"]), row["start_offset"], bool(row["enabled"]), row["category"])

    def sounds(self, query: str = "", enabled_only: bool = False, category: str | None = None) -> list[Sound]:
        clauses, args = ["1=1"], []
        if query: clauses.append("(name LIKE ? OR category LIKE ?)"); args.extend([f"%{query}%"] * 2)
        if enabled_only: clauses.append("enabled=1")
        if category: clauses.append("category=?"); args.append(category)
        rows = self.connection.execute(f"SELECT * FROM sounds WHERE {' AND '.join(clauses)} ORDER BY name", args).fetchall()
        return [self._sound(row) for row in rows]

    def sound(self, sound_id: int) -> Sound:
        row = self.connection.execute("SELECT * FROM sounds WHERE id=?", (sound_id,)).fetchone()
        if not row: raise KeyError(sound_id)
        return self._sound(row)

    def save_sound(self, name: str, filepath: str, offset: float, enabled: bool, category: str | None, aliases: list[str], sound_id: int | None = None) -> int:
        now = datetime.now(timezone.utc).isoformat()
        if sound_id is None:
            cursor = self.connection.execute("INSERT INTO sounds(name,filepath,start_offset,enabled,category,created_at,updated_at) VALUES (?,?,?,?,?,?,?)", (name, filepath, offset, enabled, category or None, now, now)); sound_id = cursor.lastrowid
        else:
            self.connection.execute("UPDATE sounds SET name=?,filepath=?,start_offset=?,enabled=?,category=?,updated_at=? WHERE id=?", (name, filepath, offset, enabled, category or None, now, sound_id))
            self.connection.execute("DELETE FROM sound_aliases WHERE sound_id=?", (sound_id,))
        self.connection.executemany("INSERT INTO sound_aliases(sound_id,alias) VALUES (?,?)", [(sound_id, alias.strip()) for alias in aliases if alias.strip()])
        self.connection.commit(); return int(sound_id)

    def delete_sound(self, sound_id: int) -> None:
        self.connection.execute("DELETE FROM sounds WHERE id=?", (sound_id,)); self.connection.commit()

    def aliases(self, sound_id: int) -> list[str]:
        return [r[0] for r in self.connection.execute("SELECT alias FROM sound_aliases WHERE sound_id=?", (sound_id,))]

    def settings(self) -> dict:
        rows = self.connection.execute("SELECT key,value FROM settings").fetchall()
        return {row["key"]: json.loads(row["value"]) for row in rows}

    def set_settings(self, settings: dict) -> None:
        self.connection.executemany("UPDATE settings SET value=? WHERE key=?", [(json.dumps(v), k) for k, v in settings.items()]); self.connection.commit()

    def record_training(self, sound_id: int, correct: bool) -> None:
        self.connection.execute("INSERT INTO training_results(sound_id,correct,created_at) VALUES (?,?,?)", (sound_id, correct, datetime.now(timezone.utc).isoformat())); self.connection.commit()

    def success_rates(self) -> dict[int, float]:
        return {r["sound_id"]: r["rate"] for r in self.connection.execute("SELECT sound_id, AVG(correct) rate FROM training_results GROUP BY sound_id")}

    def statistics(self) -> dict:
        row = self.connection.execute("SELECT COUNT(*) attempts, COALESCE(AVG(correct),0) rate FROM training_results").fetchone()
        return {"attempts": row["attempts"], "rate": row["rate"], "exams": self.connection.execute("SELECT COUNT(*) FROM exams").fetchone()[0]}

    def record_exam(self, difficulty: int, started_at: str, answers: list[dict]) -> int:
        completed = datetime.now(timezone.utc).isoformat()
        correct = sum(answer["result"] == "correct" for answer in answers)
        cursor = self.connection.execute("INSERT INTO exams(difficulty,question_count,score,percentage,started_at,completed_at) VALUES (?,?,?,?,?,?)", (difficulty, len(answers), correct, (correct / len(answers) * 100) if answers else 0, started_at, completed))
        exam_id = cursor.lastrowid
        self.connection.executemany("INSERT INTO exam_answers(exam_id,sound_id,user_answer,normalized_answer,expected_answer,similarity,result) VALUES (?,?,?,?,?,?,?)", [(exam_id, a["sound"].id, a.get("answer", ""), a.get("normalized", ""), a["sound"].name, a.get("similarity"), a["result"]) for a in answers])
        self.connection.commit()
        return int(exam_id)

    def recent_exams(self) -> list[sqlite3.Row]:
        return self.connection.execute("SELECT * FROM exams ORDER BY completed_at DESC LIMIT 8").fetchall()

    def exam_answers(self, exam_id: int) -> list[sqlite3.Row]:
        """Return an exam's review rows, including enough sound metadata to replay it."""
        return self.connection.execute(
            """SELECT ea.*, s.filepath, s.start_offset, s.category
               FROM exam_answers ea JOIN sounds s ON s.id = ea.sound_id
               WHERE ea.exam_id=? ORDER BY ea.id""",
            (exam_id,),
        ).fetchall()

    def export_library(self, destination: Path) -> None:
        payload = [{"name": s.name, "filepath": str(s.filepath), "start_offset": s.start_offset, "enabled": s.enabled, "category": s.category, "aliases": self.aliases(s.id)} for s in self.sounds()]
        destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def import_library(self, source: Path) -> list[str]:
        missing = []
        for item in json.loads(source.read_text(encoding="utf-8")):
            file = item["filepath"]
            self.save_sound(item["name"], file, float(item.get("start_offset", 0)), bool(item.get("enabled", True)), item.get("category"), item.get("aliases", []))
            if not Path(file).is_file(): missing.append(file)
        return missing
