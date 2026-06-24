# Installation

Termina can be installed globally on your system, allowing you to invoke it from anywhere using the `termina` command.

## Prerequisites

- Python 3.10+

## Installation Steps

1. Clone or download this repository
2. Navigate to the project directory
3. Install Termina globally using pip:

```bash
pip install -e .
```

The `-e` flag installs the package in "editable" mode, meaning changes you make to the source code will be reflected without reinstalling.

## Verification

After installation, verify that Termina is correctly installed by running:

```bash
termina --help
```

You should see the help output showing available commands and options.

## Post-Installation Setup

Before using Termina, you need to configure your API keys for the providers you wish to use. See the [Configuration](#configuration) section for details.