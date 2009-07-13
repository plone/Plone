from StringIO import StringIO

from zope.component import queryUtility

from Acquisition import aq_base
from Products.CMFActionIcons.interfaces import IActionIconsTool
from Products.CMFCore.Expression import Expression
from Products.CMFCore.interfaces import IActionProvider
from Products.CMFCore.utils import getToolByName

from Products.CMFPlone.migrations import logger
from Products.CMFPlone.migrations.migration_util import loadMigrationProfile


def beta1_beta2(context):
    """ 3.0-beta1 -> 3.0-beta2
    """
    portal = getToolByName(context, 'portal_url').getPortalObject()

    loadMigrationProfile(context, 'profile-Products.CMFPlone.migrations:3.0b1-3.0b2')


def beta2_beta3(context):
    """ 3.0-beta2 -> 3.0-beta3
    """
    loadMigrationProfile(context, 'profile-Products.CMFPlone.migrations:3.0b2-3.0b3')


def beta3_rc1(context):
    """ 3.0-beta3 -> 3.0-rc1
    """
    loadMigrationProfile(context, 'profile-Products.CMFPlone.migrations:3.0b3-3.0b4')


def migrateHistoryTab(context):
    portal_actions = getToolByName(context, 'portal_actions', None)
    if portal_actions is not None:
        objects = getattr(portal_actions, 'object', None)
        if objects is not None:
            if 'rss' in objects.objectIds():
                objects.manage_renameObjects(['rss'], ['history'])
                logger.info('Migrated history action.')


def changeOrderOfActionProviders(context):
    portal_actions = getToolByName(context, 'portal_actions', None)
    if portal_actions is not None:
        portal_actions.deleteActionProvider('portal_actions')
        portal_actions.addActionProvider('portal_actions')
        logger.info('Changed the order of action providers.')

def cleanupOldActions(context):
    portal_actions = getToolByName(context, 'portal_actions', None)
    if portal_actions is not None:
        # Remove some known unused actions from the object_tabs category and
        # remove the category completely if no actions are left
        object_tabs = getattr(portal_actions, 'object_tabs', None)
        if object_tabs is not None:
            if 'contentrules' in object_tabs.objectIds():
                object_tabs._delObject('contentrules')
            if 'change_ownership' in object_tabs.objectIds():
                object_tabs._delObject('change_ownership')
            if len(object_tabs.objectIds()) == 0:
                del object_tabs
                portal_actions._delObject('object_tabs')
                logger.info('Removed object_tabs action category.')
        object_ = getattr(portal_actions, 'object', None)
        if object_ is not None:
            if 'reply' in object_.objectIds():
                object_._delObject('reply')
        user = getattr(portal_actions, 'user', None)
        if user is not None:
            if 'logged_in' in user.objectIds():
                user._delObject('logged_in')
            if 'myworkspace' in user.objectIds():
                user._delObject('myworkspace')
        global_ = getattr(portal_actions, 'global', None)
        if global_ is not None:
            if 'manage_members' in global_.objectIds():
                global_._delObject('manage_members')
            if 'configPortal' in global_.objectIds():
                global_._delObject('configPortal')
            if len(global_.objectIds()) == 0:
                del global_
                portal_actions._delObject('global')
                logger.info('Removed global action category.')

