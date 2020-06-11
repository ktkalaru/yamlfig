"""Module contains functions that test for common config patterns.

Standard test functions and higher-order functions for use with
yamlfig's rule testing functionality.  Function names that begin with
is_* are meant to be passed as the test parameter when instantiating
or adding a YamlConfigRule.  Many of the tests include a variant with
match_* which simply takes the value to be tested.  Both variants
return None if the test succeeds and a string explaining the error if
not.  The match variants are standalone and can incorporate
functionally equivalent testing into other code.

"""

# Standard modules
import os
import re


def is_interval(lower, upper, exclude_lower=False, include_upper=False):
    """Test that value is within the specified interval.

    The lower is the bottom of the interval, and upper is the top.  By
    default, the interval includes the lower bound and excludes the
    upper bound, for consistency with python ranges and lots of other
    things.  In mathematical notation, the default is: [lower, upper)

    The exclude_lower flag will exclude the lower bound, and the
    include_upper flag will include the upper bound.

    Note that since the implementation relies only on inequality
    comparisons which are implemented for all objects, by providing
    lower and upper of type str, the intervals can be defined as more
    lexicographical or otherwise, based on the object type.

    """
    # pylint: disable=unused-argument # args defined by test definition
    lowersym = '(' if exclude_lower else '['
    uppersym = ']' if include_upper else ')'
    intervalstr = '{0}{1}, {2}{3}'.format(
        lowersym, repr(lower), repr(upper), uppersym)
    if (lower > upper or (lower == upper and (
            exclude_lower or not include_upper))):
        raise ValueError('invalid interval "{0}"'.format(intervalstr))

    def is_interval_test(conf, path, value):
        if value < lower or (value <= lower and exclude_lower):
            return u'{0} is below the interval {1}'.format(
                repr(value), intervalstr)
        if value > upper or (value >= upper and not include_upper):
            return u'{0} is above the interval {1}'.format(
                repr(value), intervalstr)
        return None

    return is_interval_test


def is_regex(regex, invert=False):
    """Test that value matches the given regex.

    The regular expression is searched against the value, so a match
    in the middle of the value will succeed.  To specifically match
    the beginning or the whole regex, use anchor characters.  If
    invert is true, then matching the regex will cause the test to
    fail.

    """
    # pylint: disable=unused-argument # args defined by test definition
    rex = re.compile(regex)

    def is_regex_test(conf, path, value):
        match = rex.search(value)
        if invert and match:
            return u'"{0}" matches /{1}/'.format(value, regex)
        if not invert and not match:
            return u'"{0}" does not match /{1}/'.format(value, regex)
        return None

    return is_regex_test


def match_is_ipv4_address(value):
    """Match given value as a valid dotted-quad IPv4 address."""
    # Apply the dotted-quad pattern to the string and detect a mismatch
    try:
        match = re.search(r'^(\d+)\.(\d+)\.(\d+)\.(\d+)$', value)
    except TypeError:
        return u'{0} must be a string in IPv4 dotted-quad notation'.format(
            repr(value))
    if not match:
        return u'"{0}" must be in IPv4 dotted-quad notation'.format(
            value)

    # Validate the range of each octet
    octets = [int(x) for x in match.groups()]
    for idx, octet in enumerate(octets):
        if octet > 255:
            return '{0} octet of "{1}" exceeds 255'.format(
                ['1st', '2nd', '3rd', '4th'][idx], value)

    return None


def is_ipv4_address(conf, path, value):
    """Test that value is a valid dotted-quad IPv4 address."""
    # pylint: disable=unused-argument # args defined by test definition
    return match_is_ipv4_address(value)


def match_is_domain_name(value):
    """Match given value against the format of a DNS domain name.

    Primary reference(s):
    https://en.wikipedia.org/wiki/Domain_Name_System

    """
    # pylint: disable=too-many-return-statements
    if value is None or len(value) == 0:
        return u'domain {0} cannot be empty'.format(repr(value))
    labels = value.split('.')
    if len(labels) > 127:
        return u'domain "{0}" cannot have more than 127 labels'.format(
            value)
    for label in labels:
        if len(label) == 0:
            return u'domain "{0}" cannot have an empty label'.format(value)
        if len(label) >= 63:
            return u'domain "{0}" cannot have a 63+ byte label'.format(value)
        match = re.search('([^A-Za-z0-9-])', label)
        if match:
            return u'domain "{0}" cannot contain "{1}"'.format(
                value, match.group(1))
        if label.startswith('-') or label.endswith('-'):
            return u'domain "{0}" label cannot start or end with "-"'.format(
                value)
    if re.search('^[0-9]+$', labels[-1]):
        return u'domain "{0}" top-level domain cannot be only digits'.format(
            value)
    return None


def is_domain_name(conf, path, value):
    """Test that the value matches the format of a DNS domain name."""
    # pylint: disable=unused-argument # args defined by test definition
    return match_is_domain_name(value)


