# plistlite

A pure-Python property list tool with the same command line as the macOS
`plutil`. It needs only the Python standard library (3.14).

```sh
python3 -m plistlite -p examples/settings.plist
python3 -m plistlite -convert json -r -o - examples/settings.plist
python3 -m unittest discover -s tests
```

## Commands

| Command | What it does |
| --- | --- |
| `-lint` (default) | check each file; prints `FILE: OK` |
| `-p` | print the property list in a human-readable form |
| `-convert FMT` | rewrite the file as `xml1`, `binary1`, `json`, `swift` or `objc` |
| `-extract KEYPATH FMT` | print the value at `KEYPATH` as `xml1`, `binary1`, `json` or `raw` |
| `-type KEYPATH` | print the type of the value at `KEYPATH` |
| `-insert KEYPATH -TYPE VALUE` | insert a value (`-bool`, `-integer`, `-float`, `-string`, `-date`, `-data`, `-xml`, `-json`, `-dictionary`, `-array`) |
| `-replace KEYPATH -TYPE VALUE` | like `-insert`, but overwrite an existing value |
| `-remove KEYPATH` | remove the value at `KEYPATH` |
| `-create FMT` | write an empty dictionary |
| `-help` | print usage |

Options: `-s` (silent), `-o PATH` (output file, `-` for stdout), `-e EXT`
(output extension), `-r` (human-readable JSON), `-n` (no trailing newline
for `-extract`/`-type`), `-expect TYPE`, `-append`, `-header`, `--`.

The file `-` means standard input.

## Formats

* XML and binary property lists are read and written with `plistlib`.
* JSON is read and written with `json`; the top level must be an array or a
  dictionary, and data and dates cannot be written as JSON.
* Key paths are dictionary keys and array indexes separated by `.`.

## Library

```python
import plistlite
status = plistlite.run(["-lint", "file.plist"])
```

`plistlite.run(argv, stdout=None, stderr=None, stdin=b"")` takes the
arguments without the program name, writes to the given binary streams and
returns the exit status.

## Layout

* `plistlite/cli.py` — argument parsing and commands
* `plistlite/formats.py` — reading and writing XML, binary and JSON
* `plistlite/printer.py` — `-p` output
* `plistlite/literals.py` — Swift and Objective-C output
* `plistlite/keypath.py` — key path lookup and editing
