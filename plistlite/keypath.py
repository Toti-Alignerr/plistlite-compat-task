"""Key paths: dictionary keys and array indexes separated by '.'."""


class KeyPathError(Exception):
    pass


def _step(container, part):
    if isinstance(container, dict):
        return container[part]
    if isinstance(container, list):
        return container[int(part)]
    raise KeyError(part)


def get(root, path):
    value = root
    for part in path.split("."):
        try:
            value = _step(value, part)
        except (KeyError, IndexError, ValueError):
            raise KeyPathError("No value at that key path or invalid key path: %s" % path)
    return value


def _parent(root, path):
    parts = path.split(".")
    parent = root
    for part in parts[:-1]:
        try:
            parent = _step(parent, part)
        except (KeyError, IndexError, ValueError):
            raise KeyPathError("Key path not found %s" % path)
    return parent, parts[-1]


def insert(root, path, value, replace=False, append=False):
    parent, last = _parent(root, path)
    if append:
        target = _step(parent, last)
        if not isinstance(target, list):
            raise KeyPathError("Appending to a non-array at key path %s" % path)
        target.append(value)
    elif isinstance(parent, dict):
        if last in parent and not replace:
            raise KeyPathError("Value already exists at key path %s" % path)
        parent[last] = value
    elif isinstance(parent, list):
        index = int(last)
        if replace:
            parent[index] = value
        else:
            parent.insert(index, value)
    else:
        raise KeyPathError("Unable to insert value at key path %s" % path)


def remove(root, path):
    parent, last = _parent(root, path)
    try:
        if isinstance(parent, dict):
            del parent[last]
        else:
            del parent[int(last)]
    except (KeyError, IndexError, ValueError, TypeError):
        raise KeyPathError("No value to remove at key path %s" % path)
