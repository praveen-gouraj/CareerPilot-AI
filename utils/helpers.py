import json
import os
import re
from typing import Iterable

from werkzeug.utils import secure_filename

from config import Config


def allowed_file(filename: str, allowed_extensions: Iterable[str]) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in set(allowed_extensions)


def ensure_upload_directory() -> None:
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)


def safe_filename(filename: str) -> str:
    return secure_filename(filename).replace(" ", "_")


def parse_skill_selection(form_data, skill_keys):
    selected = []
    for key in skill_keys:
        if form_data.get(key) in {"on", "1", "true", "True"} or key in form_data:
            selected.append(key)
    return selected


def json_dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def json_loads(value, default=None):
    if not value:
        return default if default is not None else []
    try:
        return json.loads(value)
    except Exception:
        return default if default is not None else []


def percent(value: float) -> int:
    return max(0, min(100, int(round(value))))


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    return text.strip("-")
