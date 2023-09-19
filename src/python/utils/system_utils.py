import os
from cpuinfo import get_cpu_info
import platform
import psutil
import imp
import sys

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


if __name__ == "__main__":
    print_system_info()
