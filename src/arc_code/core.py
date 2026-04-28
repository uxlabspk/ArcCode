"""
Core functionality for Arc Code CLI
"""

import os
import sys
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List


class ArcCodeCore:
    """Main class for Arc Code CLI functionality"""
    
    def __init__(self, model: str = "llama.cpp", verbose: bool = False, server_url: str = "http://localhost:8080"):
        self.model = model
        self.verbose = verbose
        self.server_url = server_url.rstrip("/")
        self.tools = {}
        self.register_default_tools()

        self._banner_title = "Arc Code v0.1.0 · llama-server · [API] Experiment plan"
        self._banner_meta = "1 model · 0 MCP servers · 0 skills"

    def _style(self, text: str, color: str) -> str:
        colors = {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "dim": "\033[2m",
            "orange": "\033[38;5;214m",
            "cyan": "\033[38;5;39m",
            "yellow": "\033[38;5;220m",
            "gray": "\033[38;5;245m",
        }
        return f"{colors.get(color, '')}{text}{colors['reset']}"

    def _print_banner(self):
        logo = [
            " .:::.    ",
            ":-=:.:.  ",
            ":..=-:.  ",
            " .:-=:.  ",
            "  ..:-.  ",
        ]
        title = (
            f"{self._style('Arc Code', 'orange')} "
            f"{self._style('v0.1.0', 'gray')} · "
            f"{self._style('llama-server', 'cyan')} · "
            f"[API] Experiment plan"
        )
        meta = f"{self._style(self._banner_meta, 'gray')}"
        info = f"Type {self._style('/help', 'cyan')} for more information"

        print(f"{logo[0]} {title}")
        print(f"{logo[1]} {meta}")
        print(f"{logo[2]} {info}")
        print(f"{logo[3]}")
        print(f"{logo[4]}")

        home_dir = os.path.expanduser("~")
        if os.getcwd() == home_dir:
            warn = self._style("WARNING: You are in the home directory", "yellow")
            warn_detail = self._style("Running in this location is not recommended.", "yellow")
            print(warn)
            print(warn_detail)
        print()
    
    def register_default_tools(self):
        """Register default tools"""
        self.tools = {
            "echo": self.tool_echo,
            "list_files": self.tool_list_files,
            "read_file": self.tool_read_file,
        }
    
    def tool_echo(self, message: str) -> str:
        """Echo a message"""
        return f"Echo: {message}"
    
    def tool_list_files(self, path: str = ".") -> str:
        """List files in a directory"""
        try:
            files = os.listdir(path)
            return f"Files in {path}: {', '.join(files)}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def tool_read_file(self, file_path: str) -> str:
        """Read content of a file"""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def execute_command(self, command: str) -> str:
        """Execute a command using available tools or the model"""
        if self.verbose:
            print(f"[ArcCode] Executing command: {command}")
        
        # Parse command and arguments
        parts = command.split(maxsplit=1)
        cmd_name = parts[0]
        cmd_args = parts[1] if len(parts) > 1 else ""
        
        # Execute the appropriate tool
        if cmd_name == "echo":
            return self.tools["echo"](cmd_args)
        elif cmd_name == "list_files":
            path = cmd_args.strip() if cmd_args.strip() else "."
            return self.tools["list_files"](path)
        elif cmd_name == "read_file":
            file_path = cmd_args.strip()
            return self.tools["read_file"](file_path)
        else:
            return self._run_agent(command)

    def _call_llama_server(self, messages: List[Dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.server_url}/v1/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = resp.read().decode("utf-8")
            payload = json.loads(body)
            return payload["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            return f"Error: llama-server HTTP {e.code}"
        except Exception as e:
            return f"Error: {str(e)}"

    def _run_agent(self, user_input: str) -> str:
        system_prompt = (
            "You are Arc Code, a CLI agent. Use tools when needed. "
            "When you need a tool, reply with JSON: {\"tool\": \"name\", \"args\": {..}}. "
            "When you are done, reply with JSON: {\"final\": \"message\"}. "
            "Available tools: echo(message), list_files(path), read_file(file_path)."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]

        for _ in range(5):
            response = self._call_llama_server(messages)
            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                return response

            if "final" in data:
                return data["final"]

            tool_name = data.get("tool")
            tool_args = data.get("args", {})
            if tool_name in self.tools:
                try:
                    tool_result = self.tools[tool_name](**tool_args)
                except Exception as e:
                    tool_result = f"Tool error: {str(e)}"
            else:
                tool_result = f"Unknown tool: {tool_name}"

            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": f"Tool result: {tool_result}"})

        return "Error: Agent exceeded maximum steps"
    
    def run(self, command: Optional[str] = None):
        """Main run method"""
        if command:
            result = self.execute_command(command)
            print(result)
        else:
            self._print_banner()
            print("Arc Code CLI - Ready for commands")
            print("Type 'exit' to quit")
            
            # Simple REPL loop
            while True:
                try:
                    user_input = input("> ")
                    if user_input.lower() in ['exit', 'quit']:
                        break
                    if user_input.strip():
                        result = self.execute_command(user_input)
                        print(result)
                except KeyboardInterrupt:
                    print("\nGoodbye!")
                    break
                except Exception as e:
                    print(f"Error: {str(e)}")