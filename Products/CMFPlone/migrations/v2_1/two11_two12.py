import string
from Products.CMFCore.ActionInformation import Action
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import AddPortalContent
from Products.CMFPlone.migrations.migration_util import safeGetMemberDataTool, \
     safeEditProperty
from Products.CMFPlone.migrations.v3_0.alphas import migrateOldActions
from Products.CMFPlone.migrations.v3_0.alphas import enableZope3Site
from Products.CMFPlone.migrations.v3_0.alphas import registerToolsAsUtilities
from Products.CMFPlone.migrations import logger

def two11_two12rc1(portal):
    """2.1.1 -> 2.1.2-rc1
    """
    # Make the portal a Zope3 site
    enableZope3Site(portal)

    # register some tools as utilities
    registerToolsAsUtilities(portal)

    # Remove plone_3rdParty\CMFTopic from skin layers
    removeCMFTopicSkinLayer(portal)


    # We need to migrate all existing actions to new-style actions first
    migrateOldActions(portal)
    # Add rename object action
    addRenameObjectButton(portal)

    # add se-highlight.js (plone_3rdParty) to ResourceRegistries
    addSEHighLightJS(portal)
    
    # Don't let Discussion item have a workflow
    removeDiscussionItemWorkflow(portal)

    # Add new member data item
    addMemberData(portal)


def two12rc2_two12(portal):
    """2.1.2-rc2 -> 2.1.2
    """
    # Make the portal a Zope3 site
    enableZope3Site(portal)

    # register some tools as utilities
    registerToolsAsUtilities(portal)

    # Reinstall PortalTransforms to activate the
    # configurable safe_html transformation.
    reinstallPortalTransforms(portal)


def removeCMFTopicSkinLayer(portal):
    """Removes plone_3rdParty\CMFTopic layer from all skins."""

    st = getToolByName(portal, 'portal_skins', None)
    if st is not None:
        old = 'plone_3rdParty/CMFTopic'
        skins = st.getSkinSelections()
        for skin in skins:
            path = st.getSkinPath(skin)
            path = map(string.strip, string.split(path,','))
            if old in path:
                path.remove(old)
            st.addSkinSelection(skin, ','.join(path))
        logger.info("Removed plone_3rdParty\CMFTopic layer from all skins.")


def addRenameObjectButton(portal):
    """Add the missing rename action for renaming single content items.
    """
    actionsTool = getToolByName(portal, 'portal_actions', None)
    if actionsTool is not None:
        category = actionsTool.object_buttons
        for action in category.objectIds():
            # if action exists, remove and re-add
            if action == 'rename':
                category._delObject('rename')
                logger.info("Removed rename contentmenu action from actions tool.")
                break

        rename = Action('rename',
            title='Rename',
            i18n_domain='plone',
            url_expr='python:"%s/object_rename"%(object.isDefaultPageInFolder() and object.getParentNode().absolute_url() or object_url)',
            available_expr='python:portal.portal_membership.checkPermission("Delete objects", object.aq_inner.getParentNode()) and portal.portal_membership.checkPermission("Copy or Move", object) and portal.portal_membership.checkPermission("Add portal content", object) and object is not portal and not (object.isDefaultPageInFolder() and object.getParentNode() is portal)',
            permissions=(AddPortalContent,),
            visible=True)

        category['rename'] = rename
        logger.info("Added rename contentmenu action to actions tool.")


def addSEHighLightJS(portal):
    """Add se-highlight.js (plone_3rdParty) to ResourceRegistries.
    """
    jsreg = getToolByName(portal, 'portal_javascripts', None)
    script = 'se-highlight.js'
    if jsreg is not None:
        script_ids = jsreg.getResourceIds()
        # Failsafe: first make sure the stylesheet doesn't exist in the list
        if script not in script_ids:
            jsreg.registerScript(script)
            try:
                jsreg.moveResourceAfter(script, 'highlightsearchterms.js')
            except ValueError:
                # put it at the bottom of the stack
                jsreg.moveResourceToBottom(script)
            logger.info("Added " + script + " to portal_javascipt")


def removeDiscussionItemWorkflow(portal):
    """Discussion Item should not have a workflow associated with it, since
    it may then have permissions out-of-sync with the parent.
    """
    wftool = getToolByName(portal, 'portal_workflow', None)
    if wftool is not None:
        wftool.setChainForPortalTypes(('Discussion Item',), ())
        logger.info("Removing workflow from Discussion Item")


def addMemberData(portal):
    """Add the must_change_password property to member data"""
    mt = safeGetMemberDataTool(portal)
    if mt is not None:
        safeEditProperty(mt, 'must_change_password', 0, 'boolean')
        logger.info('Added must_change_password property to member data')


def reinstallPortalTransforms(portal):
    """Reinstalls PortalTransforms."""
    reinstall = False
    if 'portal_transforms' not in portal.keys():
        reinstall = True
    if 'portal_transforms' in portal.keys():
        transforms = portal.portal_transforms
        try:
            transforms.safe_html.get_parameter_value('disable_transform')
        except (AttributeError, KeyError):
            reinstall = True
    if reinstall:
        qi = getToolByName(portal, 'portal_quickinstaller', None)
        if qi is not None:
            qi.reinstallProducts(['PortalTransforms'])
            logger.info('Reinstalled PortalTransforms.')
