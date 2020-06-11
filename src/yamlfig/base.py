"""This module defines the fundamental yamlfig classes.

Classes for the parser:

  * YamlConfigParser objects contain all the rules needed for parsing
    and validating a family of config files.  It is technically a rule
    itself; the root of the rule tree.

  * YamlConfigRule objects establish properties that must hold for a
    particular field in a config file.

Classes for parsed objects:

  * YamlConfig objects represent YAML mappings (i.e., sets of field
    names mapped to values).  The interface is similar to dict, but
    also expose the fields as attributes for more succinct usage.

  * YamlConfigList objects represent YAML sequences (i.e., lists of
    values).  Unlike a python list, thir interface is very similar to
    YamlConfig, except that the fields must be numeric strings and the
    elements are their corresponding values.

  * BaseYamlConfig is an abstract class inherited by both
    parsed-object classes.

Exceptions:

  * ParseError is raised when YAML parsing and validation fails.

"""
# pylint: disable=protected-access, useless-object-inheritance, too-many-lines

from __future__ import print_function

# Standard modules
import abc
import collections
import sys
import textwrap

# Installed packages
import yaml

WILDCARD = '*'
DELIM = '.'


def print_underscore_warning(field):
    """Print warning if we encounter a field with a leading underscore."""
    # pylint: disable=undefined-variable # for unicode / Python 2 support
    if not print_underscore_warning.off:
        warntext = textwrap.dedent("""
        Warning: fields that start with underscores ("{0}") are discouraged
        when using yamlfig due to the risk that you will corrupt the
        namespace of the YamlConfig object.""".format(field))
        if sys.version_info.major == 2:
            print(unicode(warntext), file=sys.stderr)
        else:
            print(warntext, file=sys.stderr)
        print_underscore_warning.off = True


# Print a warning for leading underscores by default
print_underscore_warning.off = False


def _path_join(*pargs):
    # Create a path string from the field arguments, stripping any nulls
    # pylint: disable=undefined-variable # for unicode / Python 2 support
    if sys.version_info.major == 2:
        pargs = [unicode(parg) for parg in pargs if parg is not None]
    else:
        pargs = [str(parg) for parg in pargs if parg is not None]
    return DELIM.join(pargs)


def _path_split(rule_path):
    # Split path string into list of fields along the path
    rule_words = rule_path.split(DELIM)
    return rule_words


def _as_list_index(field, validate=False):
    # Try to make field an integer index if possible; fail if validate is true
    # Use field type to determine if conversion is needed and what to do
    if isinstance(field, int):
        return field
    try:
        return int(field)
    except (TypeError, ValueError):
        pass
    if validate:
        raise KeyError('"{0}" is not an integer list index'.format(field))
    return field


def _value_to_conf(parent, field, value):
    """Convert container value into a config object.

    Helper function that turns a container value (e.g., a dict or
    list) into a config object, using the member variables of the
    parent and the field of the object within the parent to establish
    the member variables of the config object.  If value is a dict,
    output a YamlConfig; a list, output a YamlConfigList; anything
    else is passed through as a value.

    """
    # pylint: disable=undefined-variable # for unicode / Python 2 support
    assert isinstance(parent, BaseYamlConfig), parent

    # Detect leading underscore and print warning (with Python 2 unicode case)
    if sys.version_info.major == 2:
        if isinstance(field, (str, unicode)) and field.startswith('_'):
            print_underscore_warning(field)
    elif isinstance(field, str):
        if field.startswith('_'):
            print_underscore_warning(field)

    # Establish the conf object parameters and instantiate the object
    path = _path_join(parent._path, field)
    root = parent._root
    filename = parent._filename
    if isinstance(value, dict):
        conf = YamlConfig(value, root=root, path=path, filename=filename)
    elif isinstance(value, (list, tuple, set)):
        conf = YamlConfigList(value, root=root, path=path, filename=filename)
    else:
        conf = value
    return conf


def _conf_to_record(conf):
    """Translate a BaseYamlConfig object back to a python type.

    Convert YamlConfig and YamlConfigList to dict and list
    respectively.

    """
    if isinstance(conf, YamlConfig):
        record = {}
        for key in conf:
            record[key] = _conf_to_record(conf[key])
        return record
    if isinstance(conf, YamlConfigList):
        record = []
        for idx in conf:
            record.append(_conf_to_record(conf[idx]))
        return record
    return conf


