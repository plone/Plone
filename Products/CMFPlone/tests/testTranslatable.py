from zope.interface import implements
from Products.CMFPlone.tests import PloneTestCase
from Products.CMFCore.tests.base.dummy import DummyContent
from Products.CMFPlone import interfaces


class DummyTranslatable(DummyContent):
    __implements__ = (interfaces.Translatable.ITranslatable,)
    implements(interfaces.ITranslatable)


class TestITranslatable(PloneTestCase.PloneTestCase):
    """ tests regarding the ITranslatable interface """

    def testZope2ITranslatableInterface(self):
        # this checks backwards compatibility after ripping out zope2-style
        # interfaces in http://dev.plone.org/plone/changeset/28518
        # it should be removed again for plone 4.0
        foo = DummyTranslatable('foo')
        from Products.CMFPlone.interfaces.Translatable import ITranslatable
        self.failUnless(ITranslatable.isImplementedBy(foo))


def test_suite():
    from unittest import defaultTestLoader
    return defaultTestLoader.loadTestsFromName(__name__)
