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
            
        MAX_READ_BYTES = 1_000_000  # 1MB
        size = file_path.stat().st_size
        if size > MAX_READ_BYTES:
            return (
                f"Error: File '{path}' is too large to read directly "
                f"({size // 1024}KB). Use grep_search to find specific content instead."
            )
            
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
        
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Record state for undo just before write (not before)
        from change_tracker import change_log
        change_log.record_state(str(file_path))
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            # Remove the phantom undo entry if write fails
            if change_log.history:
                change_log.history.pop()
            raise
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
            
        # Record state for undo just before write (not before)
        from change_tracker import change_log
        change_log.record_state(str(file_path))
            
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
        except Exception:
            # Remove the phantom undo entry if write fails
            if change_log.history:
                change_log.history.pop()
            raise
            
        return f"Successfully edited file '{path}'."
        
    except UnicodeDecodeError:
        return f"Error: File '{path}' appears to be a binary file."
    except Exception as e:
        return f"Error editing file: {e}"

def read_files(paths: list) -> str:
    """
    Reads multiple files in one call. Returns concatenated content with headers.
    Useful for loading several related files into context at once.
    """
    results = []
    for path in paths:
        results.append(f"\n{'='*60}\n# FILE: {path}\n{'='*60}\n")
        results.append(read_file(path))
    return "\n".join(results)

def glob_files(pattern: str, path: str = ".") -> str:
    """
    Find files matching a glob pattern (e.g. '**/*.py', 'src/*.ts').
    Returns a newline-separated list of matching file paths.
    """
    search_root = Path(path)
    matches = list(search_root.glob(pattern))
    # Filter out ignored directories
    ignore_parts = {'.git', 'node_modules', '__pycache__', '.venv', 'venv'}
    matches = [m for m in matches if not any(p in ignore_parts for p in m.parts)]
    if not matches:
        return f"No files matched pattern '{pattern}' in '{path}'."
    return "\n".join(str(m) for m in sorted(matches))
