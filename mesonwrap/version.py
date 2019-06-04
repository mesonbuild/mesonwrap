from distutils import version
from typing import Tuple


def version_key(version_tuple: Tuple[str, int]):
    return (version.LooseVersion(version_tuple[0]), version_tuple[1])
