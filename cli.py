import os
import typer
from rich.console import Console
from rich.panel import Panel
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style

from config import set_api_key, set_default_model, get_default_model
from agent import Agent
from startup import startup_scan

app = typer.Typer(help="Termina: An AI Coding Assistant (Claude Code Alternative)", invoke_without_command=True)
config_app = typer.Typer(help="Configuration commands")
app.add_typer(config_app, name="config")

console = Console()

from session import save_session, load_session, list_sessions

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Termina: AI Coding Assistant"""
    if ctx.invoked_subcommand is None:
        chat()

@app.command()
def history():
    """List all past chat sessions."""
    sessions = list_sessions()
    if not sessions:
        console.print("No saved sessions found.")
        return
    console.print("[bold cyan]Past Sessions:[/bold cyan]")
    for s in sessions:
        console.print(f"  - {s}")
    console.print("\nTo resume a session, run: termina resume <session_id>")

@app.command()
def resume(session_id: str):
    """Resume a past chat session."""
    chat(session_id=session_id)

@app.command()
def chat(session_id: str = None):
    """
    Start an interactive chat session with Termina.
    """
    provider, model = get_default_model()
    
    # Run startup scan
    cwd = os.getcwd()
    context = startup_scan(cwd)
    
    welcome_message = f"""
[bold blue]  _____                    _             [/bold blue]
[bold blue] |_   _|__ _ __ _ __ ___ (_)_ __   __ _  [/bold blue]
[bold blue]   | |/ _ \\ '__| '_ ` _ \\| | '_ \\ / _` | [/bold blue]
[bold blue]   | |  __/ |  | | | | | | | | | | (_| | [/bold blue]
[bold blue]   |_|\\___|_|  |_| |_| |_|_|_| |_|\\__,_| [/bold blue]

   ◆ [bold]Termina v0.1.0[/bold]
   Model: [cyan]{model}[/cyan] via [yellow]{provider}[/yellow]
   
   📁 Working in: {context['cwd']}
   📦 Project: {context['project_type']}
   📄 {context['file_count']} files across {context['dir_count']} directories
"""
    if context['readme_summary']:
        welcome_message += f"\n   [green]✓[/green] README.md loaded into context"
    if context['custom_rules']:
        welcome_message += f"\n   [green]✓[/green] Custom rules loaded into context"
        
    welcome_message += "\n\n   Type 'exit' or 'quit' to leave."

    console.print(Panel(welcome_message, border_style="blue"))
    
    agent = Agent(context)
    if session_id:
        messages = load_session(session_id)
        if messages:
            agent.messages = messages
            console.print(f"[bold green]Successfully resumed session '{session_id}'[/bold green]")
        else:
            console.print(f"[bold red]Error: Session '{session_id}' not found.[/bold red]")
            return
    
    style = Style.from_dict({
        'prompt': 'ansicyan bold',
    })

    while True:
        try:
            user_input = prompt("Termina> ", style=style)
            
            # Basic exit
            if user_input.lower() in ["exit", "quit", "\\q"]:
                console.print("Goodbye!")
                break
                
            if not user_input.strip():
                continue
                
            # Intercept slash commands
            if user_input.startswith("/"):
                cmd = user_input.strip().lower()
                if cmd == "/help":
                    console.print("[bold cyan]Available Commands:[/bold cyan]")
                    console.print("  /help   - Show this message")
                    console.print("  /clear  - Clear conversation history")
                    console.print("  /cost   - Show token usage and estimated cost")
                    console.print("  /undo   - Revert the last file modification")
                    console.print("  /tree   - Print the project directory tree")
                    console.print("  exit    - Exit the application")
                elif cmd == "/clear":
                    # Keep the system prompt, clear everything else
                    agent.messages = agent.messages[:1]
                    console.print("[dim]Conversation history cleared.[/dim]")
                elif cmd == "/cost":
                    from cost_tracker import tracker
                    console.print(f"[bold green]{tracker.get_summary()}[/bold green]")
                elif cmd == "/undo":
                    from change_tracker import change_log
                    result = change_log.undo_last()
                    console.print(result)
                elif cmd == "/tree":
                    # Reuse startup scan tree
                    from startup import scan_directory
                    tree_str, _, _ = scan_directory(os.getcwd())
                    console.print(tree_str)
                else:
                    console.print(f"[red]Unknown command: {cmd}[/red]. Type /help for options.")
                continue
                
            agent.chat(user_input)
            
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
            
    # Save session on exit
    sid = save_session(agent.messages)
    if sid:
        console.print(f"[dim]Session saved: {sid}[/dim]")

@config_app.command("set-key")
def config_set_key(provider: str, key: str):
    """
    Set the API key for a specific provider (e.g., nvidia, openai, anthropic, gemini).
    """
    set_api_key(provider, key)
    console.print(f"[bold green]Successfully saved API key for provider: {provider}[/bold green]")

@config_app.command("set-model")
def config_set_model(provider: str, model: str):
    """
    Set the default model and provider to use.
    Example: termina config set-model nvidia meta/llama-3.1-70b-instruct
    """
    set_default_model(provider, model)
    console.print(f"[bold green]Default model set to {model} via {provider}[/bold green]")

@config_app.command("show")
def config_show():
    """
    Show current configuration.
    """
    provider, model = get_default_model()
    console.print(f"Current Provider: [bold yellow]{provider}[/bold yellow]")
    console.print(f"Current Model: [bold cyan]{model}[/bold cyan]")

if __name__ == "__main__":
    app()
