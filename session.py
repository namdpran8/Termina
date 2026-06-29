import json
import os
from pathlib import Path
from datetime import datetime

SESSION_DIR = Path(os.path.expanduser("~/.termina/sessions"))
DIRECTORY_MAP_FILE = SESSION_DIR / "directory_map.json"

def _ensure_session_dir():
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

def save_session(messages: list, session_id: str = None) -> str:
    """Save the chat history to a JSON file."""
    if len(messages) <= 1:
        return None # Only system prompt exists
        
    _ensure_session_dir()
    
    if not session_id:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_id = f"session_{timestamp}"
        
    file_path = SESSION_DIR / f"{session_id}.json"
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2)
            
        # Automatically link this session to the current working directory
        link_session_to_directory(session_id, os.getcwd())
        
        return session_id
    except Exception:
        return None

def link_session_to_directory(session_id: str, cwd: str):
    """Link a directory path to its most recent session ID."""
    _ensure_session_dir()
    mapping = {}
    if DIRECTORY_MAP_FILE.exists():
        try:
            with open(DIRECTORY_MAP_FILE, "r", encoding="utf-8") as f:
                mapping = json.load(f)
        except Exception:
            pass
            
    # Normalize path for cross-platform consistency
    normalized_cwd = os.path.normpath(os.path.abspath(cwd))
    mapping[normalized_cwd] = session_id
    
    try:
        with open(DIRECTORY_MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2)
    except Exception:
        pass

def get_session_for_directory(cwd: str) -> str:
    """Get the most recent session ID for a given directory path."""
    if not DIRECTORY_MAP_FILE.exists():
        return None
        
    normalized_cwd = os.path.normpath(os.path.abspath(cwd))
    try:
        with open(DIRECTORY_MAP_FILE, "r", encoding="utf-8") as f:
            mapping = json.load(f)
            return mapping.get(normalized_cwd)
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
    except json.JSONDecodeError:
        print(f"Warning: Session file '{session_id}' is corrupted and cannot be loaded.")
        return None
    except Exception as e:
        print(f"Warning: Could not load session '{session_id}': {e}")
        return None

def list_sessions() -> list:
    """List all available saved sessions."""
    _ensure_session_dir()
    sessions = []
    for f in sorted(SESSION_DIR.glob("*.json"), reverse=True):
        sessions.append(f.stem)
    return sessions
