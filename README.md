# Arc Code CLI

A Mistral Vibe-like CLI tool with llama.cpp backend.

## Features

- AI-powered command-line assistant
- Basic tool integration (echo, list_files, read_file)
- Interactive mode with REPL
- Extensible architecture for adding more tools

## Installation

```bash
pip install -e .
```

## Usage

### Single command mode:

```bash
arc-code "echo Hello World"
arc-code "list_files /path/to/directory"
arc-code "read_file filename.txt"
```

### Interactive mode:

```bash
arc-code
>>> echo Hello
>>> list_files .
>>> read_file README.md
>>> exit
```

### Options:

- `--model`: Specify the model name exposed by llama-server (default: llama.cpp)
- `--server-url`: llama-server base URL (default: http://localhost:8080)
- `--verbose`: Enable verbose output

## Available Commands

- `echo <message>`: Echo a message
- `list_files <path>`: List files in a directory
- `read_file <file>`: Read content of a file

## Development

To contribute, clone the repository and install in development mode:

```bash
git clone <repository-url>
cd ArcCode
pip install -e .
```

## Adding New Tools

To add new tools, modify the `register_default_tools` method in `src/arc_code/core.py` and add your tool methods.