class ParseError(ValueError):
    """Error raised from parse_record when the validation fails.

    Like its parent class, ValueError, the message field contains an
    explanation of what went wrong.  The Exception object will also
    have a filename and pathstr object that will be filled in when
    present and None if not.

    """

    def __init__(self, message, filename=None, pathstr=None):
        """Insantiate error with given message.

        The filename and pathstr will be incorporated into the
        message if given.

        """
        if pathstr:
            if pathstr != '*root*':
                pathstr = u'"{0}"'.format(pathstr)
            message = u'{0} {1}'.format(pathstr, message)
        if filename:
            message = u'{0}: {1}'.format(filename, message)
        super(ParseError, self).__init__(message)
        self.filename = filename
        self.pathstr = pathstr


class YamlConfigRule(object):
    """Rules describe properties to be verified for a config-file element.

    A rule consists of the following parts:

    rule_path: The rule path is a non-empty string, with fields in the
      path separated by the delimiter character, and each field must
      either be a match or the wildcard character.

    path_type: Python class that matching values must have or an error
      is raised.  Note that 'dict' and 'list' are shorthand for
      YamlConfig and YamlConfigList respectively.  Note that like
      isinstance, a path_type can be a tuple of types, indicating that
      any included type is to be accepted.

    default: String or object that will be used as a default if no
      match is found for the rule path in the YAML document.
      Effectively ensures that the path will exist.

    optional: Boolean indicator that if no match is found in the YAML
      record, a value of None should be used as the default, rather
      than raising a parse error.  If a rule is optional, descendants
      can be required, but it means that if the optional path is
      present, then that field must also be there.

    nofollow: Boolean indicator that the rule should have no children
      and the child values or containers should be passed as is.  One
      use for this is when an entire dict or list is to be passed to a
      transform, and it is not necessary or desired to test the
      individual element.

    test: A function that will be called on the value in the config
      file (after optional and default flags are exercised), to
      further validate the value.  The syntax of a test function is:

      test(conf, path, value)

      where conf is the entire parsed conf record, path is the rule
      path corresponding to the rule, and value is the value in the
      config file.  After checking value, and possibly referencing
      conf, a successful test should return None, and a failed test
      should return a string explaining what failed.  A non-None
      return value will be incorporated into a raised ParseError.

    transform: After the validation pass, a transform pass will be
      made over the object, with this function called to transform
      each matching rule (roughly like the following pseudocode):

      record[path] = transform(record, path, value)

      Note that transformation rules can make it such that the
      original config file cannot be recovered.

    example: String or object that will be used as an example of the
      kinds of values the rule path takes, to be incorporated into
      config-file templates or other user feedback.

    desc: The description of the purpose of the field or fields to
      which the rule corresponds, to be incorporated into config-file
      templates or other user feedback.

    Loader and Dumper are the classes used to parse a stream into a
      YAML record.  By default, they use SafeLoader and SafeDumper so
      that untrusted config files and values can be read and written.

    root: is a pointer to the root YamlConfigRule in a rule tree.  For
      the root node, it is a pointer to itself.

    A YamlConfigRule object also contains a rules dictionary which
    will contain a mapping from zero or more field names to
    sub-YamlConfigRule objects, that apply to the subpath associated
    with that field (or WILDCARD) beneath the current rule's
    rule_path.

    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, rule_path=None, path_type=None, default=None,
                 optional=False, nofollow=False, test=None,
                 transform=None, example=None, desc=None,
                 Loader=yaml.SafeLoader, Dumper=yaml.SafeDumper,
                 root=None):
        """Instantiate a new rule with the given properties."""
        # pylint: disable=invalid-name, too-many-arguments

        self._validate_rule_path(rule_path)
        self._validate_path_type(rule_path, path_type)

        self.rule_path = rule_path
        self.path_type = path_type
        self.default = default
        self.optional = optional
        self.nofollow = nofollow
        self.test = test
        self.transform = transform
        self.example = example
        self.desc = desc
        self.Loader = Loader
        self.Dumper = Dumper
        self.root = root if root else self
        self.rules = collections.OrderedDict()

        if self.root == self:
            if self.rule_path is not None:
                raise ValueError(
                    'Root rule cannot have a rule path "{0}"'.format(
                        rule_path))
            if self.default is not None:
                raise ValueError('Root rule cannot take a default value')
            if self.optional:
                raise ValueError('Root rule cannot be optional')
        else:
            if self.rule_path is None:
                raise ValueError('Non-root rule must have a rule path')

        if self.default is not None and self.optional:
            raise ValueError(
                'Rule with path "{0}" cannot be optional and have a default'
                .format(rule_path))

    def _is_root(self):
        # Returns true if and only if the object is a root rule
        assert self.root is not None
        assert self.root == self.root.root
        if self.root == self:
            assert self.rule_path is None
            return True
        return False

    @staticmethod
    def _validate_rule_path(rule_path):
        # Verify that the rule is well formed
        # pylint: disable=undefined-variable # for unicode / Python 2 support
        if rule_path is None:
            return

        # Check that rule path is a str (with Python 2 unicode case)
        if sys.version_info.major == 2:
            non_str_type = not isinstance(rule_path, (str, unicode))
        else:
            non_str_type = not isinstance(rule_path, str)
        if non_str_type:
            raise ValueError(
                'Rule path {0} is a(n) {1} not a str'.format(
                    rule_path, type(rule_path).__name__))

        # Check for empty fields and fields with partial wildcards
        rule_words = _path_split(rule_path)
        for rule_word in rule_words:
            if WILDCARD in rule_word:
                if not WILDCARD == rule_word:
                    raise ValueError(
                        'Rule path "{0}" cannot use a partial wildcard'.format(
                            rule_path))
            if len(rule_word) == 0:
                raise ValueError(
                    'Rule path "{0}" is missing a field name'.format(
                        rule_path))

    @staticmethod
    def _validate_path_type(rule_path, path_type):
        # pylint: disable=redefined-argument-from-local
        if path_type is None:
            return
        if isinstance(path_type, tuple):
            path_types = list(path_type)
        else:
            path_types = [path_type]
        for path_type in path_types:
            if not isinstance(path_type, type):
                raise ValueError(
                    'Rule path "{0}" path_type is a(n) {1} not a type'.format(
                        rule_path, type(path_type).__name__))

    def path_match(self, path):
        """Indicate if the rule path matches the given path.

        To match, both rule and path are split on '.' delimiters and
        compared field by field, where the fields must match or the
        rule path must be a wildcard.

        """
        rule_words = _path_split(self.rule_path)
        path_words = _path_split(path)
        if len(rule_words) != len(path_words):
            return False
        for rule_word, path_word in zip(rule_words, path_words):
            if rule_word not in (WILDCARD, path_word):
                return False
        return True

    def check_type(self, conf, path, value, filename=None):
        """Indicate if the value is an instance of the rule's path_type.

        If there is a mismatch, it raises a ParseError.  Note that
        this does no checking that the paths match.  (It is meant to
        be combined with path_match to determine if a rule applies.)

        """
        # pylint: disable=unused-argument
        pathstr = path if path is not None else '*root*'
        if self.path_type is None:
            return
        if isinstance(value, YamlConfig):
            value_type = dict
        elif isinstance(value, YamlConfigList):
            value_type = list
        else:
            value_type = type(value)
        if issubclass(value_type, self.path_type):
            return
        if value is None and self.optional:
            return
        if isinstance(self.path_type, tuple):
            typestr = ' or '.join([typ.__name__ for typ in self.path_type])
        else:
            typestr = self.path_type.__name__

        raise ParseError(
            u'has type {0} not type {1}'.format(value_type.__name__, typestr),
            filename, pathstr)

    def check_test(self, conf, path, value, filename=None):
        """Indicate if the rule's test returns an error on the value.

        Takes a record, path, and value (either container or leaf
        object), and if the rule includes a test, run the test, and
        raise a ParseError if the test returns an error message.  If
        it returns None, continue.

        """
        pathstr = path if path is not None else '*root*'
        if self.test is None:
            return
        if value is None and self.optional:
            return
        try:
            err = self.test(conf, path, value)
        except Exception as exc:
            raise ParseError(
                u'test raised exception: {0}'.format(str(exc)),
                filename, pathstr)
        if err is None:
            return
        raise ParseError(u'failed test: {0}'.format(err), filename, pathstr)

    def do_transform(self, conf, path, value, filename=None):
        """Apply any transformation to the given config path value.

        Takes a record, path, and value (either container or leaf
        object), and if the rule includes a transform, run the
        transform, and return the transformed object.  Otherwise,
        return the value.

        """
        pathstr = path if path is not None else '*root*'
        if self.transform is None:
            return value
        try:
            return self.transform(conf, path, value)
        except Exception as exc:
            raise ParseError(
                u'transform raised exception: {0}'.format(exc),
                filename, pathstr)

    def add_rule(self, rule_path, **kwargs):
        """Add a new rule to the parser at the given path.

        If parent rules in the rule tree are needed, create them.
        Note that parent rules will be created with only a required
        rule_path and no other parameters, so if they should also be
        optional or have other constraints set, that parent rule must
        be added first.

        """
        # Create rule
        rule = YamlConfigRule(rule_path, root=self.root, **kwargs)

        # Descend the rule path, so that after this while loop, parent
        # points to the direct parent of the final field being added, and
        # rule_field is that field.
        rule_words = _path_split(rule_path)
        rule_prefix = []
        parent = self
        while len(rule_words) > 0:

            # Check that we are not descending into a nofollow region
            if parent.nofollow:
                raise ValueError(
                    'Rule path "{0}" is a descendant of a nofollow rule'
                    .format(rule_path))

            # Check that we are not trying to transform a transformed ancestor
            if parent.transform and rule.transform:
                raise ValueError(
                    'Rule path "{0}" has multiple transforms on the path'
                    .format(rule_path))

            # Retrieve the next field in the path
            rule_field = rule_words.pop(0)

            # If it isn't the final rule in the path, descend one rule in
            # the path, creating it if necessary, and update parent to point
            # to it
            if len(rule_words) > 0:
                rule_prefix.append(rule_field)
                if rule_field not in parent.rules:
                    next_rule_path = _path_join(*rule_prefix)
                    next_rule = self.add_rule(next_rule_path)
                    parent.rules[rule_field] = next_rule
                parent = parent.rules[rule_field]

        # Sanity check the consistency of the sibling rules
        if rule_field in parent.rules:
            raise ValueError(
                'Rule path "{0}" cannot be defined multiple times'.format(
                    rule_path))
        if rule_field == WILDCARD and len(parent.rules) > 0:
            raise ValueError(
                'Rule path "{0}" wildcard cannot have sibling rules'
                .format(rule_path))
        if rule_field != WILDCARD and WILDCARD in parent.rules.keys():
            raise ValueError(
                'Rule path "{0}" cannot be the sibling of a wildcard rule'
                .format(rule_path))

        # Add and return the rule
        parent.rules[rule_field] = rule
        return rule

    def attach_rules(self, conf, conffile=None, path=None):
        """Associate each rule to element(s) of the config recursively.

        Sanity check that the current rule applies to the conf object
        which is typically a container object (i.e., a YamlConfig or
        YamlConfigList), so sweep through all of the child rules of
        the current rule and attach them to the container element, by
        populating the _child_rules dictionary of the conf object.  It
        recursively calls itself on any subrules.

        For each child rule of the current rule, the checks raise an
        error if a required (non-optional) rule matches nothing.  If a
        rule with a default matches nothing, it adds the default value
        to the conf object.

        Note that this already assumes a correspondence between the
        current rule (self) and the conf object given, since that
        correspondence will be tracked in the parent's _child_rules or
        in _root_rule if conf is the root.

        It can be called with a conf object that is an atomic element,
        but in that case conffile and path must be specified since the
        object does not store the conffile name in it.  Typically that
        usage is only used internally, and all it will do in those
        cases is check that the current rule has no subrules which
        would fail to match on an atomic element.  If path is not
        specified (i.e., None), it will be assumed to be root.

        """
        # pylint: disable=too-many-locals, too-many-branches
        # pylint: disable=too-many-statements

        # Handle the leaf-node case where conf is not a YamlConfig.
        # The only action to check if there are subrules, since they
        # cannot be matched.  Even optional subrules raise an error,
        # since the stubs for them cannot be added to this
        # non-container.  The only exceptions, where the current rule
        # is optional or default should have been handled at the
        # parent level of the recursion, so they are assumed here.
        if not isinstance(conf, BaseYamlConfig):
            assert conffile is not None
            pathstr = path if path is not None else '*root*'
            if len(self.rules) == 0:
                return
            raise ParseError(
                u'is a(n) {0} but a record or list is expected'.format(
                    type(conf).__name__), conffile, pathstr)

        # At this point, the conf object is a YamlConfig or YamlConfigList
        # Check that it has not already had a rule tree attached to it
        assert conf._state == 'NEW'
        assert conffile is None or conf._filename == conffile

        # Sanity check that we are on the right path and have consistency
        if conf._is_root():
            if not self._is_root():
                raise RuntimeError('non-root rule given root conf')
            conf_root_rule = conf._get_root_rule()
            if not conf_root_rule == self:
                raise RuntimeError('root rule mismatch: {0} vs {1}'.format(
                    self, conf_root_rule))
        else:
            if self._is_root():
                raise RuntimeError('root rule given non-root conf')
            if not self.path_match(conf._path):
                raise RuntimeError('rule called on non-matching {0}'.format(
                    conf._path), conffile)
            conf_root_rule = conf._get_root_rule()
            if not conf_root_rule == self.root:
                raise RuntimeError('root rule mismatch: {0} vs {1}'.format(
                    self.root, conf_root_rule))

        # Check that we don't already have attached rules
        if len(conf._child_rules) > 0:
            raise RuntimeError('Child rules already attached to {0}'.format(
                self.rule_path))

        # Before we sweep through the subrules, define several helper
        # 'macro-like' functions that occur under various conditions, so
        # it is better to instantiate the code once.

        def handle_matched_path(subrule, conf, field, pathstr):
            # In the standard case, the rule is 'attached' to the
            # parent, mapping the child field name to the rule.  Then
            # we recursively attach any subrules to the child.
            conf._child_rules[field] = subrule
            subrule.attach_rules(conf[field], conf._filename, pathstr)
            handle_nofollow_check(subrule, conf, field)

        def handle_nofollow_check(subrule, conf, field):
            # Once we have attached a subrule to conf for a field
            # (either because the field was found or because we
            # substituted a default for it), if the subrule is marked
            # nofollow, convert the value back to a native python type
            # (e.g., a dict or list).
            if subrule.nofollow:
                conf[field] = _conf_to_record(conf[field])

        def handle_exercised_default(subrule, conf, field, pathstr):
            # In the case of an exercised default, the conf is either
            # missing field or has an explicit null.  So construct the
            # subconf from the default, attach it to the conf, attach
            # the rule to the parent, and recursively attach any
            # subrules to the new child.
            assert subrule.default is not None
            assert field not in conf or conf[field] is None
            subconf = _value_to_conf(conf, field, subrule.default)
            conf[field] = subconf
            conf._child_rules[field] = subrule
            subrule.attach_rules(subconf, conf._filename, pathstr)
            handle_nofollow_check(subrule, conf, field)

        def handle_exercised_optional(subrule, conf, field):
            # In the case of an exercised optional, the conf is either
            # missing field or has an explicit null.  So, ensure that
            # it exists and has a null.  Then treat it as missing
            # (i.e., do not try to recursively attach subrules).
            assert subrule.optional
            assert field not in conf or conf[field] is None
            conf[field] = None
            conf._child_rules[field] = subrule

        def attach_subrule_for_field(subrule, conf, field, pathstr):
            # Whether because the rule path is a wildcard or matched
            # the field, we are attaching the subrule for the field.
            # However, the field could still be an explicit null
            # value, in which case, if the rule is an optional or
            # default, those handlers are invoked.

            subconf = conf[field]
            if subconf is None and subrule.default is not None:
                handle_exercised_default(subrule, conf, field, pathstr)
            elif subconf is None and subrule.optional:
                handle_exercised_optional(subrule, conf, field)
            else:
                handle_matched_path(subrule, conf, field, pathstr)

        # Sweep through subrules, fill in defaults, and attach to config node
        for rule_field, subrule in self.rules.items():
            if rule_field == WILDCARD:
                # If not optional a wildcard rule must match at least one field
                if len(conf) == 0 and not subrule.optional:
                    raise ParseError(
                        'must contain at least one field',
                        conf._filename,
                        conf._path if conf._path else '*root*')
                # The wildcard path matches all fields
                for field in conf:
                    pathstr = _path_join(conf._path, field)
                    attach_subrule_for_field(subrule, conf, field, pathstr)
            else:
                pathstr = _path_join(conf._path, rule_field)
                if rule_field in conf:
                    # The rule path matches the field
                    attach_subrule_for_field(
                        subrule, conf, rule_field, pathstr)
                elif subrule.default is not None:
                    # Field is missing but subrule has a default
                    handle_exercised_default(
                        subrule, conf, rule_field, pathstr)
                elif subrule.optional:
                    # Field is missing but subrule is an optional
                    handle_exercised_optional(subrule, conf, rule_field)
                else:
                    # required field is missing - raise an error
                    raise ParseError('is missing', conf._filename, pathstr)

        # Unless nofollow is set, check that all fields match rules,
        # and that containers have all had their rules attached.
        if not self.nofollow:
            for field in conf:
                subpath = _path_join(conf._path, field)
                value = conf[field]

                # Detect any field for which no rule path was attached
                if field not in conf._child_rules:
                    raise ParseError(
                        'unexpected by parser', conf._filename, subpath)

                # Sanity check that we haven't somehow already descended into
                # the value at this field and attached rules to it
                if(isinstance(value, BaseYamlConfig) and
                   value._state != 'RULED'):
                    raise ParseError(
                        'had no rules attached', conf._filename, subpath)

        # Update the state to signal rules attached
        conf._state = 'RULED'

    def parse_record(self, record, filename=None,
                     check_types=True,
                     check_tests=True,
                     do_transforms=True):
        """Verify typing and testing rules and return converted record.

        The record will be converted to a YamlConfig object if it is a
        dict and a YamlConfigList object if it is a list.  The rules
        of the parser will be attached to each field of the record,
        verifying that the required field names exist, no unexpected
        field names are present, and handling any rules that allow
        rules that are optional or take a default.

        If check_types is set, invoke _check_types.  If check_tests is
        set, invoke _check_tests.  If do_transforms is set, invoke
        do_transforms.  Return the YamlBaseConfig object (or
        transformed object if a root level transform was given).

        """
        # pylint: disable=too-many-arguments
        if isinstance(record, (list, tuple, set)):
            conf = YamlConfigList(
                record, root=None, filename=filename, rule=self)
        elif isinstance(record, dict):
            conf = YamlConfig(record, filename=filename, rule=self)
        elif record is None:
            raise ParseError('config cannot be empty or null', filename)
        else:
            raise ParseError(
                'config is a(n) {0} but a record or list is expected'.format(
                    type(record).__name__), filename)
        self.attach_rules(conf, filename)

        if check_types:
            conf._check_types()

        if check_tests:
            conf._check_tests()

        if do_transforms:
            conf = conf._do_transforms()

        return conf

    def parse_file(self, filename, **kwargs):
        """Read in file as YAML, verify rules, and return converted record.

        Open the given file, parse it as YAML, and then invoke
        parse_record on the parsed object, passing all the remaining
        arguments to it.

        """
        with open(filename, 'r') as ifh:
            try:
                record = yaml.load(ifh, Loader=self.Loader)
            except yaml.parser.ParserError as exc:
                raise ParseError(u'{0}'.format(exc), filename)
            except yaml.composer.ComposerError as exc:
                raise ParseError(u'{0}'.format(exc), filename)
            except ValueError as exc:
                raise ParseError(u'{0}'.format(exc), filename)
        conf = self.parse_record(record, filename=filename, **kwargs)
        return conf


class YamlConfigParser(YamlConfigRule):
    """Root-level rules to which the rest of a rule tree is added.

    The YamlConfigParser is the object that a developer would
    instantiate to build out a tree of YamlConfigRules.  It is a
    YamlConfigRule itself; it just happens to be the root rule and has
    a name that denotes its usage as a parsing object.

    """


class BaseYamlConfig(object):
    """Abstract base class that is inherited by all yamlfig containers.

    Both YamlConfig and YamlConfigList derive from this class.  It
    provides some standard interfaces and basic testing and
    transformation functionality that must be implemented by both.

    The containers are intended to be arranged hierarchically forming
    a tree from a YamlConfig as the root and values as leaves.  All
    containers (not values) in the tree have a root pointer, to the
    root YamlConfig.  The root also has a _root_rules pointer that
    points to the YamlConfigRules object that initially parsed the
    config record.

    Each container maintains an ordered list of its children, and a
    _child_rules dictionary that maps from the field corresponding to
    each of those children to the rule within the _root_rules object
    that apply to those children (or None if no rule need apply).

    The _state variable takes the following states (in this order):
      NEW: container has been created and in tree with root rule
      RULED: attach_rules has been called and rules have been attached
      TYPED: _check_types has been called and the tree types check out
      TESTED: _check_tests has been called and the nodes have all tested out
      FORMED: _do_transform has been called and nodes replaced with transforms

    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, root=None, path=None, filename=None, rule=None):
        """Instantiate a new container object."""
        # pylint: disable=superfluous-parens
        assert not ((root is None) ^ (path is None))
        assert (root is None) ^ (rule is None)
        assert (rule is None) ^ (path is None)
        self._root = root if root is not None else self
        self._path = path
        self._root_rule = rule
        self._child_rules = collections.OrderedDict()
        self._filename = filename
        self._state = 'NEW'

    def _is_root(self):
        if self._root == self:
            assert self._path is None
            assert self._root_rule is not None
            return True
        assert self._path is not None
        assert self._root._root == self._root
        assert self._root._root_rule is not None
        return False

    def _get_root_rule(self):
        if self._is_root():
            return self._root_rule
        return self._root._root_rule

    def _check_types(self):
        """Check that config values matches attached-rule types.

        Any specified types in the attached rules are checked, raising
        a ParseError if not.  Note that the root call checks both its
        own type and those of the children, so recursive calls only
        need to check children.

        """
        assert self._state == 'RULED'
        if self._is_root():
            root_rule = self._get_root_rule()
            root_rule.check_type(self, None, self, self._filename)
        if not self._is_root() or not root_rule.nofollow:
            for field in self:
                subrule = self._child_rules[field]
                value = self[field]
                subpath = _path_join(self._path, field)
                subrule.check_type(self._root, subpath, value, self._filename)
                if isinstance(value, BaseYamlConfig) and not subrule.nofollow:
                    value._check_types()
        self._state = 'TYPED'

    def _check_tests(self):
        """Check that any tests in the attached rules validate the values.

        Raise a ParseError if not.  Note that the root call runs both
        its own test and those of the children, so recursive calls
        only need to check children.

        """
        assert self._state == 'TYPED'
        if self._is_root():
            root_rule = self._get_root_rule()
            root_rule.check_test(self, None, self, self._filename)
        if not self._is_root() or not root_rule.nofollow:
            for field in self:
                subrule = self._child_rules[field]
                value = self[field]
                subpath = _path_join(self._path, field)
                subrule.check_test(self._root, subpath, value, self._filename)
                if isinstance(value, BaseYamlConfig) and not subrule.nofollow:
                    value._check_tests()
        self._state = 'TESTED'

    def _do_transforms(self):
        """Run any attached transforms updating in place and returning result.

        Sweep through the config object and for any object that has an
        attached rule with a transform, run the transform, and return
        the transformed object.  If there is a chance that the
        top-level YamlConfig is going to be transformed, the caller
        should use the returned object and not simply assume in-place
        transformation of the conf object.

        """
        assert self._state == 'TESTED'
        is_formed = False
        if self._is_root():
            root_rule = self._get_root_rule()
            if root_rule.transform:
                rule = self._root_rule
                return rule.do_transform(self, None, self, self._filename)
        if not self._is_root() or not root_rule.nofollow:
            for field in self:
                subrule = self._child_rules[field]
                value = self[field]
                subpath = _path_join(self._path, field)
                tvalue = subrule.do_transform(
                    self._root, subpath, value, self._filename)
                if tvalue != value:
                    self[field] = tvalue
                    is_formed = True
                elif (isinstance(value, BaseYamlConfig) and
                      not subrule.nofollow):
                    value._do_transforms()
                    if value._state == 'FORMED':
                        is_formed = True
        if is_formed:
            self._state = 'FORMED'
        return self

    def __getattr__(self, field):
        """Allow access to fields as attributes.

        Provides some syntactic sugar by treating unresolved
        attributes as items, so that a caller can do
        "conf.sectionA.valueB" rather than having to write
        "conf['sectionA']['valueB']".  Note that we explicitly do not
        make setattr or delattr pass through.

        """
        return self[field]

    # Abstract methods must be implemented by child classes
    #  - len: returns the number of values in the container
    #  - contains: tests if the given value is a contained field name
    #  - iter: iterates over contained field names
    #  - getitem: retrieve a contained value given its field name
    #  - setitem: set the contained value given its field name and new value
    #  - delitem: delete the contained value given its field name

    @abc.abstractmethod
    def __len__(self):
        """(Abstract) Must return the number of items in the container."""

    @abc.abstractmethod
    def __contains__(self, field):
        """(Abstract) Must return true iff the field is in the container."""

    @abc.abstractmethod
    def __iter__(self):
        """(Abstract) Must return the list of fields in the container."""

    @abc.abstractmethod
    def __getitem__(self, field):
        """(Abstract) Must return the value associated with the given field."""

    @abc.abstractmethod
    def __setitem__(self, field, value):
        """(Abstract) Must set given field to given value."""

    @abc.abstractmethod
    def __delitem__(self, field):
        """(Abstract) Must delete given field."""


