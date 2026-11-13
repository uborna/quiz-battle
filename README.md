# Quiz Club

[فارسی](READMEFA.md)

A two-player quiz you run locally. One person creates a room, shares the invite link, and both players take turns answering the same questions. A correct answer is worth 10 points, with 3 extra points for answering in the first half of the 30-second turn.

## Requirements

- Python 3.10 or newer

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY="your Google AI Studio API key"
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).
Alternatively, put `GEMINI_API_KEY=your-key` and `GEMINI_MODEL=gemini-3.5-flash-lite` in a `.env` file in the project directory; the app loads it on startup. `GEMINI_MODEL` defaults to `gemini-3.5-flash-lite`. Restart the app after editing `.env`. Quiz Club requires `GEMINI_API_KEY` and uses Google's Gemini API to generate five new questions for each match. It does not load questions from `questions.json`. Keep the key private and do not commit it to the repository. If the key is missing or generation fails, the app shows an error instead of starting a match with local questions.

After updating dependencies or code, reinstall packages with `pip install -r requirements.txt` and restart the running server.
Gemini API errors are written to `quiz_game.log` in the project directory. The log includes the sanitized API error and status code, but never the API key. This file is ignored by Git.

| Variable | Default | Purpose |
|---|---|---|
| `HOST` | `127.0.0.1` | Bind address |
| `PORT` | `5000` | Bind port |
| `SECRET_KEY` | a local development value | Signs the session cookie. Set this before sharing the server. |
| `GEMINI_API_KEY` | required | Google AI Studio API key used to generate fresh questions for each match. |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Gemini model used to generate questions. |
| `APP_DEBUG` | unset | Set to `1` to reload on code changes |

## Play

1. Choose a question category, enter your name, and create a room.
2. Send the invite link to the other player. Their name must be different from yours.
3. Both players mark ready. The match starts on the host's turn.
4. Answer A–D before the clock runs out. The turn then passes to the other player.
5. After both answers, review the round and continue together.
6. When the questions run out, the results page shows the winner. Ties have no winner.

Wins and total points are kept in the hall of fame on the home page. Wins rank first, then points.

Gemini generates five questions for each new match; local JSON questions are not used.

## Layout

| Path | Role |
|---|---|
| `app.py` | FastAPI routes: rooms, turns, chat, results |
| `engine.py` | Scoring rules (`Question`, `Match`, `Chat`) |
| `storage.py` | JSON leaderboard, SQLite answer log |
| `templates/` | Home, join, game, and results pages |
| `tests/` | Engine, storage, and web-flow tests |

Active rooms live in memory and disappear when the process stops. Finished matches still update `leaderboard.json`, and each answer is written to `quiz.db`. Both of those files are created on first use and are gitignored.

## Tests

```bash
pytest
```
