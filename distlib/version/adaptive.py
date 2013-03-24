from .base import Version, Matcher, VersionScheme
from .normalized import NormalizedVersionScheme, NormalizedMatcher
from .semantic import SemanticVersionScheme


class AdaptiveVersion(Version):

    # Adaptive Acts as a combined set of versions, falling back each time
    version_schemes = [
        # Scheme, Suggest?
        (NormalizedVersionScheme, True),
        (SemanticVersionScheme, False),
    ]

    def __new__(cls, version_string):
        for scheme, should_suggest in cls.version_schemes:
            try:
                # See if this is a valid version
                return scheme.version_class(version_string)
            except ValueError:
                if should_suggest:
                    # Attempt to see if we can suggest a valid version
                    suggested = scheme().suggest(version_string)
                    if suggested:
                        return scheme.version_class(suggested)
        else:
            return super(AdaptiveVersion, cls).__new__(cls, version_string)

    def parse(self, version_string):
        raise ValueError("Not a valid version: '%s'" % version_string)


class AdaptiveMatcher(NormalizedMatcher, Matcher):

    version_class = AdaptiveVersion


class AdaptiveVersionScheme(VersionScheme):

    version_class = AdaptiveVersion
    matcher = AdaptiveMatcher

    version_schemes = [
        NormalizedVersionScheme,
        SemanticVersionScheme,
    ]

    def suggest(self, version_string):
        # Try to run through each of the version_schemes suggest functions
        for scheme in self.version_schemes:
            suggested = scheme().suggest(version_string)
            if suggested:
                return suggested
