import json
import time
import uuid
from litellm import completion
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live

# Import our local tools and config
from tools.filesystem import list_directory, read_file, write_file, edit_file
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
    "git_log": git_log
}

class Agent:
    def __init__(self, context=None):
        if context is None:
            context = {"cwd": ".", "project_type": "Unknown", "readme_summary": "", "custom_rules": ""}
            
        system_prompt = f"""You are Termina, a powerful AI coding assistant that runs in the user's terminal.

## CONVERSATION RULES
- For greetings, questions, explanations, and general discussion: respond naturally in conversation. Do NOT use tools for these.
- Only use tools when the user explicitly asks you to read/write files, run commands, search code, or perform actions on their system.
- When explaining code, use markdown formatting.
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

    def chat(self, user_input: str) -> None:
        """
        Main chat loop for a single turn. It handles tool calls recursively until the model gives a final text response.
        """
        self.messages.append({"role": "user", "content": user_input})
        
        provider, model = get_default_model()
        api_key = get_api_key(provider)
        
        if not api_key:
            console.print(f"[bold red]Error:[/bold red] API key for '{provider}' not found. Please set it using 'termina config set-key {provider} <YOUR_KEY>'.")
            self.messages.pop() # Remove the user input so they can retry
            return

        kwargs = {
            "messages": self.messages,
            "api_key": api_key,
            "tools": TOOLS_SCHEMA,
            "tool_choice": "auto",
            "stream": True,
            "stream_options": {"include_usage": True}
        }
        
        if provider.lower() == "nvidia":
            kwargs["model"] = f"openai/{model}"
            kwargs["api_base"] = "https://integrate.api.nvidia.com/v1"
        else:
            kwargs["model"] = model
        
        while True:
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

            # Check if the model wants to call a function
            if tool_calls:
                # Execute all tool calls
                for tc in tool_calls:
                    # Create a mock object to match litellm's expected interface inside our execute logic
                    class MockFunction:
                        def __init__(self, name, arguments):
                            self.name = name
                            self.arguments = arguments
                    class MockToolCall:
                        def __init__(self, id, function):
                            self.id = id
                            self.function = function
                            
                    mock_tc = MockToolCall(tc["id"], MockFunction(tc["function"]["name"], tc["function"]["arguments"]))
                    
                    result = self._execute_tool_call(mock_tc)
                    
                    # Append tool response to messages
                    self.messages.append({
                        "tool_call_id": tc["id"],
                        "role": "tool",
                        "name": tc["function"]["name"],
                        "content": result
                    })
                # Loop continues, sending the tool results back to the model
                console.print("") # Empty line for padding
            else:
                # No tool calls, just normal text response
                console.print("") # padding
                break
