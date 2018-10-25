#!/bin/bash

# Python virtual environment directory: packenv variable in my_config.sh
source my_config.sh;
# Ensure the success of importing procedure
if [ -z ${packenv} ];
then
  printf "Please set in ""my_config.sh"" the path to bot python virtual environment\n\nExample:\npackenv=""path/to/virtual/env""\n";
  exit;
fi

# Merge, push, build and publish package to pypi.org
bash merge_and_push.sh;
$packenv/python setup.py sdist bdist_wheel;
$packenv/twine upload --skip-existing dist/*;
