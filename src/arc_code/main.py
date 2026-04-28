#!/usr/bin/env python3
"""
Arc Code CLI - A Mistral Vibe-like CLI tool with llama.cpp backend.
"""

import argparse
import sys
from arc_code.core import ArcCodeCore

def main():
    parser = argparse.ArgumentParser(description="Arc Code CLI - AI-powered command-line assistant")
    parser.add_argument("--model", type=str, default="llama.cpp", help="Model backend to use")
    parser.add_argument("--server-url", type=str, default="http://localhost:8080", help="llama-server URL")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("command", nargs="?", help="Command to execute")
    
    args = parser.parse_args()
    
    # Initialize ArcCode core
    arc_code = ArcCodeCore(model=args.model, verbose=args.verbose, server_url=args.server_url)
    
    # Run with the provided command or start interactive mode
    arc_code.run(args.command)

if __name__ == "__main__":
    main()