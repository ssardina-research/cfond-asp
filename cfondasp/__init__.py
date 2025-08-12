#
# This file is part of cfond-asp.
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
#

"""Top-level package for cfond-asp."""
from importlib.metadata import version
from .utils.system_utils import get_pkg_root

try:
    # this requires the package to be installed!
    from importlib.metadata import version, PackageNotFoundError
    VERSION = version("cfond-asp")
except PackageNotFoundError:
    VERSION = "dev"  # fallback version - running with python -m lzvcup

ROOT_PATH = get_pkg_root()
