"""Import helper for host-tools, whose hyphen is not a Python package name."""

import importlib.util
from pathlib import Path


def load_verify():
    path = Path(__file__).resolve().parents[1] / "host-tools" / "verify_repo.py"
    spec = importlib.util.spec_from_file_location("topazio_verify_repo", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load verify_repo.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
