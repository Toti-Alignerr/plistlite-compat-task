"""Reading and writing property list formats."""

import json
import plistlib

XML, BINARY, JSON = "xml1", "binary1", "json"


class FormatError(Exception):
    pass


def detect(data):
    if data.startswith(b"bplist"):
        return BINARY
    stripped = data.lstrip()
    if stripped.startswith(b"<"):
        return XML
    return JSON


def load(data):
    """Returns (value, format)."""
    if not data:
        raise FormatError("Cannot parse a NULL or zero-length data")
    fmt = detect(data)
    if fmt in (XML, BINARY):
        try:
            return plistlib.loads(data), fmt
        except Exception as e:  # plistlib raises several types
            raise FormatError("Property List error: %s" % e)
    try:
        value = json.loads(data.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        raise FormatError("JSON error: %s" % e)
    if not isinstance(value, (dict, list)):
        raise FormatError("JSON error: JSON text did not start with array or object")
    return value, JSON


def dump(value, fmt, readable=False):
    if fmt == XML:
        return plistlib.dumps(value, fmt=plistlib.FMT_XML, sort_keys=True)
    if fmt == BINARY:
        return plistlib.dumps(value, fmt=plistlib.FMT_BINARY, sort_keys=True)
    if fmt == JSON:
        _check_json(value)
        if readable:
            text = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)
        else:
            text = json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
        return text.encode("utf-8")
    raise FormatError("Unknown format %s" % fmt)


def _check_json(value):
    if isinstance(value, (bytes, bytearray)) or hasattr(value, "isoformat"):
        raise FormatError("Invalid object in plist for JSON format")
    if isinstance(value, dict):
        for v in value.values():
            _check_json(v)
    elif isinstance(value, list):
        for v in value:
            _check_json(v)
