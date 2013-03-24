import re

from .base import Version, Matcher, VersionScheme


class LegacyVersion(Version):

    VERSION_PART_REGEX = re.compile(r'([a-z]+|\d+|[\.-])', re.I)
    VERSION_REPLACE = {
        "pre": "c",
        "preview": "c",
        "-": "final-",
        "rc": "c",
        "dev": "@",
        "": None,
        ".": None,
    }

    def parse(self, version_string):
        def _get_parts(version_string):
            result = []
            for part in self.VERSION_PART_REGEX.split(version_string.lower()):
                part = self.VERSION_REPLACE.get(part, part)
                if part:
                    if "0" <= part[:1] <= "9":
                        part = part.zfill(8)
                    else:
                        part = "*" + part
                    result.append(part)
            result.append("*final")
            return result

        result = []
        for part in _get_parts(version_string):
            if part.startswith("*"):
                if part < "*final":
                    while result and result[-1] == "*final-":
                        result.pop()
                while result and result[-1] == "00000000":
                    result.pop()
            result.append(part)
        return tuple(result)

    PREREL_TAGS = set(
        ['*a', '*alpha', '*b', '*beta', '*c', '*rc', '*r', '*@', '*pre']
    )

    @property
    def is_prerelease(self):
        return any(x in self.PREREL_TAGS for x in self._parts)


class LegacyMatcher(Matcher):

    version_class = LegacyVersion


class LegacyVersionScheme(VersionScheme):

    version_class = LegacyVersion
    matcher = LegacyMatcher
