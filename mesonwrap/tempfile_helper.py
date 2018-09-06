# This code is borrowed from mesonbuild.mesonlib
# https://github.com/mesonbuild/meson/blob/master/mesonbuild/mesonlib.py

import os
import stat
import shutil
import time


def _make_tree_writable(topdir):
    # Ensure all files and directories under topdir are writable
    # (and readable) by owner.
    for d, _, files in os.walk(topdir):
        os.chmod(d, os.stat(d).st_mode | stat.S_IWRITE | stat.S_IREAD)
        for fname in files:
            fpath = os.path.join(d, fname)
            if os.path.isfile(fpath):
                mode = os.stat(fpath).st_mode | stat.S_IWRITE | stat.S_IREAD
                os.chmod(fpath, mode)


def windows_proof_rmtree(f):
    # On Windows if anyone is holding a file open you can't
    # delete it. As an example an anti virus scanner might
    # be scanning files you are trying to delete. The only
    # way to fix this is to try again and again.
    delays = [0.1, 0.1, 0.2, 0.2, 0.2, 0.5, 0.5, 1, 1, 1, 1, 2]
    # Start by making the tree wriable.
    _make_tree_writable(f)
    for d in delays:
        try:
            shutil.rmtree(f)
            return
        except FileNotFoundError:
            return
        except (OSError, PermissionError):
            time.sleep(d)
    # Try one last time and throw if it fails.
    shutil.rmtree(f)
