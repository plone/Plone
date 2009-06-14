import os
from Acquisition import aq_base

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.DirectoryView import createDirectoryView
from Products.GenericSetup.tool import SetupTool

from Products.CMFPlone.factory import _TOOL_ID as SETUP_TOOL_ID
from Products.CMFPlone.migrations.migration_util import installOrReinstallProduct
from Products.CMFPlone.migrations.v3_0.alphas import enableZope3Site
from Products.CMFPlone.migrations.v3_0.alphas import registerToolsAsUtilities
from Products.CMFPlone.migrations import logger


def two5_alpha1(portal):
    """2.1.2 -> 2.5-alpha1
    """
    # Make the portal a Zope3 site
    enableZope3Site(portal)

    # register some tools as utilities
    registerToolsAsUtilities(portal)

    # Install portal_setup
    installPortalSetup(portal)

    # Install CMFPlacefulWorkflow
    installPlacefulWorkflow(portal)


def alpha1_alpha2(portal):
    """2.5-alpha1 -> 2.5-alpha2
    """
    # Make the portal a Zope3 site
    enableZope3Site(portal)

    # register some tools as utilities
    registerToolsAsUtilities(portal)

    # Install PlonePAS
    installPlonePAS(portal)

    # Install plone_deprecated skin
    installDeprecated(portal)


def installPlacefulWorkflow(portal):
    """Quickinstalls CMFPlacefulWorkflow if not installed yet."""
    # CMFPlacefulWorkflow is not installed by e.g. tests
    if 'CMFPlacefulWorkflow' in portal.Control_Panel.Products.objectIds():
        installOrReinstallProduct(portal, 'CMFPlacefulWorkflow', [])


def installPlonePAS(portal):
    """Quickinstalls PlonePAS if not installed yet."""
    NO_PLONEPAS = os.environ.get('SUPPRESS_PLONEPAS_INSTALLATION',None)=='YES'
    if not NO_PLONEPAS:
        installOrReinstallProduct(portal, 'PasswordResetTool', [])
        installOrReinstallProduct(portal, 'PlonePAS', [])


def installDeprecated(portal):
    # register login skin
    st = getToolByName(portal, 'portal_skins', None)
    if st is None:
        return
    if not hasattr(aq_base(st), 'plone_deprecated'):
        createDirectoryView(st, 'Products.CMFPlone:skins/plone_deprecated')
        logger.info('Added directory view for plone_deprecated')

    # add deprecated skin to default skins
    skins = ['Plone Default', 'Plone Tableless']
    selections = st._getSelections()
    for s in skins:
        if not selections.has_key(s):
           continue
        path = st.getSkinPath(s)
        path = [p.strip() for p in  path.split(',')]
        if not 'plone_deprecated' in path:
            if 'plone_3rdParty' in path:
                path.insert(path.index('plone_3rdParty'), 'plone_deprecated')
            else:
                path.append('plone_deprecated')
            st.addSkinSelection(s, ','.join(path))
            logger.info('Added plone_deprecated to %s' % s)


def installPortalSetup(portal):
    """Adds portal_setup if not installed yet."""
    if SETUP_TOOL_ID not in portal.objectIds():
        portal._setObject(SETUP_TOOL_ID, SetupTool(SETUP_TOOL_ID))
        logger.info('Added setup_tool.')
