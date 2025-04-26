# -*- coding: utf-8 -*-

"""Dummy module to enable 'import Fr'

Do not use this, use the 'framel' directly
"""

import warnings

warnings.warn(
    "the Fr module has been renamed framel",
    DeprecationWarning,
)

del warnings

from framel import *
