import re

from .base import Version, Matcher, VersionScheme


def _match_at_front(x, y):
    # We want '2.5' to match '2.5.4' but not '2.50'.
    if x == y:
        return True
    x = str(x)
    y = str(y)
    if not x.startswith(y):
        return False
    n = len(y)
    return x[n] == '.'


class NormalizedVersion(Version):
    """A rational version.

    Good:
        1.2         # equivalent to "1.2.0"
        1.2.0
        1.2a1
        1.2.3a2
        1.2.3b1
        1.2.3c1
        1.2.3.4
        TODO: fill this out

    Bad:
        1           # mininum two numbers
        1.2a        # release level must have a release serial
        1.2.3b
    """

    VERSION_REGEX = re.compile(r'^(\d+\.\d+(\.\d+)*)((a|b|c|rc)(\d+))?'
                               r'(\.(post)(\d+))?(\.(dev)(\d+))?$')

    def parse(self, version_string):
        version_string = version_string.strip()

        matches = self.VERSION_REGEX.match(version_string)
        if not matches:
            raise ValueError("Not a valid version: '%s'" % version_string)

        groups = matches.groups()
        nums = tuple(int(v) for v in groups[0].split('.'))
        while len(nums) > 1 and nums[-1] == 0:
            nums = nums[:-1]

        pre = groups[3:5]
        post = groups[6:8]
        dev = groups[9:11]
        if pre == (None, None):
            pre = ()
        else:
            pre = pre[0], int(pre[1])
        if post == (None, None):
            post = ()
        else:
            post = post[0], int(post[1])
        if dev == (None, None):
            dev = ()
        else:
            dev = dev[0], int(dev[1])
        if not pre:
            # either before pre-release, or final release and after
            if not post and dev:
                # before pre-release
                pre = ('a', -1)  # to sort before a0
            else:
                pre = ('z',)    # to sort after all pre-releases
        # now look at the state of post and dev.
        if not post:
            post = ('_',)   # sort before 'a'
        if not dev:
            dev = ('final',)

        #print('%s -> %s' % (s, m.groups()))
        return nums, pre, post, dev

    PREREL_TAGS = set(['a', 'b', 'c', 'rc', 'dev'])

    @property
    def is_prerelease(self):
        return any(t[0] in self.PREREL_TAGS for t in self._parts)


class NormalizedMatcher(Matcher):
    version_class = NormalizedVersion

    _operators = dict(Matcher._operators)
    _operators.update({
        "<=": lambda x, y: _match_at_front(x, y) or x < y,
        ">=": lambda x, y: _match_at_front(x, y) or x > y,
        "==": lambda x, y: _match_at_front(x, y),
        "!=": lambda x, y: not _match_at_front(x, y),
    })


