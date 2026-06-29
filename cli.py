import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_WARNINGS"] = "1"
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

import threading

@app.command()
def chat(session_id: str = None, initial_prompt: str = typer.Option(None, "-p", "--prompt",
         help="Run a single prompt non-interactively and exit."),
         new: bool = typer.Option(False, "--new", help="Start a new session instead of resuming directory session.")):
    """
    Start an interactive chat session with Termina.
    """
    # If called directly from Python (e.g. from main()), Typer might inject OptionInfo
    if not isinstance(initial_prompt, str):
        initial_prompt = None

    provider, model = get_default_model()
    cwd = os.getcwd()

    # Show a minimal welcome instantly — scan fills in details in background
    console.print(Panel(
        f"[bold blue]Termina[/bold blue] v0.1.0  |  Model: [cyan]{model}[/cyan] via [yellow]{provider}[/yellow]\n"
        f"Working in: {cwd}\n[dim]Scanning project...[/dim]",
        border_style="blue"
    ))

    # Run startup scan in background thread
    context_holder = {}
    scan_done = threading.Event()

    def _scan():
        from startup import startup_scan_cached
        context_holder["ctx"] = startup_scan_cached(cwd)
        scan_done.set()

    scan_thread = threading.Thread(target=_scan, daemon=True)
    scan_thread.start()

    # Initialize agent with minimal context immediately
    agent = Agent({"cwd": cwd, "project_type": "Scanning...", "readme_summary": "", "custom_rules": ""})

    # Wait for scan (up to 5 seconds) before first user input
    scan_done.wait(timeout=5)
    if context_holder.get("ctx"):
        ctx = context_holder["ctx"]
        # Update agent system prompt with real context
        agent = Agent(ctx)
        
        # Display local providers if running
        local = ctx.get("local_providers", {})
        running = [k for k, v in local.items() if v]
        if running:
            console.print(f"[dim][Local] {', '.join(running)} detected[/dim]")
            
        console.print(
            f"[dim][*] {ctx['project_type']} · {ctx['file_count']} files · "
            f"{ctx['dir_count']} dirs"
            + (" · README loaded" if ctx.get('readme_summary') else "")
            + (" · Custom rules loaded" if ctx.get('custom_rules') else "")
            + "[/dim]"
        )

    if not session_id and not new:
        from session import get_session_for_directory
        mapped_session = get_session_for_directory(cwd)
        if mapped_session:
            import rich.prompt
            if rich.prompt.Confirm.ask(f"\n[yellow]Found previous session for this directory. Resume?[/yellow]", default=True):
                session_id = mapped_session

    if session_id:
        from session import load_session
        messages = load_session(session_id)
        if messages:
            agent.messages = messages
            agent.session_id = session_id
            console.print(f"[bold green]Successfully resumed session '{session_id}'[/bold green]")
        else:
            console.print(f"[bold red]Error: Session '{session_id}' not found.[/bold red]")
            return
    
    # Non-interactive one-shot mode
    if initial_prompt:
        # Also check if there's piped stdin to prepend
        import sys
        if not sys.stdin.isatty():
            piped = sys.stdin.read().strip()
            if piped:
                initial_prompt = f"{piped}\n\n{initial_prompt}"
        agent.chat(initial_prompt)
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
            # Intercept CLI commands typed inside chat
            if user_input.startswith("termina "):
                import subprocess
                subprocess.run(user_input, shell=True)
                continue
                
            # Intercept slash commands
            if user_input.startswith("/"):
                cmd = user_input.strip().lower()
                if cmd == "/help":
                    console.print("[bold cyan]Available Commands:[/bold cyan]")
                    console.print("  /help              - Show this message")
                    console.print("  /clear             - Clear conversation history")
                    console.print("  /compact           - Summarize and compress conversation history")
                    console.print("  /cost              - Show token usage and estimated cost")
                    console.print("  /undo              - Revert the last file modification")
                    console.print("  /tree              - Print the project directory tree")
                    console.print("  /plan <task>       - Plan a task before executing it")
                    console.print("  /model             - Show current model")
                    console.print("  /model <p> <m>     - Switch model mid-session")
                    console.print("  /skill             - List available skills")
                    console.print("  /skill <name>      - Activate a skill")
                    console.print("  exit               - Exit the application")
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
                    from startup import build_tree
                    tree_str, _, _ = build_tree(os.getcwd())
                    console.print(tree_str)
                elif cmd.startswith("/plan"):
                    task = cmd[5:].strip()
                    if not task:
                        console.print("[dim]Usage: /plan <task description>[/dim]")
                        continue

                    plan_prompt = (
                        f"The user wants you to: {task}\n\n"
                        "Before doing ANYTHING, output a numbered plan of exactly what you will do — "
                        "which files you'll read, which you'll edit, what commands you'll run, in order. "
                        "Do NOT use any tools. Do NOT write any code yet. "
                        "Just list the plan as numbered steps. End with: 'Shall I proceed? [y/N]'"
                    )
                    agent.chat(plan_prompt)

                    try:
                        confirm = prompt("Proceed? [y/N] ", style=style).strip().lower()
                        if confirm in ("y", "yes"):
                            agent.chat(f"The user approved the plan. Now execute it step by step: {task}")
                        else:
                            console.print("[dim]Plan cancelled.[/dim]")
                            # Remove plan exchange from history to keep context clean
                            agent.messages = agent.messages[:-2]
                    except (KeyboardInterrupt, EOFError):
                        console.print("[dim]Plan cancelled.[/dim]")
                elif cmd == "/compact":
                    if len(agent.messages) <= 2:
                        console.print("[dim]Nothing to compact yet.[/dim]")
                        continue

                    console.print("[dim]Compacting conversation...[/dim]")
                    
                    history_text = "\n".join(
                        f"[{m['role'].upper()}]: {m['content'][:500] if isinstance(m.get('content'), str) else '(tool call)'}"
                        for m in agent.messages[1:]
                    )
                    
                    compaction_prompt = (
                        "Summarize the conversation so far into a concise context block that preserves:\n"
                        "- What the user is trying to build or fix\n"
                        "- Key decisions made\n"
                        "- Files that were read or modified\n"
                        "- Any important findings\n\n"
                        "Keep it under 300 words. Write in second person (e.g. 'You are working on...').\n\n"
                        f"Conversation to summarize:\n{history_text}"
                    )
                    
                    from litellm import completion
                    from config import get_api_key
                    kwargs = agent._build_completion_kwargs(
                        agent._provider, agent._model, agent._api_key
                    )
                    kwargs.pop("tools", None)
                    kwargs.pop("tool_choice", None)
                    kwargs["stream"] = False
                    kwargs["messages"] = [
                        agent.messages[0],
                        {"role": "user", "content": compaction_prompt}
                    ]
                    
                    try:
                        resp = completion(**kwargs)
                        summary = resp.choices[0].message.content
                        
                        agent.messages = [
                            agent.messages[0],
                            {"role": "user", "content": f"[Context from compacted history]\n{summary}"},
                            {"role": "assistant", "content": "Understood. I have the context from our previous work."}
                        ]
                        console.print(f"[dim]+ Compacted to {len(summary)} characters.[/dim]")
                    except Exception as e:
                        console.print(f"[red]Compaction failed: {e}[/red]")
                elif cmd.startswith("/model"):
                    parts = cmd.split()
                    if len(parts) == 3:
                        new_provider, new_model = parts[1], parts[2]
                        from config import set_default_model
                        set_default_model(new_provider, new_model)
                        agent.reload_model_config()
                        console.print(
                            f"[bold green]+ Switched to [cyan]{new_model}[/cyan] "
                            f"via [yellow]{new_provider}[/yellow][/bold green]"
                        )
                    elif len(parts) == 1:
                        console.print(
                            f"Current: [cyan]{agent._model}[/cyan] via [yellow]{agent._provider}[/yellow]\n"
                            "[dim]Usage: /model <provider> <model-name>[/dim]\n"
                            "[dim]See all options: termina config list-models[/dim]"
                        )
                    else:
                        console.print("[dim]Usage: /model <provider> <model-name>[/dim]")
                elif cmd == "/skill" or cmd == "/skills":
                    from skills import discover_skills
                    skills = discover_skills()
                    if not skills:
                        console.print(
                            "[dim]No skills found. Add skills to .termina/skills/ or ~/.termina/skills/\n"
                            "Create one with: termina skill new <name>[/dim]"
                        )
                    else:
                        console.print("[bold cyan]Available Skills:[/bold cyan]")
                        for s in skills:
                            console.print(f"  [green]{s['name']}[/green] - {s['description']}")
                        console.print("\n[dim]Activate with: /skill <name>[/dim]")
                elif cmd.startswith("/skill "):
                    skill_name = cmd[7:].strip()
                    from skills import discover_skills, load_skill
                    skills = discover_skills()
                    content = load_skill(skill_name, skills)
                    if content:
                        console.print(f"[dim]◆ Activating skill: {skill_name}[/dim]")
                        agent.chat(
                            f"[SKILL ACTIVATED: {skill_name}]\n\n"
                            f"Follow the instructions in this skill exactly:\n\n{content}"
                        )
                    else:
                        console.print(
                            f"[red]Skill '{skill_name}' not found.[/red] "
                            f"Run /skills to see available skills."
                        )
                else:
                    console.print(f"[red]Unknown command: {cmd}[/red]. Type /help for options.")
                continue
                
            agent.chat(user_input)
            
            # Save session immediately after every turn so progress isn't lost on crash
            from session import save_session
            agent.session_id = save_session(agent.messages, agent.session_id)
            
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
            
    # Save session on exit
    from session import save_session
    sid = save_session(agent.messages, agent.session_id)
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

