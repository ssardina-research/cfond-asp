#
# Copyright 2023-2025 Sebastian Sardina & Nitin Yadav
#
# ------------------------------
#
# This file is part of cfond-asp.
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.
import argparse
from pathlib import Path
import coloredlogs
import logging
import os
import sys
import shutil
from timeit import default_timer as timer

from cfondasp import VERSION
from cfondasp.base.config import PYTHON_MINOR_VERSION
from cfondasp.checker.verify import verify

logger: logging.Logger = None


def main():
    """Main function to run the planner. Entry point of the program."""
    # set logger
    logger = logging.getLogger(__name__)
    coloredlogs.install(level=logging.DEBUG)

    # CLI options
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=f"CFOND-ASP Verifier: A FOND verifier for strong cyclic solution - Version: {VERSION}"
    )
    parser.add_argument(
        "output_dir",
        help="location of output folder (Default: %(default)s).",
        type=str,
        default="./output",
    )

    args = parser.parse_args()
    args.output_dir = os.path.abspath(args.output_dir)
    print(args)

    # 1. perform necessary checks before starting...

    # check python version
    if sys.version_info[0] < 3 or sys.version_info[1] < PYTHON_MINOR_VERSION:
        logger.error(f"Python version sould be at least 3.{PYTHON_MINOR_VERSION}")
        sys.exit(1)


    # create a fresh output folder
    if not os.path.exists(args.output_dir):
        logger.error(f"Output folder does not exist.")
        sys.exit(1)

    # 2. All good to go. Next, build a whole FONDProblem object with all the info needed
    start = timer()

    # 3. Run the requested mode
    verify(args.output_dir)

    # 4. Done! Wrap up and summary info
    end = timer()
    total_time = end - start
    logger.debug(f"Output folder: {args.output_dir}")
    logger.warning(f"Time taken: {total_time}")


# run all code (marcos' funny comment)

if __name__ == "__main__":
    main()
