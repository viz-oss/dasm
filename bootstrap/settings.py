"""Load *.toml settings"""

import tomllib
from typing import Dict, Any
from pathlib import Path


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
    allsettings = { 'options': {}, 'env': {}, 'paths': [] }
    current_dir = Path('.')
    toml_files = sorted(list(current_dir.glob('*.toml')))
    for file in toml_files:
        settings = load_toml(file)
        allsettings['options'] = { **allsettings['options'], **settings.get('dasm', {}).get('options', {}) }
        allsettings['env'] = { **allsettings['env'], **settings.get('dasm', {}).get('env', {}) }
        allsettings['paths'] = [ *allsettings['paths'], *settings.get('dasm', {}).get('imports', {}).get('paths', []) ]
    allsettings['paths'] = list(set(allsettings['paths']))
    return allsettings
