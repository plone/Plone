#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
monkey.py

Created by Manabu Terada on 2009-08-08.
Copyright (c) 2009 CMScom. All rights reserved.
"""
from Products.ZCTextIndex.Lexicon import Lexicon
from Products.ZCTextIndex.Lexicon import _text2list

def termToWordIds(self, text):
    last = _text2list(text)
    for element in self._pipeline:
        process = getattr(element, "process_post_glob", 
                    getattr(element, "processGlob", element.process))
        last = process(last)
    wids = []
    for word in last:
        wids.append(self._wids.get(word, 0))
    return wids

Lexicon.termToWordIds = termToWordIds