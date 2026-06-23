import json
import os
from pathlib import Path
from datetime import datetime

SESSION_DIR = Path(os.path.expanduser("~/.termina/sessions"))

def _ensure_session_dir():
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

def save_session(messages: list) -> str:
    """Save the chat history to a JSON file."""
    if len(messages) <= 1:
        return None # Only system prompt exists
        
    _ensure_session_dir()
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    session_id = f"session_{timestamp}"
    file_path = SESSION_DIR / f"{session_id}.json"
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2)
        return session_id
    except Exception:
        return None

def load_session(session_id: str) -> list:
    """Load a chat history from a JSON file."""
    file_path = SESSION_DIR / f"{session_id}.json"
    if not file_path.exists():
        return None
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def list_sessions() -> list:
    """List all available saved sessions."""
    _ensure_session_dir()
    sessions = []
    for f in sorted(SESSION_DIR.glob("*.json"), reverse=True):
        sessions.append(f.stem)
    return sessions
