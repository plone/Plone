from Products.CMFPlone.tests import PloneTestCase
from Products.CMFCore.tests.base.dummy import DummyContent


class TestITranslatable(PloneTestCase.PloneTestCase):
    """ tests regarding the ITranslatable interface """

    def testZope2ITranslatableInterface(self):
        # this checks backwards compatibility after ripping out zope2-style
        # interfaces in http://dev.plone.org/plone/changeset/28518
        # it should be removed again for plone 4.0
        from Products.CMFPlone.interfaces.Translatable import ITranslatable
        class DummyTranslatable(DummyContent):
            __implements__ = (ITranslatable,)
        foo = DummyTranslatable('foo')
        self.failUnless(ITranslatable.isImplementedBy(foo))


def test_suite():
    from unittest import defaultTestLoader
    return defaultTestLoader.loadTestsFromName(__name__)
