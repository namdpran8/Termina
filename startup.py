import os
from pathlib import Path

def find_project_root(cwd: str) -> str:
    """Walk up the directory tree to find the project root."""
    current = Path(cwd).resolve()
    markers = ['.git', 'pyproject.toml', 'package.json', 'setup.py', 'requirements.txt']
    
    for _ in range(5): # Limit search depth
        for marker in markers:
            if (current / marker).exists():
                return str(current)
        if current.parent == current:
            break
        current = current.parent
        
    return cwd # Fallback to cwd if no markers found

def detect_project_type(root_dir: str) -> str:
    """Detect the primary language or framework of the project."""
    root = Path(root_dir)
    if (root / 'pyproject.toml').exists() or (root / 'setup.py').exists() or (root / 'requirements.txt').exists():
        return "Python"
    if (root / 'package.json').exists():
        return "Node.js / JavaScript"
    if (root / 'Cargo.toml').exists():
        return "Rust"
    if (root / 'go.mod').exists():
        return "Go"
    if (root / 'pom.xml').exists() or (root / 'build.gradle').exists():
        return "Java"
    
    return "Unknown / General"

def build_tree(root_dir: str, max_depth: int = 2) -> tuple[str, int, int]:
    """
    Builds a text representation of the directory tree.
    Returns (tree_string, file_count, dir_count)
    """
    ignore_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.env', '.idea', '.vscode'}
    
    tree_lines = []
    file_count = 0
    dir_count = 0
    
    root_path = Path(root_dir)
    
    def walk(directory, prefix="", depth=1):
        nonlocal file_count, dir_count
        if depth > max_depth:
            return
            
        try:
            entries = sorted(list(directory.iterdir()), key=lambda x: (x.is_file(), x.name.lower()))
            entries = [e for e in entries if e.name not in ignore_dirs and not e.name.endswith('.pyc')]
        except PermissionError:
            return

        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            
            tree_lines.append(f"{prefix}{connector}{entry.name}")
            
            if entry.is_dir():
                dir_count += 1
                extension_prefix = "    " if is_last else "│   "
                walk(entry, prefix + extension_prefix, depth + 1)
            else:
                file_count += 1

    walk(root_path)
    
    # If the tree is empty or too small, that's fine
    return "\n".join(tree_lines), file_count, dir_count

def read_first_n_lines(filepath: str, n: int = 100) -> str:
    """Read the first N lines of a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [next(f) for _ in range(n)]
        content = "".join(lines)
        return content
    except StopIteration:
        # File has fewer than n lines
        pass
    except Exception:
        return ""
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ""

def startup_scan(cwd: str) -> dict:
    """Scan the directory and return project context for the LLM."""
    context = {
        "cwd": cwd,
        "project_root": find_project_root(cwd),
        "project_type": "Unknown",
        "file_count": 0,
        "dir_count": 0,
        "tree": "",
        "readme_summary": "",
        "custom_rules": "",
    }
    
    context["project_type"] = detect_project_type(context["project_root"])
    
    tree, files, dirs = build_tree(context["project_root"], max_depth=2)
    context["tree"] = tree
    context["file_count"] = files
    context["dir_count"] = dirs
    
    # Check for README
    root_path = Path(context["project_root"])
    for readme_name in ['README.md', 'readme.md', 'README.txt']:
        readme_path = root_path / readme_name
        if readme_path.exists():
            context["readme_summary"] = read_first_n_lines(str(readme_path), 100)
            break
            
    # Check for custom rules
    for rule_name in ['.terminarc', 'AGENTS.md']:
        rule_path = root_path / rule_name
        if rule_path.exists():
            context["custom_rules"] = read_first_n_lines(str(rule_path), 200)
            break
            
    return context
