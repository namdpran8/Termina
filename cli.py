import typer
from rich.console import Console
from rich.panel import Panel
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style

from config import set_api_key, set_default_model, get_default_model
from agent import Agent

app = typer.Typer(help="Termina: An AI Coding Assistant (Claude Code Alternative)")
config_app = typer.Typer(help="Configuration commands")
app.add_typer(config_app, name="config")

console = Console()

@app.command()
def chat():
    """
    Start an interactive chat session with Termina.
    """
    provider, model = get_default_model()
    console.print(Panel(f"Welcome to Termina!\nUsing Model: [bold cyan]{model}[/bold cyan] via [bold yellow]{provider}[/bold yellow]", title="Termina Chat", border_style="blue"))
    
    agent = Agent()
    
    style = Style.from_dict({
        'prompt': 'ansicyan bold',
    })

    while True:
        try:
            user_input = prompt("Termina> ", style=style)
            if user_input.lower() in ["exit", "quit", "\\q"]:
                console.print("Goodbye!")
                break
            if not user_input.strip():
                continue
                
            agent.chat(user_input)
            
        except KeyboardInterrupt:
            continue
        except EOFError:
            break

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
