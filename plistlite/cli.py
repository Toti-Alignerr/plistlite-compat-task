"""plutil-compatible command line."""

import base64
import datetime
import json
import os
import plistlib

from . import formats, keypath, literals, printer

USAGE = """plutil: [command_option] [other_options] file...
The file '-' means stdin
Command options are (-lint is the default):
 -help                         show this message and exit
 -lint                         check the property list files for syntax errors
 -convert fmt                  rewrite property list files in format
                               fmt is one of: xml1 binary1 json swift objc
 -insert keypath -type value   insert a value into the property list before writing it out
 -replace keypath -type value  same as -insert, but it will overwrite an existing value
 -remove keypath               removes the value at 'keypath' from the property list before writing it out
 -extract keypath fmt          outputs the value at 'keypath' in the property list as a new plist of type 'fmt'
 -type keypath                 outputs the type of the value at 'keypath' in the property list
 -create fmt                   creates an empty plist of the specified format
 -p                            print property list in a human-readable fashion
"""

COMMANDS = {"-help", "-lint", "-convert", "-insert", "-replace", "-remove",
            "-extract", "-type", "-create", "-p"}


class UsageError(Exception):
    pass


class Options:
    command = "-lint"
    fmt = None
    keypath = None
    value_type = None
    value = None
    silent = False
    output = None
    extension = None
    readable = False
    no_newline = False
    expect = None
    append = False
    header = False

    def __init__(self):
        self.files = []


def parse_args(argv):
    opts = Options()
    args = list(argv)
    if args and args[0] in COMMANDS:
        opts.command = args.pop(0)
    try:
        if opts.command in ("-convert", "-create"):
            opts.fmt = args.pop(0)
        elif opts.command == "-extract":
            opts.keypath = args.pop(0)
            opts.fmt = args.pop(0)
        elif opts.command in ("-type", "-remove"):
            opts.keypath = args.pop(0)
        elif opts.command in ("-insert", "-replace"):
            opts.keypath = args.pop(0)
            opts.value_type = args.pop(0)
            if opts.value_type not in ("-dictionary", "-array"):
                opts.value = args.pop(0)
    except IndexError:
        raise UsageError("Missing argument for %s" % opts.command)
    while args:
        a = args.pop(0)
        if a == "--":
            opts.files.extend(args)
            break
        if a == "-s":
            opts.silent = True
        elif a == "-r":
            opts.readable = True
        elif a == "-n":
            opts.no_newline = True
        elif a == "-append":
            opts.append = True
        elif a == "-header":
            opts.header = True
        elif a in ("-o", "-e", "-expect"):
            if not args:
                raise UsageError("Missing argument for %s." % a)
            val = args.pop(0)
            if a == "-o":
                opts.output = val
            elif a == "-e":
                opts.extension = val
            else:
                opts.expect = val
        elif a.startswith("-") and a != "-":
            raise UsageError("unrecognized option: %s" % a)
        else:
            opts.files.append(a)
    return opts


def type_name(value):
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (bytes, bytearray)):
        return "data"
    if isinstance(value, datetime.datetime):
        return "date"
    if isinstance(value, dict):
        return "dictionary"
    if isinstance(value, list):
        return "array"
    return "unknown"


def make_value(opts):
    t, v = opts.value_type, opts.value
    if t == "-dictionary":
        return {}
    if t == "-array":
        return []
    if t == "-bool":
        return v in ("YES", "true")
    if t == "-integer":
        return int(v)
    if t == "-float":
        return float(v)
    if t == "-string":
        return v
    if t == "-date":
        return datetime.datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ")
    if t == "-data":
        return base64.b64decode(v)
    if t == "-xml":
        return plistlib.loads(v.encode())
    if t == "-json":
        return json.loads(v)
    raise UsageError("Unknown insert or replace type %s" % t)


class Session:
    def __init__(self, stdout, stderr, stdin):
        self.stdout = stdout
        self.stderr = stderr
        self.stdin = stdin
        self.status = 0

    def error(self, name, message):
        self.stderr.write(("%s: %s\n" % (name, message)).encode("utf-8"))
        self.status = 1

    def read(self, path):
        if path == "-":
            return self.stdin, "<stdin>"
        with open(path, "rb") as f:
            return f.read(), path

    def write(self, path, data):
        if path == "-":
            self.stdout.write(data)
        else:
            with open(path, "wb") as f:
                f.write(data)