def cleanDefaultCharset(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    charset = portal.getProperty('default_charset', None)
    if charset is not None:
        if not charset.strip():
            portal.manage_delProperties(['default_charset'])
            logger.info('Removed empty default_charset portal property')


def addAutoGroupToPAS(context):
    from Products.PlonePAS.Extensions.Install import activatePluginInterfaces

    portal = getToolByName(context, 'portal_url').getPortalObject()
    sout = StringIO()

    if not portal.acl_users.objectIds(['Automatic Group Plugin']):
        from Products.PlonePAS.plugins.autogroup import manage_addAutoGroup
        manage_addAutoGroup(portal.acl_users, 'auto_group',
                'Automatic Group Provider',
                'AuthenticatedUsers', "Logged-in users (Virtual Group)")
        activatePluginInterfaces(portal, "auto_group")
        logger.info("Added automatic group PAS plugin")

def removeS5Actions(context):
    portalTypes = getToolByName(context, 'portal_types', None)
    if portalTypes is not None:
        document = portalTypes.restrictedTraverse('Document', None)
        if document:
            ids = [x.getId() for x in document.listActions()]
            if 's5_presentation' in ids:
                index = ids.index('s5_presentation')
                document.deleteActions([index])
                logger.info("Removed 's5_presentation' action from actions tool.")

    iconsTool = queryUtility(IActionIconsTool)
    if iconsTool is not None:
        ids = [x.getActionId() for x in iconsTool.listActionIcons()]
        if 's5_presentation' in ids:
            iconsTool.removeActionIcon('plone','s5_presentation')
            logger.info("Removed 's5_presentation' icon from actionicons tool.")

def addCacheForKSSRegistry(context):
    ram_cache_id = 'ResourceRegistryCache'
    reg = getToolByName(context, 'portal_kss', None)
    if reg is not None and getattr(aq_base(reg), 'ZCacheable_setManagerId', None) is not None:
        reg.ZCacheable_setManagerId(ram_cache_id)
        reg.ZCacheable_setEnabled(1)
        logger.info('Associated portal_kss with %s' % ram_cache_id)

def modifyKSSResources(context):
    # make kukit.js conditonol and not load for anonymous
    reg = getToolByName(context, 'portal_javascripts', None)
    if reg is not None:
        id = '++resource++kukit-src.js'
        entry = aq_base(reg).getResourcesDict().get(id, None)
        if entry:
            reg.updateScript(id, expression='not:here/@@plone_portal_state/anonymous', compression='safe')
            logger.info('Updated kss javascript resource %s, to disable kss for anonymous.' % id)
    # register the new kss resources
    reg = getToolByName(context, 'portal_kss', None)
    if reg is not None:
        new_resources = ['at_experimental.kss', 'plone_experimental.kss']
        for id in new_resources:
            entry = aq_base(reg).getResourcesDict().get(id, None)
            if not entry:
                reg.registerKineticStylesheet(id, enabled=0)
                logger.info('Added kss resource %s, disabled by default.' % id)

def modifyKSSResourcesForDevelMode(context):
    # separate kukit.js and kukit-src-js based on debug mode
    reg = getToolByName(context, 'portal_javascripts', None)
    if reg is not None:
        id = '++resource++kukit-src.js'
        entry = aq_base(reg).getResourcesDict().get(id, None)
        if entry:
            pos = aq_base(reg).getResourcePosition(id)
            # delete kukit-src.js
            aq_base(reg).unregisterResource(id)
            # add the new ones
            id1 = '++resource++kukit.js'
            if aq_base(reg).getResourcesDict().get(id1, None):
                aq_base(reg).unregisterResource(id1)
            aq_base(reg).registerScript(id1,
                    expression="python: not here.restrictedTraverse('@@plone_portal_state').anonymous() and here.restrictedTraverse('@@kss_devel_mode').isoff()",
                    inline=False, enabled=True,
                    cookable=True, compression='none', cacheable=True)
            id2 = '++resource++kukit-devel.js'
            if aq_base(reg).getResourcesDict().get(id2, None):
                aq_base(reg).unregisterResource(id2)
            aq_base(reg).registerScript(id2,
                    expression="python: not here.restrictedTraverse('@@plone_portal_state').anonymous() and here.restrictedTraverse('@@kss_devel_mode').ison()",
                    inline=False, enabled=True,
                    cookable=True, compression='none', cacheable=True)
            # move them to where the old one has been
            aq_base(reg).moveResource(id1, pos)
            aq_base(reg).moveResource(id2, pos + 1)
            logger.info('Updated kss javascript resources, to enable the use '
                        'of production and development versions.')

def addContributorToCreationPermissions(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    if 'Contributor' not in portal.valid_roles():
        portal._addRole('Contributor')
    if 'Contributor' not in portal.acl_users.portal_role_manager.listRoleIds():
        portal.acl_users.portal_role_manager.addRole('Contributor')
    
    for p in ['Add portal content', 'Add portal folders', 'ATContentTypes: Add Document',
                'ATContentTypes: Add Event',
                'ATContentTypes: Add File', 'ATContentTypes: Add Folder', 
                'ATContentTypes: Add Image', 'ATContentTypes: Add Large Plone Folder',
                'ATContentTypes: Add Link', 'ATContentTypes: Add News Item', ]:
        roles = [r['name'] for r in portal.rolesOfPermission(p) if r['selected']]
        if 'Contributor' not in roles:
            roles.append('Contributor')
            portal.manage_permission(p, roles, bool(portal.acquiredRolesAreUsedBy(p)))

def removeSharingAction(context):
    portal_types = getToolByName(context, 'portal_types', None)
    if portal_types is not None:
        for fti in portal_types.objectValues():
            action_ids = [a.id for a in fti.listActions()]
            if 'local_roles' in action_ids:
                fti.deleteActions([action_ids.index('local_roles')])
                
        logger.info('Removed explicit references to sharing action')

def addEditorToSecondaryEditorPermissions(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    for p in ['Manage properties', 'Modify view template', 'Request review']:
        roles = [r['name'] for r in portal.rolesOfPermission(p) if r['selected']]
        if 'Editor' not in roles:
            roles.append('Editor')
            portal.manage_permission(p, roles, bool(portal.acquiredRolesAreUsedBy(p)))

def updateEditActionConditionForLocking(context):
    """
    Condition on edit views for Document, Event, File, Folder, Image, 
    Large_Plone_Folder, Link, Topic has been added to not display the Edit
    tab if an item is locked
    """
    portal_types = getToolByName(context, 'portal_types', None)
    lockable_types = ['Document', 'Event', 'File', 'Folder',
                      'Image', 'Large Plone Folder', 'Link',
                      'News Item', 'Topic']
    if portal_types is not None:
        for contentType in lockable_types:
            fti = portal_types.getTypeInfo(contentType)
            if fti:
                for action in fti.listActions():
                    if action.getId() == 'edit' and not action.condition:
                        action.condition = Expression("not:object/@@plone_lock_info/is_locked_for_current_user|python:True")

def addOnFormUnloadJS(context):
    """
    add the form unload JS to the js registry
    """
    jsreg = getToolByName(context, 'portal_javascripts', None)
    script = 'unlockOnFormUnload.js'
    if jsreg is not None:
        script_ids = jsreg.getResourceIds()
        # Failsafe: first make sure the stylesheet doesn't exist in the list
        if script not in script_ids:
            jsreg.registerScript(script,
                                 enabled = True,
                                 cookable = True)
            # put it at the bottom of the stack
            jsreg.moveResourceToBottom(script)
            logger.info("Added " + script + " to portal_javascripts")

def moveKupuAndCMFPWControlPanel(context):
    """
    Move Kupu control panel to the Plone section and the CMFPW control panel
    to the add-on section if it is installed.
    """
    cp = getToolByName(context, 'portal_controlpanel', None)
    if cp is not None:
        kupu = cp.getActionObject('Products/kupu')
        if kupu is not None:
            kupu.category = 'Plone'
        cmfpw = cp.getActionObject('Plone/placefulworkflow')
        if cmfpw is not None:
            cmfpw.category = 'Products'

def updateLanguageControlPanel(context):
    """Use the new configlet for the language control panel"""
    cp = getToolByName(context, 'portal_controlpanel', None)
    if cp is not None:
        lang = cp.getActionObject('Plone/PloneLanguageTool')
        if lang is not None:
            lang.action = Expression('string:${portal_url}/@@language-controlpanel')

def updateTopicTitle(context):
    """Update the title of the topic type."""
    tt = getToolByName(context, 'portal_types', None)
    if tt is not None:
        topic = tt.get('Topic')
        if topic is not None:
            topic.title = 'Collection'


def cleanupActionProviders(context):
    """Remove no longer existing action proiders."""
    at = getToolByName(context, "portal_actions")
    for provider in at.listActionProviders():
        candidate = getToolByName(context, provider, None)
        if candidate is None or not IActionProvider.providedBy(candidate):
            at.deleteActionProvider(provider)
            logger.info("%s is no longer an action provider" % provider)

def hidePropertiesAction(context):
    tt = getToolByName(context, 'portal_types', None)
    if not IActionProvider.providedBy(tt):
        return
    for ti in tt.listTypeInfo():
        actions = ti.listActions()
        index=[i for i in range(len(actions) )
                if actions[i].category=="object" and 
                   actions[i].id=="metadata"]
        if index:
            ti.deleteActions(index)
            logger.info("Removed properties action from type %s" % ti.id)