class NormalizedVersionScheme(VersionScheme):

    version_class = NormalizedVersion
    matcher = NormalizedMatcher

    def suggest(self, version_string):
        """
        Suggest a normalized version close to the given version string.

        If you have a version string that isn't rational (i.e. NormalizedVersion
        doesn't like it) then you might be able to get an equivalent (or close)
        rational version from this function.

        This does a number of simple normalizations to the given string, based
        on observation of versions currently in use on PyPI. Given a dump of
        those version during PyCon 2009, 4287 of them:
        - 2312 (53.93%) match NormalizedVersion without change
          with the automatic suggestion
        - 3474 (81.04%) match when using this suggestion method

        @param s {str} An irrational version string.
        @returns A rational version string, or None, if couldn't determine one.
        """
        try:
            self.version_class(version_string)
            return version_string
        except ValueError:
            pass

        suggested = version_string.lower()

        # part of this could use maketrans
        for orig, repl in (('-alpha', 'a'), ('-beta', 'b'), ('alpha', 'a'),
                           ('beta', 'b'), ('rc', 'c'), ('-final', ''),
                           ('-pre', 'c'),
                           ('-release', ''), ('.release', ''), ('-stable', ''),
                           ('+', '.'), ('_', '.'), (' ', ''), ('.final', ''),
                           ('final', '')):
            suggested = suggested.replace(orig, repl)

        # if something ends with dev or pre, we add a 0
        suggested = re.sub(r"pre$", r"pre0", suggested)
        suggested = re.sub(r"dev$", r"dev0", suggested)

        # if we have something like "b-2" or "a.2" at the end of the
        # version, that is pobably beta, alpha, etc
        # let's remove the dash or dot
        suggested = re.sub(r"([abc]|rc)[\-\.](\d+)$", r"\1\2", suggested)

        # 1.0-dev-r371 -> 1.0.dev371
        # 0.1-dev-r79 -> 0.1.dev79
        suggested = re.sub(r"[\-\.](dev)[\-\.]?r?(\d+)$", r".\1\2", suggested)

        # Clean: 2.0.a.3, 2.0.b1, 0.9.0~c1
        suggested = re.sub(r"[.~]?([abc])\.?", r"\1", suggested)

        # Clean: v0.3, v1.0
        if suggested.startswith('v'):
            suggested = suggested[1:]

        # Clean leading '0's on numbers.
        #TODO: unintended side-effect on, e.g., "2003.05.09"
        # PyPI stats: 77 (~2%) better
        suggested = re.sub(r"\b0+(\d+)(?!\d)", r"\1", suggested)

        # Clean a/b/c with no version. E.g. "1.0a" -> "1.0a0". Setuptools infers
        # zero.
        # PyPI stats: 245 (7.56%) better
        suggested = re.sub(r"(\d+[abc])$", r"\g<1>0", suggested)

        # the 'dev-rNNN' tag is a dev tag
        suggested = re.sub(r"\.?(dev-r|dev\.r)\.?(\d+)$", r".dev\2", suggested)

        # clean the - when used as a pre delimiter
        suggested = re.sub(r"-(a|b|c)(\d+)$", r"\1\2", suggested)

        # a terminal "dev" or "devel" can be changed into ".dev0"
        suggested = re.sub(r"[\.\-](dev|devel)$", r".dev0", suggested)

        # a terminal "dev" can be changed into ".dev0"
        suggested = re.sub(r"(?![\.\-])dev$", r".dev0", suggested)

        # a terminal "final" or "stable" can be removed
        suggested = re.sub(r"(final|stable)$", "", suggested)

        # The 'r' and the '-' tags are post release tags
        #   0.4a1.r10       ->  0.4a1.post10
        #   0.9.33-17222    ->  0.9.33.post17222
        #   0.9.33-r17222   ->  0.9.33.post17222
        suggested = re.sub(r"\.?(r|-|-r)\.?(\d+)$", r".post\2", suggested)

        # Clean 'r' instead of 'dev' usage:
        #   0.9.33+r17222   ->  0.9.33.dev17222
        #   1.0dev123       ->  1.0.dev123
        #   1.0.git123      ->  1.0.dev123
        #   1.0.bzr123      ->  1.0.dev123
        #   0.1a0dev.123    ->  0.1a0.dev123
        # PyPI stats:  ~150 (~4%) better
        suggested = re.sub(r"\.?(dev|git|bzr)\.?(\d+)$", r".dev\2", suggested)

        # Clean '.pre' (normalized from '-pre' above) instead of 'c' usage:
        #   0.2.pre1        ->  0.2c1
        #   0.2-c1         ->  0.2c1
        #   1.0preview123   ->  1.0c123
        # PyPI stats: ~21 (0.62%) better
        suggested = re.sub(r"\.?(pre|preview|-c)(\d+)$", r"c\g<2>", suggested)

        # Tcl/Tk uses "px" for their post release markers
        suggested = re.sub(r"p(\d+)$", r".post\1", suggested)

        try:
            self.version_class(suggested)
        except ValueError:
            suggested = None

        return suggested