@config_app.command("set-local")
def config_set_local(
    provider: str = typer.Argument(..., help="Local provider: ollama, lmstudio, custom"),
    api_base: str = typer.Argument(None, help="Optional custom URL (e.g. http://localhost:8080/v1)")
):
    """Enable a local model provider."""
    from config import set_local_provider
    valid = ["ollama", "lmstudio", "custom"]
    if provider not in valid:
        console.print(f"[red]Unknown local provider '{provider}'. Choose: {', '.join(valid)}[/red]")
        raise typer.Exit(1)
    if provider == "custom" and not api_base:
        console.print("[red]Custom provider requires a URL. Example: termina config set-local custom http://localhost:8080/v1[/red]")
        raise typer.Exit(1)
    set_local_provider(provider, api_base)
    console.print(f"[bold green]+ Local provider '{provider}' enabled.[/bold green]")
    console.print(f"  Switch to it: termina config set-model {provider} <model-name>")

@config_app.command("list-models")
def config_list_models():
    """Show all available model presets by provider."""
    from config import MODEL_PRESETS
    for provider, models in MODEL_PRESETS.items():
        console.print(f"\n[bold cyan]{provider}[/bold cyan]")
        for model_name, description in models:
            console.print(f"  [green]{model_name}[/green]")
            if description:
                console.print(f"    [dim]{description}[/dim]")
    console.print("\n[dim]Usage: termina config set-model <provider> <model>[/dim]")

