import os
import warnings
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _get_env(key: str, default: str, *, secret: bool = False) -> str:
    """Return env var or default, emitting a warning when falling back."""
    value = os.environ.get(key)
    if value is None:
        warnings.warn(
            f"[config] {key} not set — using {'placeholder' if secret else 'default'} value. "
            f"Set {key} in your environment or .env file before deploying.",
            stacklevel=3,
        )
        return default
    return value


# ── Collected at import time so the summary prints once ──────────────────────
_MISSING: list[str] = []


def _require_env(key: str, default: str) -> str:
    """Like _get_env but also records the key as missing for the summary."""
    value = os.environ.get(key)
    if value is None:
        _MISSING.append(key)
        return default
    return value


class Config:
    # ── Secrets (warn loudly) ─────────────────────────────────────────────────
    SECRET_KEY = _require_env("SECRET_KEY", "change-me-in-production")
    DEV_KEY    = _require_env("DEV_KEY",    "bb-huge-dev-key-change-me")

    # ── Database ──────────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'bb_huge.db')}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Uploads ───────────────────────────────────────────────────────────────
    UPLOAD_FOLDER       = os.path.join(BASE_DIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH  = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS  = {"png", "jpg", "jpeg", "gif", "pdf", "txt", "md", "xml", "json", "html", "zip"}

    # ── Sessions ──────────────────────────────────────────────────────────────
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY    = True
    SESSION_COOKIE_SAMESITE    = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE      = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    SESSION_COOKIE_NAME        = os.environ.get("SESSION_COOKIE_NAME", "bb_huge_session")
    PREFERRED_URL_SCHEME       = "https" if SESSION_COOKIE_SECURE else "http"

    # ── MCP / Flask ports ─────────────────────────────────────────────────────
    MCP_HOST   = os.environ.get("MCP_HOST",   "127.0.0.1")
    MCP_PORT   = int(os.environ.get("MCP_PORT",   "5001"))
    FLASK_PORT = int(os.environ.get("FLASK_PORT", "5000"))

    # ── Validation summary (runs once when the class body is evaluated) ───────
    @classmethod
    def validate(cls) -> None:
        """Call from your app factory — prints a grouped warning summary."""
        if _MISSING:
            border = "=" * 60
            lines  = [
                border,
                "  ⚠️  CONFIG WARNING — missing environment variables",
                border,
                "  The following vars were not found; safe defaults are",
                "  being used so the app can still start, but you MUST",
                "  set real values before going to production:",
                "",
            ]
            for key in _MISSING:
                lines.append(f"    • {key}")
            lines += [
                "",
                "  Tip: copy .env.example → .env and fill in the blanks.",
                border,
            ]
            warnings.warn("\n".join(lines), stacklevel=2)


# Pretty-print the summary at import time (useful during `flask run`)
if _MISSING:
    Config.validate()