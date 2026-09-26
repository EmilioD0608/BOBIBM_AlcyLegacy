"""BOB Backend (Alcy Legacy) package."""

import importlib.util
import sys
from pathlib import Path

# Setup path and module alias so imports like `from backend.api...` resolve
# seamlessly regardless of whether the folder is named `backend` or `backend_ai`.
_PKG_DIR = Path(__file__).resolve().parent
for _p in [str(_PKG_DIR), str(_PKG_DIR.parent)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

if "backend" not in sys.modules:
    _spec = importlib.util.spec_from_file_location(
        "backend",
        str(_PKG_DIR / "__init__.py"),
        submodule_search_locations=[str(_PKG_DIR)],
    )
    if _spec and _spec.loader:
        _mod = importlib.util.module_from_spec(_spec)
        sys.modules["backend"] = _mod
        _spec.loader.exec_module(_mod)
