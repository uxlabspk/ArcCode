#!/usr/bin/env python3
"""
Arc Code CLI - An interactive agentic coding assistant with llama.cpp backend.
Inspired by Mistral Vibe CLI.
"""

import argparse
import sys
import os
import readline  # Enable readline for history and arrow keys

from arc_code.core import ArcCodeCore


def setup_readline():
    """Setup readline for better REPL experience"""
    # Try to load history file
    history_file = os.path.expanduser("~/.arc_code_history")

    try:
        readline.read_history_file(history_file)
    except FileNotFoundError:
        pass

    readline.set_history_length(1000)

    # Save history on exit
    import atexit
    atexit.register(readline.write_history_file, history_file)


def main():
    parser = argparse.ArgumentParser(
        description="Arc Code - Agentic Coding Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  arc-code                      Start interactive mode
  arc-code "read_file main.py"  Read a file
  arc-code "list_files src"     List files in directory
  arc-code --model codellama    Use a different model
  arc-code --verbose            Enable verbose output
        """
    )

    parser.add_argument(
        "--model",
        type=str,
        default="llama.cpp",
        help="Model backend to use (default: llama.cpp)"
    )
    parser.add_argument(
        "--server-url",
        type=str,
        default="http://localhost:8080",
        help="llama-server base URL (default: http://localhost:8080)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output with detailed tool call info"
    )
    parser.add_argument(
        "command",
        nargs="?",
        help="Command to execute (optional, starts interactive mode if omitted)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode - skip banner in interactive mode"
    )

    args = parser.parse_args()

    # Setup readline for history support
    setup_readline()

    # Initialize ArcCode core
    arc_code = ArcCodeCore(
        model=args.model,
        verbose=args.verbose,
        server_url=args.server_url
    )

    # Run with the provided command or start interactive mode
    arc_code.run(args.command)


if __name__ == "__main__":
    main()
