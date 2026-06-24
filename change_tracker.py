# change_tracker.py
import os
from typing import Optional


class ChangeLog:
    """
    Tracks file modifications for undo support.
    Supports grouping multiple file changes into a single transaction
    (e.g. all edits made during one user turn) so /undo reverts everything
    from the last turn atomically.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.history: list[list[dict]] = []
            cls._instance._current_tx: Optional[list[dict]] = None
        return cls._instance

    def begin_transaction(self) -> None:
        """Start grouping file changes into one undoable unit."""
        self._current_tx = []

    def commit_transaction(self) -> None:
        """Finish the current transaction and push it to history."""
        if self._current_tx is not None:
            if self._current_tx:  # only save if something was recorded
                self.history.append(self._current_tx)
            self._current_tx = None

    def record_state(self, filepath: str) -> None:
        """Record the pre-modification state of a file."""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = None  # new file — undo will delete it

            entry = {"path": filepath, "content": content}

            if self._current_tx is not None:
                self._current_tx.append(entry)
            else:
                # No open transaction — treat as single-file transaction
                self.history.append([entry])

        except Exception:
            pass  # binary files or read errors — silently skip

    def undo_last(self) -> str:
        """Revert all file changes from the last transaction."""
        if not self.history:
            return "Nothing to undo."

        tx = self.history.pop()
        results = []

        for change in reversed(tx):
            filepath = change["path"]
            old_content = change["content"]
            try:
                if old_content is None:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    results.append(f"Deleted '{filepath}' (newly created file).")
                else:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(old_content)
                    results.append(f"Reverted '{filepath}'.")
            except Exception as e:
                # Restore the failed transaction
                self.history.append(tx)
                return f"Undo failed on '{filepath}': {e}"

        file_count = len(tx)
        header = f"Undo successful ({file_count} file{'s' if file_count > 1 else ''}):"
        return header + "\n  " + "\n  ".join(results)


change_log = ChangeLog()
