# This test confirms that views assigned to theme-specific layers (a la
# plone.theme) take precedence over views assigned to layers from other
# add-on products (a la plone.browserlayer).

from Products.CMFPlone.tests import PloneTestCase
from zope.publisher.browser import TestRequest

from zope.event import notify
from zope.interface import Interface
from zope.component import getGlobalSiteManager
from zope.publisher.interfaces.browser import IBrowserSkinType, IDefaultBrowserLayer
from zope.app.publication.interfaces import BeforeTraverseEvent
from plone.browserlayer.utils import register_layer, unregister_layer

class IThemeSpecific(Interface):
    pass

class IAdditiveLayer(Interface):
    pass

class TestBrowserLayerPrecedence(PloneTestCase.FunctionalTestCase):

    def _get_request_interfaces(self):
        request = TestRequest()
        notify(BeforeTraverseEvent(self.portal, request))
        iro = list(request.__provides__.__iro__)
        return iro

    def testCustomBrowserLayerHasPrecedenceOverDefaultLayer(self):
        register_layer(IAdditiveLayer, 'Plone.testlayer')
        iro = self._get_request_interfaces()
        unregister_layer('Plone.testlayer')
        
        self.failUnless(iro.index(IAdditiveLayer) < iro.index(IDefaultBrowserLayer))

    def testThemeSpecificLayerTakesHighestPrecedence(self):
        gsm = getGlobalSiteManager()
        gsm.registerUtility(IThemeSpecific, IBrowserSkinType, 'Plone Default')
        register_layer(IAdditiveLayer, 'Plone.testlayer')
        iro = self._get_request_interfaces()
        gsm.unregisterUtility(IThemeSpecific, IBrowserSkinType, 'Plone Default')
        unregister_layer('Plone.testlayer')
        
        self.failUnless(iro.index(IThemeSpecific) < iro.index(IAdditiveLayer),
            'Theme-specific browser layers should take precedence over other browser layers.')

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestBrowserLayerPrecedence))
    return suite