class YamlConfig(BaseYamlConfig):
    """Objects presents a dict-like interface to config values.

    In addition to exposing an indexed-lookup interface, these objects
    allow attr-like access.  They maintain a dictionary of the
    attributes, sorted in rule-addition order, not config-file order.
    Also supports get/set/delitem for the same attributes.  Note that
    we avoid creating any attributes without leading underscores to
    avoid collisions with config variables.  To iterate through the
    attributes, use iter to retrieve the keys (in the order they were
    added to the object).

    """

    def __init__(self, record, **kwargs):
        """Instantiate a new object from the given record."""
        assert isinstance(record, dict)
        super(YamlConfig, self).__init__(**kwargs)
        self._val = collections.OrderedDict()
        for key, value in record.items():
            subconf = _value_to_conf(self, key, value)
            self[key] = subconf

    def __len__(self):
        """Return the number of fields in the container."""
        return len(self._val)

    def __contains__(self, field):
        """Indicate if the field is in the container."""
        return field in self._val

    def __iter__(self):
        """Return a list of the fields in the container."""
        fields = list(self._child_rules.keys())
        for field in self._val.keys():
            if field not in fields:
                fields.append(field)
        return iter(fields)

    def __getitem__(self, field):
        """Return the value associated with the field."""
        return self._val[field]

    def __setitem__(self, field, value):
        """Set the given field to the given value."""
        self._val[field] = value

    def __delitem__(self, field):
        """Delete the given field from the container."""
        del self._val[field]


