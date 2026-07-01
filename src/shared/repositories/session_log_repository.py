from datetime import datetime, timezone

from pymongo.database import Database

from shared.models.session_log import ErrorLog, MessageLog, SessionLog, SessionMode, ToolCallLog


class SessionLogRepository:
    COLLECTION = "session_logs"

    def __init__(self, db: Database):
        self._col = db[self.COLLECTION]

    def start_session(self, session_id: str, name: str | None = None) -> None:
        session = SessionLog(session_id=session_id, name=name)
        self._col.insert_one(session.model_dump(mode="json"))

    def set_name(self, session_id: str, name: str) -> None:
        self._col.update_one({"session_id": session_id}, {"$set": {"name": name}})

    def start_message(self, session_id: str, message_number: int, mode: SessionMode, prompt: str) -> None:
        message = MessageLog(message_number=message_number, mode=mode, prompt=prompt)
        self._col.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": message.model_dump(mode="json")},
                "$inc": {"message_count": 1},
            },
        )

    def log_tool_call(self, session_id: str, message_number: int, tool_call: ToolCallLog) -> None:
        self._col.update_one(
            {"session_id": session_id, "messages.message_number": message_number},
            {"$push": {"messages.$.tool_calls": tool_call.model_dump(mode="json")}},
        )

    def complete_message(self, session_id: str, message_number: int, answer: str, sources: list[str]) -> None:
        self._col.update_one(
            {"session_id": session_id, "messages.message_number": message_number},
            {"$set": {"messages.$.answer": answer, "messages.$.sources": sources}},
        )

    def log_message_error(self, session_id: str, message_number: int, error: ErrorLog) -> None:
        self._col.update_one(
            {"session_id": session_id, "messages.message_number": message_number},
            {"$set": {"messages.$.error": error.model_dump(mode="json")}},
        )

    def end_session(self, session_id: str) -> None:
        self._col.update_one(
            {"session_id": session_id},
            {"$set": {"ended_at": datetime.now(timezone.utc).isoformat()}},
        )
