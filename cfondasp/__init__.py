#
# This file is part of cfondasp.
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
#

"""Top-level package for cfond-asp."""

from .__version__ import (
    __author__,
    __author_email__,
    __copyright__,
    __description__,
    __license__,
    __title__,
    __url__,
    __version__,
)
from .utils.system_utils import get_pkg_root

ROOT_PATH = get_pkg_root()
VERSION = __version__
