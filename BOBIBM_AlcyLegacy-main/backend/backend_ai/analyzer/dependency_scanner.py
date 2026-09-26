"""AST-based dependency scanner for BOB Backend.

Inspects Python source code without executing untrusted code.
Detects imports, function calls, class definitions, and unresolved global variables.
"""

from __future__ import annotations

import ast
import builtins
from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Union


# Standard builtin and runtime magic names that should not be flagged as unresolved globals
BUILTIN_NAMES: Set[str] = set(dir(builtins))
SPECIAL_NAMES: Set[str] = {
    "__name__",
    "__file__",
    "__doc__",
    "__package__",
    "__spec__",
    "__annotations__",
    "__builtins__",
    "__path__",
    "self",
    "cls",
}


@dataclass
class DependencyScanResult:
    """Result of static AST dependency analysis."""

    file_path: str
    external_imports: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)  # Alias for external_imports
    external_modules: List[str] = field(default_factory=list)
    internal_calls: List[str] = field(default_factory=list)
    function_definitions: List[str] = field(default_factory=list)
    class_definitions: List[str] = field(default_factory=list)
    unresolved_globals: List[str] = field(default_factory=list)
    afferent_coupling: int = 0  # Inward references from other files in repo
    efferent_coupling: int = 0  # Outward dependencies imported
    dependencies_count: int = 0  # Total coupling metric matching API contract
    total_coupling: int = 0  # Alias for dependencies_count
    syntax_valid: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Union[str, int, bool, List[str], Optional[str]]]:
        """Convert result to dictionary representation."""
        return {
            "file_path": self.file_path,
            "external_imports": self.external_imports,
            "imports": self.imports,
            "external_modules": self.external_modules,
            "internal_calls": self.internal_calls,
            "function_definitions": self.function_definitions,
            "class_definitions": self.class_definitions,
            "unresolved_globals": self.unresolved_globals,
            "afferent_coupling": self.afferent_coupling,
            "efferent_coupling": self.efferent_coupling,
            "dependencies_count": self.dependencies_count,
            "total_coupling": self.total_coupling,
            "syntax_valid": self.syntax_valid,
            "error_message": self.error_message,
        }


