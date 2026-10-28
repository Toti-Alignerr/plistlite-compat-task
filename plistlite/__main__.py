import sys

from . import run


def main():
    argv = sys.argv[1:]
    stdin = sys.stdin.buffer.read() if "-" in argv else b""
    sys.exit(run(argv, sys.stdout.buffer, sys.stderr.buffer, stdin))


if __name__ == "__main__":
    main()
