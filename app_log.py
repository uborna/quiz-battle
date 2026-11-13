import logging
from pathlib import Path


class AppLog:
    @staticmethod
    def setup(filename: str | Path | None = None):
        logger = logging.getLogger("quiz_battle")
        logger.setLevel(logging.INFO)
        if not any(
            getattr(handler, "_quiz_battle_file_handler", False)
            for handler in logger.handlers
        ):
            log_path = (
                Path(filename)
                if filename
                else Path(__file__).with_name("quiz_game.log")
            )
            handler = logging.FileHandler(log_path, encoding="utf-8")
            handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
            )
            setattr(handler, "_quiz_battle_file_handler", True)
            logger.addHandler(handler)
        return logger

    @staticmethod
    def get(name: str) -> logging.Logger:
        return logging.getLogger(f"quiz_battle.{name}")