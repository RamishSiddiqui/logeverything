import platform


def is_windows_terminal():
    return platform.system() == "Windows"


def supports_unicode():
    return False


def get_platform_symbols():
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


def get_ascii_only_mode():
    return True


_PLATFORM_SYMBOLS = None


def get_symbols():
    global _PLATFORM_SYMBOLS
    if _PLATFORM_SYMBOLS is None:
        _PLATFORM_SYMBOLS = get_platform_symbols()
    return _PLATFORM_SYMBOLS


def clear_symbol_cache():
    global _PLATFORM_SYMBOLS
    _PLATFORM_SYMBOLS = None
