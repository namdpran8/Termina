import os
from pathlib import Path
import difflib
from permissions import require_approval
from rich.console import Console

console = Console()

def list_directory(path: str = ".") -> str:
    """
    Lists the contents of a directory.
    """
    try:
        dir_path = Path(path)
        if not dir_path.exists():
            return f"Error: Path '{path}' does not exist."
        if not dir_path.is_dir():
            return f"Error: Path '{path}' is not a directory."
            
        items = list(dir_path.iterdir())
        if not items:
            return f"Directory '{path}' is empty."
            
        result = []
        for item in items:
            item_type = "DIR" if item.is_dir() else "FILE"
            result.append(f"[{item_type}] {item.name}")
            
        return "\n".join(result)
    except Exception as e:
        return f"Error listing directory: {e}"

def read_file(path: str) -> str:
    """
    Reads the content of a file.
    """
    try:
        file_path = Path(path)
        if not file_path.exists():
            return f"Error: File '{path}' does not exist."
        if not file_path.is_file():
            return f"Error: Path '{path}' is not a file."
            
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        return f"Error: File '{path}' appears to be a binary file."
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(path: str, content: str) -> str:
    """
    Writes content to a file, creating it if it doesn't exist.
    """
    if not require_approval(f"Create or overwrite file: {path}", f"{len(content)} characters to write"):
        return f"Error: User denied permission to write to file '{path}'."
        
    try:
        file_path = Path(path)
        
        # Record state for undo
        from change_tracker import change_log
        change_log.record_state(str(file_path))
        
        file_path.parent.mkdir(parents=True, exist_ok=True)

        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to file '{path}'."
    except Exception as e:
        return f"Error writing to file: {e}"

def edit_file(path: str, target_content: str, replacement_content: str) -> str:
    """
    Replaces a specific block of text within a file.
    """
    try:
        file_path = Path(path)
        if not file_path.exists():
            return f"Error: File '{path}' does not exist."
            
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            
        if target_content not in file_content:
            return f"Error: The target_content was not found in '{path}'. Please ensure exact string matching including whitespace."
            
        # Check if multiple occurrences
        if file_content.count(target_content) > 1:
            return f"Error: target_content occurs multiple times in '{path}'. Please provide a larger block of text to ensure unique matching."
            
        new_content = file_content.replace(target_content, replacement_content)
        
        # Display diff to user
        diff = list(difflib.unified_diff(
            file_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"{path} (old)",
            tofile=f"{path} (new)",
            n=3
        ))
        
        if not diff:
            return f"No changes detected in '{path}'."
            
        diff_text = "".join(diff)
        
        if not require_approval(f"Edit file: {path}", diff_text):
            return f"Error: User denied permission to edit file '{path}'."
            
        # Record state for undo
        from change_tracker import change_log
        change_log.record_state(str(file_path))
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        return f"Successfully edited file '{path}'."
        
    except UnicodeDecodeError:
        return f"Error: File '{path}' appears to be a binary file."
    except Exception as e:
        return f"Error editing file: {e}"
