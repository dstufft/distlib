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


# The "Normalized" version scheme, this implements PEP426
normalized = NormalizedVersionScheme()

# The "Legacy" version scheme, this is setuptools/distribute compatible
legacy = LegacyVersionScheme()

# The "Semantic" version scheme, this implements SemVer.org
semantic = SemanticVersionScheme()

# The "Adaptive" version scheme, this is Normalized and Semantic combined
adaptive = AdaptiveVersionScheme()

# The default version scheme
default = adaptive
