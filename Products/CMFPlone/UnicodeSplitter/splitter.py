#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
splitter.py

Created by Manabu Terada on 2009-09-30.
Copyright (c) 2009 CMScom. All rights reserved.
"""
import re
import unicodedata

from zope.interface import implements
from Products.ZCTextIndex.ISplitter import ISplitter
from Products.ZCTextIndex.PipelineFactory import element_factory
from Products.CMFPlone.utils import getSiteEncoding

from Products.CMFPlone.UnicodeSplitter.config import rx_U, rxGlob_U, \
            rx_L, rxGlob_L, rx_all, pattern, pattern_g

def bigram(u,limit=1):
    """ バイグラムに分ける。limit=0 なら
    日本人-> [日本,本人, 人]
    金 -> [金]
    limit = 1なら
    日本人-> [日本,本人]
    金 -> []
    """
    return [u[i:i+2] for i in xrange(len(u) - limit)]

def process_str_post(s,enc):
    """strの受け取り、?と*を取り除き、
    strを返す。
    decodeできればユニコードとして処理し、
    失敗すれば、asciiとして処理する。
    """
    try:
        uni = s.decode(enc, "strict")
    except UnicodeDecodeError, e:
        return s.replace("?", "").replace("*", "")
    try:
        return uni.replace(u"?", u"").replace(u"*", u"").encode(enc, "strict")
    except UnicodeEncodeError, e:
        return s.replace("?", "").replace("*", "")

def process_str(s, enc):
    """ strとエンコードを受け取り、
    バイグラム化した結果として、strのlistを返す。
    ユニコードにdecodeし、process_unicodeに渡す。
    decodeに失敗した場合は、rx_Lにより、
    ロケールに合わせたword単位でスプリットした結果を返す。
    """
    try:
        uni = s.decode(enc, "strict")
    except UnicodeDecodeError, e:
        return [x for x in rx_L.findall(s)]
    bigrams = process_unicode(uni)
    return [x.encode(enc, "strict") for x in bigrams]

def process_str_glob(s, enc):
    """ strとエンコードを受け取り、
    バイグラム化した結果として、strのlistを返す。
    globを考慮して処理する。
    ユニコードにdecodeし、process_unicode_globに渡す。
    decodeに失敗した場合は、rxGlob_Lにより、
    ロケールに合わせたword単位でスプリットした結果を返す。
    """
    try:
        uni = s.decode(enc, "strict")
    except UnicodeDecodeError, e:
        return [x for x in rxGlob_L.findall(s)]
    bigrams = process_unicode_glob(uni)
    return [x.encode(enc, "strict") for x in bigrams]

def process_unicode(uni):
    """ ユニコード文字列を受け取り、
    バイグラム化した結果として、ユニコードのlistを返す。
    """
    normalized = unicodedata.normalize('NFKC', uni)
    for word in rx_U.findall(normalized):
        swords = [g.group() for g in pattern.finditer(word)]
        for sword in swords:
            if not rx_all.match(sword[0]):
                yield sword
            else:
                for x in bigram(sword, 0):
                    yield x

def process_unicode_glob(uni):
    """ ユニコード文字列を受け取り、
    バイグラム化した結果として、ユニコードのlistを返す。
    globを考慮して処理する。
    """
    normalized = unicodedata.normalize('NFKC', uni)
    for word in rxGlob_U.findall(normalized):
        swords = [g.group() for g in pattern_g.finditer(word)
                  if g.group() not in u"*?"]
        for i,sword in enumerate(swords):
            if not rx_all.match(sword[0]):
                yield sword
            else:
                if i == len(swords) - 1:
                    limit = 1
                else:
                    limit = 0
                if len(sword) == 1:
                    bigramed = [sword + u"*"]
                else:
                    bigramed = bigram(sword, limit)
                for x in bigramed:
                    yield x


class Splitter(object):

    implements(ISplitter)
    
    def process(self, lst):
        """Index時に呼ばれる
        strのlistを受け取り、バイグラムの処理を行い
        strのlistを返す。
        """
        enc = getSiteEncoding(self)
        result = [x for s in lst for x in process_str(s, enc)]
        return result
    
    def processGlob(self, lst):
        """Search時の1回目に呼ばれる
        strのlistを受け取り、バイグラムのglobを考慮した処理を行い
        strのlistを返す。
        """
        enc = getSiteEncoding(self)
        result = [x for s in lst for x in process_str_glob(s, enc)]
        return result

    def process_post_glob(self, lst):
        """Search時の2回目に呼ばれる
        strのlistを受け取り、?と*を取り除き、
        strのlistを返す。
        """
        enc = getSiteEncoding(self)
        result = [process_str_post(s, enc) for s in lst]
        return result

try:
    element_factory.registerFactory('Word Splitter',
        'Unicode Whitespace splitter', Splitter)
except ValueError:
    # In case the splitter is already registered, ValueError is raised
    pass


class CaseNormalizer(object):

    def process(self, lst):
        enc = getSiteEncoding(self)
        result = []
        for s in lst:
            # This is a hack to get the normalizer working with
            # non-unicode text.
            try:
                if not isinstance(s, unicode):
                    s = unicode(s, enc)
            except (UnicodeDecodeError, TypeError):
                result.append(s.lower())
            else:
                result.append(s.lower().encode(enc))
        return result

try:
    element_factory.registerFactory('Case Normalizer',
        'Unicode Case Normalizer', CaseNormalizer)
except ValueError:
    # In case the normalizer is already registered, ValueError is raised
    pass