def main(argv, stdout, stderr, stdin=b""):
    try:
        opts = parse_args(argv)
    except UsageError as e:
        stderr.write(("%s\n" % e).encode())
        return 1
    if opts.command == "-help":
        stdout.write(USAGE.encode())
        return 0
    if not opts.files:
        stderr.write(b"No files specified.\n")
        return 1
    s = Session(stdout, stderr, stdin)
    for path in opts.files:
        try:
            handle(s, opts, path)
        except (UsageError, ValueError) as e:
            s.error(path, str(e))
    return s.status


def handle(s, opts, path):
    if opts.command == "-create":
        s.write(path, formats.dump({}, opts.fmt, opts.readable))
        return
    try:
        data, name = s.read(path)
    except OSError as e:
        s.error(path, "(%s)" % e.strerror)
        return
    try:
        value, fmt = formats.load(data)
    except formats.FormatError as e:
        s.error(name, "(%s)" % e if opts.command == "-lint" else str(e))
        return
    cmd = opts.command
    if cmd == "-lint":
        if not opts.silent:
            s.stdout.write(("%s: OK\n" % name).encode())
    elif cmd == "-p":
        s.stdout.write((printer.describe(value) + "\n").encode("utf-8"))
    elif cmd == "-convert":
        convert(s, opts, path, name, value)
    elif cmd in ("-extract", "-type"):
        extract(s, opts, name, value)
    else:
        edit(s, opts, path, name, value, fmt)


def convert(s, opts, path, name, value):
    try:
        if opts.fmt == "swift":
            data = literals.swift(value, name).encode("utf-8")
            target = opts.output or os.path.splitext(path)[0] + ".swift"
        elif opts.fmt == "objc":
            data = literals.objc(value, name).encode("utf-8")
            target = opts.output or os.path.splitext(path)[0] + ".m"
        else:
            data = formats.dump(value, opts.fmt, opts.readable)
            target = opts.output or path
            if opts.extension and not opts.output:
                target = os.path.splitext(path)[0] + "." + opts.extension
    except (formats.FormatError, literals.LiteralError) as e:
        s.error(name, str(e))
        return
    s.write(target, data)


def extract(s, opts, name, value):
    try:
        found = keypath.get(value, opts.keypath)
    except keypath.KeyPathError as e:
        s.error(name, "Could not extract value, error: %s" % e)
        return
    kind = type_name(found)
    if opts.expect and opts.expect != kind:
        s.error(name, "Value at [%s] expected to be %s but is %s" % (opts.keypath, opts.expect, kind))
        return
    end = b"" if opts.no_newline else b"\n"
    if opts.command == "-type":
        s.stdout.write(kind.encode() + end)
        return
    if opts.fmt == "raw":
        if isinstance(found, dict):
            text = "\n".join(sorted(found))
        elif isinstance(found, list):
            text = str(len(found))
        elif isinstance(found, bool):
            text = "true" if found else "false"
        elif isinstance(found, (bytes, bytearray)):
            text = base64.b64encode(found).decode()
        elif isinstance(found, datetime.datetime):
            text = found.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            text = str(found)
        s.write(opts.output or "-", text.encode("utf-8") + end)
        return
    try:
        data = formats.dump(found, opts.fmt, opts.readable)
    except formats.FormatError as e:
        s.error(name, str(e))
        return
    s.write(opts.output or "-", data + end)


def edit(s, opts, path, name, value, fmt):
    try:
        if opts.command == "-remove":
            keypath.remove(value, opts.keypath)
        else:
            keypath.insert(value, opts.keypath, make_value(opts),
                           replace=opts.command == "-replace", append=opts.append)
    except keypath.KeyPathError as e:
        s.error(name, str(e))
        return
    try:
        data = formats.dump(value, fmt, opts.readable)
    except formats.FormatError as e:
        s.error(name, str(e))
        return
    s.write(opts.output or path, data)
