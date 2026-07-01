import logging
import uuid
from typing import Callable

from pymongo.errors import PyMongoError

from shared.models.session_log import ErrorLog, SessionMode, ToolCallLog
from shared.repositories.session_log_repository import SessionLogRepository

logger = logging.getLogger(__name__)


class SessionLogger:
    """Wraps SessionLogRepository so a Mongo outage degrades to a console warning instead of crashing the CLI."""

    def __init__(self, repo: SessionLogRepository):
        self._repo = repo
        self.session_id = str(uuid.uuid4())

    def start_session(self, name: str | None = None) -> None:
        self._safe(self._repo.start_session, self.session_id, name)

    def set_name(self, name: str) -> None:
        self._safe(self._repo.set_name, self.session_id, name)

    def start_message(self, message_number: int, mode: SessionMode, prompt: str) -> None:
        self._safe(self._repo.start_message, self.session_id, message_number, mode, prompt)

    def log_tool_call(self, message_number: int, tool_call: ToolCallLog) -> None:
        self._safe(self._repo.log_tool_call, self.session_id, message_number, tool_call)

    def complete_message(self, message_number: int, answer: str, sources: list[str]) -> None:
        self._safe(self._repo.complete_message, self.session_id, message_number, answer, sources)

    def log_message_error(self, message_number: int, error: ErrorLog) -> None:
        self._safe(self._repo.log_message_error, self.session_id, message_number, error)

    def end_session(self) -> None:
        self._safe(self._repo.end_session, self.session_id)

    def _safe(self, fn: Callable, *args) -> None:
        try:
            fn(*args)
        except PyMongoError as exc:
            logger.warning("Session logging failed (%s): %s", fn.__name__, exc)
