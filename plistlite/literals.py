"""Swift and Objective-C literal output (-convert swift / objc)."""

import os


class LiteralError(Exception):
    pass


def variable_name(path):
    base = os.path.splitext(os.path.basename(path))[0]
    return "".join(c if c.isalnum() else "_" for c in base)


def swift(value, source):
    return "/// Generated from %s\nlet %s = %s\n" % (source, variable_name(source), _swift(value, 0))


def _swift(v, level):
    pad = "    " * (level + 1)
    if isinstance(v, dict):
        body = "".join('%s"%s" : %s,\n' % (pad, k, _swift(v[k], level + 1)) for k in sorted(v))
        return "[\n" + body + "    " * level + "]"
    if isinstance(v, list):
        body = "".join("%s%s,\n" % (pad, _swift(e, level + 1)) for e in v)
        return "[\n" + body + "    " * level + "]"
    if isinstance(v, str):
        return '"%s"' % v.replace("\\", "\\\\").replace('"', '\\"')
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (bytes, bytearray)):
        return "Data(bytes: [%s])" % ", ".join("0x%02x" % b for b in v)
    if hasattr(v, "isoformat"):
        raise LiteralError("Input contains an object that cannot be represented in Swift literal syntax")
    return repr(v)


def objc(value, source):
    name = variable_name(source)
    kind = {dict: "NSDictionary", list: "NSArray", str: "NSString"}.get(type(value), "NSNumber")
    return ("/// Generated from %s\n__attribute__((visibility(\"hidden\")))\n%s * const %s = %s;\n"
            % (source, kind, name, _objc(value, 0)))


def _objc(v, level):
    pad = "    " * (level + 1)
    if isinstance(v, dict):
        body = "".join('%s@"%s" : %s,\n' % (pad, k, _objc(v[k], level + 1)) for k in sorted(v))
        return "@{\n" + body + "    " * level + "}"
    if isinstance(v, list):
        body = "".join("%s%s,\n" % (pad, _objc(e, level + 1)) for e in v)
        return "@[\n" + body + "    " * level + "]"
    if isinstance(v, str):
        return '@"%s"' % v.replace('"', '\\"')
    if isinstance(v, bool):
        return "@YES" if v else "@NO"
    if isinstance(v, (int, float)):
        return "@%r" % v
    raise LiteralError("Input contains an object that cannot be represented in Obj-C literal syntax")
