import json
import time
import uuid
from dataclasses import dataclass

@dataclass
class _ToolFunction:
    name: str
    arguments: str

@dataclass
class _ToolCall:
    id: str
    function: _ToolFunction
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live

# Import our local tools and config
from tools.filesystem import list_directory, read_file, write_file, edit_file, read_files, glob_files
from tools.search import grep_search
from tools.terminal import run_command
from tools.git import git_status, git_diff, git_commit, git_log
from config import get_api_key, get_default_model
from cost_tracker import tracker

console = Console()

# Define the tools available to the LLM in OpenAI schema format
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Lists the contents of a directory to see files and folders.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the directory to list. Defaults to '.'"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads the content of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the file to read."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Writes content to a file, creating it if it doesn't exist. Overwrites existing content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the file to write."
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file."
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replaces a specific block of text within a file. Prefer this over write_file for surgical edits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the file to edit."
                    },
                    "target_content": {
                        "type": "string",
                        "description": "The exact block of text to replace. Must match perfectly."
                    },
                    "replacement_content": {
                        "type": "string",
                        "description": "The new content that will replace target_content."
                    }
                },
                "required": ["path", "target_content", "replacement_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "grep_search",
            "description": "Search for patterns across files recursively.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The regex pattern to search for."
                    },
                    "path": {
                        "type": "string",
                        "description": "The root path to search in. Defaults to '.'"
                    },
                    "include": {
                        "type": "string",
                        "description": "Glob pattern to filter files (e.g. '*.py')."
                    },
                    "case_insensitive": {
                        "type": "boolean",
                        "description": "Whether the search should ignore case."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Executes a shell command and returns its output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "Shows the current git status.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": "Shows the git diff of unstaged changes.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_commit",
            "description": "Stages all changes and commits them with the provided message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The commit message."
                    }
                },
                "required": ["message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_log",
            "description": "Shows the recent git log.",
            "parameters": {
                "type": "object",
                "properties": {
                    "n": {
                        "type": "integer",
                        "description": "Number of commits to show."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_files",
            "description": "Reads multiple files in one call. Useful for loading several related files into context at once.",
            "parameters": {
                "type": "object",
                "properties": {
                    "paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths to read"
                    }
                },
                "required": ["paths"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "glob_files",
            "description": "Find files matching a glob pattern (e.g. '**/*.py', 'src/*.ts'). Returns a newline-separated list of matching file paths.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "The glob pattern to search for."
                    },
                    "path": {
                        "type": "string",
                        "description": "The root path to search in. Defaults to '.'"
                    }
                },
                "required": ["pattern"]
            }
        }
    }
]

# Map function names to actual python functions
AVAILABLE_FUNCTIONS = {
    "list_directory": list_directory,
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "grep_search": grep_search,
    "run_command": run_command,
    "git_status": git_status,
    "git_diff": git_diff,
    "git_commit": git_commit,
    "git_log": git_log,
    "read_files": read_files,
    "glob_files": glob_files
}