class YamlConfigList(BaseYamlConfig):
    """Objects presents a list-like interface to config values.

    Note that in some ways it is really more like a dictionary with
    consecutive numeric keys.  In particular, the iterator returns
    strings representing numbers from 0 to len-1, and the actual value
    at that index must be retrieved by converting the string to the
    corresponding index integer.  This makes the iterator interface
    usable the same way as a YamlConfig object.  Note that if provided
    a numeric index, it will provide some syntactic sugar and convert
    it to the string representation.

    Also note that this class handles tuple data structures by
    effectively converting them to lists.

    Finally, note that unlike a standard python list, this setitem
    interface enables appending to the list if the field index matches
    the length of the list.  In this way, a list x of len(x) == 5 can
    have 'foo' appended to it via x[5] = 'foo'.  This greatly
    simplifies the underlying code by collapsing YamlConfig and
    YamlConfigList special cases into one.

    """

    def __init__(self, record, root, **kwargs):
        """Instantiate a new object from the given list."""
        assert isinstance(record, (list, tuple, set))
        super(YamlConfigList, self).__init__(root=root, **kwargs)
        self._val = list()
        for idx, value in enumerate(record):
            subconf = _value_to_conf(self, str(idx), value)
            self.append(subconf)

    def __len__(self):
        """Return the number of items in the list."""
        return len(self._val)

    def __contains__(self, field):
        """Indicate if the field (a numeric index) is in the container."""
        field = _as_list_index(field)
        if isinstance(field, int):
            return 0 <= field < len(self)
        return False

    def __iter__(self):
        """Return the list of numeric index fields in the container.

        This returns a list of numeric strings starting at '0' and
        incrementing sequentially.  It does not return the list of
        values, the way a standard python list would.

        """
        return iter((str(idx) for idx in range(len(self._val))))

    def __getitem__(self, field):
        """Return the value corresponding to the given field index."""
        field = _as_list_index(field, validate=True)
        return self._val[field]

    def __setitem__(self, field, value):
        """Set the value at the given field index to the given value."""
        field = _as_list_index(field, validate=True)
        if isinstance(field, int) and field == len(self):
            self.append(value)
        else:
            self._val[field] = value

    def __delitem__(self, field):
        """Splice out the value at the given index."""
        field = _as_list_index(field, validate=True)
        del self._val[field]

    def insert(self, field, value):
        """Insert the given value at the given field index."""
        field = _as_list_index(field, validate=True)
        self._val.insert(field, value)

    def append(self, value):
        """Assign the given value to the next field index in the sequence."""
        field = len(self)
        self.insert(field, value)
