from Products.CMFCore.utils import getToolByName

from Products.CMFPlone.migrations.v3_0.alphas import enableZope3Site
from Products.CMFPlone.migrations.v3_0.alphas import registerToolsAsUtilities
from Products.CMFPlone.migrations import logger


def beta2_rc1(portal):
    """2.5-beta2 -> 2.5-rc1
    """
    # Make the portal a Zope3 site
    enableZope3Site(portal)

    # register some tools as utilities
    registerToolsAsUtilities(portal)

    # add a property indicating if this is a big or small site, so the UI can
    # change depending on it
    propTool = getToolByName(portal, 'portal_properties', None)
    propSheet = getattr(propTool, 'site_properties', None)
    if not propSheet.hasProperty('many_users'):
        if propSheet.hasProperty('large_site'):
            logger.info("Migrating 'large_site' to 'many_users' property.")
            default=propSheet.getProperty('large_site')
            propSheet.manage_delProperties(ids=['large_site'])
        else:
            default=0
        propSheet.manage_addProperty('many_users', default, 'boolean')
        logger.info("Added 'many_users' property to site_properties.")

