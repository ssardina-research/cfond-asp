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

ROOT_PATH = get_pkg_root()
VERSION = version("cfond-asp")
