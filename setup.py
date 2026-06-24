from setuptools import setup, find_packages

setup(
    name="termina",
    version="0.1.0",
    description="A powerful terminal-based AI coding assistant with BYOK support",
    author="Pranshu Namdeo",
    author_email="namdeopranshu8@gmail.com",
    url="https://github.com/namdpran8/Termina",
    packages=find_packages(),
    py_modules=[
        "cli", "agent", "config", "session", "startup", 
        "permissions", "cost_tracker", "change_tracker", "skills"
    ],
    install_requires=[
        "typer",
        "rich",
        "litellm>=1.41.27",
        "prompt_toolkit",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "termina=cli:app",
        ],
    },
    python_requires=">=3.10",
)
