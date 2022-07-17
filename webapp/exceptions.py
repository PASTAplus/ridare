#!/usr/bin/env python
# -*- coding: utf-8 -*-


class DataPackageError(Exception):
    """Raised when a requested PASTA data package does not exist
    Args:
        msg (str): explanation of the error
    """


class PastaEnvironmentError(Exception):
    """Raised when a requested PASTA environment does not exist
    Args:
        msg (str): explanation of the error
    """


class FormatError(Exception):
    """Raised when a markdown format error occurs
    Args:
        msg (str): explanation of the error
    """


class StyleError(Exception):
    """Raised when a markdown style error occurs
    Args:
        msg (str): explanation of the error
    """
