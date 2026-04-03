import platform
from typing import Any, Dict, Optional


def is_windows_terminal() -> bool:
    return platform.system() == "Windows"


def supports_unicode() -> bool:
    return False


def get_platform_symbols() -> Dict[str, Any]:
    return {
        "level_symbols": {
            "DEBUG": "[D]",
            "INFO": "[I]",
            "WARNING": "[W]",
            "ERROR": "[E]",
            "CRITICAL": "[C]",
            "EXCEPTION": "[X]",
        },
        "context_start": "+-->",
        "context_end": "+<--",
        "call_symbol": "[CALL]",
        "done_symbol": "[DONE]",
        "io_start": "+-> I/O",
        "io_end": "+<- I/O",
        "indent_char": "|",
        "entry_char": "+-> ",
        "exit_char": "+<- ",
        "continue_char": "+-- ",
    }


def get_ascii_only_mode() -> bool:
    return True


_PLATFORM_SYMBOLS: Optional[Dict[str, Any]] = None


def get_symbols() -> Dict[str, str]:
    global _PLATFORM_SYMBOLS
    if _PLATFORM_SYMBOLS is None:
        _PLATFORM_SYMBOLS = get_platform_symbols()
    return _PLATFORM_SYMBOLS


def clear_symbol_cache() -> None:
    global _PLATFORM_SYMBOLS
    _PLATFORM_SYMBOLS = None
