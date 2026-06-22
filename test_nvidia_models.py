import os
import json
import requests
from pathlib import Path

# Load user's nvidia api key
config_file = Path.home() / ".nemi" / "config.json"
with open(config_file) as f:
    config = json.load(f)

api_key = config.get("api_keys", {}).get("nvidia")
if not api_key:
    print("No nvidia API key found in config.json")
    exit(1)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

url = "https://integrate.api.nvidia.com/v1/chat/completions"

models_to_test = [
    "nvidia/nemotron-4-340b-instruct",
    "meta/llama-3.1-70b-instruct",
    "meta/llama-3.1-405b-instruct"
]

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"]
            }
        }
    }
]

for model in models_to_test:
    print(f"\nTesting model: {model}")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hello"}],
        "tools": tools,
        "max_tokens": 50
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
    else:
        print("Success!")
