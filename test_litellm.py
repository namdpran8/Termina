import os
from litellm import completion

# test 1: prefix nvidia_nim/
try:
    print("Testing nvidia_nim/nemotron-4-340b-instruct")
    completion(model="nvidia_nim/nvidia/nemotron-4-340b-instruct", messages=[{"role": "user", "content": "hi"}], api_key="dummy")
    print("Success test 1")
except Exception as e:
    print(f"Test 1 failed: {e}")

try:
    print("Testing custom openai base")
    completion(model="openai/nvidia/nemotron-4-340b-instruct", api_base="https://integrate.api.nvidia.com/v1", messages=[{"role": "user", "content": "hi"}], api_key="dummy")
    print("Success test 2")
except Exception as e:
    print(f"Test 2 failed: {e}")

