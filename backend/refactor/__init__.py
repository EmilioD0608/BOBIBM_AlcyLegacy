"""Modernization and refactoring package for BOB Backend."""

from backend.refactor.diff_generator import (
    extract_changes_summary,
    generate_unified_diff,
)
from backend.refactor.engine import RefactorEngine, refactor_code
from backend.refactor.provider import (
    BaseWatsonxProvider,
    MockWatsonxProvider,
    WatsonxProvider,
    get_watsonx_provider,
)
from backend.refactor.safety_harness import (
    generate_characterization_tests,
    generate_safety_harness,
)
from backend.refactor.validator import (
    strip_markdown_code_blocks,
    validate_python_syntax,
)

__all__ = [
    "RefactorEngine",
    "refactor_code",
    "BaseWatsonxProvider",
    "WatsonxProvider",
    "MockWatsonxProvider",
    "get_watsonx_provider",
    "generate_safety_harness",
    "generate_characterization_tests",
    "generate_unified_diff",
    "extract_changes_summary",
    "validate_python_syntax",
    "strip_markdown_code_blocks",
]
