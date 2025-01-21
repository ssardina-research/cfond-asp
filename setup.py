import glob
from setuptools import setup, find_packages

import os

here = os.path.abspath(os.path.dirname(__file__))
about = {}
with open(os.path.join(here, "cfondasp", "__version__.py"), "r") as f:
    exec(f.read(), about)

with open("README.md", "r") as fh:
    long_description = fh.read()
    long_description = long_description.replace("> [!IMPORTANT]", "### IMPORTANT")
    long_description = long_description.replace("> [!TIP]", "### TIP")
    long_description = long_description.replace("> [!NOTE]", "### NOTE")
    long_description = long_description.replace("> [!WARNING]", "### WARNING")

install_requires = [
    "async-timeout",
    "cffi",
    "clingo",
    "cmake",
    "coloredlogs",
    "Cython",
    "fond-utils",
    "graphviz",
    "humanfriendly",
    "lxml",
    "markdown-it-py",
    "mdurl",
    "networkit",
    "numpy",
    "psutil",
    "py-cpuinfo",
    "pddl",
    "Pygments",
    "rich",
    "scipy",
]

setup(
    name=about["__title__"],
    description=about["__description__"],
    version=about["__version__"],
    author=about["__author__"],
    url=about["__url__"],
    author_email=about["__author_email__"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    license=about["__license__"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.10",
    packages=find_packages(include=["cfondasp*"]),
    include_package_data=True,
    data_files=[
        ("cfondasp/asp/", glob.glob("cfondasp/asp/**/*.lp", recursive=True)),
    ],
    install_requires=install_requires,
    entry_points={
        "console_scripts": ["cfond-asp=cfondasp.__main__:main","cfond-asp-verify=cfondasp.__verify__:main"]
    },
    zip_safe=False,
)
