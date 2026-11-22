import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path

CONFIG_DIR = Path(os.path.expanduser("~")) / ".pdfprocessor"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class AppConfig:
    theme_mode: str = "System"
    default_export_dir: str = ""
    brute_force_max_length: int = 4
    ocr_language: str = "eng"
    recent_files: list = field(default_factory=list)
    max_recent_files: int = 10

    def add_recent_file(self, path):
        path = str(path)
        if path in self.recent_files:
            self.recent_files.remove(path)
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[: self.max_recent_files]


def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            valid_keys = set(AppConfig.__dataclass_fields__.keys())
            filtered = {k: v for k, v in data.items() if k in valid_keys}
            return AppConfig(**filtered)
        except (json.JSONDecodeError, TypeError, KeyError):
            return AppConfig()
    return AppConfig()


def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(asdict(config), f, indent=2, ensure_ascii=False)
