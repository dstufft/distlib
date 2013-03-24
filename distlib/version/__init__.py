# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
"""
Implementation of a flexible versioning scheme providing support for PEP-386,
distribute-compatible and semantic versioning.
"""

import re

from .base import Version, Matcher, VersionScheme
from .standard import NormalizedVersion, NormalizedMatcher, NormalizedVersionScheme
from .legacy import LegacyVersion, LegacyMatcher, LegacyVersionScheme

__all__ = ['NormalizedVersion', 'NormalizedMatcher',
           'LegacyVersion', 'LegacyMatcher',
           'SemanticVersion', 'SemanticMatcher',
           'AdaptiveVersion', 'AdaptiveMatcher',
           'UnsupportedVersionError', 'HugeMajorVersionError',
           'suggest_semantic_version',
           'suggest_adaptive_version',
           'normalized_key', 'legacy_key', 'semantic_key', 'adaptive_key',
           'get_scheme']


# A marker used in the second and third parts of the `parts` tuple, for
# versions that don't have those segments, to sort properly. An example
# of versions in sort order ('highest' last):
#   1.0b1                 ((1,0), ('b',1), ('z',))
#   1.0.dev345            ((1,0), ('z',),  ('dev', 345))
#   1.0                   ((1,0), ('z',),  ('z',))
#   1.0.post256.dev345    ((1,0), ('z',),  ('z', 'post', 256, 'dev', 345))
#   1.0.post345           ((1,0), ('z',),  ('z', 'post', 345, 'z'))
#                                   ^        ^                 ^
#   'b' < 'z' ---------------------/         |                 |
#                                            |                 |
#   'dev' < 'z' ----------------------------/                  |
#                                                              |
#   'dev' < 'z' ----------------------------------------------/
# 'f' for 'final' would be kind of nice, but due to bugs in the support of
# 'rc' we must use 'z'
_FINAL_MARKER = ('z',)

_VERSION_RE = re.compile(r'''
    ^
    (?P<version>\d+\.\d+(\.\d+)*)          # minimum 'N.N'
    (?:
        (?P<prerel>[abc]|rc)       # 'a'=alpha, 'b'=beta, 'c'=release candidate
                                   # 'rc'= alias for release candidate
        (?P<prerelversion>\d+(?:\.\d+)*)
    )?
    (?P<postdev>(\.post(?P<post>\d+))?(\.dev(?P<dev>\d+))?)?
    $''', re.VERBOSE)


def _parse_numdots(s, full_ver, drop_zeroes=False, min_length=0):
    """Parse 'N.N.N' sequences, return a list of ints.

    @param s {str} 'N.N.N...' sequence to be parsed
    @param full_ver_str {str} The full version string from which this
           comes. Used for error strings.
    @param min_length {int} The length to which to pad the
           returned list with zeros, if necessary. Default 0.
    """
    result = []
    for n in s.split("."):
        #if len(n) > 1 and n[0] == '0':
        #    raise UnsupportedVersionError("cannot have leading zero in "
        #        "version number segment: '%s' in %r" % (n, full_ver))
        result.append(int(n))
    if drop_zeroes:
        while (result and result[-1] == 0 and
               (1 + len(result)) > min_length):
            result.pop()
    return result

def pep386_key(s, fail_on_huge_major_ver=True):
    """Parses a string version into parts using PEP-386 logic."""

    match = _VERSION_RE.search(s)
    if not match:
        raise ValueError(s)

    groups = match.groupdict()
    parts = []

    # main version
    block = _parse_numdots(groups['version'], s, min_length=2)
    parts.append(tuple(block))

    # prerelease
    prerel = groups.get('prerel')
    if prerel is not None:
        block = [prerel]
        block += _parse_numdots(groups.get('prerelversion'), s, min_length=1)
        parts.append(tuple(block))
    else:
        parts.append(_FINAL_MARKER)

    # postdev
    if groups.get('postdev'):
        post = groups.get('post')
        dev = groups.get('dev')
        postdev = []
        if post is not None:
            postdev.extend((_FINAL_MARKER[0], 'post', int(post)))
            if dev is None:
                postdev.append(_FINAL_MARKER[0])
        if dev is not None:
            postdev.extend(('dev', int(dev)))
        parts.append(tuple(postdev))
    else:
        parts.append(_FINAL_MARKER)
    if fail_on_huge_major_ver and parts[0][0] > 1980:
        raise ValueError("huge major version number, %r, "
           "which might cause future problems: %r" % (parts[0][0], s))
    return tuple(parts)


PEP426_VERSION_RE = re.compile('^(\d+\.\d+(\.\d+)*)((a|b|c|rc)(\d+))?'
                               '(\.(post)(\d+))?(\.(dev)(\d+))?$')

def pep426_key(s, _=None):
    s = s.strip()
    m = PEP426_VERSION_RE.match(s)
    if not m:
        raise ValueError('Not a valid version: %s' % s)
    groups = m.groups()
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
            pre = ('a', -1) # to sort before a0
        else:
            pre = ('z',)    # to sort after all pre-releases
    # now look at the state of post and dev.
    if not post:
        post = ('_',)   # sort before 'a'
    if not dev:
        dev = ('final',)

    #print('%s -> %s' % (s, m.groups()))
    return nums, pre, post, dev


normalized_key = pep426_key


class UnlimitedMajorVersion(Version):
    def parse(self, s): return normalized_key(s, False)


