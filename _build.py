#!/usr/bin/env python3
"""Simple script for linting, testing, and building package

Actions performed:
  pylint: run pylint for static code checking
  pydocstyle: run pep257 checks of docstring conventions
  pycodestyle: run pep8 checks of code conventions
  tox: run battery of tests using pytest and tox
  dist: run setup.py to build source and wheel packages

Specify a build environment to run the battery of build test programs,
culminating in building source and binary packages if the tests all
pass.

"""

import argparse
import subprocess

class RawDefFormat(
        argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    """Help format that respects the raw formatting and prints the defaults."""

############################################################################
# Configuration Variables
name = 'yamlfig'
dist_args = 'setup.py sdist bdist_wheel --universal'

pylint_targets = ['setup.py', f'src/{name}', 'tests/*.py']
pycodestyle_targets = ['setup.py', f'src/{name}', 'tests']
pydocstyle_args = '--match=".*.py"'
pydocstyle_targets = ['setup.py', f'src/{name}', 'tests']
python_bin = 'python3'

build_envs = {
    'local': {
        'actions': ['pylint', 'pycodestyle', 'pydocstyle', 'tox', 'dist'],
        'tox_envlist': 'py27,py36'
    }
}

############################################################################

def pxcmd(cmdline):
    """Print and execute the command-line."""
    print(f'\n+ {cmdline}')
    try:
        subprocess.check_call(cmdline, shell=True)
    except subprocess.CalledProcessError as exc:
        print(f'BUILD STOPPED: {exc}')
        exit(1)

def main(argv=None):
    """Build and run tests based on command-line arguments."""
    argp = argparse.ArgumentParser(formatter_class=RawDefFormat)
    argp.description = __doc__
    argp.add_argument(
        'buildenv', choices=build_envs.keys(),
        help='one or more configured build environments to choose among')
    args = argp.parse_args(args=argv)
    build_env = build_envs[args.buildenv]
    actions = build_env['actions']
    for action in actions:
        print(f'\n[{action}]')
        if action == 'pylint':
            for target in pylint_targets:
                pxcmd(f'pylint {target}')
        elif action == 'pycodestyle':
            for target in pycodestyle_targets:
                pxcmd(f'pycodestyle {target}')
        elif action == 'pydocstyle':
            for target in pydocstyle_targets:
                pxcmd(f'pydocstyle {pydocstyle_args} {target}')
        elif action == 'tox':
            tox_envlist = build_env['tox_envlist']
            pxcmd(f'tox -e {tox_envlist}')
        elif action == 'dist':
            pxcmd(f'{python_bin} {dist_args}')
        else:
            assert False, f'unhandled action: "{action}"'

    print(f'BUILD COMPLETED: {name} ({" ".join(actions)})')

if __name__ == '__main__':
    main()
