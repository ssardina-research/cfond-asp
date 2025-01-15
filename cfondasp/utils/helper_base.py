# This file is part of cfondasp.
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
#

"""Helper functions."""
from pathlib import Path
from urllib.parse import urlparse


def _get_current_path() -> Path:
    """Get the path to the file where the function is called."""
    import inspect
    import os

    return Path(os.path.dirname(inspect.getfile(inspect.currentframe()))).parent  # type: ignore


def is_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