_REPLACEMENTS = (
    (re.compile('[.+-]$'), ''),                     # remove trailing puncts
    (re.compile(r'^[.](\d)'), r'0.\1'),             # .N -> 0.N at start
    (re.compile('^[.-]'), ''),                      # remove leading puncts
    (re.compile(r'^\((.*)\)$'), r'\1'),             # remove parentheses
    (re.compile(r'^v(ersion)?\s*(\d+)'), r'\2'),    # remove leading v(ersion)
    (re.compile(r'^r(ev)?\s*(\d+)'), r'\2'),        # remove leading v(ersion)
    (re.compile('[.]{2,}'), '.'),                   # multiple runs of '.'
    (re.compile(r'\b(alfa|apha)\b'), 'alpha'),      # misspelt alpha
    (re.compile(r'\b(pre-alpha|prealpha)\b'),
                'pre.alpha'),                       # standardise
    (re.compile(r'\(beta\)$'), 'beta'),             # remove parentheses
)

_SUFFIX_REPLACEMENTS = (
    (re.compile('^[:~._+-]+'), ''),                   # remove leading puncts
    (re.compile('[,*")([\]]'), ''),                        # remove unwanted chars
    (re.compile('[~:+_ -]'), '.'),                    # replace illegal chars
    (re.compile('[.]{2,}'), '.'),                   # multiple runs of '.'
    (re.compile(r'\.$'), ''),                       # trailing '.'
)

_NUMERIC_PREFIX = re.compile(r'(\d+(\.\d+)*)')

def suggest_semantic_version(s):
    """
    Try to suggest a semantic form for a version for which
    suggest_normalized_version couldn't come up with anything.
    """
    result = s.strip().lower()
    for pat, repl in _REPLACEMENTS:
        result = pat.sub(repl, result)
    if not result:
        result = '0.0.0'

    # Now look for numeric prefix, and separate it out from
    # the rest.
    #import pdb; pdb.set_trace()
    m = _NUMERIC_PREFIX.match(result)
    if not m:
        prefix = '0.0.0'
        suffix = result
    else:
        prefix = m.groups()[0].split('.')
        prefix = [int(i) for i in prefix]
        while len(prefix) < 3:
            prefix.append(0)
        if len(prefix) == 3:
            suffix = result[m.end():]
        else:
            suffix = '.'.join([str(i) for i in prefix[3:]]) + result[m.end():]
            prefix = prefix[:3]
        prefix = '.'.join([str(i) for i in prefix])
        suffix = suffix.strip()
    if suffix:
        #import pdb; pdb.set_trace()
        # massage the suffix.
        for pat, repl in _SUFFIX_REPLACEMENTS:
            suffix = pat.sub(repl, suffix)

    if not suffix:
        result = prefix
    else:
        sep = '-' if 'dev' in suffix else '+'
        result = prefix + sep + suffix
    if not is_semver(result):
        result = None
    return result


def suggest_adaptive_version(s):
    return NormalizedVersionScheme().suggest(s) or suggest_semantic_version(s)



#
#   Semantic versioning
#

_SEMVER_RE = re.compile(r'^(\d+)\.(\d+)\.(\d+)'
                        r'(-[a-z0-9]+(\.[a-z0-9-]+)*)?'
                        r'(\+[a-z0-9]+(\.[a-z0-9-]+)*)?$', re.I)

def is_semver(s):
    return _SEMVER_RE.match(s)

def semantic_key(s):
    def make_tuple(s, absent):
        if s is None:
            result = (absent,)
        else:
            parts = s[1:].split('.')
            # We can't compare ints and strings on Python 3, so fudge it
            # by zero-filling numeric values so simulate a numeric comparison
            result = tuple([p.zfill(8) if p.isdigit() else p for p in parts])
        return result

    result = None
    m = is_semver(s)
    if not m:
        raise ValueError(s)
    groups = m.groups()
    major, minor, patch = [int(i) for i in groups[:3]]
    # choose the '|' and '*' so that versions sort correctly
    pre, build = make_tuple(groups[3], '|'), make_tuple(groups[5], '*')
    return ((major, minor, patch), pre, build)


class SemanticVersion(Version):
    def parse(self, s): return semantic_key(s)

    @property
    def is_prerelease(self):
        return self._parts[1][0] != '|'


class SemanticMatcher(Matcher):
    version_class = SemanticVersion

#
# Adaptive versioning. When handed a legacy version string, tries to
# determine a suggested normalized version, and work with that.
#

def adaptive_key(s):
    try:
        result = normalized_key(s, False)
    except ValueError:
        ss = NormalizedVersionScheme().suggest(s)
        if ss is not None:
            result = normalized_key(ss)     # "guaranteed" to work
        else:
            ss = s # suggest_semantic_version(s) or s
            result = semantic_key(ss)       # let's hope ...
    return result


class AdaptiveVersion(NormalizedVersion):
    def parse(self, s): return adaptive_key(s)

    @property
    def is_prerelease(self):
        try:
            normalized_key(self._string)
            not_sem = True
        except ValueError:
            ss = NormalizedVersionScheme().suggest(self._string)
            not_sem = ss is not None
        if not_sem:
            return any(t[0] in self.PREREL_TAGS for t in self._parts)
        return self._parts[1][0] != '|'

class AdaptiveMatcher(NormalizedMatcher):
    version_class = AdaptiveVersion


_SCHEMES = {
    'normalized': NormalizedVersionScheme(),
    'legacy': LegacyVersionScheme(),
    'semantic': VersionScheme(SemanticVersion, SemanticMatcher,
                              suggest_semantic_version),
    'adaptive': VersionScheme(AdaptiveVersion, AdaptiveMatcher,
                              suggest_adaptive_version),
}

_SCHEMES['default'] = _SCHEMES['adaptive']

def get_scheme(name):
    if name not in _SCHEMES:
        raise ValueError('unknown scheme name: %r' % name)
    return _SCHEMES[name]
