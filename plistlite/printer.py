"""The human-readable -p format."""

import datetime


def describe(value, indent=0):
    pad = "  " * (indent + 1)
    if isinstance(value, dict):
        lines = ["{"]
        for key in sorted(value):
            lines.append('%s"%s" => %s' % (pad, key, describe(value[key], indent + 1)))
        lines.append("  " * indent + "}")
        return "\n".join(lines)
    if isinstance(value, list):
        lines = ["["]
        for i, item in enumerate(value):
            lines.append("%s%d => %s" % (pad, i, describe(item, indent + 1)))
        lines.append("  " * indent + "]")
        return "\n".join(lines)
    if isinstance(value, str):
        return '"%s"' % value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (bytes, bytearray)):
        return "{length = %d, bytes = 0x%s}" % (len(value), bytes(value).hex())
    if isinstance(value, datetime.datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S +0000")
    return str(value)
