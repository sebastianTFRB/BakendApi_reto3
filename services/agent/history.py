"""
In-memory conversation history for the lead agent.
Helps keep per-user context so the LLM does not re-ask for data.
"""

from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from typing import Deque, Dict, List, Optional, Tuple

ChatTurn = Tuple[str, str]


def _clean_key(key: Optional[str]) -> Optional[str]:
    if not key:
        return None
    cleaned = key.strip()
    return cleaned or None


class ConversationHistory:
    def __init__(self, max_messages: int = 20) -> None:
        self.max_messages = max_messages
        self._store: Dict[str, Deque[ChatTurn]] = defaultdict(deque)
        self._lock = Lock()

    def append(self, key: Optional[str], role: str, message: str) -> None:
        """
        Save a message in the conversation identified by `key`.
        Role is stored as "user" or "agent" for readability in prompts.
        """
        cleaned_key = _clean_key(key)
        if not cleaned_key or not message:
            return

        normalized_role = role if role in {"user", "agent"} else "user"
        content = message.strip()
        if not content:
            return

        with self._lock:
            turns = self._store[cleaned_key]
            turns.append((normalized_role, content))
            while len(turns) > self.max_messages:
                turns.popleft()

    def get(self, key: Optional[str]) -> List[ChatTurn]:
        cleaned_key = _clean_key(key)
        if not cleaned_key:
            return []
        with self._lock:
            return list(self._store.get(cleaned_key, ()))

    def clear(self, key: Optional[str]) -> None:
        cleaned_key = _clean_key(key)
        if not cleaned_key:
            return
        with self._lock:
            self._store.pop(cleaned_key, None)


def format_history(turns: List[ChatTurn]) -> str:
    """
    Render the history as plain text to be injected in the prompt.
    """
    if not turns:
        return "Sin historial previo."

    lines = ["Contexto recopilado del usuario (no repitas preguntas ya respondidas):"]
    for role, content in turns:
        speaker = "Usuario" if role == "user" else "Agente"
        lines.append(f"{speaker}: {content}")
    return "\n".join(lines)


def resolve_history_key(*identifiers: Optional[str]) -> Optional[str]:
    """
    Choose the first non-empty identifier to use as history key.
    Front y WhatsApp pueden enviar el mismo id/telefono/email
    para compartir contexto.
    """
    for value in identifiers:
        if value:
            cleaned = value.strip()
            if cleaned:
                return cleaned
    return None


history_store = ConversationHistory(max_messages=20)
