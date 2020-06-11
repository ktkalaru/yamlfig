#!/bin/sh
############################################################################

# Simple script for linting, testing, and building package
# 
# Actions performed:
#   pylint: run pylint for static code checking
#   pydocstyle: run pep257 checks of docstring conventions
#   pycodestyle: run pep8 checks of code conventions
#   tox: run battery of tests using pytest and tox
#   dist: run setup.py to build source and wheel packages
#

NAME=yamlfig
VERSION=$(grep __version__ src/${NAME}/__version__.py | cut -d "'" -f 2)

PYLINT_TARGETS=("setup.py" "src/${NAME}" "tests")

PYCODESTYLE_TARGETS=("setup.py" "src/${NAME}" "tests")

PYDOCSTYLE_ARGS="--match='.*.py'"
PYDOCSTYLE_TARGETS=("setup.py" "src/${NAME}" "tests")

TOX_LOCAL_ENVLIST="py27,py36"
TOX_SERVER_ENVLIST="py27,py35,py37"

DIST_ARGS='setup.py sdist bdist_wheel --universal'

PYTHON_BIN=python3

LOCAL_ACTIONS=(pylint pycodestyle pydocstyle tox-local dist)
SERVER_ACTIONS=(pylint pycodestyle pydocstyle tox-server dist)

############################################################################

function usage {
    echo "$0 (local|server)"
    echo ''
    echo 'Run the battery of build test programs, culminating in building'
    echo 'source and binary packages if the tests all pass.'
    echo ''
    echo 'Specify on of the following build environments:'
    echo '  local: run tests available on standard build environment'
    echo '  server: run full range of tests available on build server'
    echo ''
}

if [ -z "$1" ]; then
    usage
    exit 1
elif [ "$1" == "local" ]; then
    actions=("${LOCAL_ACTIONS[*]}")
elif [ "$1" == "server" ]; then
    actions=("${SERVER_ACTIONS[*]}")
else
    usage
    exit 1
fi

set -e

for action in ${actions[*]}; do
    if [ $action == 'pylint' ]; then
	echo "[ $action ]"
	for target in ${PYLINT_TARGETS[*]}; do
	    (set -x; pylint $target)
	done
    elif [ $action == 'pycodestyle' ]; then
	echo "[ $action ]"
	for target in ${PYCODESTYLE_TARGETS[*]}; do
	    (set -x; pycodestyle $target)
	done
    elif [ $action == 'pydocstyle' ]; then
	echo "[ $action ]"
	for target in ${PYDOCSTYLE_TARGETS[*]}; do
	    (set -x; pydocstyle $PYDOCSTYLE_ARGS $target)
	done
    elif [ $action == 'tox-local' ]; then
	echo "[ $action ]"
	(set -x; tox -e "${TOX_LOCAL_ENVLIST}")
    elif [ $action == 'tox-server' ]; then
	echo "[ $action ]"
	(set -x; tox -e "${TOX_SERVER_ENVLIST}")
    elif [ $action == 'dist' ]; then
	echo "[ $action ]"
	(set -x; $PYTHON_BIN $DIST_ARGS)
    else
	echo "Unhandled action: $action"
	exit 1
    fi
done

echo ''
echo "${NAME}-${VERSION}: ${actions[*]} -- successful"
echo ''
