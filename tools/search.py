import os
from pathlib import Path
import re

def grep_search(query: str, path: str = ".", include: str = "", case_insensitive: bool = False) -> str:
    """
    Search for patterns across files recursively.
    """
    try:
        search_path = Path(path)
        if not search_path.exists():
            return f"Error: Path '{path}' does not exist."
            
        results = []
        flags = re.IGNORECASE if case_insensitive else 0
        try:
            pattern = re.compile(query, flags)
        except re.error as e:
            return f"Error: Invalid regex pattern '{query}': {e}"

        def is_match(filepath: Path) -> bool:
            if not include:
                return True
            # Simple glob matching for 'include'
            from fnmatch import fnmatch
            return fnmatch(filepath.name, include)

        # Simple recursive search (ignoring .git, node_modules etc.)
        ignore_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv'}
        
        for root, dirs, files in os.walk(search_path):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                filepath = Path(root) / file
                if not is_match(filepath):
                    continue
                    
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if pattern.search(line):
                                results.append(f"{filepath}:{line_num}:{line.strip()}")
                except UnicodeDecodeError:
                    continue # Skip binary files
                except Exception:
                    continue
                    
        if not results:
            return f"No matches found for '{query}' in '{path}'."
            
        return "\n".join(results[:100]) # Cap at 100 results to avoid massive output
    except Exception as e:
        return f"Error executing search: {e}"
