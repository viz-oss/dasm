"""Dynamic Python module loader"""

import importlib, re
from functools import lru_cache
from lang.exceptions import DasmSyntaxError


SAFE_IDENTIFIER = re.compile(r"^[a-zA-Z0-9_]+$")
def _validate_input(value: str, field_name: str):
    if not SAFE_IDENTIFIER.match(value):
        raise DasmSyntaxError(f"Bad name for {field_name}: '{value}'. Only letters, numbers, and underscores are allowed.")


@lru_cache(maxsize=32)
def _cached_import(module_path: str):
    return importlib.import_module(module_path)


def load_module(dir: str, name: str):
    """Dynamically loads the module from <dir>/<name>.py"""
    
    # Validate path
    _validate_input(dir, 'directory')
    _validate_input(name, 'module')
    
    # Load module
    module_path = f"{dir}.{name}"
    try:
        module = _cached_import(module_path)
    except ModuleNotFoundError as e:
        raise DasmSyntaxError(f"Module '{dir}/{name}' not found ") from e
    except Exception as e:
        raise DasmSyntaxError(f"Error importing module '{dir}/{name}': {e}") from e

    # Validate EXPORTS
    if not hasattr(module, 'EXPORTS'):
        raise DasmSyntaxError(f"Module {dir}/{name}.py does not contain EXPORTS")
    exports_target = module.EXPORTS
    if not callable(exports_target):
        raise DasmSyntaxError(f"The EXPORTS attribute in module '{dir}/{name}.py' must be a function or a class.")

    return exports_target()
