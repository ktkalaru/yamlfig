"""Verify the structure of YAML-formatted configuration files.

The yamlfig package provides developers with a framework for defining
rules that test and verify a config file's structure.  Those rules are
captured in a parser object which can be applied to YAML-based config
files to validate them.

In particular, this module enables a developer to:

  - define which fields are required, optional, or will be assigned
    default values if omitted;

  - declare types for those fields (e.g., str, int, date, dict, list,
    etc.);

  - run arbitrary functions to test the values in each field (e.g.,
    regular expressions matches or file-path-existence checks).

After a config file is parsed, validated, and accepted, the returned
object can be used to access the field values with some confidence
that they exist, are of the expected type, and have whatever other
properties the rules established.  If a config file is rejected, an
error explaining the violated rule is raised.

This package was inspired by the similar capability that argparse
brought to command-line argument parsing.

"""

from __future__ import absolute_import

from .__version__ import __version__

from .base import *
from . import test
