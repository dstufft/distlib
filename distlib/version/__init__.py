# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
"""
Implementation of a flexible versioning scheme providing support for PEP-426,
distribute-compatible and semantic versioning.
"""

from .standard import NormalizedVersion, NormalizedMatcher, NormalizedVersionScheme
from .semantic import SemanticVersion, SemanticMatcher, SemanticVersionScheme
from .legacy import LegacyVersion, LegacyMatcher, LegacyVersionScheme
from .adaptive import AdaptiveVersion, AdaptiveMatcher, AdaptiveVersionScheme

__all__ = ['NormalizedVersion', 'NormalizedMatcher',
           'LegacyVersion', 'LegacyMatcher',
           'SemanticVersion', 'SemanticMatcher',
           'AdaptiveVersion', 'AdaptiveMatcher',
           'UnsupportedVersionError', 'HugeMajorVersionError',
           'suggest_semantic_version',
           'suggest_adaptive_version',
           'normalized_key', 'legacy_key', 'semantic_key', 'adaptive_key',
           'get_scheme']


_SCHEMES = {
    'normalized': NormalizedVersionScheme(),
    'legacy': LegacyVersionScheme(),
    'semantic': SemanticVersionScheme(),
    'adaptive': AdaptiveVersionScheme(),
}

_SCHEMES['default'] = _SCHEMES['adaptive']


def get_scheme(name):
    if name not in _SCHEMES:
        raise ValueError('unknown scheme name: %r' % name)
    return _SCHEMES[name]