@config_app.command("show")
def config_show():
    """
    Show current configuration.
    """
    provider, model = get_default_model()
    console.print(f"Current Provider: [bold yellow]{provider}[/bold yellow]")
    console.print(f"Current Model: [bold cyan]{model}[/bold cyan]")

@app.command("sessions")
def sessions_cmd(
    clear: bool = typer.Option(False, "--clear", help="Delete all saved sessions")
):
    """Manage saved chat sessions."""
    from session import list_sessions, SESSION_DIR
    import shutil

    if clear:
        confirm = typer.confirm("Delete ALL saved sessions? This cannot be undone.")
        if confirm:
            shutil.rmtree(SESSION_DIR, ignore_errors=True)
            console.print("[bold green]+ All sessions deleted.[/bold green]")
        return

    sessions = list_sessions()
    if not sessions:
        console.print("[dim]No saved sessions.[/dim]")
        return
    console.print(f"[bold cyan]{len(sessions)} saved session(s):[/bold cyan]")
    for s in sessions:
        console.print(f"  [green]{s}[/green]")
    console.print("\n[dim]Resume: termina resume <session_id>[/dim]")
    console.print("[dim]Clear all: termina sessions --clear[/dim]")

skill_app = typer.Typer(help="Manage Termina skills")
app.add_typer(skill_app, name="skill")

