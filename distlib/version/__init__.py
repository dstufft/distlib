# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 The Python Software Foundation.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
"""
Implementation of a flexible versioning scheme providing support for PEP-426,
distribute-compatible and semantic versioning.
"""

from .normalized import NormalizedVersionScheme
from .legacy import LegacyVersionScheme
from .semantic import SemanticVersionScheme
from .adaptive import AdaptiveVersionScheme


__all__ = ["normalized", "legacy", "semantic", "adaptive", "default"]


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
