The **yamlfig** package provides developers with a framework for
defining rules that test and verify a config file's structure.  Those
rules are captured in a parser object which can be applied to
YAML-based config files to validate them.

In particular, this module enables a developer to:

  - define which fields are required, optional, or will be assigned
    default values if omitted;

  - declare types for those fields (e.g., `str`, `int`, `date`, `dict`,
    `list`, etc.);

  - run arbitrary functions to test the values in each field (e.g.,
    regular expressions matches or file-path-existence checks).

After a config file is parsed, validated, and accepted, the returned
object can be used to access the field values with some confidence
that they exist, are of the expected type, and have whatever other
properties the rules established.  If a config file is rejected, an
error explaining the violated rule is raised.

This package was inspired by the similar capability that `argparse`
brought to command-line argument parsing.

## Contents

  * [Getting Started](#getting-started)
    - [Installation](#installation)
    - [Website and Repository](#website-and-repository)
    - [Example Usage](#example-usage)
    - [Walk-through](#walk-through)
  * [Details](#details)
    - [Basic Usage](#basic-usage)
    - [Fields, Paths, and Structure](#fields-paths-and-structure)
    - [Handling Parsed Objects](#handling-parsed-objects)  
    - [Optional, Default, and No-Follow Rules](#optional-default-and-no-follow-rules)
    - [Path Type Checking](#path-type-checking)
    - [Rule Test Functions](#rule-test-functions)
    - [Warnings and Caveats](#warnings-and-caveats)
  * [Next Steps](#next-steps)
    - [Future Work](#future-work)
    - [Support and Collaboration](#support-and-collaboration)


## Getting Started

### Installation

  `pip install yamlfig`

### Website and Repository

The Python package is hosted on PyPI:

  * https://pypi.com/project/yamlfig

The source code, documentation, and issue tracker is hosted on GitHub:

  * https://github.com/ktkalaru/yamlfig

### Example Usage

As an example for when a developer might use **yamlfig**, consider
developing a server that binds to an address and port.  When any of a
list of authorized users connects, it displays the server's name and
the contents of a file.  The following YAML file could act as the
config file for such a server:

  `$ cat > quickstart_server.yaml`

```yaml
name: Simple Single-File Server
server:
  port: 81
file_path: 'quickstart_shared_file.txt'
users:
- alice
- bob
- carol
```

The following script uses the **yamlfig** package to construct a
parser for this example server.  It instantiates a parser object and
adds a set of rules that establish which fields and structures should
be in a server's config file.  Those rules establish what form those
fields must take and what to do if they are missing.  It then invokes
this parser on a config file passed as a command line argument.  Where
an actual server script would then use those values to spin up a
server, this script just demonstrates that the values can be accessed
from the parsed object by printing them:

  `$ cat > quickstart_server.py`

```python
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
```

When we execute this server script on the above config file, it prints
the following values:

  `$ python quickstart_server.py quickstart_server.yaml`

```
conf.name = 'Simple Single-File Server'
conf.description = None
conf.server.addr = '127.0.0.1'
conf.server.port = 81
conf.file_path = 'quickstart_shared_file.txt'
conf.users[0] = 'alice'
conf.users[1] = 'bob'
conf.users[2] = 'carol'
```

Note how the fields and values printed came not only from the config
file but also from the rules.  Fields marked as optional or taking a
default are present even though they were not in the config file.
Also note how the values have the type and form required by the rules
(e.g., an integer within a given interval, a string in IPv4
dotted-quad notation, and a list of usernames that all match a regular
expression).

### Walk-through

In this example, the config file specified a ``name`` to display, a
``port`` to listen on within a ``server`` block, a ``file_path`` to a
file to share, and the list of accounts of authorized ``users``.  The
rules added to the `confp` parser ensure that those rules exist; they
also define rules for some paths not in the config file and configured
as ``optional`` or taking a ``default`` value:

  - a `description` field, if provided, would be displayed to the user, but
    it is optional;

  - an `addr` field within the `server` block that, if provided, would
    set the binding IP address, but that takes a default of
    `127.0.0.1` if omitted.

Additionally, the `confp` parser verifies that the values present in
the config file are suitable for our intended use.  Some of the values
are type-checked or otherwise validated:

   - the `addr` field, if provided, will be tested to confirm that it
     has the format of an IPv4 address (i.e., a string in dotted-quad
     notation);

   - the `port` field will have its type checked to ensure it is an
     `int`, and its value will be tested to confirm that in the range
     1 to 65535;

   - the `file_path` will be interpreted as a path to a filesystem
     object, and that object will be tested to confirm it exists and
     is a file (rather than a directory);

   - all the account names in the `users` list will be tested against
     a regular expression to confirm they match the format of accounts
     on this particular system (i.e., they start with a lowercase
     letters followed by zero or more digits or lowercase letters).

Once the `confp` parser is constructed and configured, its
`parse_file` method is called on the config-file path given on the
command line, and it returns a parsed `conf` object.  To demonstrate
that the `conf` object contains all the fields and values from the
config file merged with the optional fields and defaults from the
parser rules, it prints those fields and values.

The values in the `conf` object returned by `parse_file` have also
been type-checked and tested.  Had the fields and values in the config
file not conformed to the rules of the `confp` parser, a `ParseError`
exception would have been raised.  Some examples:

  - If the `name` field were omitted:

    `ParseError: quickstart_server.yaml: "name" is missing`

  - If the `server` block contained a field called `the_ip_address`
    that did not match any of the parser's rules:

    `ParseError: quickstart_server.yaml: "server.the_ip_address"
    unexpected by parser`

  - If the `port` field of the `server` block contained the string
    `"eighty-one"` rather than the integer `81`:

    `ParseError: quickstart_server.yaml: "server.port" has type str
    not type int`

  - If the `addr` field were present in the server block and had
    the value `452.34.256.193`:

    `ParseError: quickstart_server.yaml: "server.addr" failed test:
    1st octet of "452.34.256.193" exceeds 255`

  - If the `file_path` field had been the path to an existing
    directory named `some_directory` instead of the path to an
    existing file:

    `ParseError: quickstart_server.yaml: "file_path" failed test:
    "some_directory" is not a file`

  - If the 3rd value of the `users` list been the display name `Carol
    C.` instead of the username `carol` (and noting zero-based
    indexing):

    `ParseError: quickstart_server.yaml: "users.2" failed test: "Carol
    C." does not match /^[a-z][a-z0-9]*$/`

The presence of such errors in the config file would have stopped
execution and provided a relatively informative explanation of which
rule failed and why.  Because none of these errors were raised, a
developer has some assurance that the structure and values in the
`conf` object meets their expectations.

Just as important as what happened in this example above is *what
didn't happen*.  When the ``read_file`` function returned the `conf`
object, it didn't raise a `ParseError` exception.  Since it executed
successfully, we know that all the parser assertions hold about which
fields must exist and what formats they take; the remaining code does
not need to perform such checks and error handling itself.


## Details

What **yamlfig** provides beyond a standard YAML parser is validation,
specifically verification that a config file conforms to the various
rules established for it.  In this section, we introduce and describe
these rules, and the various constraints that can be placed on
a config file's structure and values.

### Basic Usage

The typical steps when using **yamlfig** are:
  
  1. instantiate a `YamlConfigParser` object, which we usually call
     `confp`,
  
  2. configure it by using `add_rule` to add rules for each field we
     intend to control through a config file,
  
  3. invoke `parse_file` on a config file which either raises a
     `ParseError` or returns a `YamlConfig` object, usually called
     `conf`, and

  4. use that `YamlConfig` in subsequent code, confident that its
     structure and values have already been validated.

The following script illustrates this typical pattern by using
**yamlfig**.  For the sake of the example, let's say we need a config
file to drive how often a loop is run, which of two functions is
called by the loop, and what parameter is passed to that function:

  `$ cat basic_usage.py`

```python
import sys

from yamlfig import YamlConfigParser

# 1. Instantiate a YamlConfigParser object (confp)
confp = YamlConfigParser()

# 2. Configure the parser by adding rules for each field
confp.add_rule('loop_count')
confp.add_rule('do_special_function')
confp.add_rule('function_parameter')

# 3. Invoke the parser on a config file (provided as an argument)
conf = confp.parse_file(sys.argv[1])

# 4. Use the YamlConfig object in subsequent code
for loop_index in range(conf.loop_count):
  if conf.do_special_function:
    special_function(conf.function_parameter)
  else:
    regular_function(conf.function_parameter)
```

One config file would cause the script to produce one behavior:

  `$ cat basic_config_1.yaml`

```yaml
loop_count: 7
do_special_function: yes
function_parameter: "a meerkat"
```

Running the script on `basic_config_1.yaml` would cause
`special_function` to be invoked 7 times, each with the parameter `"a
meerkat"`.

Another config file would cause the script to produce a different behavior:

  `$ cat basic_config_2.yaml`

```yaml
loop_count: 3
do_special_function: no
function_parameter: a pony
```

Running the script on `basic_config_2.yaml` would cause
`regular_function` to be invoked 3 times, each with the parameter `"a
pony"`.

Just as important is understanding the behavior of the script on a bad
config file.  The following config file is missing one of the three
required fields:

  `$ cat basic_config_bad.yaml`

```yaml
loop_count: 3
function_parameter: 'a unicorn'
```

Running the script on `basic_config_bad.yaml` exits unsuccessfully and
prints an exception:

```
Traceback (most recent call last):
  File "basic_usage.py", line 22, in <module>
    conf = confp.parse_file(sys.argv[1])
  [...]
yamlfig.base.ParseError: basic_config_bad.yaml: "do_special_function" is missing
```

The error is raised within the `confp.parse_file` function.  All
verification and validation occurs as part of that function called in
step 3 of the pattern, so if it return successfully, the `YamlConfig`
object conforms with the parser rules.

### Fields, Paths, and Structure

The fundamental thing that **yamlfig** rules do is establish which
fields should be in a config file and which fields should not.

#### Test that a field exists

```python
confp.add_rule('dirname')
```

The first argument to `add_rule` is the `rule_path`.  Every rule added
to a `confp` object must have one, and&mdash;unless additional
modifiers make the field optional or take a default value&mdash;it is
an existence requirement for the field.  Given the rule above, any
config file must contain a line such as:

```yaml
dirname: /var/share/SomeApp/SharedDir
```

A config file without a `dirname` field would generate a parse error.

#### Test that a path exists

Part of YAML's descriptive power comes from its ability to encode
nested structures, like maps and lists, and **yamlfig** rules can
describe constraints on that structure:

```python
confp.add_rule('server.storage.dirname')
```

Rules use the `'.'` character
to delimit fields within a nested structure.  The rule above expects
there to be a `server` block, within which is contained a `storage`
block, within which there is a `dirname` field.  The following config
would satisfy such a rule:

```yaml
server:
  storage:
    dirname: /var/share/SomeApp/SharedDir
```

Such a rule path implicitly includes existence requirements for
`server` and `server.storage`.  The existence of those paths would not
need to be explicitly required through separate rules, unless we
wanted to modify them (e.g., by making them optional or take defaults
as described in a [later
section](#optional-default-and-no-follow-rules).

#### Test that a block has a specific substructure

In this example, we need a config file to describe how a server's
local storage cache is configured (i.e., where it is on the
filesystem, how big it can grow, and what permissions the cache files
have).

```python
confp.add_rule('server.storage.dirname')
confp.add_rule('server.storage.maxsize')
confp.add_rule('server.storage.umask')
```

In combination, these three rules describe the structure that the
`server.storage` block must have (i.e., three fields with the names
`dirname`, `maxsize`, and `umask`).

The following config file would be accepted by this parser:

```yaml
server:
  storage:
    dirname: /var/share/SomeApp/SharedDir
    maxsize: 10GB
    umask: 0644
```

#### Test that a field or path *does not* exist

Any field or path for which there is no matching rule will raise a
parse error.  In a sense, the **yamlfig** field-existence validation
is deny-by-default.  We do not need to do anything specific to assert
that a field does not exist; just don't add an existence requirement.

#### Test that a block contains fields without specifying which fields by using wildcards

A rule path can contain wildcards.  For the sake of this example, we
need a config file to specify upload paths for each of one or more
users.  A `server.upload_paths` block will map from username to their
corresponding upload directory, as in the following example:

```yaml
server:
  upload_paths:
    alice:   /home/alice/uploads
    bob:     /home/bob/public
```

Since we do not want to hardcode the usernames in the parser, we can
use a wildcard rule to accept one or more fields within a block
without specifying the specific field names:

```python
confp.add_rule('server.upload_paths.*')
```

Such a rule asserts that the `server.upload_paths` block contains
non-empty substructure (i.e., it is a block), but not the specific
field names within the substructure.  In the above example config
file, the wildcard woudl match both `alice` and `bob`, even though
neither are explicitly listed field paths.

A new user could be added with their own upload path, and the same
parser would accept the config file:

```yaml
server:
  upload_paths:
    alice:   /home/alice/uploads
    bob:     /home/bob/public
    carol:   /home/carol/tmp
```

Note that a wildcard rule must match *one or more* fields, not zero.
If the `server.upload_paths` block were empty, the config file would
raise an error: `"server.upload_paths" must contain at least one
field`.  A [later
segment](#default-block-and-optional-wildcarded-path-recognize-zero-or-more)
describes how the `optional` and `default` flags can be used with
wildcards to implement a zero-or-more match.

Also note that *partial* wildcard matches are not currently supported.
A path like `server.upload_paths.user-*` intending to accept fields
like `user-alice` and `user-bob` would instead raise an error.  As
described in a [different later
segment](#writing-our-own-test-functions), one way to implement such a
check would be to write a function that tests every field within a
block against a regular expression, and then specify that function as
a test function for the `server.upload_paths` block.

#### Wildcard fields can have substructure and rules can enforce matching substructure

For the sake of this example, a server hosts one or more projects,
each of which has a directory of static web pages associated with it,
and a backend database.  Our configuration file maps from one or more
arbitrary project names (e.g., `ProjectX` and `meerkat_works`) to
blocks that contain precisely three datapoints (1) a path to a
directory of webpages, (2) a path or URL to a database, and (3) the
type of the database (e.g., `sqlite`, `mysql`, or `mongodb`).

The following config file gives an example of this structure:

```yaml
projects:
  ProjectX:
    webpath: /home/alice/projx/html
    dbpath:  /home/alice/projx/project.db
    dbtype: sqlite
  meerkat_works:
    webpath: /home/bob/public/meerkat/www
    dbpath:  mongodb://192.168.1.200:27017
    dbtype: mongodb
```

With **yamlfig**, we can specify wildcards on paths while still
requiring that any fields matching the wildcard have a required,
fixed-field substructure.  The following parser will accept one or
more blocks, each corresponding to a project name, but every one must
have the three required fields:

```python
confp.add_rule('projects.*.webpath')
confp.add_rule('projects.*.dbpath')
confp.add_rule('projects.*.dbtype')
```

These rules implicitly assert that the `projects` block exists and
contains one or more sub-blocks, with no restriction on their field
names.  The rules explicitly assert that each one of those sub-blocks
must contain exactly three fields: `webpath`, `dbpath`, and `dbtype`.
This parser would accept the example config file above.

If a project sub-block were missing one of the three required fields
or had an extra field, an error would have been raised.


#### Wildcards are also useful for accepting lists of values

YAML's nested structure supports not only the mappings described above
but also lists.  Technically, YAML offers a whole lot of different
nesting types (e.g., `omap`, `pairs`, etc.) but our python parser
represents them all as either `dict` or `list` objects, with mappings
represented as `dict` objects and lists as `lists`.  To most easily
and succinctly accommodate both mappings and lists, **yamlfig**
effectively treats lists as a very specific kind of mapping, where
each field is a list index and each value is the item in the list.

Consider a config file where a `users` block contains a list of one or
more authorized users:

```yaml
users:
- alice
- bob
- carol
```

The following rule would accept such a `users` block:

```python
confp.add_rule('users.*')
```

Note that the wildcard rule by itself just ensure that there are
subfields, not that they take the form of a list as opposed to a
mapping.  That same parser would accept a config file with a mapping:

```yaml
users:
  alice:  Alice A.
  bob:    Bob B.
  carol:  Carol C.
```

These two config files&mdash;the list version and the mapping
version&mdash;have very different structures, and a program would
likely be expecting one and not the other.  To ensure that a rule with
a wildcard matches only a list (and not a map) or only a map (and not
a list), we would need to use type checking, as described in a [later
segment](#ensure-that-a-path-contains-a-map-or-a-list), to assert that
the type of the block is either `list` or `dict` respectively.

Also note that when accessing list values parsed into a `conf` object,
we need to be aware of some difference in their behavior from that of
a standard python list, as described in the [Handling Parsed
Objects](#handling-parsed-objects) section.

#### Test that a list has exactly *n* elements

While not a typical occurrence, parser rules can be configured to
ensure that a list has a specific number of elements.  The following
rules would accept a list of length 2 by explicitly requiring fields
named `0` and `1`:

```python
confp.add_rule('network.route.0')
confp.add_rule('network.route.1')
```

For the sake of the example, perhaps the application must have two
network routes, a primary and a secondary.

As noted above, **yamlfig** treats lists as mappings from numeric
fields to values, so the parser would accept the following config:

```yaml
network:
  route:
  - 192.0.2.1
  - 198.51.100.1
```

As a side note, the same two rules would accept a config in which the
`route` block contained a mapping from numeric string fields (i.e.,
`"0"` and `"1"`) to the two IPv4 addresses.  As we keep stressing, the
rules simply treat lists as mappings from numeric fields to the list
elements.  To differentiate a list from a mapping, we would need to
use type checking, as described in a [later
segment](#ensure-that-a-path-contains-a-map-or-a-list)


### Handling Parsed Objects

As described in the [Basic Usage](#basic-usage) section, to parse a
config file, a parser's `parse_file` method would be called with the
name of the file:

```python
conf = confp.parse_file(conffile)
```

Assuming the parsing and validation succeeds, the `conf` object would
have type `YamlConfig` or `YamlConfigList`, depending on whether the
root-level YAML object in the config file is a mapping or a list.
Typically, a YAML-formatted config file will have a mapping as its
root-level structure, and so we will consider that common case first.

Throughout this section, assume that we have successfully parsed the
following config file into a `YamlConfig` object named `conf`:

```yaml
dirname: /var/share/SomeApp/SharedDir
server:
  projects:
    ProjectX:
      webpath: /home/alice/projx/html
      dbpath:  /home/alice/projx/project.db
      dbtype:  sqlite
    meerkat_works:
      webpath: /home/bob/public/meerkat/www
      dbpath:  mongodb://192.168.1.200:27017
      dbtype:  mongodb
users:
- alice
- bob
- carol
- dave
```

While the focus of this section is on accessing the `conf` object
after `confp` successfully parses and validates the config file, for
the sake of completeness, the following rules would configure a
parser that accepts this file:

```python
confp = YamlConfigParser()
confp.add_rule('dirname')
confp.add_rule('server.projects.*.webpath')
confp.add_rule('server.projects.*.dbpath')
confp.add_rule('server.projects.*.dbtype')
confp.add_rule('users.*')
```

#### Fields and paths can be accessed as attributes

Fields in a config file can be accessed as attributes of the
`YamlConfig` object.

```python
conf.dirname                # '/var/share/SomeApp/SharedDir'
```
    
If an attribute corresponds to a block in a config file, it will
return that block as a `YamlConfig` or `YamlConfigList` object.

```python
conf.server                 # <YamlConfig object at 0x[...]>
conf.users                  # <YamlConfigList object at 0x[...]>
```

As such, attributes can be strung together in a sequence:

```python
conf.server.projects.ProjectX.webpath      # '/home/alice/projx/html'
conf.server.projects.ProjectX.dbpath       # '/home/alice/projx/project.db'
conf.server.projects.ProjectX.dbtype       # 'sqlite'
```

```python
conf.server.projects.meerkat_works.dbtype  # 'mongodb'
```

Note that to be accessed as an attribute, a field must be a valid
Python attribute (e.g., must be a string, cannot start with a number,
etc.).

#### Fields and paths can be accessed via index lookups

A values stored in a `YamlConfig` object can also be accessed via
index lookup.

```python
conf.server.projects['ProjectX'].dbtype               # 'sqlite'
```

```python
proj = 'ProjectX'
conf.server.projects[proj].dbtype                     # 'sqlite'
````

````python
conf['server']['projects']['ProjectX']['dbtype']      # 'sqlite'
````

````python
path = ['server', 'projects', 'ProjectX', 'dbtype']
functools.reduce(lambda d, idx: d[idx], path, conf)   # 'sqlite'
````

#### List values can be accessed via index lookups

Index lookups must be used to access the elements of a `YamlConfigList`
since attributes cannot be numbers.

```python
conf.users[0]             # 'alice'
conf.users[1]             # 'bob'
conf.users[2]             # 'carol'
conf.users[3]             # 'carol'
```

```python
conf.users[-1]            # 'dave'
conf.users[-2]            # 'carol'
```

In a departure from standard python lists, a `YamlConfigList` object
will translate to or from a string representation of an index as
needed.

```python
conf.users["1"]           # 'bob'
conf.users['-2']          # 'carol'
```

Once again, this is to allow&mdash;as much as possible&mdash;lists to
be treated like mappings from the list indexes to the list elements.

#### Length checks can be used to determine the number of fields

As with `dict` and `list` objects, we can see how many elements are
in a `YamlConfig` and `YamlConfigList` object by querying their
length.

```python
len(conf)                                  # 3
len(conf.server)                           # 1
len(conf.server.projects)                  # 2
len(conf.server.projects.ProjectX)         # 3
len(conf.server.projects.meerkat_works)    # 3
len(conf.users)                            # 4
```

#### Iterators return field names for `YamlConfig` objects

Iterating on a `YamlConfig` object will return the field names
contained within the block, like what we would get from iterating on
a `dict` object:

```python
list(conf)                                 # ['dirname', 'server', 'users']
list(conf.server)                          # ['projects']
list(conf.server.projects)                 # ['ProjectX', 'meerkat_works']
list(conf.server.projects.ProjectX)        # ['webpath', 'dbpath', 'dbtype']
list(conf.server.projects.meerkat_works)   # ['webpath', 'dbpath', 'dbtype']
```

Note that the order in which `YamlConfig` fields are returned is **the
order the rules were added to the parser**, not the order in which the
rules appear in the config file.  When a single parser rule matches
multiple fields (i.e., a wildcard rule), the fields are returned in
arbitrary order.  Note however, that around Python 3.6 and Python 3.7,
they have started being returned in the order they appear in the
config file, likely due to `dict` objects beginning to return keys in
the order they were inserted.

#### Iterators return list indexes _not values_ for `YamlConfigList` objects

Iterating on a `YamlConfigList` object is **significantly different
from iterating on a python list**.  In particular, it will return the
list of index values as strings, **not the actual list values**:

```python
list(conf.users)                            # ['0','1','2','3']
```

As noted previously, a `YamlConfigList` treats lists less like lists
per-se and more like mappings from zero-based, sequential, numeric
indexes to values.  As such, its iterator returns field names that can
be used as indexes to look up values, not the values themselves.

This behavior is likely unexpected at first and arguably
controversial, but was chosen for greater overall simplicity.  A lot
of code can iterate over fields, descend into blocks, and so on much
more simply, when it does not need to treat `YamlConfigList` objects
as a special case, separate from `YamlConfig` objects.

To get the values rather than the indexes, we recommend list
comprehension:

```python
[conf.users[idx] for idx in conf.users]     # ['alice', 'bob', 'carol', 'dave']
```

Unlike the fields of a `YamlConfig`, indexes of a `YamlConfigList`
will be returned in a specific order: sequential and increasing from
a base of zero.

### Optional, Default, and No-Follow Rules

Having examined how to configure a parser to require certain fields
and structure, and how values will be represented in the parsed
object, we introduce ways to make rules optional, take default values,
and have the parser ignore their substructure.

#### A field flagged as optional can be omitted

When instantiating and adding a new rule, we can specify `optional=True`:

```python
confp.add_rule('name')
confp.add_rule('description', optional=True)
```

The above parser would require a `name` field but not a description
field, as in the following config file:

```yaml
name: Simple Single-File Server
```

The parser will accept the file, create a `description` field, and assign
it the value `None`.

```python
conf.name                           # 'Simple Single-File Server'
conf.description                    # None
```

A program acting on the `conf` object can assume that the optional
field exists, but it will have the value `None` if it was not present
in the config file (or if it was explicitly assigned the value `None`
since the two are treated as equivalent).

#### Optional fields can have required substructure

A rule representing a nested block can be marked optional and still
have substructure with required fields.  For the sake of example, a
server requires three files in order to encrypt its communications
using SSL.  If a `server.ssl` block is present in the config file,
those files must be provided, and the server will use SSL.  If the
block is omitted, the config file should still be accepted, but the
server will fall back to unencrypted communications.

The following parser is configured with an optional `server.ssl` block
that, if it exists, must have three specific fields:

```python
confp.add_rule('server.addr')
confp.add_rule('server.port')
confp.add_rule('server.ssl', optional=True)
confp.add_rule('server.ssl.key')
confp.add_rule('server.ssl.cert')
confp.add_rule('server.ssl.chain')
```

In the following config, the optional `ssl` block and its substructure
have been omitted:

```yaml
server:
  addr: 127.0.0.1
  port: 81
```

Since the block was not included, the `ssl` field is present in the
`conf` object but assigned a value of None.

```python
conf.server.ssl           # None
```

In the following config, the optional `ssl` block and its substructure
have been included:

```yaml
server:
  addr: 127.0.0.1
  port: 81
  ssl:
    key: /etc/ssl/privkey.pem
    cert: /etc/ssl/cert.pem
    chain: /etc/ssl/full_chain.pem
```

Since the block was included, its substructure was parsed and
validated.  The `conf` object includes the block and its substructure.

```python
conf.server.ssl               # <YamlConfig object at 0x[...]>
conf.server.ssl.key           # '/etc/ssl/privkey.pem'
conf.server.ssl.cert          # '/etc/ssl/cert.pem'
conf.server.ssl.chain         # '/etc/ssl/full_chain.pem'
```

The existence requirements on the substructure will only be checked
and enforced if the optional field is present.  In the following
config, the optional `ssl` block is present, but it is missing one of
its required fields:

```yaml
server:
  addr: 127.0.0.1
  port: 81
  ssl:
    key: /etc/ssl/privkey.pem
    # cert: /etc/ssl/cert.pem
    chain: /etc/ssl/full_chain.pem
```

When `parse_file` is invoked on this config file, a `ParseError` is
raised: `"server.ssl.cert" is missing`.


#### A default field will take a default value if omitted

When instantiating and adding a new rule, we can specify a `default`.

```python
confp.add_rule('server.addr', default='127.0.0.1')
confp.add_rule('server.port')
```

In the following config, the default rule has been omitted:

```yaml
server:
  port: 81
```

The parser will accept the file, create not only a `port` field but
also an `addr` field within the `server` block, and since the `addr`
field does not appear in the config, it will assign the default value
(`127.0.0.1`) to the field.

```python
conf.server.port            # 81
conf.server.addr            # '127.0.0.1'
```

#### Default substructure must still undergo validation

The following config rule will provide an entire server block if none
is specified in the config file:

```python
confp.add_rule('server', default={'addr': '127.0.0.1', port: 81})
```

Providing such structure is possible, but the above rule would
generate a `ParseError` unless it was accompanied by rules to accept
the `server.addr` and `server.port` paths.  With only the rule above,
a config file that triggered the default would raise a `ParseError`:
 `"server.addr" unexpected by parser`.

We need to add rules to prepare the parser for the substructure, as
in the following parser that accompanies the default rule with two
more:

```python
confp.add_rule('server', default={'addr': '127.0.0.1', port: 81})
confp.add_rule('server.addr')
confp.add_rule('server.port')
```

With these two additional rules, a config file will be accepted with
the default values if `server` is omitted, and it will require those
two values be present if a `server` block is present.  In both cases,
once parsing is successful, the program can assume that
`conf.server.addr` and `conf.server.port` exist.

If we really did not want to validate the fields of the default
substructure, rather than adding rules for the fields, we could mark
the block as no-follow as described in a [later
segment](#a-path-marked-no-follow-can-also-be-optional-or-take-defaults-but-not-both).

#### Fields cannot both be optional and take a default

The `optional` and `default` parameters to `add_rule` are mutually
exclusive; if both are specified, an error will be raised.
Essentially, `optional=True` acts like a default rule for which the
default value is `None`.  In fact, setting `optional=True` is the only
way for a missing field to be assigned a value of `None`, since
setting `default=None` is a no-op.  A value of `None` for `default`
actually signals that no default has been specified, so the field is
still required.

It is unclear what the semantics would even be for an optional rule
that also takes a default, so the pairing is just not allowed.

#### A default path *can* have optional subpaths and vice versa

In the following parser configuration, the `server` block takes a default,
while the `server.ssl` block is optional:

```python
confp.add_rule('server', default={'addr': '127.0.0.1', 'port': 81})
confp.add_rule('server.addr')
confp.add_rule('server.port')
confp.add_rule('server.ssl', optional=True)
confp.add_rule('server.ssl.key')
confp.add_rule('server.ssl.cert')
confp.add_rule('server.ssl.chain')
```

We can see what will happen in the following config, where the
`server` field is omitted.  Note that this config file uses the
convention that leaving a field value blank assigns it a value of
`None` (or `null` in YAML terms), and that causes it to be treated as
omitted by **yamlfig**:

```yaml
server:
```

The parser above will accept this config file.  Since the `server`
block has been omitted, it will substitute its default value.  Since
the `server.addr` and `server.port` fields are provided by the
default, they will pass the rules requiring their existence.  The
`server.ssl` field has not been provided by the default, but since
it is flagged as optional, the field will be created and assigned a
value of None:

```python
conf.server                  # <YamlConfig object at 0x[...]>
conf.server.addr             # '127.0.0.1'
conf.server.port             # 81
conf.server.ssl              # None
```

The reverse is also true.  Default fields can be included in the
substructure of an optional field, and they will take the default
values if they are omitted from the config but the optional block is
included.  Other combinations work as well (e.g., default fields
within default blocks; optional fields within optional blocks;
optional fields within default blocks within optional blocks; etc.).

If it helps, we can think of optional and default flags being handled
from the top down in a cascade.  If a parent field is omitted, it will
be checked for `optional` or `default` flags first.  If it is
optional, the field will be created with a `None` value and the
parsing will move on.  If it takes a default, the field will be
created with the default value or substructure, and the parser will
descend into that substructure, checking those fields and values before
moving on.  The parser will only encounter child fields and values
after the parent's optional or default nature has been handled.


#### Default block and optional wildcarded path recognize *zero-or-more*

As noted earlier, a wildcard rule path requires that a config file
have one or more fields matching the path.  By default, a wildcard
rule will raise an error if there are no fields matching it, but there
are times when we want to accept zero-or-more matches.

The following rules configure a parser for cases where we want a block
with zero or more subfields:

```python
confp.add_rule('server.upload_paths', default={})
confp.add_rule('server.upload_paths.*', optional=True)
```

The `optional` flag on the wildcard path will cause the parser to
allow the `upload_paths` block to contain no fields.  The default on
the `upload_paths` field will create that empty block if the field is
null.  The following config file would be accepted by this parser:

```yaml
server:
  upload_paths:
```

By leaving `upload_paths` null, we signal that it has been explicitly
omitted, so it is given its default value (i.e., an empty mapping).
Then, since the wildcard path for the fields within `upload_paths` is
flagged as optional, that rule will be satisfied with zero fields.
The `YamlConfig` object would exist but contain zero fields:

```python
conf.server.upload_paths         # <YamlConfig object at 0x[...]>
len(conf.server.upload_paths)    # 0
```

For completeness sake, the same parser would also accept a config
file with one or more fields within `upload_paths`:

```yaml
server:
  upload_paths:
    alice:   /home/alice/uploads
    bob:     /home/bob/public
```

In this case, the `YamlConfig` object would contain two fields:

```python
conf.server.upload_paths         # <YamlConfig object at 0x[...]>
len(conf.server.upload_paths)    # 2
set(conf.server.upload_paths)    # {'alice','bob'}
```

This pattern&mdash;with the block taking an empty substructure as the
default and the wildcard rule flagged as optional&mdash;is the
recommended way to implement a parser that accepts zero-or-more fields
or list elements.


#### A path marked no-follow can have any and arbitrary substructure

In some cases, we want to stop a **yamlfig** parser from attempting to
validate a substructure, either because the program is designed to
handle whatever is beneath that value or, more often the case, the
actual structure follows a complicated syntax, but the program will be
passing that structure to another package, and it has its own
functions for validating the input.

For example, consider an example where a program needs to pull back a
list of projects from a MongoDB database.  The following config file
provides values that might be needed to (1) access the database, (2)
reference the specific collection within the database, and (3) filter
the results to only a subset of all projects, using a MongoDB query:

```yaml
mongodburl: mongodb://192.168.1.200:27017/
collection: projects
filterquery: { 'is_private': { '$ne': true } }
```

All three fields must exist, but the `filterquery` field contains a
MongoDB query *as* its substructure.  MongoDB queries can be expressed
as JSON objects, and YAML syntax is a superset of JSON, so the query
can be expressed as JSON/YAML right within the YAML config file.

By default, the **yamlfig** parser will try to validate that object
(i.e., check whether the paths `filterquery.is_private` and
`filterquery.is_private['$ne']` are expected by the parser).
Configuring a `confp` parser to correctly validate the syntax of an
arbitrary MongoDB query is impossible and an unnecessary waste of
complexity.  As soon as the script hands the query off to MongoDB, it
is going to do a much better job of validating it.

The following parser is configured to accept the above config file:

```python
confp.add_rule('mongodburl')
confp.add_rule('collection')
confp.add_rule('filterquery', nofollow=True)
```

This parser will require that a `filterquery` field exists along with
the `mongodburl` and `collection` fields, but the `nofollow` argument
ensures that it will not descend into the substructure within the
`filterquery` field.  No additional validation of that substructure
will take place.

The value at `conf.filterquery` is a standard python `dict` which can be
passed to a MongoDB `find` command as-is.

```python
conf.filterquery        # {'is_private': {'$ne': True}}
```

As an aside, note that until this example, we have been using YAML
block-structure syntax rather than JSON syntax, but there is no
difference between the two formats once parsed.  The config file
above could have been written equivalently as follows:

```yaml
mongodburl: mongodb://192.168.1.200:27017
collection: projects
filterquery:
  is_private:
    "$ne": true
```

A distinct alternative would have been to encode the MongoDB query
object as a string, as in the following line:

```yaml
filterquery: "{ is_private: { $ne: { true }}}"`
```

While a viable alternative, there are benefits to *not* doing so.  By
storing the query object as a query object, we actually do perform
some syntax checking at parse time, before handing it off to MongoDB.
We ensure that the brackets are balanced and the JSON is legal.  We
also get whatever syntax highlighting our editor provides to
YAML/JSON.  A string would simply be treated as a string by the
**yamlfig** parser, and we would eventually have to invoke a JSON
parser ourselves.


#### A path marked no-follow can also be optional or take defaults (but not both)

The `nofollow` parameter really affects the handling of the value not
the field, whereas `optional` and `default` are parameters that affect
the handling of the field (i.e., what to do if it is omitted).

If a field is omitted from a config, and if its path is marked in the
parser as both optional and no-follow, the field will be created and
assigned the value `None`.  If it were not optional, an error would be
raised.  Since the value `None` is terminal and has no substructure,
being marked no-follow has little effect.

If a field is omitted from a config, and if its path is marked in the
parser as no-follow and taking a default, the field will be created
and the default value will be substituted.  If the default value has
substructure (i.e., it is a `dict` or a `list`), then the no-follow
marking would apply and no additional validation would be performed by
the parser on that substructure.


#### A path marked no-follow cannot have any subrules

A parser configuration such as the following would raise an error:

```python
confp.add_rule('filterquery', nofollow=True)
confp.add_rule('filterquery.is_private')
```

The no-follow condition on a path means that no rules on descendant
paths will ever be checked or validated, so we prevent such rules from
being added.  For this example, a `ValueError` would be raised
explaining that `"filterquery.is_private" is a descendant of a
no-follow rule`.

### Path Type Checking

Within the **yamlfig** parser, after establishing that every required
field exists, that every optional or default field has been handled,
and that there are no unexpected fields, the parser's next step is to
check that any type assertions on the values for each field are
satisfied.

#### Ensure that a field is a str (or int or bool or float, etc.)

When instantiating and adding a new rule, we can specify a `path_type`.

```python
confp.add_rule('server.addr', path_type=str)
confp.add_rule('server.port', path_type=int)
```

In addition to requiring that the `server` block contains an `addr`
field and a `port` field, these rules will further check that the
values are instances of the given `path_type` types.

The following config has a null in the `addr` field:

```yaml
server:
  addr: ~
  port: 81
```

The above parser would raise an error: `"server.addr" has type
NoneType not type str`.

Likewise, the following config has a string in the port field:

```yaml
server:
  addr: 127.0.0.1
  port: "81"
```

The above parser would raise an error: `"server.port" has type
str not type int`.

The type that a value takes is determined by the underlying raw-YAML
parser that **yamlfig** uses.  By defalt, we use `SafeLoader` within
[`PyYAML`](https://github.com/yaml/pyyaml).  It recognizes the
following types:

  * `bool`
  * `str`
  * `unicode` (in Python 2, when the value contains non-ASCII characters)
  * `int`
  * `long` (in Python 2, when the value is larger than `sys.maxint`)
  * `float`
  * `date` (in the `datetime` package)
  * `datetime` (in the `datetime` package)
  * `dict` (for mappings and mapping-like tags)
  * `list` (for lists and list-like tags)
  * `NoneType` (i.e., `path_type=type(None)`)

Any of those types could arise in a config and be accepted or rejected
by a `path_type` argument.  Additionally, it is possible to replace
`SafeLoader` with a different YAML parsing class, in which case the
set of types would depend on what types it constructed.


#### Union types handle complex types like *a number* or *a string*

In the following config, the `timeout` field will be parsed as a float:

```yaml
server:
  timeout: 1.2
```

But in the following config, the `timeout` value will be parsed as an int:

```yaml
server:
  timeout: 1
```

Assuming the underlying server wants a float but handles the
conversion of an int all by itself, we don't really want to force a
user to add spurious decimal points (e.g., changing `1` to `1.` will
ensure the parser returns a float) just to consistently achieve a
single type across all configs.

The following parser configuration rule will accept a `timeout` that
is either an `int` or a `float`:

```python
confp.add_rule('server.timeout', path_type=(int, float))
```

By specifying a tuple of types, we can direct **yamlfig** to accept
values that are instances of either type.

This feature was a lot more urgent in Python 2, where we almost always
wanted a string to be checked against `(str, unicode)`, so that the
appearance of a word with an accent or umlaut in a descriptive string
wouldn't suddenly cause our config file to be rejected.  Things have
gotten calmer with Python 3 (e.g., `str` vs `unicode` and `int` vs
`long` are no longer issues), but union types do still arise (e.g.,
`int` vs `float`).

#### Ensure that a path contains a map or a list

Consider this parser configured to accept mappings from project names
to descriptions:

```python
confp.add_rule('projects', path_type=dict)
confp.add_rule('projects.*')
```

Contrast it with this parser configured to accept lists of authorized
user names:

```python
confp.add_rule('users', path_type=list)
confp.add_rule('users.*')
```

In both cases, the wildcard rule accepts one-or-more arbitrary fields
within the block, but as noted in an [earlier
segment](#wildcards-are-also-useful-for-accepting-lists-of-values),
the wildcard does not distinguish a map from a list.  The
`path_type=dict` constraint is what ensures that the first parser
accepts config files with a map, like this:

```yaml
projects:
  ProjectX: "Project X is an eXtreme project (for more info talk to Alice)"
  meerkat_works: "Bob's not-quite skunkworks project"
```

The `path_type=list` constraint is what ensures that the second parser
accepts config files with a list, like this:

```yaml
users:
- alice
- bob
- carol
```

Since few programs are written to expect either a mapping or a list,
we typically want to use type checking to ensure that a config-file
block contains the expected structure.

#### A config file itself can be verified as either a list or a map

While we have so far considered YAML files with a map structure at the
root level, a YAML file could also be a list:

```yaml
- addr: 192.0.2.200
  port: 81
- addr: 192.0.2.201
  port: 81
- addr: 198.51.100.15
  port: 8080
- addr: 203.0.113.130
  port: 8080
```

In this example, these address-port pairs might be a list of mirrors,
ordered by proximity.  The following parser is configured to check that
the YAML file itself is a list, and then that each element of the list
has the proper substructure:

```python
confp = YamlConfigParser(path_type=list)
confp.add_rule('*.addr', path_type=str)
confp.add_rule('*.port', path_type=int)
```

After reading and validating the above config file, this parser
returns a `YamlConfigList` object:

```python
len(conf)                  # 4
conf[0].addr               # '192.0.2.200'
conf[0].port               # 81
```

Note that in this example, we actually included the instantiation of
the `YamlConfigParser` as `confp`.  All our previous examples (after
[Basic Usage](#basic-usage)) assumed that step.  But when we are
making assertions about the top-level object parsed from the config
file, those are configured as part of the `YamlConfigParser`
instantiation.

Down deep, every rule that gets added to the parser is of type
`YamlConfigRule`.  The `YamlConfigParser` class inherits from
`YamlConfigRule`, and any arguments are used to validate the
root-level object rather than any particular field or path within the
object.  The primary difference between the root `YamlConfigParser`
object and the `YamlConfigRule` objects that are added to it is that
the `YamlConfigParser` cannot have a `rule_path` while the other
objects must.  Additionally, the root-level object cannot be optional
or take a default.  (It can be flagged no-follow, though.)


#### A config file cannot be an atomic value; it must be a map or list

A **yamlfig** parser will not accept a config file without any
substructure.  Technically, this is a valid YAML file:

```yaml
42
```

A standard YAML parser will parsed it as an `int`.  However,
**yamlfig** will raise an error: `config is a(n) int but a record or
list is expected`.

Honestly, if our program must accept config files consisting of a
single value, **yamlfig** might not be the right tool for the
situation.  If we still desired to make a go of it, we could nest that
value in a single-field mapping, like so:

```yaml
number: 42
```

The following parser would accept that config file, with a single
field, the value of which is a list:

```python
confp = YamlConfigParser(path_type=dict)
confp.add_rule('number', path_type=int)
```

Even more concisely, we could nest the value in a singleton list:

```yaml
- 42
```

The following parser would accept such a config file:

```python
confp = YamlConfigParser(path_type=list)
confp.add_rule('0', path_type=int)
```

Note the space between `-` and `42`.  Without it, the singleton list
collapses back to a single (negative) integer:

```yaml
-42
```

Such a single value would not be accepted.


### Rule Test Functions

While type checking helps validate the values in a config file, we
often want to place additional constraints on those values.  For
instance, we might want a value not only to be an `int` but to fall
within a particular range.  We might want another value not only to be
a `str`, but also to match a regular expression.  We might want a
third value not only to be a `str` but also to point to an existing
file.

When adding a rule to a parser, we can specify a test function using
the `test` argument, to perform additional checking of values.  The
`yamlfig.test` package contains a variety of pre-packaged test
functions for some common validation scenarios.

#### Verify that a value matches a regular expression

This parser rule will constrain `username` to start with a lower case
letter and be followed by zero or more lowercase letters or numbers:

```python
confp.add_rule('username', test=test.is_regex('^[a-z][a-z0-9]*$'))
```

This config file would be accepted by such a parser:

```yaml
username: 'carol57'
```

This config file would be rejected:

```yaml
username: 'Carol C.'
```

The parse error would include the explanation `"username" failed test:
"Carol C." does not match /^[a-z][a-z0-9*$/`.

#### Verify that a value is an IPv4 address

This parser rule will constrain the `addr` field of the `server` block to
be a valid dotted-quad IPv4 address:

```python
confp.add_rule('server.addr', test=test.is_ipv4_address)
```

#### Test functions packaged within yamlfig

The `yamlfig.test` module that contains various common validation
tests has been directly imported as the `test` object in the examples
of this documentation, but would otherwise be accessed as
`yamlfig.test` (e.g., `test=yamlfig.test.is_regex('^[a-z][a-z0-9]*$')`).

The following test functions are available in the `yamlfig.test`
module:

 * `is_interval(lower, upper)` verifies that the value is within the
   range defined by the lower and upper bounds;

 * `is_regex(regex, invert=False)` verifies that the value matches the
   regular expression (or does not match it, if inverted);

 * `is_ipv4_address` verifies that the value is an IPv4 address in
   dotted-quad notation;

 * `is_domain_name` verifies that the value conforms to the
   specification of a DNS domain name (which, note, is a looser
   constraint than that it be an actual operating and reachable domain
   name);

 * `is_email_address` verifies that the value (roughly) conforms to
   the specification of an email address;

 * `is_url` verifies that the value (roughly) conforms to the
   specification for URLs;

 * `is_file_path(*ostests)` takes one or more strings corresponding to
   properties of filesystem objects, interprets the value as a
   filesystem path, and verifies that the path satisfies *all* of the
   listed properties.  Properties include:

   * `'exists'` and `'!exists'`: the path exists (or is not);
   * `'isdir'` and `'!isdir'`: the path is a directory (or is not);
   * `'isfile'` and `'!isfile'`: the path is a file (or is not);
   * `'islink'` and `'!islink'`: the path is a symlink (or is not);
   * `'ismount'` and `'!ismount'`: the path is a mount point (or is not).

Note that for higher-order functions (i.e., the ones that return the
test functions suitable for `test`), not all optional parameters are
shown and described.  Check the help documentation for each function
for additional detail on usage and options.

#### Writing our own test functions

The `test` parameter to `add_rule` takes a function with three
parameters: `conf`, `path`, and `value`.  It signals acceptance of the
value by returning None, and rejection by returning a string
explaining what caused the failure.

Some of the test functions packaged within **yamlfig**, like
`test.is_ipv4_address`, directly match that specification.  Others,
like `test.is_regex`, return a function that matches the specification
based on their arguments.

In an [earlier
segment](#test-that-a-block-contains-fields-without-specifying-which-fields-by-using-wildcards),
we explained that rule paths could not contain *partial* wildcards
(e.g., `user-*` to require that all fields start with a particular
prefix).  However, test functions do offer a way to recognize such
properties and more.  Consider a config file in which a block must
contain a `default` field, and can optionally contain zero or more
fields that must all match a partial wildcard like `user-*`.

Test functions offer a way to implement any test that we can write as
a Python function:

```python
def has_default_and_user_fields(conf, path, value):
  if not 'default' in value:
    return '"default" field is missing'
  for field in value:
    if field != 'default' and not field.startswith('user-'):
      return '"{0}" is neither "default" nor starts with "user-"'.format(field)
  return None

confp = YamlConfigParser()
confp.add_rule('uploads', test=has_default_and_user_fields)
confp.add_rule('uploads.*', path_type=str, optional=True)
```

The following config file would be accepted by this parser:

```yaml
uploads:
  default: /var/share/SomeApp/uploads
  user-alice: /home/alice/uploads
  user-bob: /home/bob/public
```

The following config file would be rejected by this parser:

```yaml
uploads:
  user-alice: /home/alice/uploads
  user-bob: /home/bob/public
```

The parse error would include the explanation `"uploads" test failed:
"default" field is missing`.

Of the three parameters (i.e., `conf`, `path`, and `value`), all of
the packaged test functions depend only on the `value`, and that will
typically be the case.  By providing the entire `conf` object as well
as the `path` to the value being verified, **yamlfig** enables the
test to evaluate the value in the context of the rest of the config
file if necessary.

### Warnings and Caveats

 * **Field names with leading underscores** &ndash; While accessing
   `YamlConfig` fields as attributes is convenient, the drawback is
   that any field names that start with a leading underscore risk
   colliding with the methods and attributes that implement the class.
   Consequently, if the parser encounters any field that start with
   `'_'`, a warning will be raised.  The warning can be suppressed by
   setting `yamlfig.print_underscore_warning.off = True`.  As with
   non-string field names, we can always look up a field with leading
   underscores via index lookup (e.g., `conf["_field"]` rather than
   `conf._field`), but the warning is intended to make us aware of the
   possibility for collision.

 * **References to `transform` functions in code and documentation**
   &ndash; The API for the `YamlConfigRule` class and the
   `YamlBaseConfig` classes expose references to a `transform`
   function or the ability to invoke `do_transform` on the container
   object.  The ability to specify a transform is planned (and
   described in more detail [below](#future-work)).  As the code
   indicates, work on this feature was already underway when this
   version was released, but consider it untested, incompletely
   documented, and subject to change.

## Next Steps
   

### Future Work

Several features are already on our list of things we would like to or
have started to implement:

  * Allow standard fielded rules to co-exist alongside wildcard rules,
    with the standard rule taking precedence if it matches and the
    wildcard being used as a catch-all.  We probably still want to
    disallow partial wildcards since (a) they can already be handled
    with test functions, and (b) they would raise the possibility of
    allowing multiple partial wildcard rules attached to the same
    parent path, and that would raise all sorts of ambiguity about
    what to do if multiple rules match the same field.

  * Allow a user to more easily specify a constraint on field names,
    for instance a `field_type` to do the same type checking on a
    field that `path_type` does on the value, and/or a `field_regex`
    to specify a pattern that the field must match.  Currently these
    are possible, but would require the user to implement their own
    rule test, as described above.

  * Add options to `test.is_file_path` that (1) allow the user to
    specify a directory from which all relative paths are resolved,
    and (2) allow the user to specify a path into `conf` where such a
    base directory would be stored.  These would enable support for a
    config file where one `homepath` field specifies where the program
    will `chdir` to, and then all the other paths (e.g., `dbfile` or
    `htmldir` are specified relative to `homepath`).

  * Extend the `rule_path` specification to allow us to express field
    types that are not strings or are strings that include 'special
    characters' like whitespace, the delimiter (`.`), or the wildcard
    (`*`).  Right now, we're thinking of using square brackets in a
    rule path, so that the string resembles the path that would be
    used to access the value once parsed (e.g.,
    `rule_path="dbhosts['192.0.2.1'].port"` would indicate the config
    file had a structure where a `dbhosts` block contained a field
    field named `192.0.2.1` which maps to a sub-block that has a
    `port` field).

  * Implement a `test.is_in_choiceset` which verifies that the value
    is one of the configured options or choices.  So, if a rule for a
    `dbtype` path had `test=test.is_in_choiceset(['sqlite', 'mysql',
    'mongodb'])`, it would verify that the `dbtype` value took one of
    those values, returning an explanatory error message if not.

  * Extend `YamlConfigParser` with a function to write a config-file
    template (or and actual config file if provided with a `conf`
    object) to use for the values.  For each rule, it is already
    possible to specify a `desc` describing the purpose of the path,
    and an `example` value.  These values could be incorporated into
    the config-file template, making it somewhat self documented, and
    making it easier for a program to provide its users with a
    template.  In truth, we would probably want to implement this as a
    `Representer` class that inherits from and extends `SafeDumper`,
    but with that class invoked by something like
    `conf.write_file(filename, conf=None)`.

  * Extend `YamlConfigRule` with support for transformations.  A goal
    for **yamlfig** was to gather into one package all of the things
    that we find ourselves doing over and over again when we read in a
    config file (e.g., checking whether fields exist, that they have
    the right types, and that they meet various other conditions).
    Another thing we do at this stage is converting them to the
    objects that we really want to use in our program.  For instance,
    we don't really want the path to the log file, we want the open
    filehandle to it; we don't really want the IPv4 address in
    dotted-quad notation, we want the `IPv4Address` object that we can
    construct with it.  Some initial groundwork for such
    transformations already exists within the code, but it needs to be
    built out and tested (lots and lots of testing, especially the
    interaction with the write-out-configs extension described above).

This list is neither exhaustive nor a promise of what is certain to
come.  Other suggestions are also welcome, of course, too.


### Support and Collaboration

We welcome reports of issues and other contributions through our
package's page on GitHub:

  * https://github.com/ktkalaru/yamlfig

Note that this is our first open-source project, and it was shared in
part so that we could get more experience with the standard tools and
workflows.  We aim to respond to any issues, requests, or other
feedback promptly and professionally, but some understanding may be
required since we are learning as we go.