@skill_app.command("new")
def skill_new(
    name: str = typer.Argument(..., help="Skill name (use-hyphens-not-spaces)"),
    description: str = typer.Option("", "-d", "--description"),
    global_skill: bool = typer.Option(False, "-g", "--global",
                                       help="Install to ~/.termina/skills instead of project")
):
    """Create a new skill scaffold."""
    from skills import create_skill
    path = create_skill(name, description, project_local=not global_skill)
    console.print(f"[bold green]+ Created skill at {path}[/bold green]")
    console.print(f"[dim]Edit the SKILL.md to define what the skill does.[/dim]")

@skill_app.command("list")
def skill_list():
    """List all available skills."""
    from skills import discover_skills
    skills = discover_skills()
    if not skills:
        console.print("[dim]No skills found.[/dim]")
        return
    for s in skills:
        loc = "(project)" if ".termina/skills" in s["path"] else "(global)"
        console.print(f"  [green]{s['name']}[/green] [dim]{loc}[/dim]")
        console.print(f"    {s['description']}")

@skill_app.command("install")
def skill_install(
    source: str = typer.Argument(..., help="GitHub repo path, e.g. owner/repo")
):
    """
    Install skills from a GitHub repository into ~/.termina/skills/.
    The repo must contain SKILL.md files in subdirectories.
    """
    console.print(f"[dim]Cloning skills from {source}...[/dim]")
    import subprocess
    from pathlib import Path
    target = Path.home() / ".termina" / "skills" / source.replace("/", "_")
    result = subprocess.run(
        ["git", "clone", f"https://github.com/{source}", str(target)],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        console.print(f"[bold green]+ Skills installed at {target}[/bold green]")
        console.print("[dim]Restart Termina to load the new skills.[/dim]")
    else:
        console.print(f"[red]Install failed:[/red] {result.stderr}")

@app.command()
def init():
    """
    Initialize Termina in the current project by creating a TERMINA.md file.
    """
    from pathlib import Path
    target = Path(".termina") / "TERMINA.md"
    target.parent.mkdir(exist_ok=True)

    if target.exists():
        console.print(f"[yellow]TERMINA.md already exists at {target}[/yellow]")
        return

    template = """\
# TERMINA.md — Project Rules for Termina

## Tech Stack
<!-- e.g. Python 3.12, FastAPI, PostgreSQL, React 18 -->

## Project Structure
<!-- Brief description of key directories -->

## Coding Conventions
<!-- Naming conventions, style guide, patterns to follow -->

## Off-Limits
<!-- Files or directories Termina should never modify -->
<!-- e.g. - NEVER touch migrations/ without explicit instruction -->

## Test Command
<!-- How to run tests in this project -->
<!-- e.g. pytest tests/ -v -->

## Build Command
<!-- How to build/run the project -->
<!-- e.g. uvicorn main:app --reload -->

## Notes for Termina
<!-- Any other context that helps the AI work better in this codebase -->
"""
    target.write_text(template, encoding="utf-8")
    console.print(f"[bold green]✓ Created {target}[/bold green]")
    console.print("[dim]Edit this file to teach Termina about your project.[/dim]")

if __name__ == "__main__":
    app()
