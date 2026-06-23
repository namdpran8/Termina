from permissions import require_approval
import subprocess

def run_command(command: str) -> str:
    """
    Executes a shell command and returns its output.
    
    Args:
        command (str): The shell command to execute.
        
    Returns:
        str: The standard output and standard error of the command, or an error message.
    """
    # Check for destructive commands roughly
    is_destructive = any(cmd in command for cmd in ['rm ', 'del ', 'format ', 'mkfs', '>'])
    if not require_approval(command, "Executing shell command", is_destructive=is_destructive):
        return f"Error: User denied permission to execute command '{command}'."
        
    try:
        # Run the command and capture output
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False # Do not raise exception on non-zero exit code
        )
        
        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
            
        if not output:
            output = f"Command executed successfully with no output. Exit code: {result.returncode}"
            
        return output
    except Exception as e:
        return f"Error executing command: {e}"
