from setuptools import setup, find_packages

setup(
    name="termina",
    version="0.1.0",
    description="An AI Coding Assistant (Claude Code Alternative)",
    author="Your Name",
    py_modules=["cli", "agent", "config"],
    packages=find_packages(),
    install_requires=[
        "typer",
        "rich",
        "litellm",
        "prompt_toolkit",
        "python-dotenv"
    ],
    entry_points={
        "console_scripts": [
            "termina=cli:app",
        ],
    },
)
