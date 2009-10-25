from Products.CMFPlone.tests import PloneTestCase

import re

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
class DummyView(BrowserView):
    __call__ = ViewPageTemplateFile("pages/view.pt")
    __name__ = "dummy"  # this is normally set at zcml interpretation time


class TestBodyTemplateClass(PloneTestCase.PloneTestCase):
    """test that the template class on the body tag is computed"""

    bodyClassesPattern = re.compile(r'\<body[^>]+class[^"]*"([^"]*)"')

    def testPageTemplate(self):
        """directly in a persistent PageTemplate"""
        from Products.PageTemplates.ZopePageTemplate \
                           import manage_addPageTemplate
        manage_addPageTemplate(self.portal, 'test',
               text='''
               <html metal:use-macro="here/main_template/macros/master">
               <body>
               </body>
               </html>''',
               encoding='ascii')

        results = self.bodyClassesPattern.search(self.portal.test())
        self.assert_(results)
        self.assert_("template-test" in results.groups()[0])

    def testViewTemplate(self):
        """in a browser view via the __name__ attribute"""
        import zope.component
        from zope.publisher.interfaces.http import IHTTPRequest
        from zope.publisher.interfaces.browser import IBrowserView
        from zope.interface import Interface
        zope.component.provideAdapter(DummyView, name=u"dummy",
            adapts=(Interface, IHTTPRequest), provides=IBrowserView)
        rendered = self.portal.unrestrictedTraverse("@@dummy")()
        results = self.bodyClassesPattern.search(rendered)
        self.assert_(results)
        self.assert_("template-dummy" in results.groups()[0])


def test_suite():
    import sys, unittest
    return unittest.findTestCases(sys.modules[__name__])
