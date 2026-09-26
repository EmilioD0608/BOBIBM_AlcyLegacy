"""AST syntax and bytecode compilation validator for Python code."""

import ast
import re
from typing import Optional, Tuple


def strip_markdown_code_blocks(code: str) -> str:
    """Strips markdown code block fences (e.g. ```python ... ```) if present."""
    trimmed = code.strip()
    # Match ```python\n ... \n``` or ```\n ... \n```
    pattern = r"^```(?:python|py)?\r?\n(.*?)\r?\n```$"
    match = re.search(pattern, trimmed, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Also handle single-line or trailing fences if any
    if trimmed.startswith("```"):
        lines = trimmed.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()

    return code


def validate_python_syntax(
    code: str, file_path: str = "<string>"
) -> Tuple[bool, Optional[str]]:
    """Validates that code is syntactically valid Python.
    
    Performs both AST parsing and bytecode compilation.
    
    Args:
        code: Python source code string.
        file_path: Virtual or real file path for error traceback context.
        
    Returns:
        Tuple of (is_valid: bool, error_message: str | None).
    """
    clean_code = strip_markdown_code_blocks(code)
    
    # Check 1: AST Parsing
    try:
        ast.parse(clean_code, filename=file_path)
    except SyntaxError as e:
        error_msg = f"SyntaxError at line {e.lineno}, col {e.offset}: {e.msg} (line text: {repr(e.text)})"
        return False, error_msg
    except Exception as e:
        return False, f"AST Parsing Error: {str(e)}"

    # Check 2: Bytecode compilation
    try:
        compile(clean_code, file_path, "exec")
    except SyntaxError as e:
        error_msg = f"Compilation SyntaxError at line {e.lineno}, col {e.offset}: {e.msg}"
        return False, error_msg
    except Exception as e:
        return False, f"Compilation Error: {str(e)}"

    return True, None
