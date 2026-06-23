import os

class ChangeLog:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChangeLog, cls).__new__(cls)
            cls._instance.history = []
        return cls._instance
        
    def record_state(self, filepath: str):
        """Record the state of a file before it is modified."""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = None # Indicates it was a new file
                
            self.history.append({
                "path": filepath,
                "content": content
            })
        except Exception:
            pass # Ignore binary files or read errors
            
    def undo_last(self) -> str:
        """Revert the last file change."""
        if not self.history:
            return "No changes to undo."
            
        last_change = self.history.pop()
        filepath = last_change["path"]
        old_content = last_change["content"]
        
        try:
            if old_content is None:
                # File was created, so we delete it to undo
                if os.path.exists(filepath):
                    os.remove(filepath)
                return f"Undo successful: Deleted '{filepath}' (it was newly created)."
            else:
                # Revert content
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(old_content)
                return f"Undo successful: Reverted '{filepath}' to its previous state."
        except Exception as e:
            # Put it back on the stack if we failed
            self.history.append(last_change)
            return f"Error during undo: {e}"

change_log = ChangeLog()
