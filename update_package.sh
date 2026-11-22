#!/bin/bash
set -e

# Get current directory
this_script_directory=$(cd "$(dirname "$0")" && pwd)

# Python virtual environment directory
packenv=""

# shellcheck disable=SC1091
source "${this_script_directory}/my_config.sh"

# Validate configuration
if [ -z "$packenv" ]; then
    printf 'Please set "packenv" in my_config.sh\n\nExample:\npackenv="path/to/virtual/env"\n'
    exit 1
fi

# Validate virtual environment
if [ ! -x "${packenv}/bin/python" ]; then
    echo "Python executable not found: ${packenv}/bin/python"
    exit 1
fi

python="${packenv}/bin/python"
twine="${packenv}/bin/twine"

if [ ! -x "$twine" ]; then
    echo "Twine not found. Install it with: ${python} -m pip install twine"
    exit 1
fi

# Push changes to remotes
bash "$this_script_directory/push_to_remotes.sh"

# Clean previous builds
rm -rf 
    "$this_script_directory/build" 
    "$this_script_directory/dist" 
    "$this_script_directory/davtelepot.egg-info"

cd "$this_script_directory" || exit 1

# Build source distribution
"${python}" setup.py sdist

# Build wheel using locally installed build dependencies
"${python}" -m pip wheel \
    --no-index \
    --no-deps \
    --no-build-isolation \
    --wheel-dir dist \
    dist/*.tar.gz

# Publish to PyPI
"${twine}" upload --skip-existing dist/*