def match_is_email_address(value):
    """Match the value matches the format of an email address.

    Primary reference(s):
    https://en.wikipedia.org/wiki/Email_address

    Note that the characters and character sequences allowed in the
    case of a quoted user part is likely still both over and under
    restrictive.  Authoritatively parsing an email address is likely
    beyond the scope of these pre-packaged testers.

    """
    # pylint: disable=too-many-return-statements, too-many-branches
    if value is None or len(value) == 0:
        return u'email address {0} cannot be empty'.format(repr(value))
    partmatch = re.search('^(?P<userpart>.*)@(?P<domainpart>.*)$', value)
    if not partmatch:
        return u'"{0}" is not of the form username@domain'.format(value)
    userpart, domainpart = partmatch.groups()
    if len(userpart) == 0:
        return u'{0} has empty userpart'.format(repr(value))
    if len(userpart) >= 64:
        return u'{0} has 64+ byte userpart'.format(repr(value))
    if not userpart.startswith('"') or not userpart.endswith('"'):
        match = re.search(r'([^A-Za-z0-9!#$%&\'*+/=?^_`{|}~.-])', userpart)
        if match:
            return u'{0} unquoted userpart cannot contain {1}'.format(
                repr(value), repr(match.group(1)))
        if userpart.startswith('.') or userpart.endswith('.'):
            return u'{0} unquoted userpart cannot start or end with "."'.format(
                repr(value))
        if '..' in userpart:
            return u'{0} unquoted userpart cannot contain ".."'.format(
                repr(value))
    else:
        qcpart = userpart[1:-1]
        match = re.search(
            r'([^A-Za-z0-9!#$%&\'*+/=?^_`{|}~.(),:;<>@\[\]\ -])', qcpart)
        if match:
            return (
                u'{0} userpart quoted content cannot contain "{1}"'.format(
                    repr(value), match.group(1)))
    if len(domainpart) == 0:
        return u'"{0} has empty domainpart'.format(value)
    if len(domainpart) >= 63:
        return u'"{0} has 63+ byte domainpart'.format(value)
    test_domain_error = match_is_domain_name(domainpart)
    if test_domain_error is not None:
        return test_domain_error
    return None


def is_email_address(conf, path, value):
    """Test that value matches the format of an email address."""
    # pylint: disable=unused-argument # args defined by test definition
    return match_is_email_address(value)


def match_is_url(value):
    """Match the value against the format of a URL.

    These patterns were derived from discussions on various websites;
    most notably the following site deserves a lot of credit:

      https://mathiasbynens.be/demo/url-regex

    A pattern from that site has been tweaked through subsequent
    experience and testing, but this test is best-effort and provides
    nothing in the way of diagnostics.

    """
    rexlist = [
        r'^((?:[A-Za-z]{3,9}:(?:\/\/)?)' +
        r'(?:[\-;:&=\+\$,\w]+@)?[A-Za-z0-9\.\-]+' +
        r'(?::[0-9]+)?(?:(?:\/[\+~%\/\.\w\-_]*)?\??(?:[\-\+\/=&;%@\.\w_]*)#?' +
        r'(?:[\.\!\/\\\w&=-]*))?)$',
        r'^((?:www\.|[\-;:&=\+\$,\w]+@)[A-Za-z0-9\.\-]+' +
        r'(?:(?:\/[\+~%\/\.\w\-_]*)?\??(?:[\-\+\/=&;%@\.\w_]*)' +
        r'#?(?:[\.\!\/\\\w]*))?)$']
    if value is None or len(value) == 0:
        return u'url {0} cannot be empty'.format(repr(value))
    for rex in rexlist:
        if re.search(rex, value):
            return None
    return u'"{0}" was not recognized as a valid url'.format(value)


def is_url(conf, path, value):
    """Test that value matches the format of a URL."""
    # pylint: disable=unused-argument # args defined by test definition
    return match_is_url(value)


def is_file_path(*ostests):
    """Create test of value against the given set of file-metadata properties.

    One or more of the following ostest values can be given:
      [!]exists:   test that the path exists (!: not exist)
      [!]isdir:    test that the path is a directory  (!: not a directory)
      [!]isfile:   test that the path is a file (!: not a file)
      [!]islink:   test that the path is a symbolic link (!: not a link)
      [!]ismount:  test that the path is a mount point (!: not a mount point)

    They will be tested in the order given, so they can be strung
    together to ensure a most helpful error message (e.g., exists,
    isdir) to first test whether the path exists, so a non-existent
    path will generate a "does not exist" error rather than the less
    helpful "is not a directory" error.

    """
    # pylint: disable=unused-argument # args defined by test definition
    for ostest in ostests:
        assert ostest in [
            'exists', '!exists',
            'isdir', '!isdir',
            'isfile', '!isfile',
            'islink', '!islink',
            'ismount', '!ismount']

    def is_file_path_test(conf, path, value):
        res = []
        for ostest in ostests:
            if ostest == 'exists' and not os.path.exists(value):
                res.append(u'"{0}" does not exist'.format(value))
            elif ostest == '!exists' and os.path.exists(value):
                res.append(u'"{0}" exists'.format(value))
            elif ostest == 'isdir' and not os.path.isdir(value):
                res.append(u'"{0}" is not a directory'.format(value))
            elif ostest == '!isdir' and os.path.isdir(value):
                res.append(u'"{0}" is a directory'.format(value))
            elif ostest == 'isfile' and not os.path.isfile(value):
                res.append(u'"{0}" is not a file'.format(value))
            elif ostest == '!isfile' and os.path.isfile(value):
                res.append(u'"{0}" is a file'.format(value))
            elif ostest == 'islink' and not os.path.islink(value):
                res.append(u'"{0}" is not a symlink'.format(value))
            elif ostest == '!islink' and os.path.islink(value):
                res.append(u'"{0}" is a symlink'.format(value))
            elif ostest == 'ismount' and not os.path.ismount(value):
                res.append(u'"{0}" is not a mount point'.format(value))
            elif ostest == '!ismount' and os.path.ismount(value):
                res.append(u'"{0}" is a mount point'.format(value))
        if len(res) > 0:
            return u' and '.join(res)
        return None
    return is_file_path_test
