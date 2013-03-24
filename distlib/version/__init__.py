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


__all__ = [
    "NormalizedVersionScheme", "LegacyVersionScheme", "SemanticVersionScheme",
    "AdaptiveVersionScheme", "get_scheme",
]


_SCHEMES = {
    "normalized": NormalizedVersionScheme(),
    "legacy": LegacyVersionScheme(),
    "semantic": SemanticVersionScheme(),
    "adaptive": AdaptiveVersionScheme(),
}

_SCHEMES["default"] = _SCHEMES["adaptive"]


def get_scheme(name):
    try:
        return _SCHEMES[name]
    except KeyError:
        raise KeyError("unknown scheme name: %s" % name)
