#!/usr/bin/env python3
"""Interactive helper: store YOUR OWN NASA Earthdata Login credentials in ~/.netrc.

Run this yourself in a terminal. The password is read with getpass (not echoed,
not logged, not written anywhere except ~/.netrc with permissions 600).
This is the standard method NASA DAACs document for scripted downloads.

Free account: https://urs.earthdata.nasa.gov/users/new
"""
import getpass
import os
import stat
import sys

HOST = "urs.earthdata.nasa.gov"
path = os.path.expanduser("~/.netrc")

print("NASA Earthdata Login -> ~/.netrc  (host: %s)" % HOST)
user = input("Earthdata username: ").strip()
pw = getpass.getpass("Earthdata password (hidden): ")
if not user or not pw:
    sys.exit("Username and password are required; nothing written.")

lines = []
if os.path.exists(path):
    with open(path) as f:
        # drop any previous entry for the same host (single-line form)
        lines = [l for l in f.read().splitlines() if HOST not in l]
lines.append("machine %s login %s password %s" % (HOST, user, pw))
with open(path, "w") as f:
    f.write("\n".join(lines) + "\n")
os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
print("Saved. ~/.netrc permissions set to 600. You can close this tab.")
