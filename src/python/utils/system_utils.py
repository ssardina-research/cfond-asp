import os
from cpuinfo import get_cpu_info
import platform
import psutil
from pathlib import Path
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

def get_root() -> Path:
    """
    Returns the root of the source folder
    :return: Root Path
    """
    loc: str =  os.path.abspath(__file__)
    p: Path = Path(loc)
    root: Path = p.parents[2]
    return root

def get_now():
    return datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")


if __name__ == "__main__":
    print_system_info()
