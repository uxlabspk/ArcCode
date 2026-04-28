"""
Markdown rendering utilities for terminal output
"""

import re
from typing import List


class TerminalMarkdownRenderer:
    """Renders markdown text with basic formatting for terminal"""

    def __init__(self, style_func):
        self.style = style_func
        self.code_block_lang = None
        self.in_code_block = False
        self.code_block_content = []
        self.output_lines: List[str] = []

    def render(self, text: str) -> str:
        """Render markdown text and return formatted string"""
        lines = text.split('\n')
        self.output_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check for code blocks
            if line.strip().startswith('```'):
                if not self.in_code_block:
                    # Starting code block
                    self.in_code_block = True
                    self.code_block_lang = line.strip()[3:].strip()
                    self.code_block_content = []
                else:
                    # Ending code block
                    self._render_code_block()
                    self.in_code_block = False
                    self.code_block_lang = None
                i += 1
                continue

            if self.in_code_block:
                self.code_block_content.append(line)
                i += 1
                continue

            # Headers
            if line.startswith('### '):
                self.output_lines.append(self.style(line[4:], 'cyan', bold=True))
            elif line.startswith('## '):
                self.output_lines.append(self.style(line[3:], 'cyan', bold=True))
            elif line.startswith('# '):
                self.output_lines.append(self.style(line[2:], 'cyan', bold=True))

            # Bold and italic (inline)
            elif '**' in line or '*' in line or '`' in line:
                self.output_lines.append(self._render_inline_format(line))

            # List items
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                indent = len(line) - len(line.lstrip())
                bullet = self.style('•', 'yellow')
                content = self._render_inline_format(line.strip()[2:])
                self.output_lines.append(' ' * indent + f'{bullet} {content}')

            # Numbered lists
            elif re.match(r'^\d+\.\s', line):
                self.output_lines.append(self.style(line, 'yellow'))

            # Empty lines
            elif not line.strip():
                self.output_lines.append('')

            # Regular text
            else:
                self.output_lines.append(line)

            i += 1

        return '\n'.join(self.output_lines)

    def _render_code_block(self):
        """Render a code block with formatting"""
        if not self.code_block_content:
            return

        # Add language label if present
        if self.code_block_lang:
            self.output_lines.append(self.style(f'┌─ {self.code_block_lang}', 'gray'))

        # Render code lines with dim styling
        for line in self.code_block_content:
            # Escape any ANSI codes that might be in the code
            self.output_lines.append(f'  {self.style(line, "gray")}')

        if self.code_block_lang:
            self.output_lines.append(self.style('└─', 'gray'))

    def _render_inline_format(self, text: str) -> str:
        """Render inline markdown (bold, italic, code)"""
        result = text

        # Inline code (backticks)
        while '`' in result:
            match = re.search(r'`([^`]+)`', result)
            if match:
                code = match.group(1)
                styled = self.style(code, 'green')
                result = result[:match.start()] + styled + result[match.end():]
            else:
                break

        # Bold (**text**)
        while '**' in result:
            match = re.search(r'\*\*([^*]+)\*\*', result)
            if match:
                bold_text = match.group(1)
                styled = self.style(bold_text, 'white', bold=True)
                result = result[:match.start()] + styled + result[match.end():]
            else:
                break

        # Italic (*text*)
        while '*' in result:
            match = re.search(r'\*([^*]+)\*', result)
            if match:
                italic_text = match.group(1)
                styled = self.style(italic_text, 'white')
                result = result[:match.start()] + styled + result[match.end():]
            else:
                break

        return result
