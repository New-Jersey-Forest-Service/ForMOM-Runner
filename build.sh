#!/bin/bash

# This script will build the program
#  1) copies /src/ into here
#  2) installs dependencies (from requirements.txt) into /src/
#  3) bundles everything as a zipapp

FINAL_NAME="ForMOM_Runner"

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR
# Checks for directory and makes it if not
[[ -d ./build/ ]] || mkdir build
cd ./build

# Step 1 - copy over src
echo
echo "[[ Copying /src/ ]]"

cp -R ../src/** ./src/


# Step 2 - install dependenecs
echo
echo "[[ Install Dependencies into /src/ ]]"

python3.8 -m pip install -r ../requirements.txt --target ./src/


# Step 3 - bundle everything
echo
echo "[[ Bundling with zipapp ]]"

python3.8 -m zipapp src --output $FINAL_NAME.pyz

