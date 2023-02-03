#!/bin/bash

# Get current directory
this_script_directory=$(cd "$(dirname "$0")" && pwd)
packenv="";

# Python virtual environment directory: packenv variable in my_config.sh
source "$this_script_directory"/my_config.sh;

# Ensure the success of importing procedure
if [ -z "${packenv}" ];
then
  printf "Please set in ""my_config.sh"" the path to bot python virtual environment\n\nExample:\npackenv=""path/to/virtual/env""\n";
  exit;
fi

# Push, build and publish package to pypi.org
bash "$this_script_directory"/push_to_remotes.sh;
rm -rf "$this_script_directory/build";
rm -rf "$this_script_directory/dist";
rm -rf "$this_script_directory/davtelepot.egg-info";
"$packenv"/python setup.py sdist;
"$packenv"/pip wheel --no-index --no-deps --wheel-dir dist dist/*.tar.gz;
"$packenv"/twine upload --skip-existing dist/*;
