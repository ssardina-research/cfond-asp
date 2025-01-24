# This file is part of cfondasp.
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
#

import os
from cpuinfo import get_cpu_info
import platform
import psutil
from pathlib import Path
from urllib.parse import urlparse
import datetime

def print_system_info():
    print("------------------------------------------------------------------------------")
    cpu_info = get_cpu_info()
    print(f"CPU Vendor:{cpu_info['vendor_id_raw']}")
    print(f"CPU:{cpu_info['brand_raw']}")
    print(f"CPU Speed Actual:{cpu_info['hz_actual_friendly']}")
    print(f"CPU Speed Advertised:{cpu_info['hz_advertised_friendly']}")
    print(f"Platform:{platform.system()}")
    print(f"Platform version:{platform.version()}")
    print(f"Platform release:{platform.release()}")
    print(f"Memory:{str(round(psutil.virtual_memory().total / (1024.0 **3)))} GB")
    print("------------------------------------------------------------------------------")

def get_pkg_root() -> Path:
    """
    Returns the root of the package folder
    :return: Root Path
    """
    import inspect

    # one way
    # loc: str = os.path.abspath(__file__)
    # p: Path = Path(loc)
    # root: Path = p.parents[1]   # one level up

    # another way...
    root = Path(os.path.dirname(inspect.getfile(inspect.currentframe()))).parent  # type: ignore
    return root

def get_now():
    return datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")

def remove_files(output_dir: str, prefix:str):
    for file in os.listdir(os.path.join(output_dir)):
        if prefix in file:
            os.remove(os.path.join(output_dir, file))

def is_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


if __name__ == "__main__":
    print_system_info()
