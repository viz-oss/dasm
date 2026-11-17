"""Log system"""

import logging, sys
from pathlib import Path


class LogGroupFilter(logging.Filter):

    def __init__(self, allowed_groups=None):
        super().__init__()
        self.allowed_groups = allowed_groups

    def filter(self, record):
        if self.allowed_groups == None:
          return False

        if self.allowed_groups == {'*'}:
          return True

        parts = record.name.split('.')
        group = parts[0] if parts else 'general'

        return (record.name in self.allowed_groups) or (group in self.allowed_groups)


def setup(groups_arg):
    allowed = None
    if groups_arg:
        # "auth+db" -> {"auth", "db"}
        allowed = set(g.strip() for g in groups_arg.split('+'))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.addFilter(LogGroupFilter(allowed))

    formatter = logging.Formatter('[%(name)s] %(message)s')
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)


RED = '\033[31m'
GREEN = '\033[32m'
GRAY = '\033[90m'
RESET = '\033[0m'


def red(s: str) -> str:
    return f"{RED}{s}{RESET}" if sys.stdout.isatty() else s

def green(s: str) -> str:
    return f"{GREEN}{s}{RESET}" if sys.stdout.isatty() else s

def gray(s: str) -> str:
    return f"{GRAY}{s}{RESET}" if sys.stdout.isatty() else s


def anonymize_path(file_path: str | Path) -> str:
    path = Path(file_path).resolve()
    home = Path.home().resolve()
    try:
        relative_path = path.relative_to(home)
        return str(Path('~') / relative_path)
    except ValueError:
        return str(path)
