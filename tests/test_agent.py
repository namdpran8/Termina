import json
import pytest
from unittest.mock import patch, MagicMock

from agent import Agent

@patch("agent.get_api_key")
@patch("agent.get_default_model")
@patch("agent.completion")
def test_agent_chat_basic_text_response(mock_completion, mock_get_model, mock_get_key):
    """Test that the agent handles a simple text response without tool calls."""
    mock_get_key.return_value = "fake_key"
    mock_get_model.return_value = ("nvidia", "nvidia/nemotron-4-340b-instruct")
    
    # Mock Litellm completion response as an iterable for streaming
    mock_chunk = MagicMock()
    mock_chunk.choices[0].delta.content = "Hello, I am Termina."
    mock_chunk.choices[0].delta.tool_calls = None
    mock_chunk.usage = MagicMock()
    mock_chunk.usage.prompt_tokens = 10
    mock_chunk.usage.completion_tokens = 5
    
    # We return an iterator yielding this chunk
    mock_completion.return_value = [mock_chunk]
    
    agent = Agent()
    agent.chat("Say hello")
    
    # Check that messages list grew (system + user + assistant)
    assert len(agent.messages) == 3
    assert agent.messages[-1]["role"] == "assistant"
    assert agent.messages[-1]["content"] == "Hello, I am Termina."

def test_agent_execute_tool_call():
    """Test that the agent correctly parses and executes a local tool."""
    agent = Agent()
    
    # Mock a tool call object from litellm
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "list_directory"
    mock_tool_call.function.arguments = json.dumps({"path": "."})
    
    # Instead of actually listing directory, we patch the function in AVAILABLE_FUNCTIONS
    with patch.dict("agent.AVAILABLE_FUNCTIONS", {"list_directory": lambda path: "mocked directory content"}):
        result = agent._execute_tool_call(mock_tool_call)
        assert result == "mocked directory content"

def test_agent_execute_tool_call_invalid_tool():
    """Test that the agent returns an error when calling a non-existent tool."""
    agent = Agent()
    
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "made_up_tool"
    mock_tool_call.function.arguments = "{}"
    
    result = agent._execute_tool_call(mock_tool_call)
    assert "Error:" in result
    assert "not found" in result
