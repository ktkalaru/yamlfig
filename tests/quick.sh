#!/bin/bash

if [ -z "$1" ]; then
    echo "$0 <testdir>"
    echo ''
    echo "Run a quick test of program functionality, creating the given"
    echo "directory, and conducting the test within it."
    echo ''
    echo "This quick test runs through the quick-start scenario from the"
    echo "documentation."
    echo ''
    exit 1
fi

set -e

testdir="$1"
SERVERYAML="quickstart_server.yaml"
SHAREDFILE="quickstart_shared_file.txt"
SERVERPY="quickstart_server.py"

if [ \! -e "$testdir" ]; then
    (set -x; mkdir $testdir)
fi

cd $testdir

echo "+ cat > $SERVERYAML"
cat > $SERVERYAML <<EOF
name: Simple Single-File Server
server:
  port: 81
file_path: '$SHAREDFILE'
users:
- alice
- bob
- carol
EOF

echo "+ cat > $SHAREDFILE"
cat > $SHAREDFILE <<EOF
This is a test file.
EOF

echo "+ cat > $SERVERPY"
cat > $SERVERPY <<EOF
#!/usr/bin/env python

from __future__ import print_function
import sys
from yamlfig import YamlConfigParser, test

# Construct a parser for the server config file
confp = YamlConfigParser()
confp.add_rule('name', path_type=str)
confp.add_rule('description', optional=True)
confp.add_rule('server.addr', path_type=str, default='127.0.0.1', test=test.is_ipv4_address)
confp.add_rule('server.port', path_type=int, test=test.is_interval(1, 65535, include_upper=True))
confp.add_rule('file_path', path_type=str, test=test.is_file_path('exists', 'isfile'))
confp.add_rule('users', path_type=list)
confp.add_rule('users.*', test=test.is_regex('^[a-z][a-z0-9]*$'))

# Parse the config file
conf = confp.parse_file(sys.argv[1])

# Retrieve values from the conf object
print('conf.name = {0}'.format(repr(conf.name)))
print('conf.description = {0}'.format(repr(conf.description)))
print('conf.server.addr = {0}'.format(repr(conf.server.addr)))
print('conf.server.port = {0}'.format(repr(conf.server.port)))
print('conf.file_path = {0}'.format(repr(conf.file_path)))
for idx in conf.users:
  print('conf.users[{0}] = {1}'.format(idx, repr(conf.users[idx])))

EOF

(set -x; chmod 755 $SERVERPY)
(set -x; ./$SERVERPY $SERVERYAML)
