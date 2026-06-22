import os
from pathlib import Path

def list_directory(path: str = ".") -> str:
    """
    Lists the contents of a directory.
    
    Args:
        path (str): The path to the directory to list. Defaults to the current directory.
        
    Returns:
        str: A formatted string of the directory contents or an error message.
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
    
    Args:
        path (str): The path to the file to read.
        
    Returns:
        str: The contents of the file or an error message.
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
    
    Args:
        path (str): The path to the file to write.
        content (str): The content to write to the file.
        
    Returns:
        str: A success message or an error message.
    """
    try:
        file_path = Path(path)
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to file '{path}'."
    except Exception as e:
        return f"Error writing to file: {e}"
