"""Load *.toml settings"""

import tomllib
from typing import Dict, Any


def load_toml(path: str) -> Dict[str, Any]:
    """
    Read single .toml settings file
    """
    settings = {}
    try:
        with open(path, 'rb') as f:
            settings = tomllib.load(f)

    except FileNotFoundError:
        print(f"File '{path}' not found.")
        
    except tomllib.TOMLDecodeError as e:
        print(f"{path}:{e.lineno}:{e.colno}: syntax error in the TOML file")
        print(e.msg)
        raise SystemExit(1)
        
    except OSError as e:
        print(f"I/O error reading: {e}")
        raise

    return settings


def load_all() -> Dict[str, Any]:
    settings = load_toml('build.toml')
    return settings
