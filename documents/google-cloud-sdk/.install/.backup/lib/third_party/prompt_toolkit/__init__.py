"""prompt_toolkit ==============

Author: Jonathan Slenders

Description: prompt_toolkit is a Library for building powerful interactive
             command lines in Python.  It can be a replacement for GNU
             readline, but it can be much more than that.

See the examples directory to learn about the usage.

Probably, to get started, you meight also want to have a look at
`prompt_toolkit.shortcuts.prompt`.
"""
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.application import AbortAction, Application
from prompt_toolkit.shortcuts import prompt

# Don't forget to update in `docs/conf.py`!
__version__ = '1.0.3'
__all__ = ['application', 'auto_suggest']
