import io
import json
import os
import tempfile
import unittest

import plistlite

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLE = os.path.join(HERE, "..", "examples", "settings.plist")

XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
\t<key>a</key>
\t<integer>1</integer>
\t<key>list</key>
\t<array>
\t\t<string>x</string>
\t\t<string>y</string>
\t</array>
</dict>
</plist>
"""


def run(argv, stdin=b""):
    out, err = io.BytesIO(), io.BytesIO()
    status = plistlite.run(argv, out, err, stdin)
    return status, out.getvalue(), err.getvalue()


class BasicTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "t.plist")
        with open(self.path, "wb") as f:
            f.write(XML)

    def tearDown(self):
        self.dir.cleanup()

    def test_lint_ok(self):
        status, out, err = run(["-lint", self.path])
        self.assertEqual(status, 0)
        self.assertEqual(out, (self.path + ": OK\n").encode())
        self.assertEqual(err, b"")

    def test_lint_silent(self):
        self.assertEqual(run(["-lint", "-s", self.path]), (0, b"", b""))

    def test_type(self):
        self.assertEqual(run(["-type", "list", self.path])[1], b"array\n")
        self.assertEqual(run(["-type", "list.1", self.path])[1], b"string\n")

    def test_extract_raw(self):
        self.assertEqual(run(["-extract", "a", "raw", self.path])[1], b"1\n")

    def test_convert_json_roundtrip(self):
        status, _, _ = run(["-convert", "json", self.path])
        self.assertEqual(status, 0)
        with open(self.path, "rb") as f:
            self.assertEqual(json.loads(f.read()), {"a": 1, "list": ["x", "y"]})

    def test_insert_and_remove(self):
        self.assertEqual(run(["-insert", "b", "-string", "hi", self.path])[0], 0)
        self.assertEqual(run(["-extract", "b", "raw", self.path])[1], b"hi\n")
        self.assertEqual(run(["-remove", "b", self.path])[0], 0)
        self.assertEqual(run(["-type", "b", self.path])[0], 1)

    def test_stdin(self):
        self.assertEqual(run(["-lint", "-"], XML), (0, b"<stdin>: OK\n", b""))

    def test_example_prints(self):
        status, out, _ = run(["-p", EXAMPLE])
        self.assertEqual(status, 0)
        self.assertIn(b"plistlite demo", out)

    def test_missing_file(self):
        status, _, err = run(["-lint", os.path.join(self.dir.name, "nope.plist")])
        self.assertEqual(status, 1)
        self.assertTrue(err)


if __name__ == "__main__":
    unittest.main()
