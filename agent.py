import json
from litellm import completion
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# Import our local tools and config
from tools.filesystem import list_directory, read_file, write_file
from tools.terminal import run_command
from config import get_api_key, get_default_model

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
    }
]

# Map function names to actual python functions
AVAILABLE_FUNCTIONS = {
    "list_directory": list_directory,
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command
}

class Agent:
    def __init__(self):
        self.messages = [
            {"role": "system", "content": "You are Termina, a powerful AI coding assistant. You run in the user's terminal and have tools to interact with their file system and execute commands. Help the user with their coding tasks."}
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
            function_args = json.loads(tool_call.function.arguments)
            console.print(f"[dim yellow]Agent is calling tool:[/dim yellow] [bold cyan]{function_name}[/bold cyan] with args: {function_args}")
            
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

        # litellm requires the model string to have the provider prefix in some cases.
        # For Nvidia, we can use the openai compatible endpoint
        kwargs = {
            "messages": self.messages,
            "api_key": api_key,
            "tools": TOOLS_SCHEMA,
            "tool_choice": "auto"
        }
        
        if provider.lower() == "nvidia":
            kwargs["model"] = f"openai/{model}"
            kwargs["api_base"] = "https://integrate.api.nvidia.com/v1"
        else:
            kwargs["model"] = model
        
        while True:
            try:
                # Call litellm completion
                response = completion(**kwargs)
            except Exception as e:
                console.print(f"[bold red]API Error:[/bold red] {e}")
                break

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            # Append the assistant's message to conversation history
            # convert the litellm message object to dict
            msg_dict = {"role": "assistant"}
            if response_message.content:
                msg_dict["content"] = response_message.content
            if tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in tool_calls
                ]
            
            self.messages.append(msg_dict)

            # Check if the model wants to call a function
            if tool_calls:
                # Execute all tool calls
                for tool_call in tool_calls:
                    result = self._execute_tool_call(tool_call)
                    
                    # Append tool response to messages
                    self.messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_call.function.name,
                        "content": result
                    })
                # Loop continues, sending the tool results back to the model
            else:
                # No tool calls, just normal text response
                if response_message.content:
                    console.print(Panel(Markdown(response_message.content), title="Termina Assistant", border_style="green"))
                break
