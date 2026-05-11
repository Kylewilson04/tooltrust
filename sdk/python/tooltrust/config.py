import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".tooltrust"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(cfg: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.chmod(0o700)
    CONFIG_FILE.write_text(json.dumps(cfg))
    CONFIG_FILE.chmod(0o600)


def clear_config():
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()


def mask_key(key: str) -> str:
    """Show only first 4 + last 4 chars. Never print full key."""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"
