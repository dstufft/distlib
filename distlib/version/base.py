import re

from ..compat import string_types


class Version(object):

    def __init__(self, s):
        self._string = s.strip()
        self._parts = self.parse(self._string)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self._string)

    def __str__(self):
        return self._string

    def parse(self, s):
        raise NotImplementedError('please implement in a subclass')

    def _check_compatible(self, other):
        if type(self) != type(other):
            raise TypeError('cannot compare %r and %r' % (self, other))

    def __eq__(self, other):
        self._check_compatible(other)
        return self._parts == other._parts

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        self._check_compatible(other)
        return self._parts < other._parts

    def __gt__(self, other):
        return not (self.__lt__(other) or self.__eq__(other))

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)

    # See http://docs.python.org/reference/datamodel#object.__hash__
    def __hash__(self):
        return hash(self._parts)

    @property
    def is_prerelease(self):
        raise NotImplementedError('Please implement in subclasses.')


class Matcher(object):
    version_class = None

    predicate_re = re.compile(r"^(\w[\s\w'.-]*)(\((.*)\))?")
    constraint_re = re.compile(r'^(<=|>=|<|>|!=|==)?\s*([^\s,]+)$')

    _operators = {
        "<": lambda x, y: x < y,
        ">": lambda x, y: x > y,
        "<=": lambda x, y: x == y or x < y,
        ">=": lambda x, y: x == y or x > y,
        "==": lambda x, y: x == y,
        "!=": lambda x, y: x != y,
    }

    def __init__(self, s):
        if self.version_class is None:
            raise ValueError('Please specify a version class')
        self._string = s = s.strip()
        m = self.predicate_re.match(s)
        if not m:
            raise ValueError('Not valid: %r' % s)
        groups = m.groups('')
        self.name = groups[0].strip()
        self.key = self.name.lower()    # for case-insensitive comparisons
        clist = []
        if groups[2]:
            constraints = [c.strip() for c in groups[2].split(',')]
            for c in constraints:
                m = self.constraint_re.match(c)
                if not m:
                    raise ValueError('Invalid %r in %r' % (c, s))
                groups = m.groups('==')
                clist.append((groups[0], self.version_class(groups[1])))
        self._parts = tuple(clist)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self._string)

    def __str__(self):
        return self._string

    def match(self, version):
        """Check if the provided version matches the constraints."""
        if isinstance(version, string_types):
            version = self.version_class(version)
        for operator, constraint in self._parts:
            if not self._operators[operator](version, constraint):
                return False
        return True

    @property
    def exact_version(self):
        result = None
        if len(self._parts) == 1 and self._parts[0][0] == '==':
            result = self._parts[0][1]
        return result

    def _check_compatible(self, other):
        if type(self) != type(other) or self.name != other.name:
            raise TypeError('cannot compare %s and %s' % (self, other))

    def __eq__(self, other):
        self._check_compatible(other)
        return (self.key == other.key and self._parts == other._parts)

    def __ne__(self, other):
        return not self.__eq__(other)

    # See http://docs.python.org/reference/datamodel#object.__hash__
    def __hash__(self):
        return hash(self.key) + hash(self._parts)


class VersionScheme(object):

    version_class = None
    matcher = None

    def __init__(self, version_class=None, matcher=None, suggester=None):
        if version_class is not None:
            self.version_class = version_class

        if matcher is not None:
            self.matcher = matcher

        if suggester is not None:
            self.suggest = suggester

        if self.version_class is None:
            raise TypeError("There is no defined version class for %s" % str(self))

        if self.matcher is None:
            raise TypeError("There is no defined matcher for %s" % str(self))

    def __call__(self, version_string):
        """
        Constucts and returns a Version instance of this scheme.
        """
        if self.version_class is None:
            raise TypeError("%s has no associated version class" % str(self))
        return self.version_class(version_string)

    def is_valid_version(self, s):
        try:
            self.version_class(s)
            result = True
        except ValueError:
            result = False
        return result

    def is_valid_matcher(self, s):
        try:
            self.matcher(s)
            result = True
        except ValueError:
            result = False
        return result

    def is_valid_constraint_list(self, s):
        """
        Used for processing some metadata fields
        """
        return self.is_valid_matcher('dummy_name (%s)' % s)

    def suggest(self, s):
        return s
