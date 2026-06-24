from rich.console import Console
from rich.prompt import Confirm
import sys

console = Console()

# Global flag to auto-approve everything, could be set via CLI arg later
AUTO_APPROVE = False

def require_approval(action: str, details: str, is_destructive: bool = False) -> bool:
    """
    Prompt the user for permission before executing a potentially dangerous action.
    Returns True if approved, False otherwise.
    """
    if AUTO_APPROVE:
        return True
        
    color = "bold red" if is_destructive else "bold yellow"
    prefix = "🚨" if is_destructive else "⚠"
    
    console.print(f"\n[{color}]{prefix} Termina wants to run:[/{color}] {action}")
    console.print(f"[dim]{details}[/dim]")
    
    # Check if we are running in an interactive terminal
    if not sys.stdin.isatty():
        console.print(
            f"[bold red]⛔ Auto-denied (non-interactive session):[/bold red] {action}\n"
            "[dim]Run termina in an interactive terminal to approve actions.[/dim]"
        )
        return False
        
    try:
        response = Confirm.ask(f"[{color}]Allow?[/{color}]", default=False)
        return response
    except (KeyboardInterrupt, EOFError):
        return False
