import subprocess

def run_command(command: str) -> str:
    """
    Executes a shell command and returns its output.
    
    Args:
        command (str): The shell command to execute.
        
    Returns:
        str: The standard output and standard error of the command, or an error message.
    """
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
