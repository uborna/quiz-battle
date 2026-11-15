import json
import sqlite3
from pathlib import Path
LEADERBOARD_PATH = "leaderboard.json"


class AnswerStore:
    def __init__(self, path: str | Path = "quiz.db") -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_code TEXT NOT NULL,
                    player TEXT NOT NULL,
                    answered_at TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT,
                    score INTEGER NOT NULL
                )
                """
            )

    def record_answer(
        self,
        match_code: str,
        player: str,
        answered_at: str,
        question: str,
        answer: str | None,
        score: int,
    ) -> None:
        with sqlite3.connect(self._path) as connection:
            connection.execute(
                """
                INSERT INTO answers (
                    match_code, player, answered_at, question, answer, score
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (match_code, player, answered_at, question, answer, score),
            )


class ScoreBoard:
    def __init__(self, path: str = LEADERBOARD_PATH) -> None:
        self._path = Path(path)
        self._data: dict[str, dict[str, int]] = {}
        self._path.parent.mkdir(parents=True, exist_ok=True)

        if self._path.exists():
            with open(self._path, encoding="utf-8") as file:
                contents = file.read()
            if contents.strip():
                self._data = json.loads(contents)

    def is_empty(self) -> bool:
        return not self._data

    def record(
        self, winner: str, player1: str, score1: int, player2: str, score2: int
    ) -> None:
        for name, points in [(player1, score1), (player2, score2)]:
            if name not in self._data:
                self._data[name] = {"wins": 0, "points": 0}
            self._data[name]["points"] += points

        if winner is not None:
            self._data[winner]["wins"] += 1
        self._save()

    def top(self, n: int = 5) -> list[tuple[str, dict[str, int]]]:
        def wins_then_points(item) -> tuple[int, int]:
            return item[1]["wins"], item[1]["points"]

        return sorted(self._data.items(), key=wins_then_points, reverse=True)[:n]

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as file:
            json.dump(self._data, file, ensure_ascii=False, indent=2)

