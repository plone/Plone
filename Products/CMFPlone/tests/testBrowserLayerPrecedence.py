# This test confirms that views assigned to theme-specific layers (a la
# plone.theme) take precedence over views assigned to layers from other
# add-on products (a la plone.browserlayer).

from Products.CMFPlone.tests import PloneTestCase
from zope.publisher.browser import TestRequest

from zope.event import notify
from zope.interface import Interface
from zope.component import getGlobalSiteManager
from zope.publisher.interfaces.browser import IBrowserSkinType
from zope.app.publication.interfaces import BeforeTraverseEvent
from plone.browserlayer.utils import register_layer, unregister_layer

class IThemeSpecific(Interface):
    pass

class IAdditiveLayer(Interface):
    pass

class TestBrowserLayerPrecedence(PloneTestCase.FunctionalTestCase):

    def afterSetUp(self):
        gsm = getGlobalSiteManager()
        gsm.registerUtility(IThemeSpecific, IBrowserSkinType, 'Plone Default')
        register_layer(IAdditiveLayer, 'Plone.testlayer')

    def testThemeSpecificLayerTakesPrecedence(self):
        request = TestRequest()
        notify(BeforeTraverseEvent(self.portal, request))
        
        # make sure the theme-specific layer comes first in the interface
        # resolution order
        iro = list(request.__provides__.__iro__)
        self.failUnless(iro.index(IThemeSpecific) < iro.index(IAdditiveLayer),
            'Theme-specific browser layers should take precedence over other browser layers.')

    def beforeTearDown(self):
        # avoid polluting test environment
        gsm = getGlobalSiteManager()
        gsm.unregisterUtility(IThemeSpecific, IBrowserSkinType, 'Plone Default')
        unregister_layer('Plone.testlayer')

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestBrowserLayerPrecedence))
    return suite
