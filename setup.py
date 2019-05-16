"""Setup."""

import codecs
import os
import re
import setuptools
import sys

if sys.version_info < (3, 5):
    raise RuntimeError("Python3.5+ is needed to run async code")

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """Read file in `part.part.part.part.ext`.

    Start from `here` and follow the path given by `*parts`
    """
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_information(info, *file_path_parts):
    """Read information in file."""
    version_file = read(*file_path_parts)
    version_match = re.search(
        r"^__{info}__ = ['\"]([^'\"]*)['\"]".format(
            info=info
        ),
        version_file,
        re.M
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

setuptools.setup(
    name='davtelepot',
    version=find_information("version", "davtelepot", "__init__.py"),
    author=find_information("author", "davtelepot", "__init__.py"),
    author_email=find_information("email", "davtelepot", "__init__.py"),
    description=(
        "telepot.aio.Bot convenient subclass, featuring dataset-powered "
        "SQLite."
    ),
    license=find_information("license", "davtelepot", "__init__.py"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gogs.davte.it/davte/davtelepot",
    packages=setuptools.find_packages(),
    platforms=['any'],
    install_requires=[
        'aiohttp>=3.4.4',
        'bs4>=0.0.1',
        'dataset>=1.1.0',
        'davteutil',
        'telepot>=12.7'
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        (
            "License :: OSI Approved :: GNU Lesser General Public License "
            "v3 (LGPLv3)"
        ),
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Communications :: Chat",
    ],
    keywords='telepot telegram bot python wrapper',
    include_package_data=True,
)
