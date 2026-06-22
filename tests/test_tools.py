import os
import pytest
from pathlib import Path
from tools.filesystem import list_directory, read_file, write_file
from tools.terminal import run_command

def test_list_directory(tmp_path):
    """Test listing directory contents."""
    # Create some dummy files in the temp directory
    (tmp_path / "test1.txt").touch()
    (tmp_path / "testdir").mkdir()
    
    result = list_directory(str(tmp_path))
    assert "[FILE] test1.txt" in result
    assert "[DIR] testdir" in result

def test_list_directory_not_exist():
    """Test listing a directory that doesn't exist."""
    result = list_directory("/path/does/not/exist/123456789")
    assert "Error:" in result

def test_read_file(tmp_path):
    """Test reading a file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello Termina!")
    
    content = read_file(str(test_file))
    assert content == "Hello Termina!"

def test_read_file_not_exist():
    """Test reading a file that doesn't exist."""
    result = read_file("/path/does/not/exist.txt")
    assert "Error:" in result

def test_write_file(tmp_path):
    """Test writing to a file."""
    test_file = tmp_path / "output.txt"
    result = write_file(str(test_file), "Test Content")
    
    assert "Successfully" in result
    assert test_file.exists()
    assert test_file.read_text() == "Test Content"

def test_run_command_success():
    """Test running a successful command."""
    # echo command works on both Windows and Linux, but let's test a simple python command to be safe
    result = run_command("python -c \"print('hello')\"")
    assert "STDOUT:" in result
    assert "hello" in result

def test_run_command_failure():
    """Test running a command that returns an error."""
    result = run_command("python -c \"import sys; sys.stderr.write('error msg'); exit(1)\"")
    assert "STDERR:" in result
    assert "error msg" in result
