import re

from .base import Version, Matcher


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
