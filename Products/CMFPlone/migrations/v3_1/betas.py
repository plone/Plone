from zope.component import getUtilitiesFor
from zope.interface import Interface

from plone.portlets.interfaces import IPortletType

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.migrations.migration_util import loadMigrationProfile
from Products.CMFPlone.migrations import logger
from Products.GenericSetup.browser.manage import ImportStepsView
from Products.GenericSetup.browser.manage import ExportStepsView

from Products.CMFPlone.setuphandlers import replace_local_role_manager

def three0_beta1(portal):
    """3.0.6 -> 3.1-beta1
    """
    loadMigrationProfile(portal, 'profile-Products.CMFPlone.migrations:3.0.6-3.1beta1')

    addBrowserLayer(portal)
    addCollectionAndStaticPortlets(portal)
    migratePortletTypeRegistrations(portal)
    removeDoubleGenericSetupSteps(portal)
    reinstallCMFPlacefulWorkflow(portal)
    replace_local_role_manager(portal)


def addBrowserLayer(portal):
    qi=getToolByName(portal, "portal_quickinstaller")
    if not qi.isProductInstalled("plone.browserlayer"):
        qi.installProduct("plone.browserlayer", locked=True)
        logger.info("Installed plone.browserlayer")

def addCollectionAndStaticPortlets(portal):
    qi=getToolByName(portal, "portal_quickinstaller")
    if not qi.isProductInstalled("plone.portlet.static"):
        qi.installProduct("plone.portlet.static", locked=True)
        logger.info("Installed plone.portlet.static")
    if not qi.isProductInstalled("plone.portlet.collection"):
        qi.installProduct("plone.portlet.collection", locked=True)
        logger.info("Installed plone.portlet.collection")

def migratePortletTypeRegistrations(portal):
    for name, portletType in getUtilitiesFor(IPortletType):
        if portletType.for_ is None:
            portletType.for_ = [Interface]
        elif type(portletType.for_) is not list:
            portletType.for_ = [portletType.for_]
    
    logger.info("Migrated portlet types to support multiple " + \
      "portlet manager interfaces.")


def removeDoubleGenericSetupSteps(portal):
    """Remove all GenericSetup steps that are registered both using
    zcml and in the persistent registry from the persistent registry.
    """
    st=getToolByName(portal, "portal_setup")
    view=ImportStepsView(st, None)
    steps=[step["id"] for step in view.doubleSteps()]
    if steps:
        for step in steps:
            st._import_registry.unregisterStep(step)
        st._p_changed=True
        logger.info("Removed doubly registered GenericSetup import steps: %s" %
                " ".join(steps))

    view=ExportStepsView(st, None)
    steps=[step["id"] for step in view.doubleSteps()]
    if steps:
        for step in steps:
            st._export_registry.unregisterStep(step)
        logger.info("Removed doubly registered GenericSetup export steps: %s" %
                " ".join(steps))

def reinstallCMFPlacefulWorkflow(portal):
    qi = getToolByName(portal, 'portal_quickinstaller', None)
    if qi is not None:
        installed = qi.isProductInstalled('CMFPlacefulWorkflow')
        if installed:
            qi.reinstallProducts(['CMFPlacefulWorkflow'])
            logger.info('Reinstalled CMFPlacefulWorkflow')
