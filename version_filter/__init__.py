# -*- coding: utf-8 -*-
from .version_filter import VersionFilter, SpecMask, SpecItemMask  # noqa: F401
import pkg_resources

__author__ = """Dropseed"""
__email__ = 'python@dropseed.io'
__version__ = pkg_resources.get_distribution("version_filter").version
