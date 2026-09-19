#!/usr/bin/env python3
"""
glyphs_remote.py — run a Python file inside a RUNNING Glyphs from Terminal (no clicking).
Uses the same NSConnection channel as the Glyphs SDK's "Glyphs remote scripts" folder.

    python3 mac/glyphs_remote.py 3 mac/headless_check.py      # Glyphs 3
    python3 mac/glyphs_remote.py 4 mac/headless_check.py      # Glyphs 4

Needs PyObjC in this Python: pip install pyobjc-framework-Cocoa
Output printed by the script inside Glyphs is echoed here. Exit code 1 if any FAIL line.
"""
import sys
import time
import objc
from Foundation import NSObject, NSConnection

PORTS = {"3": ["com.GeorgSeifert.Glyphs3"],
         "4": ["com.GeorgSeifert.Glyphs4", "com.GeorgSeifert.Glyphs3"]}   # Glyphs 4 name unverified; both tried


class StdOut(NSObject):
    def init(self):
        self = objc.super(StdOut, self).init()
        self.text = ""
        return self

    def setWrite_(self, t):
        self.text += str(t); sys.stdout.write(str(t)); sys.stdout.flush()

    def setWriteError_(self, t):
        self.text += str(t); sys.stdout.write(str(t)); sys.stdout.flush()



def connect(version):
    for port in PORTS[version]:
        for _ in range(10):
            conn = NSConnection.connectionWithRegisteredName_host_(port, None)
            if conn:
                return conn.rootProxy(), port
            time.sleep(1)
    return None, None


def main():
    version, script = sys.argv[1], sys.argv[2]
    app, port = connect(version)
    if app is None:
        print("no NSConnection to Glyphs %s (tried %s). Is it running? Fallback: paste the script into Window > Macro Panel." % (version, PORTS[version]))
        sys.exit(2)
    print("connected to %s (%s)" % (port, app.versionString()))
    code = open(script, encoding="utf-8").read()
    out = StdOut.alloc().init()
    app.scriptingHandler().runMacroString_stdOut_(code, out)
    sys.exit(1 if "FAIL" in out.text else 0)


if __name__ == "__main__":
    main()
