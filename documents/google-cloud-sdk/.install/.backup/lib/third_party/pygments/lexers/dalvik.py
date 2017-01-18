#!/usr/bin/python2.4
#
# Copyright 2011 Google Inc. All Rights Reserved.

"""Smali lexer for the Pygments syntax highlighting library.

Smali is a langauge that represents Dalvik VM assembly language used by Android.
For more information on Smali, see http://code.google.com/p/smali/.
"""

__author__ = 'jlarimer@google.com (Jon Larimer)'

from pygments.lexer import RegexLexer, include, bygroups, using
from pygments.token import *

__all__ = ['SmaliLexer']

class SmaliLexer(RegexLexer):
    """
    For Smali (Android/Dalvik) assembly code.
    """
    name = 'Smali'
    aliases = ['smali']
    filenames = ['*.smali']
    mimetypes = ['text/smali']

    tokens = {
        'root': [
            include('comment'),
            include('label'),
            include('field'),
            include('method'),
            include('class'),
            include('directive'),
            include('access-modifier'),
            include('instruction'),
            include('literal'),
            include('punctuation'),
            include('type'),
            include('whitespace')
        ],
        'directive': [
            (r'^[ \t]*\.(class|super|implements|field|subannotation|annotation|'
             r'enum|method|registers|locals|array-data|packed-switch|'
             r'sparse-switch|catchall|catch|line|parameter|local|prologue|'
             r'epilogue|source)', Keyword),
            (r'^[ \t]*\.end (field|subannotation|annotation|method|array-data|'
             'packed-switch|sparse-switch|parameter|local)', Keyword),
            (r'^[ \t]*\.restart local', Keyword),
        ],
        'access-modifier': [
            (r'(public|private|protected|static|final|synchronized|bridge|'
             r'varargs|native|abstract|strictfp|synthetic|constructor|'
             r'declared-synchronized|interface|enum|annotation|volatile|'
             r'transient)', Keyword),
        ],
        'whitespace': [
            (r'\n', Text),
            (r'\s+', Text),
        ],
        'instruction': [
            (r'\b[vp]\d+\b', Name.Builtin), # registers
            (r'\b[a-z][A-Za-z0-9/-]+\s+', Text), # instructions
        ],
        'literal': [
            (r'".*"', String),
            (r'0x[0-9A-Fa-f]+t?', Number.Hex),
            (r'[0-9]*\.[0-9]+([eE][0-9]+)?[fd]?', Number.Float),
            (r'[0-9]+L?', Number.Integer),
        ],
        'field': [
            (r'\$?\b([A-Za-z0-9_$]*)(:)', bygroups(Name.Variable,
                                                   Punctuation)),
        ],
        'method': [
            (r'<(?:cl)?init>', Name.Function), # constructor
            (r'\$?\b([A-Za-z0-9_$]*)(\()', bygroups(Name.Function,
                                                    Punctuation)),
        ],
        'label': [
            (r':[A-Za-z0-9_]+', Name.Label),
        ],
        'class': [
            # class names in the form Lcom/namespace/ClassName;
            # I only want to color the ClassName part, so the namespace part is
            # treated as 'Text'
            (r'(L)((?:[A-Za-z0-9_$]+/)*)([A-Za-z0-9_$]+)(;)',
                bygroups(Keyword.Type, Text, Name.Class, Text)),
        ],
        'punctuation': [
            (r'->', Punctuation),
            (r'[{},\(\):=\.-]', Punctuation),
        ],
        'type': [
            (r'[ZBSCIJFDV\[]+', Keyword.Type),
        ],
        'comment': [
            (r'#.*?\n', Comment),
        ],
    }