class _ModuleScopeCollector(ast.NodeVisitor):
    """Collects top-level declarations and imports in module scope."""

    def __init__(self) -> None:
        self.imported_names: Set[str] = set()
        self.imported_modules: Set[str] = set()
        self.defined_functions: Set[str] = set()
        self.defined_classes: Set[str] = set()
        self.defined_globals: Set[str] = set()
        self.all_imports: List[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root_pkg = alias.name.split(".")[0]
            self.imported_modules.add(root_pkg)
            self.imported_names.add(alias.asname or alias.name)
            self.imported_names.add(root_pkg)
            self.all_imports.append(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module_name = node.module or ""
        root_pkg = module_name.split(".")[0] if module_name else ""
        if root_pkg:
            self.imported_modules.add(root_pkg)
        for alias in node.names:
            self.imported_names.add(alias.asname or alias.name)
            if module_name:
                self.all_imports.append(f"{module_name}.{alias.name}")
            else:
                self.all_imports.append(alias.name)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.defined_functions.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.defined_functions.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.defined_classes.add(node.name)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._extract_target_names(target)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._extract_target_names(node.target)

    def _extract_target_names(self, target: ast.AST) -> None:
        if isinstance(target, ast.Name):
            self.defined_globals.add(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self._extract_target_names(elt)


class _LocalScopeVisitor(ast.NodeVisitor):
    """Collects local bindings and parameters inside a function scope."""

    def __init__(self, func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> None:
        self.local_names: Set[str] = set()
        # Collect parameters
        args = func_node.args
        for arg in getattr(args, "posonlyargs", []):
            self.local_names.add(arg.arg)
        for arg in args.args:
            self.local_names.add(arg.arg)
        for arg in getattr(args, "kwonlyargs", []):
            self.local_names.add(arg.arg)
        if args.vararg:
            self.local_names.add(args.vararg.arg)
        if args.kwarg:
            self.local_names.add(args.kwarg.arg)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.local_names.add(node.id)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        # Comprehension target variable is local
        self.visit(node.target)
        self.generic_visit(node)


class _UsageVisitor(ast.NodeVisitor):
    """Visits function bodies and calls to record calls and loaded names."""

    def __init__(self, module_scope: _ModuleScopeCollector) -> None:
        self.module_scope = module_scope
        self.calls: List[str] = []
        self.unresolved_globals: Set[str] = set()
        self._scope_stack: List[Set[str]] = []

    def visit_Call(self, node: ast.Call) -> None:
        call_name = self._resolve_call_name(node.func)
        if call_name:
            self.calls.append(call_name)
        self.generic_visit(node)

    def _resolve_call_name(self, func_node: ast.AST) -> Optional[str]:
        if isinstance(func_node, ast.Name):
            return func_node.id
        if isinstance(func_node, ast.Attribute):
            val_name = self._resolve_call_name(func_node.value)
            if val_name:
                return f"{val_name}.{func_node.attr}"
            return func_node.attr
        return None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function_scope(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function_scope(node)

    def _visit_function_scope(
        self, func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> None:
        local_collector = _LocalScopeVisitor(func_node)
        for item in func_node.body:
            local_collector.visit(item)
        self._scope_stack.append(local_collector.local_names)

        # Visit inner nodes
        for item in func_node.body:
            self._visit_inner(item)

        self._scope_stack.pop()

    def _visit_inner(self, node: ast.AST) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._visit_function_scope(node)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            name_id = node.id
            if not self._is_name_resolved(name_id):
                self.unresolved_globals.add(name_id)
        else:
            if isinstance(node, ast.Call):
                call_name = self._resolve_call_name(node.func)
                if call_name:
                    self.calls.append(call_name)
            for child in ast.iter_child_nodes(node):
                self._visit_inner(child)

    def _is_name_resolved(self, name: str) -> bool:
        # Check current and enclosing function scopes
        for scope in reversed(self._scope_stack):
            if name in scope:
                return True
        # Check module scope
        if name in self.module_scope.defined_globals:
            return True
        if name in self.module_scope.defined_functions:
            return True
        if name in self.module_scope.defined_classes:
            return True
        if name in self.module_scope.imported_names:
            return True
        # Check builtins and python internals
        if name in BUILTIN_NAMES or name in SPECIAL_NAMES:
            return True
        return False


def _compute_afferent_coupling(
    target_module_name: str,
    target_stem: str,
    repo_path: Path,
    target_file_resolved: Path,
    target_exported_symbols: Set[str],
) -> int:
    """Scans other Python files in the repository to measure afferent coupling (inward references)."""
    afferent_count = 0
    excluded_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}

    try:
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            for file_name in files:
                if not file_name.endswith(".py"):
                    continue
                file_path = Path(root) / file_name
                try:
                    if file_path.resolve() == target_file_resolved:
                        continue
                except (OSError, RuntimeError):
                    if file_path == target_file_resolved:
                        continue

                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    tree = ast.parse(content, filename=str(file_path))
                except Exception:
                    continue

                imported_symbols: Set[str] = set()
                imported_module = False

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name == target_stem or alias.name.endswith(f".{target_stem}"):
                                afferent_count += 1
                                imported_module = True
                    elif isinstance(node, ast.ImportFrom):
                        mod = node.module or ""
                        if mod == target_stem or mod.endswith(f".{target_stem}"):
                            imported_module = True
                            for alias in node.names:
                                afferent_count += 1
                                imported_symbols.add(alias.asname or alias.name)

                    elif isinstance(node, ast.Call):
                        # Detect calls to imported symbols or module functions
                        if isinstance(node.func, ast.Name):
                            if node.func.id in imported_symbols or node.func.id in target_exported_symbols:
                                if imported_module:
                                    afferent_count += 1
                        elif isinstance(node.func, ast.Attribute):
                            if isinstance(node.func.value, ast.Name):
                                if node.func.value.id == target_stem and node.func.attr in target_exported_symbols:
                                    afferent_count += 1
    except Exception:
        pass

    return afferent_count


def scan_dependencies(
    file_path: Union[str, Path],
    repo_path: Optional[Union[str, Path]] = None,
    source_code: Optional[str] = None,
) -> DependencyScanResult:
    """Inspects a Python file or source code string via AST without executing it.

    Args:
        file_path: Path or relative path to the Python file.
        repo_path: Optional repository root path for afferent coupling analysis.
        source_code: Optional source code string. If omitted, file_path will be read.

    Returns:
        DependencyScanResult containing detected imports, calls, unresolved globals,
        and dependencies count.
    """
    file_path_str = str(file_path).replace("\\", "/")
    target_path = Path(file_path)

    # Resolve full path if repo_path is provided and file_path is relative
    if repo_path and not target_path.is_absolute():
        full_target_path = Path(repo_path) / target_path
    else:
        full_target_path = target_path

    # Read source code if not supplied
    if source_code is None:
        if not full_target_path.exists() or not full_target_path.is_file():
            return DependencyScanResult(
                file_path=file_path_str,
                syntax_valid=False,
                error_message=f"File not found: {full_target_path}",
            )
        try:
            with open(full_target_path, "r", encoding="utf-8", errors="replace") as f:
                code_to_parse = f.read()
        except Exception as e:
            return DependencyScanResult(
                file_path=file_path_str,
                syntax_valid=False,
                error_message=f"Error reading file: {e}",
            )
    else:
        code_to_parse = source_code

    # Parse AST
    try:
        tree = ast.parse(code_to_parse, filename=file_path_str)
    except SyntaxError as e:
        return DependencyScanResult(
            file_path=file_path_str,
            syntax_valid=False,
            error_message=f"SyntaxError on line {e.lineno}: {e.msg}",
        )
    except Exception as e:
        return DependencyScanResult(
            file_path=file_path_str,
            syntax_valid=False,
            error_message=f"AST parse error: {e}",
        )

    # 1. Collect top-level declarations and imports
    scope_collector = _ModuleScopeCollector()
    for node in tree.body:
        scope_collector.visit(node)

    # 2. Visit function bodies and calls
    usage_visitor = _UsageVisitor(scope_collector)
    usage_visitor.visit(tree)

    external_imports = sorted(list(set(scope_collector.all_imports)))
    external_modules = sorted(list(scope_collector.imported_modules))
    internal_calls = usage_visitor.calls
    function_defs = sorted(list(scope_collector.defined_functions))
    class_defs = sorted(list(scope_collector.defined_classes))
    unresolved = sorted(list(usage_visitor.unresolved_globals))

    efferent_count = len(external_imports) + len(internal_calls)
    target_exported_symbols = set(function_defs) | set(class_defs) | set(scope_collector.defined_globals)

    # 3. Calculate afferent coupling if repo_path is provided
    afferent_count = 0
    if repo_path:
        r_path = Path(repo_path)
        if r_path.exists() and r_path.is_dir():
            target_stem = target_path.stem
            try:
                resolved_target = full_target_path.resolve()
            except (OSError, RuntimeError):
                resolved_target = full_target_path
            afferent_count = _compute_afferent_coupling(
                target_module_name=target_path.name,
                target_stem=target_stem,
                repo_path=r_path,
                target_file_resolved=resolved_target,
                target_exported_symbols=target_exported_symbols,
            )

    total_coupling = efferent_count + afferent_count

    return DependencyScanResult(
        file_path=file_path_str,
        external_imports=external_imports,
        imports=external_imports,
        external_modules=external_modules,
        internal_calls=internal_calls,
        function_definitions=function_defs,
        class_definitions=class_defs,
        unresolved_globals=unresolved,
        afferent_coupling=afferent_count,
        efferent_coupling=efferent_count,
        dependencies_count=total_coupling,
        total_coupling=total_coupling,
        syntax_valid=True,
        error_message=None,
    )
