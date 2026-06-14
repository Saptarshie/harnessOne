"""Session persistence manager."""

import json
import logging
from pathlib import Path

from harness.session.session import Session

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages session CRUD operations and persistence."""

    def __init__(self, storage_path: str = "sessions", auto_save: bool = True):
        self._path = Path(storage_path)
        self._path.mkdir(parents=True, exist_ok=True)
        self._auto_save = auto_save

    def create_session(self) -> str:
        session = Session()
        self.save_session(session)
        return session.id

    def load_session(self, session_id: str) -> Session | None:
        file_path = self._path / f"{session_id}.json"
        if not file_path.exists():
            return None
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            return Session.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None

    def save_session(self, session: Session):
        file_path = self._path / f"{session.id}.json"
        file_path.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")

    def list_sessions(self) -> list[dict]:
        sessions = []
        for file_path in self._path.glob("*.json"):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                sessions.append({
                    "id": data["id"],
                    "title": data.get("title", ""),
                    "last_active": data.get("last_active", ""),
                    "message_count": len(data.get("messages", [])),
                })
            except Exception:
                continue
        sessions.sort(key=lambda s: s["last_active"], reverse=True)
        return sessions

    def delete_session(self, session_id: str):
        file_path = self._path / f"{session_id}.json"
        if file_path.exists():
            file_path.unlink()
