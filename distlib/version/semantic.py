import re

from .base import Version, Matcher, VersionScheme


class SemanticVersion(Version):

    SEMVER_REGEX = re.compile(r'^(\d+)\.(\d+)\.(\d+)'
                              r'(-[a-z0-9]+(\.[a-z0-9-]+)*)?'
                              r'(\+[a-z0-9]+(\.[a-z0-9-]+)*)?$', re.I)

    def parse(self, version_string):
        def _make_tuple(s, absent):
            if s is None:
                result = (absent,)
            else:
                parts = s[1:].split('.')
                # We can't compare ints and strings on Python 3, so fudge it
                # by zero-filling numeric values so simulate a numeric
                #   comparison
                result = tuple(
                    [p.zfill(8) if p.isdigit() else p for p in parts])
            return result

        matches = self.SEMVER_REGEX.match(version_string)

        if not matches:
            raise ValueError("Not a valid version: '%s'" % version_string)

        groups = matches.groups()
        major, minor, patch = [int(i) for i in groups[:3]]

        # choose the '|' and '*' so that versions sort correctly
        pre, build = _make_tuple(groups[3], '|'), _make_tuple(groups[5], '*')

        return ((major, minor, patch), pre, build)

    @property
    def is_prerelease(self):
        return self._parts[1][0] != '|'


class SemanticMatcher(Matcher):
    version_class = SemanticVersion


class SemanticVersionScheme(VersionScheme):

    version_class = SemanticVersion
    matcher = SemanticMatcher

    _REPLACEMENTS = (
        (re.compile('[.+-]$'), ''),                   # remove trailing puncts
        (re.compile(r'^[.](\d)'), r'0.\1'),           # .N -> 0.N at start
        (re.compile('^[.-]'), ''),                    # remove leading puncts
        (re.compile(r'^\((.*)\)$'), r'\1'),           # remove parentheses
        (re.compile(r'^v(ersion)?\s*(\d+)'), r'\2'),  # remove leading v(ersion)
        (re.compile(r'^r(ev)?\s*(\d+)'), r'\2'),      # remove leading v(ersion)
        (re.compile('[.]{2,}'), '.'),                 # multiple runs of '.'
        (re.compile(r'\b(alfa|apha)\b'), 'alpha'),    # misspelt alpha
        (re.compile(r'\b(pre-alpha|prealpha)\b'),
            'pre.alpha'),                             # standardise
        (re.compile(r'\(beta\)$'), 'beta'),           # remove parentheses
    )

    _SUFFIX_REPLACEMENTS = (
        (re.compile('^[:~._+-]+'), ''),               # remove leading puncts
        (re.compile('[,*")([\]]'), ''),               # remove unwanted chars
        (re.compile('[~:+_ -]'), '.'),                # replace illegal chars
        (re.compile('[.]{2,}'), '.'),                 # multiple runs of '.'
        (re.compile(r'\.$'), ''),                     # trailing '.'
    )

    _NUMERIC_PREFIX = re.compile(r'(\d+(\.\d+)*)')

    def suggest(self, version_string):
        """
        Try to suggest a semantic form for a version for which
        suggest_normalized_version couldn't come up with anything.
        """
        suggested = version_string.strip().lower()

        for pat, repl in self._REPLACEMENTS:
            suggested = pat.sub(repl, suggested)

        if not suggested:
            suggested = "0.0.0"

        # Now look for numeric prefix, and separate it out from
        # the rest.
        matches = self._NUMERIC_PREFIX.match(suggested)
        if not matches:
            prefix = "0.0.0"
            suffix = suggested
        else:
            prefix = matches.groups()[0].split(".")
            prefix = [int(i) for i in prefix]
            while len(prefix) < 3:
                prefix.append(0)
            if len(prefix) == 3:
                suffix = suggested[matches.end():]
            else:
                suffix = ".".join(
                    [str(i) for i in prefix[3:]]) + suggested[matches.end():]
                prefix = prefix[:3]
            prefix = ".".join([str(i) for i in prefix])
            suffix = suffix.strip()
        if suffix:
            # Massage the suffix
            for pat, repl in self._SUFFIX_REPLACEMENTS:
                suffix = pat.sub(repl, suffix)

        if not suffix:
            suggested = prefix
        else:
            sep = "-" if "dev" in suffix else "+"
            suggested = prefix + sep + suffix

        try:
            self.version_class(suggested)
        except ValueError:
            suggested = None

        return suggested
