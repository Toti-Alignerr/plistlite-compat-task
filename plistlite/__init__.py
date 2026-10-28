"""plistlite: a pure-Python replacement for macOS plutil."""

import sys

__all__ = ["run"]


def run(argv, stdout=None, stderr=None, stdin=b""):
    """Run plutil with `argv` (without the program name).

    stdout and stderr are binary streams (default: the process's own);
    stdin is the bytes read for the input file '-'.  Returns the exit
    status."""
    from .cli import main
    out = stdout if stdout is not None else sys.stdout.buffer
    err = stderr if stderr is not None else sys.stderr.buffer
    return main(list(argv), out, err, stdin)