class Agent:
    def __init__(self, context=None):
        if context is None:
            context = {"cwd": ".", "project_type": "Unknown", "readme_summary": "", "custom_rules": ""}
            
        # Cache provider + key at init — re-read only when user calls /model
        from config import get_default_model, get_api_key
        self._provider, self._model = get_default_model()
        self._api_key = get_api_key(self._provider)
        self.session_id = None
            
        system_prompt = f"""You are Termina, a powerful AI coding assistant that runs in the user's terminal.

## CONVERSATION RULES
- If the user asks you to write code or create a file, ALWAYS use the `write_file` or `edit_file` tools. Do NOT dump large blocks of code in the chat.
- For greetings, questions, explanations, and general discussion: respond naturally in conversation.
- If a request is ambiguous, ASK the user to clarify before taking action.

## SAFETY
- NEVER run destructive commands (rm -rf, format, etc.) without explicit user confirmation.
- Always prefer editing over overwriting entire files.
- Show the user what you're about to do before doing it.

## CONTEXT
Working directory: {context.get('cwd', '.')}
Project type: {context.get('project_type', 'Unknown')}
"""
        if context.get('readme_summary'):
            system_prompt += f"\n## README SUMMARY\n{context['readme_summary']}\n"
            
        if context.get('custom_rules'):
            system_prompt += f"\n## CUSTOM RULES\n{context['custom_rules']}\n"

        from skills import discover_skills, build_skills_index
        self._skills = discover_skills()
        skills_block = build_skills_index(self._skills)
        if skills_block:
            system_prompt += skills_block

        self.messages = [
            {"role": "system", "content": system_prompt}
        ]

    def _execute_tool_call(self, tool_call) -> str:
        """
        Executes a single tool call requested by the LLM and returns the result.
        """
        function_name = tool_call.function.name
        function_to_call = AVAILABLE_FUNCTIONS.get(function_name)
        
        if not function_to_call:
            return f"Error: Tool '{function_name}' not found."
            
        try:
            # Fallback for empty arguments that might come from streaming parse errors
            args_str = tool_call.function.arguments
            function_args = json.loads(args_str) if args_str else {}
            
            # Print similar to Antigravity CLI
            if function_name == "write_file":
                console.print(f"[bold green]● Create[/bold green]({function_args.get('path')})")
            elif function_name == "run_command":
                console.print(f"[bold green]● Bash[/bold green]({function_args.get('command')})")
            elif function_name == "read_file":
                console.print(f"[bold green]● Read[/bold green]({function_args.get('path')})")
            elif function_name == "edit_file":
                console.print(f"[bold green]● Edit[/bold green]({function_args.get('path')})")
            elif function_name.startswith("git_"):
                console.print(f"[bold magenta]● Git[/bold magenta]({function_name.replace('git_', '')})")
            else:
                console.print(f"[bold green]● {function_name}[/bold green]({function_args})")
            
            # Call the python function
            function_response = function_to_call(**function_args)
            return str(function_response)
        except Exception as e:
            return f"Error executing tool '{function_name}': {str(e)}"

    def reload_model_config(self) -> None:
        from config import get_default_model, get_api_key
        self._provider, self._model = get_default_model()
        self._api_key = get_api_key(self._provider)

    def _warn_if_tool_limited(self, model: str) -> None:
        """Warn if the chosen local model may not support tool calling."""
        LOCAL_TOOL_CAPABLE_MODELS = [
            "llama3.2", "llama3.1", "qwen2.5", "qwen2.5-coder",
            "mistral", "deepseek-coder-v2", "mistral-nemo"
        ]
        if not any(m in model.lower() for m in LOCAL_TOOL_CAPABLE_MODELS):
            console.print(
                f"[yellow]⚠ '{model}' may have limited tool-calling support. "
                f"For best results use llama3.2, qwen2.5-coder, or mistral.[/yellow]"
            )

    def _build_completion_kwargs(self, provider: str, model: str, api_key: str) -> dict:
        """Build the litellm.completion() kwargs dict for any provider."""
        from config import get_local_provider_base

        base_kwargs = {
            "messages":              self.messages,
            "tools":                 TOOLS_SCHEMA,
            "tool_choice":           "auto",
            "parallel_tool_calls":   False,
            "stream":                True,
            "stream_options":        {"include_usage": True},
        }

        p = provider.lower()

        if p == "nvidia":
            return {
                **base_kwargs,
                "model":    f"nvidia_nim/{model}",
                "api_base": "https://integrate.api.nvidia.com/v1",
                "api_key":  api_key,
            }

        elif p == "ollama":
            self._warn_if_tool_limited(model)
            return {
                **base_kwargs,
                "model":    f"ollama_chat/{model}",
                "api_base": get_local_provider_base("ollama") or "http://localhost:11434",
                "api_key":  "ollama",  # litellm requires a non-empty key
            }

        elif p == "lmstudio":
            self._warn_if_tool_limited(model)
            return {
                **base_kwargs,
                "model":    f"openai/{model}",
                "api_base": get_local_provider_base("lmstudio") or "http://localhost:1234/v1",
                "api_key":  "lmstudio",
            }

        elif p == "custom":
            self._warn_if_tool_limited(model)
            api_base = get_local_provider_base("custom")
            if not api_base:
                console.print("[bold red]Error:[/bold red] Custom provider api_base not set. "
                              "Run: termina config set-local custom <URL>")
                return {}
            return {
                **base_kwargs,
                "model":    f"openai/{model}",
                "api_base": api_base,
                "api_key":  api_key or "custom",
            }
            
        elif p == "groq":
            return {
                **base_kwargs,
                "model":    f"groq/{model}",
                "api_key":  api_key,
            }
            
        elif p == "openrouter":
            return {
                **base_kwargs,
                "model":    f"openrouter/{model}",
                "api_key":  api_key,
            }

        else:
            # openai, anthropic, gemini — litellm handles natively
            return {
                **base_kwargs,
                "model":   model,
                "api_key": api_key,
            }

    def chat(self, user_input: str) -> None:
        """
        Main chat loop for a single turn. It handles tool calls recursively until the model gives a final text response.
        """
        # Lazy import litellm — do NOT move this to module level
        import litellm
        litellm.suppress_debug_info = True
        from litellm import completion
        
        self.messages.append({"role": "user", "content": user_input})
        
        provider = self._provider
        model    = self._model
        
        # Always fetch latest api key in case user ran 'termina config set-key' mid-session
        from config import get_api_key
        api_key = get_api_key(provider)
        self._api_key = api_key
        
        from cost_tracker import tracker
        tracker.set_model(model)
        
        if not api_key and provider.lower() not in ["ollama", "lmstudio"]:
            console.print(f"[bold red]Error:[/bold red] API key for '{provider}' not found. Please set it using 'termina config set-key {provider} <YOUR_KEY>'.")
            self.messages.pop() # Remove the user input so they can retry
            return

        kwargs = self._build_completion_kwargs(provider, model, api_key)
        if not kwargs:
            return  # provider config error, already printed
        
        MAX_TOOL_ITERATIONS = 15
        
        for iteration in range(MAX_TOOL_ITERATIONS):
            start_time = time.time()
            try:
                # Call litellm completion with streaming
                response = completion(**kwargs)
            except Exception as e:
                console.print(f"[bold red]API Error:[/bold red] {e}")
                break
                
            text_content = ""
            tool_calls_dict = {}
            
            with Live(console=console, refresh_per_second=15, vertical_overflow="visible") as live:
                for chunk in response:
                    # Update token usage if present
                    if hasattr(chunk, 'usage') and chunk.usage:
                        tracker.add_usage(chunk.usage.prompt_tokens, chunk.usage.completion_tokens)

                    if not chunk.choices:
                        continue
                        
                    delta = chunk.choices[0].delta
                    
                    if hasattr(delta, 'content') and delta.content:
                        text_content += delta.content
                        live.update(Markdown(text_content))
                        
                    if hasattr(delta, 'tool_calls') and delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_dict:
                                tool_calls_dict[idx] = {
                                    "id": tc.id,
                                    "type": "function",
                                    "function": {"name": getattr(tc.function, 'name', ''), "arguments": ""}
                                }
                            if tc.function and hasattr(tc.function, 'name') and tc.function.name:
                                tool_calls_dict[idx]["function"]["name"] = tc.function.name
                            if tc.function and hasattr(tc.function, 'arguments') and tc.function.arguments:
                                tool_calls_dict[idx]["function"]["arguments"] += tc.function.arguments

            duration = round(time.time() - start_time, 1)

            tool_calls = list(tool_calls_dict.values())
            
            # NVIDIA NIM API strict single tool-call limit workaround
            if len(tool_calls) > 1:
                console.print(f"\n[dim]Model attempted {len(tool_calls)} parallel tool calls. Forcing sequential execution to prevent API error.[/dim]")
                tool_calls = tool_calls[:1]
            
            # JSON Fallback: Check if model output a raw JSON tool call string instead of using native function calling
            if not tool_calls and text_content:
                clean_content = text_content.strip()
                if clean_content.startswith("```json"):
                    clean_content = clean_content[7:]
                if clean_content.endswith("```"):
                    clean_content = clean_content[:-3]
                clean_content = clean_content.strip()
                
                if clean_content.startswith("{") and '"name"' in clean_content and '"parameters"' in clean_content:
                    try:
                        parsed = json.loads(clean_content)
                        if "name" in parsed and "parameters" in parsed:
                            tc = {
                                "id": f"call_{uuid.uuid4().hex[:10]}",
                                "type": "function",
                                "function": {
                                    "name": parsed["name"],
                                    "arguments": json.dumps(parsed["parameters"])
                                }
                            }
                            tool_calls = [tc]
                            # We don't wipe text_content here because it was already rendered to the user.
                            # Just silently inject the tool call so execution continues.
                    except Exception:
                        pass
            
            # Append the assistant's message to conversation history
            msg_dict = {"role": "assistant"}
            if text_content:
                msg_dict["content"] = text_content
            if tool_calls:
                msg_dict["tool_calls"] = tool_calls
                
                console.print(f"\n[dim]▶ Thought for {duration}s[/dim]")
                console.print("[dim]Prioritizing Tool Usage[/dim]\n")
            
            self.messages.append(msg_dict)

            if tool_calls:
                from change_tracker import change_log
                change_log.begin_transaction()
                
                # Execute all tool calls
                for tc in tool_calls:
                    mock_tc = _ToolCall(tc["id"], _ToolFunction(tc["function"]["name"], tc["function"]["arguments"]))
                    
                    result = self._execute_tool_call(mock_tc)
                    
                    # Append tool response to messages
                    self.messages.append({
                        "tool_call_id": tc["id"],
                        "role": "tool",
                        "name": tc["function"]["name"],
                        "content": result
                    })
                
                change_log.commit_transaction()
                # Loop continues, sending the tool results back to the model
                console.print("") # Empty line for padding
            else:
                # No tool calls, just normal text response
                console.print("") # padding
                break
        else:
            # Loop exhausted without a final text response
            console.print(
                f"[bold yellow]⚠ Agent reached the {MAX_TOOL_ITERATIONS}-step limit "
                f"without a final response. The task may be incomplete.[/bold yellow]"
            )
