"""
Core functionality for Arc Code CLI - Enhanced Interactive Agentic Coding Assistant
"""

import os
import sys
import json
import re
import time
import shlex
import subprocess
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List
from pathlib import Path


class ArcCodeCore:
    """Main class for Arc Code CLI - Agentic Coding Assistant"""

    def __init__(self, model: str = "llama.cpp", verbose: bool = False, server_url: str = "http://localhost:8080"):
        self.model = model
        self.verbose = verbose
        self.server_url = server_url.rstrip("/")
        self.tools = {}
        self.slash_commands = {}
        self.history = []
        self.max_history = 100
        self.conversation_history = []
        self.max_context_messages = 20  # Limit context window
        self.session_started = False
        self.thinking_mode = False
        self.current_session = None

        # UI Configuration
        self._colors = {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "dim": "\033[2m",
            "italic": "\033[3m",
            "underline": "\033[4m",
            "orange": "\033[38;5;214m",
            "cyan": "\033[38;5;39m",
            "yellow": "\033[38;5;220m",
            "gray": "\033[38;5;245m",
            "dark_gray": "\033[38;5;240m",
            "green": "\033[38;5;46m",
            "red": "\033[38;5;196m",
            "magenta": "\033[38;5;201m",
            "blue": "\033[38;5;27m",
        }

        # Spinner for loading states
        self._spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

        self.register_default_tools()
        self.register_slash_commands()

    def _style(self, text: str, color: str, bold: bool = False, underline: bool = False) -> str:
        """Apply styling to text with support for multiple styles"""
        result = self._colors.get(color, '') + str(text) + self._colors['reset']
        if bold:
            result = self._colors['bold'] + result
        if underline:
            result = self._colors['underline'] + result
        return result

    def _print_banner(self):
        """Print enhanced ASCII art banner"""
        logo = [
            " .:::.    ",
            ":-=:.:.  ",
            ":..=-:.  ",
            " .:-=:.  ",
            "  ..:-.  ",
        ]

        title = (
            f"{self._style('Arc Code', 'orange', bold=True)} "
            f"{self._style('v0.2.0', 'gray')} · "
            f"{self._style('Agentic Coding Assistant', 'cyan')}"
        )
        meta = f"{self._style(f'Backend: {self.model} | Server: {self.server_url}', 'gray')}"
        info = f"Type {self._style('/help', 'cyan', bold=True)} for commands or {self._style('/menu', 'cyan', bold=True)} for interactive mode"

        print()
        print(f"{logo[0]} {title}")
        print(f"{logo[1]} {meta}")
        print(f"{logo[2]} {info}")
        print(f"{logo[3]}")
        print(f"{logo[4]}")
        print()

        # Show quick stats
        cwd = os.getcwd()
        print(f"  {self._style('📁', 'cyan')} {self._style('Working Dir:', 'gray')} {cwd}")
        print(f"  {self._style('⚡', 'cyan')} {self._style('Tools:', 'gray')} {len(self.tools)} registered")
        print(f"  {self._style('📝', 'cyan')} {self._style('History:', 'gray')} {len(self.history)} commands")
        print()

        home_dir = os.path.expanduser("~")
        if os.getcwd() == home_dir:
            warn = self._style("⚠ WARNING: You are in the home directory", "yellow", bold=True)
            warn_detail = self._style("  Running in this location is not recommended. Consider navigating to a project directory.", "yellow")
            print(f"  {warn}")
            print(f"  {warn_detail}")
            print()

    def _print_tool_call(self, tool_name: str, args: Dict[str, Any]):
        """Print a formatted tool call indicator"""
        print(f"\n  {self._style('🔧', 'cyan')} {self._style(f'Calling: {tool_name}', 'cyan', bold=True)}")
        if args and self.verbose:
            for key, val in args.items():
                print(f"     {self._style(f'{key}:', 'gray')} {self._style(str(val), 'yellow')}")

    def _print_tool_result(self, success: bool, preview: str = ""):
        """Print a formatted tool result indicator"""
        icon = "✓" if success else "✗"
        color = "green" if success else "red"
        status = "Success" if success else "Failed"
        print(f"  {self._style(icon, color)} {self._style(status, color)}")
        if preview and self.verbose:
            print(f"     {self._style(preview[:100], 'gray')}")
        print()

    def _spinner(self, message: str, duration: float = 0.1):
        """Show a simple spinner animation"""
        frame = self._spinner_frames[0]
        sys.stdout.write(f"\r  {self._style(frame, 'cyan')} {message}")
        sys.stdout.flush()
        time.sleep(duration)

    # ==========================================
    # Tool System
    # ==========================================

    def register_default_tools(self):
        """Register default tools for agentic coding"""
        self.tools = {
            # File Operations
            "read_file": {
                "fn": self.tool_read_file,
                "desc": "Read content of a file",
                "usage": "read_file <path>",
            },
            "write_file": {
                "fn": self.tool_write_file,
                "desc": "Write content to a file (creates or overwrites)",
                "usage": "write_file <path> <content>",
            },
            "edit_file": {
                "fn": self.tool_edit_file,
                "desc": "Edit a file by replacing old_text with new_text",
                "usage": "edit_file <path> <old_text> <new_text>",
            },
            "list_files": {
                "fn": self.tool_list_files,
                "desc": "List files in a directory",
                "usage": "list_files <path>",
            },
            "search_files": {
                "fn": self.tool_search_files,
                "desc": "Search for files by pattern",
                "usage": "search_files <pattern> [path]",
            },
            # Code Operations
            "run_command": {
                "fn": self.tool_run_command,
                "desc": "Execute a shell command",
                "usage": "run_command <command>",
            },
            "grep_search": {
                "fn": self.tool_grep_search,
                "desc": "Search for text pattern in files",
                "usage": "grep_search <pattern> [path]",
            },
            # Utility
            "echo": {
                "fn": self.tool_echo,
                "desc": "Echo a message",
                "usage": "echo <message>",
            },
            "get_env": {
                "fn": self.tool_get_env,
                "desc": "Get environment variable",
                "usage": "get_env <name>",
            },
        }

    def tool_echo(self, message: str = "") -> str:
        """Echo a message"""
        return f"Echo: {message}"

    def tool_list_files(self, path: str = ".") -> str:
        """List files in a directory with detailed info"""
        try:
            path = Path(path).expanduser().resolve()
            if not path.exists():
                return f"Error: Path '{path}' does not exist"
            if not path.is_dir():
                return f"Error: '{path}' is not a directory"

            items = sorted(path.iterdir())
            dirs = [i for i in items if i.is_dir()]
            files = [i for i in items if i.is_file()]

            result = [f"Directory: {path}"]
            if dirs:
                result.append(f"\n{self._style('Directories:', 'cyan', bold=True)}")
                for d in dirs:
                    result.append(f"  {self._style('📁', 'cyan')} {d.name}/")
            if files:
                result.append(f"\n{self._style('Files:', 'yellow')}")
                for f in files:
                    size = f.stat().st_size
                    size_str = self._format_size(size)
                    result.append(f"  {self._style('📄', 'gray')} {f.name} ({size_str})")

            result.append(f"\nTotal: {len(dirs)} dirs, {len(files)} files")
            return "\n".join(result)
        except Exception as e:
            return f"Error: {str(e)}"

    def tool_read_file(self, file_path: str, max_lines: int = 200) -> str:
        """Read content of a file with line numbers"""
        try:
            path = Path(file_path).expanduser().resolve()
            if not path.exists():
                return f"Error: File '{path}' does not exist"
            if not path.is_file():
                return f"Error: '{path}' is not a file"

            # Check file size
            size = path.stat().st_size
            if size > 1024 * 1024:  # 1MB limit
                return f"Error: File too large ({self._format_size(size)}). Maximum is 1MB."

            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            total_lines = len(lines)
            display_lines = lines[:max_lines]

            result = [f"{self._style(f'File: {path}', 'cyan', bold=True)} ({total_lines} lines, {self._format_size(size)})"]
            result.append(self._style('─' * 60, 'gray'))

            for i, line in enumerate(display_lines, 1):
                line_num = self._style(str(i).rjust(4), 'gray')
                result.append(f"{line_num} │ {line.rstrip()}")

            if total_lines > max_lines:
                result.append(f"\n{self._style(f'... ({total_lines - max_lines} more lines)', 'gray')}")

            return "\n".join(result)
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def tool_write_file(self, file_path: str, content: str = "") -> str:
        """Write content to a file"""
        try:
            path = Path(file_path).expanduser().resolve()

            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            # Check if file exists
            exists = path.exists()
            action = "Updated" if exists else "Created"

            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            size = self._format_size(len(content.encode('utf-8')))
            return f"{action} {self._style(str(path), 'green', bold=True)} ({size}, {content.count(chr(10)) + 1} lines)"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def tool_edit_file(self, file_path: str, old_text: str, new_text: str) -> str:
        """Edit a file by replacing old_text with new_text"""
        try:
            path = Path(file_path).expanduser().resolve()
            if not path.exists():
                return f"Error: File '{path}' does not exist"

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            if old_text not in content:
                return f"Error: Text not found in file"

            new_content = content.replace(old_text, new_text, 1)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return f"{self._style('✓', 'green')} {self._style('Updated', 'green', bold=True)} {path}"
        except Exception as e:
            return f"Error editing file: {str(e)}"

    def tool_search_files(self, pattern: str, path: str = ".") -> str:
        """Search for files by glob pattern"""
        try:
            search_path = Path(path).expanduser().resolve()
            matches = list(search_path.rglob(pattern))

            if not matches:
                return f"No files matching '{pattern}' in {search_path}"

            result = [f"{self._style(f'Found {len(matches)} files matching', 'green', bold=True)} '{pattern}' in {search_path}"]
            for m in matches[:50]:  # Limit to 50 results
                icon = "📁" if m.is_dir() else "📄"
                result.append(f"  {self._style(icon, 'gray')} {m}")

            if len(matches) > 50:
                result.append(f"\n{self._style(f'... and {len(matches) - 50} more', 'gray')}")

            return "\n".join(result)
        except Exception as e:
            return f"Error searching files: {str(e)}"

    def tool_grep_search(self, pattern: str, path: str = ".") -> str:
        """Search for text pattern in files"""
        try:
            search_path = Path(path).expanduser().resolve()
            results = []

            # Common code file extensions
            code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.json', '.yaml', '.yml', '.md', '.txt', '.sh', '.rs', '.go', '.java', '.c', '.cpp', '.h'}

            for file_path in search_path.rglob('*'):
                if file_path.is_file() and file_path.suffix in code_extensions:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                            for line_num, line in enumerate(f, 1):
                                if pattern.lower() in line.lower():
                                    results.append({
                                        'file': str(file_path),
                                        'line': line_num,
                                        'content': line.rstrip()
                                    })
                    except:
                        pass

            if not results:
                return f"No matches for '{pattern}' in {search_path}"

            result = [f"{self._style(f'Found {len(results)} matches', 'green', bold=True)} for '{pattern}'"]
            for r in results[:30]:  # Limit to 30 results
                result.append(f"  {self._style(r['file'], 'cyan')}:{self._style(str(r['line']), 'yellow')}")
                result.append(f"    {r['content'][:120]}")

            if len(results) > 30:
                result.append(f"\n{self._style(f'... and {len(results) - 30} more', 'gray')}")

            return "\n".join(result)
        except Exception as e:
            return f"Error searching: {str(e)}"

    def tool_run_command(self, command: str, timeout: int = 30) -> str:
        """Execute a shell command"""
        try:
            self._spinner(f"Running: {command}")

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd()
            )

            output = []
            output.append(f"{self._style('Command:', 'cyan', bold=True)} {command}")

            if result.stdout:
                output.append(f"\n{self._style('STDOUT:', 'green')}")
                output.append(result.stdout[:2000])

            if result.stderr:
                output.append(f"\n{self._style('STDERR:', 'red')}")
                output.append(result.stderr[:2000])

            output.append(f"\n{self._style(f'Exit Code: {result.returncode}', 'gray')}")
            return "\n".join(output)
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout}s"
        except Exception as e:
            return f"Error running command: {str(e)}"

    def tool_get_env(self, name: str) -> str:
        """Get environment variable"""
        value = os.environ.get(name)
        if value is None:
            return f"Environment variable '{name}' not set"
        return f"{self._style(name, 'cyan')} = {self._style(value, 'yellow')}"

    # ==========================================
    # Slash Commands
    # ==========================================

    def register_slash_commands(self):
        """Register slash commands for interactive mode"""
        self.slash_commands = {
            "help": {
                "fn": self.cmd_help,
                "desc": "Show this help message",
            },
            "tools": {
                "fn": self.cmd_tools,
                "desc": "List available tools",
            },
            "model": {
                "fn": self.cmd_model,
                "desc": "Show or change model settings",
                "usage": "/model [new_model_name]",
            },
            "server": {
                "fn": self.cmd_server,
                "desc": "Show or change server URL",
                "usage": "/server [new_url]",
            },
            "clear": {
                "fn": self.cmd_clear,
                "desc": "Clear conversation history",
            },
            "history": {
                "fn": self.cmd_history,
                "desc": "Show command history",
                "usage": "/history [count]",
            },
            "think": {
                "fn": self.cmd_think,
                "desc": "Toggle thinking mode (verbose LLM reasoning)",
            },
            "verbose": {
                "fn": self.cmd_verbose,
                "desc": "Toggle verbose output",
            },
            "save": {
                "fn": self.cmd_save,
                "desc": "Save conversation to file",
                "usage": "/save [filename]",
            },
            "load": {
                "fn": self.cmd_load,
                "desc": "Load conversation from file",
                "usage": "/load [filename]",
            },
            "context": {
                "fn": self.cmd_context,
                "desc": "Show context window info",
            },
            "menu": {
                "fn": self.cmd_menu,
                "desc": "Show interactive menu",
            },
            "exit": {
                "fn": self.cmd_exit,
                "desc": "Exit the REPL",
            },
            "quit": {
                "fn": self.cmd_exit,
                "desc": "Exit the REPL",
            },
        }

    def cmd_help(self, args: str = "") -> str:
        """Show help information"""
        help_text = []
        help_text.append(f"\n{self._style('╔══════════════════════════════════════════════════════════╗', 'cyan')}")
        help_text.append(f"{self._style('║', 'cyan')}          {self._style('Arc Code - Help & Commands', 'orange', bold=True)}              {self._style('║', 'cyan')}")
        help_text.append(f"{self._style('╚══════════════════════════════════════════════════════════╝', 'cyan')}\n")

        help_text.append(f"  {self._style('🔧 TOOLS', 'cyan', bold=True)}")
        help_text.append(f"  {self._style('─' * 50, 'gray')}")
        for name, info in sorted(self.tools.items()):
            help_text.append(f"    {self._style(name, 'green', bold=True):<20} {info['desc']}")

        help_text.append(f"\n  {self._style('⚡ SLASH COMMANDS', 'cyan', bold=True)}")
        help_text.append(f"  {self._style('─' * 50, 'gray')}")
        for name, info in sorted(self.slash_commands.items()):
            desc = info['desc']
            usage = info.get('usage', '')
            if usage:
                desc = f"{desc} {self._style(usage, 'gray')}"
            help_text.append(f"    {self._style('/' + name, 'magenta', bold=True):<20} {desc}")

        help_text.append(f"\n  {self._style('💡 TIPS', 'cyan', bold=True)}")
        help_text.append(f"  {self._style('─' * 50, 'gray')}")
        help_text.append(f"    • Use ↑↓ arrow keys to navigate history")
        help_text.append(f"    • Type naturally - the AI understands commands")
        help_text.append(f"    • Use /think for detailed reasoning")
        help_text.append(f"    • Use /menu for interactive tool selection")
        help_text.append("")

        return "\n".join(help_text)

    def cmd_tools(self, args: str = "") -> str:
        """List available tools"""
        output = [f"\n{self._style('🔧 Available Tools', 'cyan', bold=True)}"]
        output.append(f"  {self._style('─' * 50, 'gray')}")

        for name, info in sorted(self.tools.items()):
            output.append(f"\n  {self._style(name, 'green', bold=True)}")
            output.append(f"    {self._style(info['desc'], 'gray')}")
            output.append(f"    {self._style('Usage:', 'dim')} {info['usage']}")

        output.append(f"\n  {self._style(f'Total: {len(self.tools)} tools', 'cyan')}")
        output.append("")
        return "\n".join(output)

    def cmd_model(self, args: str = "") -> str:
        """Show or change model settings"""
        if args.strip():
            old_model = self.model
            self.model = args.strip()
            return f"{self._style('✓', 'green')} Model changed: {self._style(old_model, 'gray')} → {self._style(self.model, 'green', bold=True)}"
        return f"\n  {self._style('Model:', 'cyan')} {self._style(self.model, 'yellow', bold=True)}\n"

    def cmd_server(self, args: str = "") -> str:
        """Show or change server URL"""
        if args.strip():
            old_url = self.server_url
            self.server_url = args.strip().rstrip("/")
            return f"{self._style('✓', 'green')} Server changed: {self._style(old_url, 'gray')} → {self._style(self.server_url, 'green', bold=True)}"
        return f"\n  {self._style('Server:', 'cyan')} {self._style(self.server_url, 'yellow', bold=True)}\n"

    def cmd_clear(self, args: str = "") -> str:
        """Clear conversation history"""
        self.conversation_history = []
        return f"{self._style('✓', 'green')} Conversation history cleared"

    def cmd_history(self, args: str = "") -> str:
        """Show command history"""
        try:
            count = int(args.strip()) if args.strip() else 10
        except:
            count = 10

        output = [f"\n{self._style('📜 Command History', 'cyan', bold=True)}"]
        output.append(f"  {self._style('─' * 50, 'gray')}")

        recent = self.history[-count:]
        for i, cmd in enumerate(recent, len(self.history) - len(recent) + 1):
            output.append(f"  {self._style(str(i).rjust(3), 'gray')}  {cmd}")

        output.append(f"\n  {self._style(f'Total: {len(self.history)} commands', 'cyan')}")
        output.append("")
        return "\n".join(output)

    def cmd_think(self, args: str = "") -> str:
        """Toggle thinking mode"""
        self.thinking_mode = not self.thinking_mode
        status = "enabled" if self.thinking_mode else "disabled"
        color = "green" if self.thinking_mode else "yellow"
        return f"{self._style('💭', 'cyan')} Thinking mode {self._style(status, color, bold=True)}"

    def cmd_verbose(self, args: str = "") -> str:
        """Toggle verbose output"""
        self.verbose = not self.verbose
        status = "enabled" if self.verbose else "disabled"
        color = "green" if self.verbose else "yellow"
        return f"{self._style('📊', 'cyan')} Verbose output {self._style(status, color, bold=True)}"

    def cmd_save(self, args: str = "") -> str:
        """Save conversation to file"""
        filename = args.strip() if args.strip() else f"arc_session_{int(time.time())}.json"

        try:
            data = {
                "history": self.history,
                "conversation": self.conversation_history,
                "timestamp": time.time()
            }
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            return f"{self._style('✓', 'green')} Saved to {self._style(filename, 'green', bold=True)}"
        except Exception as e:
            return f"{self._style('✗', 'red')} Error: {str(e)}"

    def cmd_load(self, args: str = "") -> str:
        """Load conversation from file"""
        filename = args.strip()
        if not filename:
            return f"{self._style('✗', 'red')} Please specify a filename"

        try:
            with open(filename, 'r') as f:
                data = json.load(f)

            self.history = data.get("history", [])
            self.conversation_history = data.get("conversation", [])
            return f"{self._style('✓', 'green')} Loaded from {self._style(filename, 'green', bold=True)} ({len(self.history)} commands)"
        except Exception as e:
            return f"{self._style('✗', 'red')} Error: {str(e)}"

    def cmd_context(self, args: str = "") -> str:
        """Show context window info"""
        output = [f"\n{self._style('🧠 Context Window', 'cyan', bold=True)}"]
        output.append(f"  {self._style('─' * 50, 'gray')}")
        output.append(f"  {self._style('Messages:', 'gray')} {len(self.conversation_history)}/{self.max_context_messages}")
        output.append(f"  {self._style('Thinking Mode:', 'gray')} {'On' if self.thinking_mode else 'Off'}")
        output.append(f"  {self._style('Verbose:', 'gray')} {'On' if self.verbose else 'Off'}")

        if self.conversation_history:
            total_tokens = sum(len(msg.get("content", "")) // 4 for msg in self.conversation_history)
            output.append(f"  {self._style('Est. Tokens:', 'gray')} ~{total_tokens}")

        output.append("")
        return "\n".join(output)

    def cmd_menu(self, args: str = "") -> str:
        """Show interactive menu options"""
        menu = []
        menu.append(f"\n{self._style('╔══════════════════════════════════════════════════════════╗', 'magenta')}")
        menu.append(f"{self._style('║', 'magenta')}           {self._style('Interactive Menu', 'orange', bold=True)}                   {self._style('║', 'magenta')}")
        menu.append(f"{self._style('╚══════════════════════════════════════════════════════════╝', 'magenta')}\n")

        menu.append(f"  {self._style('File Operations', 'cyan', bold=True)}")
        menu.append(f"    {self._style('1.', 'yellow')} Read file          {self._style('2.', 'yellow')} Write file")
        menu.append(f"    {self._style('3.', 'yellow')} Edit file          {self._style('4.', 'yellow')} List files")
        menu.append(f"    {self._style('5.', 'yellow')} Search files       {self._style('6.', 'yellow')} Grep search")
        menu.append("")
        menu.append(f"  {self._style('Code & Commands', 'cyan', bold=True)}")
        menu.append(f"    {self._style('7.', 'yellow')} Run command        {self._style('8.', 'yellow')} Get env variable")
        menu.append("")
        menu.append(f"  {self._style('AI & Settings', 'cyan', bold=True)}")
        menu.append(f"    {self._style('9.', 'yellow')} Ask AI (normal)    {self._style('10.', 'yellow')} Ask AI (thinking)")
        menu.append(f"    {self._style('11.', 'yellow')} Change model       {self._style('12.', 'yellow')} Change server")
        menu.append(f"    {self._style('13.', 'yellow')} Save session       {self._style('14.', 'yellow')} Load session")
        menu.append("")
        menu.append(f"  {self._style('0.', 'red')} Exit")
        menu.append("")

        return "\n".join(menu)

    def cmd_exit(self, args: str = "") -> str:
        """Exit the REPL"""
        return "EXIT"

    # ==========================================
    # LLM Integration
    # ==========================================

    def _call_llama_server(self, messages: List[Dict[str, str]]) -> str:
        """Call the llama-server API with streaming support"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "stream": True,
            "max_tokens": 8192,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.server_url}/v1/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                # Handle streaming response
                full_content = []
                spin_idx = 0
                for line in resp:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        line = line[6:]
                    if line == "[DONE]":
                        break
                    try:
                        chunk = json.loads(line)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            full_content.append(content)
                            # Show live progress
                            spin = self._spinner_frames[spin_idx % len(self._spinner_frames)]
                            chars = sum(len(c) for c in full_content)
                            sys.stdout.write(f"\r  {self._style(spin, 'cyan')} Receiving... ({chars} chars)")
                            sys.stdout.flush()
                            spin_idx += 1
                    except json.JSONDecodeError:
                        continue
                sys.stdout.write("\r" + " " * 50 + "\r")  # Clear progress line
                return "".join(full_content)
        except urllib.error.HTTPError as e:
            return f"Error: llama-server HTTP {e.code}"
        except Exception as e:
            return f"Error: {str(e)}"

    def _run_agent(self, user_input: str) -> str:
        """Run the agentic reasoning loop"""
        # Build system prompt based on mode
        system_prompt = self._build_system_prompt()

        # Add to conversation history
        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # Add recent conversation context
        messages.extend(self.conversation_history[-self.max_context_messages:])
        messages.append({"role": "user", "content": user_input})

        # Show thinking indicator
        print(f"\n  {self._style('💭', 'cyan')} {self._style('Thinking...', 'gray')}", end="")
        sys.stdout.flush()

        for step in range(8):  # Max 8 steps for complex tasks
            response = self._call_llama_server(messages)

            # Clear thinking indicator
            print("\r" + " " * 40 + "\r", end="")

            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                # Non-JSON response - treat as final answer
                self.conversation_history.append({"role": "assistant", "content": response})
                return response

            if "final" in data:
                # Final answer
                final_msg = data["final"]
                self.conversation_history.append({"role": "assistant", "content": final_msg})
                return final_msg

            # Tool call
            tool_name = data.get("tool")
            tool_args = data.get("args", {})

            if tool_name:
                self._print_tool_call(tool_name, tool_args)

                if tool_name in self.tools:
                    try:
                        tool_result = self.tools[tool_name]["fn"](**tool_args)
                        self._print_tool_result(True, tool_result)
                    except Exception as e:
                        tool_result = f"Tool error: {str(e)}"
                        self._print_tool_result(False, tool_result)
                else:
                    tool_result = f"Unknown tool: {tool_name}"
                    self._print_tool_result(False)

                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"Tool result: {tool_result}"})
            else:
                # No tool call, treat as final
                self.conversation_history.append({"role": "assistant", "content": response})
                return response

        return f"{self._style('⚠️', 'yellow')} Reached maximum agent steps. Consider breaking down the task."

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM"""
        base_prompt = (
            "You are Arc Code, an expert AI coding assistant running in a CLI environment. "
            "You help users write, edit, debug, and understand code. "
            "You can use tools to interact with the file system and execute commands.\n\n"
        )

        if self.thinking_mode:
            base_prompt += (
                "THINKING MODE: Before taking actions, explain your reasoning step by step. "
                "Show your thought process clearly.\n\n"
            )

        tools_desc = "Available tools (use JSON format {\"tool\": \"name\", \"args\": {...}}):\n"
        for name, info in sorted(self.tools.items()):
            tools_desc += f"  - {name}: {info['desc']}\n"

        tools_desc += (
            "\nWhen you need a tool, reply with: {\"tool\": \"name\", \"args\": {...}}\n"
            "When done, reply with: {\"final\": \"your response\"}\n"
            "You can chain multiple tool calls before giving your final answer.\n\n"
            "IMPORTANT:\n"
            "- Always use absolute or relative paths correctly\n"
            "- When editing files, be precise with old_text matching\n"
            "- Provide clear, helpful responses with code formatting\n"
            "- If unsure, ask clarifying questions\n"
        )

        return base_prompt + tools_desc

    # ==========================================
    # Command Execution
    # ==========================================

    def execute_command(self, command: str) -> str:
        """Execute a command using available tools or the model"""
        if self.verbose:
            print(f"[ArcCode] Executing: {command}")

        # Save to history
        self.history.append(command)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        # Check for slash commands
        if command.startswith('/'):
            parts = command.split(maxsplit=1)
            cmd_name = parts[0][1:]  # Remove leading /
            cmd_args = parts[1] if len(parts) > 1 else ""

            if cmd_name in self.slash_commands:
                return self.slash_commands[cmd_name]["fn"](cmd_args)
            else:
                return f"{self._style('✗', 'red')} Unknown command: /{cmd_name}. Type /help for available commands."

        # Try to parse as direct tool call
        parts = command.split(maxsplit=1)
        tool_name = parts[0]
        tool_args_str = parts[1] if len(parts) > 1 else ""

        if tool_name in self.tools:
            # Direct tool execution
            tool_info = self.tools[tool_name]
            try:
                # Parse arguments based on tool
                args = self._parse_tool_args(tool_name, tool_args_str)
                result = tool_info["fn"](**args)
                return result
            except Exception as e:
                return f"{self._style('✗', 'red')} Error: {str(e)}"
        else:
            # Send to AI agent
            return self._run_agent(command)

    def _parse_tool_args(self, tool_name: str, args_str: str) -> Dict[str, Any]:
        """Parse arguments for a tool"""
        # Simple argument parsing
        if tool_name in ["read_file", "search_files", "grep_search", "get_env"]:
            # First arg is the main parameter
            parts = args_str.split(maxsplit=1)
            if tool_name == "search_files":
                return {"pattern": parts[0], "path": parts[1] if len(parts) > 1 else "."}
            elif tool_name == "grep_search":
                return {"pattern": parts[0], "path": parts[1] if len(parts) > 1 else "."}
            elif tool_name == "get_env":
                return {"name": args_str}
            else:
                return {"file_path" if tool_name == "read_file" else "path": parts[0]}
        elif tool_name == "list_files":
            return {"path": args_str.strip() if args_str.strip() else "."}
        elif tool_name == "echo":
            return {"message": args_str}
        elif tool_name == "run_command":
            return {"command": args_str}
        elif tool_name in ["write_file", "edit_file"]:
            # These need special handling - use AI for complex args
            return {"file_path": args_str}

        return {}

    # ==========================================
    # Interactive Menu Handler
    # ==========================================

    def _handle_menu_selection(self):
        """Handle interactive menu selection"""
        while True:
            menu_output = self.cmd_menu()
            print(menu_output)

            try:
                choice = input(f"  {self._style('Select option (0-14):', 'cyan', bold=True)} ")
            except (EOFError, KeyboardInterrupt):
                print()
                return

            if choice == "0":
                return "exit"
            elif choice == "1":
                path = input(f"{self._style('File path: ', 'cyan')}")
                if path:
                    print(self.execute_command(f"read_file {path}"))
            elif choice == "2":
                path = input(f"{self._style('File path: ', 'cyan')}")
                if path:
                    print(f"{self._style('Enter content (empty line to finish):', 'cyan')}")
                    content_lines = []
                    while True:
                        try:
                            line = input()
                            if not line and content_lines:
                                break
                            content_lines.append(line)
                        except EOFError:
                            break
                    content = '\n'.join(content_lines)
                    print(self.execute_command(f"write_file {path} {content}"))
            elif choice == "3":
                path = input(f"{self._style('File path: ', 'cyan')}")
                if path:
                    print(self._style("Note: Use AI to edit - describe what you want to change", "gray"))
            elif choice == "4":
                path = input(f"{self._style('Directory path (enter for .): ', 'cyan')}")
                path = path.strip() or "."
                print(self.execute_command(f"list_files {path}"))
            elif choice == "5":
                pattern = input(f"{self._style('Search pattern: ', 'cyan')}")
                if pattern:
                    print(self.execute_command(f"search_files {pattern}"))
            elif choice == "6":
                pattern = input(f"{self._style('Text pattern: ', 'cyan')}")
                if pattern:
                    print(self.execute_command(f"grep_search {pattern}"))
            elif choice == "7":
                cmd = input(f"{self._style('Command: ', 'cyan')}")
                if cmd:
                    print(self.execute_command(f"run_command {cmd}"))
            elif choice == "8":
                var = input(f"{self._style('Variable name: ', 'cyan')}")
                if var:
                    print(self.execute_command(f"get_env {var}"))
            elif choice == "9":
                query = input(f"{self._style('Your question: ', 'cyan')}")
                if query:
                    old_think = self.thinking_mode
                    self.thinking_mode = False
                    print(self.execute_command(query))
                    self.thinking_mode = old_think
            elif choice == "10":
                query = input(f"{self._style('Your question: ', 'cyan')}")
                if query:
                    old_think = self.thinking_mode
                    self.thinking_mode = True
                    print(self.execute_command(query))
                    self.thinking_mode = old_think
            elif choice == "11":
                model = input(f"{self._style('Model name (current: {self.model}): ', 'cyan')}")
                if model:
                    print(self.execute_command(f"/model {model}"))
            elif choice == "12":
                url = input(f"{self._style('Server URL (current: {self.server_url}): ', 'cyan')}")
                if url:
                    print(self.execute_command(f"/server {url}"))
            elif choice == "13":
                filename = input(f"{self._style('Filename: ', 'cyan')}")
                if filename:
                    print(self.execute_command(f"/save {filename}"))
            elif choice == "14":
                filename = input(f"{self._style('Filename: ', 'cyan')}")
                if filename:
                    print(self.execute_command(f"/load {filename}"))
            else:
                print(f"{self._style('Invalid option', 'red')}")

            print()

    # ==========================================
    # REPL Loop
    # ==========================================

    def run(self, command: Optional[str] = None):
        """Main run method - handles single command or interactive REPL mode"""
        if command:
            # Single command mode
            result = self.execute_command(command)
            print(result)
        else:
            # Interactive REPL mode
            self._print_banner()

            print(f"{self._style('Quick Start:', 'cyan', bold=True)}")
            print(f"  • Type naturally to ask questions or give instructions")
            print(f"  • Use {self._style('/menu', 'magenta', bold=True)} for interactive tool selection")
            print(f"  • Use {self._style('/help', 'magenta', bold=True)} to see all commands")
            print(f"  • Use {self._style('↑/↓', 'gray')} arrow keys for command history\n")

            while True:
                try:
                    # Styled prompt
                    prompt = f"{self._style('❯', 'orange', bold=True)} "
                    user_input = input(prompt)

                    # Handle empty input
                    if not user_input.strip():
                        continue

                    # Check for menu command
                    if user_input.strip() == '/menu':
                        result = self._handle_menu_selection()
                        if result == "exit":
                            print(f"\n{self._style('Goodbye!', 'green', bold=True)}")
                            break
                        continue

                    # Execute command and display result
                    result = self.execute_command(user_input)

                    # Check for exit
                    if result == "EXIT":
                        print(f"\n{self._style('Goodbye!', 'green', bold=True)}")
                        break

                    print(result)

                except KeyboardInterrupt:
                    print(f"\n{self._style('Goodbye!', 'green', bold=True)}")
                    break
                except EOFError:
                    print(f"\n{self._style('Goodbye!', 'green', bold=True)}")
                    break

    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
