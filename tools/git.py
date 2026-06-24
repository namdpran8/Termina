import subprocess
from permissions import require_approval

def run_git_command(command: str) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )
        output = result.stdout + result.stderr
        return output if output else f"Command '{command}' executed successfully with no output."
    except Exception as e:
        return f"Error executing git command: {e}"

def git_status() -> str:
    """Shows the current git status."""
    return run_git_command("git status")

def git_diff() -> str:
    """Shows the git diff of unstaged changes."""
    return run_git_command("git diff")

def git_commit(message: str) -> str:
    # Show what will be staged BEFORE asking for approval
    status = run_git_command("git status --short")
    details = f"Commit message: {message}\n\nFiles to be staged:\n{status}"

    if not require_approval("git add . && git commit", details):
        return "Error: User denied permission to commit."

    run_git_command("git add .")
    return run_git_command(f'git commit -m "{message}"')

def git_log(n: int = 5) -> str:
    """Shows the recent git log."""
    return run_git_command(f"git log -n {n} --oneline")
