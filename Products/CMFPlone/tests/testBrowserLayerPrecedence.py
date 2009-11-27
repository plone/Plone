# This test confirms that views assigned to theme-specific layers (a la
# plone.theme) take precedence over views assigned to layers from other
# add-on products (a la plone.browserlayer).

from Products.CMFPlone.tests import PloneTestCase
from zope.publisher.browser import TestRequest

from zope.event import notify
from zope.interface import Interface
from zope.component import getGlobalSiteManager
from zope.publisher.interfaces.browser import IBrowserSkinType, IDefaultBrowserLayer
from zope.publisher.browser import setDefaultSkin
from zope.app.publication.interfaces import BeforeTraverseEvent
from Products.CMFDefault.interfaces import ICMFDefaultSkin
from plone.browserlayer.utils import register_layer, unregister_layer
from plone.theme.interfaces import IDefaultPloneLayer

class IThemeSpecific(IDefaultPloneLayer):
    pass

class IAdditiveLayer(Interface):
    pass

class IAdditiveLayerExtendingDefault(IDefaultPloneLayer):
    pass

class LayerPrecedenceTestCase(PloneTestCase.FunctionalTestCase):

    additive_layer = None
    theme_layer = None

    def afterSetUp(self):
        register_layer(self.additive_layer, 'Plone.testlayer')
        gsm = getGlobalSiteManager()
        if self.theme_layer is not None:
            self._old_theme_layer = gsm.queryUtility(IBrowserSkinType, name='Plone Default')
            gsm.registerUtility(self.theme_layer, IBrowserSkinType, 'Plone Default')
    
    def _get_request_interfaces(self):
        request = TestRequest()
        setDefaultSkin(request)
        notify(BeforeTraverseEvent(self.portal, request))
        iro = list(request.__provides__.__iro__)
        return iro
    
    def testLayerPrecedence(self):
        iro = self._get_request_interfaces()
        if self.theme_layer is not None:
            theme_layer_pos = iro.index(self.theme_layer)
            plone_default_pos = iro.index(IDefaultPloneLayer)
        additive_layer_pos = iro.index(self.additive_layer)
        cmf_default_pos = iro.index(ICMFDefaultSkin)
        zope_default_pos = iro.index(IDefaultBrowserLayer)
        
        # We want to have the theme layer first, followed by additive layers,
        # followed by default layers.
        if self.theme_layer is not None:
            self.assertEqual(theme_layer_pos, 0)
            self.failUnless(theme_layer_pos < additive_layer_pos)
            # for BBB, IDefaultPloneLayer and ICMFDefaultSkin are not present
            # unless there are theme layers which extend them.
            self.failUnless(additive_layer_pos < plone_default_pos)
            self.failUnless(plone_default_pos < cmf_default_pos)
        else:
            self.failUnless(additive_layer_pos < cmf_default_pos)
        self.failUnless(cmf_default_pos < zope_default_pos)
    
    def beforeTearDown(self):
        unregister_layer('Plone.testlayer')
        gsm = getGlobalSiteManager()
        if self.theme_layer is not None:
            self.assertEqual(True, gsm.unregisterUtility(provided=IBrowserSkinType, name='Plone Default'))
            if self._old_theme_layer is not None:
                gsm.registerUtility(self._old_theme_layer, IBrowserSkinType, 'Plone Default')

class TestPrecedenceWithAdditiveLayerExtendingInterface(LayerPrecedenceTestCase):
    theme_layer = IThemeSpecific
    additive_layer = IAdditiveLayer

class TestPrecedenceWithAdditiveLayerExtendingDefault(LayerPrecedenceTestCase):
    theme_layer = IThemeSpecific
    additive_layer = IAdditiveLayerExtendingDefault

class TestPrecedenceWithNoThemeLayer(LayerPrecedenceTestCase):
    theme_layer = None
    additive_layer = IAdditiveLayer
    

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPrecedenceWithAdditiveLayerExtendingInterface))
    suite.addTest(makeSuite(TestPrecedenceWithAdditiveLayerExtendingDefault))
    suite.addTest(makeSuite(TestPrecedenceWithNoThemeLayer))
    return suite
