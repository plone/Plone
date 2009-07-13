import os
from StringIO import StringIO

from five.localsitemanager import make_objectmanager_site
from five.localsitemanager.registry import FiveVerifyingAdapterLookup
from plone.app.portlets.utils import convert_legacy_portlets
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import ILocalPortletAssignmentManager
from plone.portlets.constants import CONTEXT_CATEGORY as CONTEXT_PORTLETS
from zope.app.component.interfaces import ISite
from zope.component import getMultiAdapter
from zope.component import getSiteManager
from zope.component import getUtility

from Acquisition import aq_base
from Globals import package_home
from Products.Archetypes.interfaces import IArchetypeTool
from Products.Archetypes.interfaces import IReferenceCatalog
from Products.Archetypes.interfaces import IUIDCatalog
from Products.ATContentTypes.interface import IATCTTool
from Products.ATContentTypes.migration.v1_2 import upgradeATCTTool
from Products.CMFActionIcons.interfaces import IActionIconsTool
from Products.CMFCalendar.interfaces import ICalendarTool
from Products.CMFCore.ActionInformation import Action
from Products.CMFCore.ActionInformation import ActionCategory
from Products.CMFCore.interfaces import IActionsTool
from Products.CMFCore.interfaces import ICachingPolicyManager
from Products.CMFCore.interfaces import ICatalogTool
from Products.CMFCore.interfaces import IContentTypeRegistry
from Products.CMFCore.interfaces import IDiscussionTool
from Products.CMFCore.interfaces import IMemberDataTool
from Products.CMFCore.interfaces import IMembershipTool
from Products.CMFCore.interfaces import IMetadataTool
from Products.CMFCore.interfaces import IPropertiesTool
from Products.CMFCore.interfaces import IRegistrationTool
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.interfaces import ISkinsTool
from Products.CMFCore.interfaces import ISyndicationTool
from Products.CMFCore.interfaces import ITypesTool
from Products.CMFCore.interfaces import IUndoTool
from Products.CMFCore.interfaces import IURLTool
from Products.CMFCore.interfaces import IConfigurableWorkflowTool
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.DirectoryView import createDirectoryView
from Products.CMFDiffTool.interfaces import IDiffTool
from Products.CMFEditions.interfaces import IArchivistTool
from Products.CMFEditions.interfaces import IPortalModifierTool
from Products.CMFEditions.interfaces import IPurgePolicyTool
from Products.CMFEditions.interfaces.IRepository import IRepositoryTool
from Products.CMFEditions.interfaces import IStorageTool
from Products.CMFFormController.interfaces import IFormControllerTool
from Products.CMFQuickInstallerTool.interfaces import IQuickInstallerTool
from Products.CMFUid.interfaces import IUniqueIdAnnotationManagement
from Products.CMFUid.interfaces import IUniqueIdGenerator
from Products.CMFUid.interfaces import IUniqueIdHandler
from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition
from Products.DCWorkflow.exportimport import WorkflowDefinitionConfigurator, _initDCWorkflow
from Products.GenericSetup.interfaces import ISetupTool
from Products.MailHost.interfaces import IMailHost
from Products.MimetypesRegistry.interfaces import IMimetypesRegistryTool
from Products.PloneLanguageTool.interfaces import ILanguageTool
from Products.PlonePAS.interfaces.group import IGroupTool
from Products.PlonePAS.interfaces.group import IGroupDataTool
from Products.PortalTransforms.interfaces import IPortalTransformsTool
from Products.ResourceRegistries.interfaces import ICSSRegistry
from Products.ResourceRegistries.interfaces import IJSRegistry
from Products.StandardCacheManagers import RAMCacheManager

from Products.CMFPlone import cmfplone_globals
from Products.CMFPlone.factory import _DEFAULT_PROFILE
from Products.CMFPlone.interfaces import IControlPanel
from Products.CMFPlone.interfaces import IFactoryTool
from Products.CMFPlone.interfaces import IInterfaceTool
from Products.CMFPlone.interfaces import IMigrationTool
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.interfaces import IPloneTool
from Products.CMFPlone.interfaces import ITranslationServiceTool
from Products.CMFPlone.migrations import logger
from Products.CMFPlone.migrations.migration_util import installOrReinstallProduct
from Products.CMFPlone.migrations.migration_util import loadMigrationProfile


def three0_alpha1(context):
    """2.5.x -> 3.0-alpha1
    """
    portal = getToolByName(context, 'portal_url').getPortalObject()

    loadMigrationProfile(portal, 'profile-Products.CMFPlone.migrations:2.5.x-3.0a1')

    # The ATCT tool has lost all type migration functionality and quite some
    # metadata and index information stored on it needs to be updated.
    upgradeATCTTool(portal, out=[])

    # Install CMFEditions and CMFDiffTool
    installProduct('CMFDiffTool', portal, hidden=True)
    installProduct('CMFEditions', portal, hidden=True)


def alpha1_alpha2(context):
    """ 3.0-alpha1 -> 3.0-alpha2
    """
    portal = getToolByName(context, 'portal_url').getPortalObject()
    
    loadMigrationProfile(portal, 'profile-Products.CMFPlone.migrations:3.0a1-3.0a2')


def alpha2_beta1(context):
    """ 3.0-alpha2 -> 3.0-beta1
    """
    portal = getToolByName(context, 'portal_url').getPortalObject()

    loadMigrationProfile(portal, 'profile-Products.CMFPlone.migrations:3.0a2-3.0b1')

    installS5(portal)
    
    addTableContents(portal)

    # Install PloneLanguageTool
    installProduct('PloneLanguageTool', portal, hidden=True)


# # --
# KSS registration
# --

class installKss(object):

    js_unregister = []

    js_all = [
        ('++resource++MochiKit.js', 'none', False),
        ('++resource++prototype.js', 'safe', True),
        ('++resource++effects.js', 'safe', True),
        ('++resource++kukit.js', 'none', True),
    ]

    css_all = [
        'ploneKss.css',
    ]

    kss_all = [
        'plone.kss',
        'at.kss',
    ]

    def __init__(self, context):
        self.context = context
        self.installKss()

    @staticmethod
    def _old_res(tool, id):
        return tool.getResourcesDict().get(id, None)
     
    def install_resources(self):
        jstool = getToolByName(self.context, 'portal_javascripts')
        for id in self.js_unregister:
            if self._old_res(jstool, id):
                jstool.unregisterResource(id)
                logger.info("Unregistered old %s" % (id, ))
        for id, compression, enabled in self.js_all:
            if not self._old_res(jstool, id):
                jstool.registerScript(
                    id = id,
                    enabled = enabled,
                    cookable = True,
                    compression = compression,
                    )
        csstool = getToolByName(self.context, 'portal_css')
        for css in self.css_all:
            if not self._old_res(csstool, css):
                csstool.manage_addStylesheet(
                    id = css,
                    rel = 'stylesheet',
                    rendering = 'link',
                    enabled = True,
                    cookable = True,
                    )
        # kss stylesheets
        for kss in self.kss_all:
            if not self._old_res(csstool, kss):
                csstool.manage_addStylesheet(id=kss,
                    rel='k-stylesheet',
                    rendering = 'link',
                    enabled=True,
                    cookable=False,
                    )
        logger.info("Registered kss resources")

    def install_mimetype(self):
        mt = getToolByName(self.context, 'mimetypes_registry')
        mt.manage_addMimeType('KSS (Azax) StyleSheet', ('text/kss', ), ('kss', ), 'text.png',
                               binary=0, globs=('*.kss', ))
        logger.info("Registered kss mimetype")

    def install_skins(self):
        st = getToolByName(self.context, 'portal_skins')
        skins = ['Plone Default', 'Plone Tableless']
        if not hasattr(aq_base(st), 'plone_kss'):
            createDirectoryView(st, 'CMFPlone/skins/plone_kss')
        if not hasattr(aq_base(st), 'archetypes_kss'):
            createDirectoryView(st, 'Archetypes/skins/archetypes_kss')
        selections = st._getSelections()
        for s in skins:
            if not selections.has_key(s):
               continue
            path = st.getSkinPath(s)
            path = [p.strip() for p in  path.split(',')]
            path_changed = False
            if not 'plone_kss' in path:
                path.append('plone_kss')
                path_changed = True
            if not 'archetypes_kss' in path:
                path.append('archetypes_kss')
                path_changed = True
            if path_changed:
                st.addSkinSelection(s, ','.join(path))
                logger.info('Added missing skins to %s' % s)

    def installKss(self):
        self.install_mimetype() 
        self.install_resources() 
        self.install_skins() 
        logger.info("Succesfully migrated portal to KSS")


def enableZope3Site(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    if not ISite.providedBy(portal):
        make_objectmanager_site(portal)
        logger.info('Made the portal a Zope3 site.')
    else:
        sm = portal.getSiteManager()
        if sm.utilities.LookupClass  != FiveVerifyingAdapterLookup:
            sm.utilities.LookupClass = FiveVerifyingAdapterLookup
            sm.utilities._createLookup()
            sm.utilities.__parent__ = aq_base(sm)
            sm.__parent__ = aq_base(portal)


def migrateOldActions(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    special_providers = ['portal_controlpanel',
                         'portal_types',
                         'portal_workflow']
    # We don't need to operate on the providers that are still valid and
    # should ignore the control panel as well
    providers = [obj for obj in portal.objectValues()
                     if hasattr(obj, '_actions') and
                     obj.getId() not in special_providers]
    non_empty_providers = [p for p in providers if len(p._actions) > 0]
    for provider in non_empty_providers:
        for action in provider._actions:
            category = action.category
            # check if the category already exists, otherwise create it
            new_category = getattr(aq_base(portal.portal_actions), category, None)
            if new_category is None:
                portal.portal_actions._setObject(category, ActionCategory(id=category))
                new_category = portal.portal_actions[category]

            # Special handling for Expressions
            url_expr = ''
            if action.action:
                url_expr = action.action.text
            available_expr = ''
            if action.condition:
                available_expr = action.condition.text

            new_action = Action(action.id,
                title=action.title,
                description=action.description,
                url_expr=url_expr,
                available_expr=available_expr,
                permissions=action.permissions,
                visible = action.visible)
                
            # Only add an action if there isn't one with that name already
            if getattr(aq_base(new_category), action.id, None) is None:
                new_category._setObject(action.id, new_action)

        # Remove old actions from migrated providers
        provider._actions = ()
    logger.info('Migrated old actions to new actions stored in portal_actions.')


def _check_ascii(text):
    try:
        unicode(text, 'ascii')
    except UnicodeDecodeError:
        return False
    return True


def updateActionsI18NDomain(context):
    actions = getToolByName(context, 'portal_actions')
    actions = actions.listActions()
    domainless_actions = [a for a in actions if not a.i18n_domain]
    for action in domainless_actions:
        if _check_ascii(action.title) and _check_ascii(action.description):
            action.i18n_domain = 'plone'
    if domainless_actions:
        logger.info('Updated actions i18n domain attribute.')


def updateFTII18NDomain(context):
    types = getToolByName(context, 'portal_types')
    types = types.listTypeInfo()
    domainless_types = [fti for fti in types if not fti.i18n_domain]
    for fti in domainless_types:
        if _check_ascii(fti.title) and _check_ascii(fti.description):
            fti.i18n_domain = 'plone'
    if domainless_types:
        logger.info('Updated type informations i18n domain attribute.')


def addPortletManagers(context):
    """Add new portlets managers."""
    loadMigrationProfile(context, 'profile-Products.CMFPlone:plone',
            steps=['portlets'])


def convertLegacyPortlets(context):
    """Convert portlets defined in left_slots and right_slots at the portal
    root to use plone.portlets. Also block portlets in the Members folder.
    
    Note - there may be other portlets defined elsewhere. These will require
    manual migration from the @@manage-portlets view. This is to avoid a 
    full walk of the portal (i.e. waking up every single object) looking for
    potential left_slots/right_slots! 
    """
    portal = getToolByName(context, 'portal_url').getPortalObject()
    convert_legacy_portlets(portal)
    logger.info('Converted legacy portlets at the portal root')
    logger.info('NOTE: You may need to convert other portlets manually.')
    logger.info(' - to do so, click "manage portlets" in the relevant folder.')

    members = getattr(portal, 'Members', None)
    if members is not None:
        membersRightSlots = getattr(aq_base(members), 'right_slots', None)
        if membersRightSlots == []:
            rightColumn = getUtility(IPortletManager, name=u'plone.rightcolumn', context=portal)
            portletAssignments = getMultiAdapter((members, rightColumn,), ILocalPortletAssignmentManager)
            portletAssignments.setBlacklistStatus(CONTEXT_PORTLETS, True)
            logger.info('Blacklisted contextual portlets in the Members folder')


def installProduct(product, portal, out=None, hidden=False):
    """Quickinstalls a product if it is not installed yet."""
    if out is None:
        out = []
    if product in portal.Control_Panel.Products.objectIds():
        installOrReinstallProduct(portal, product, out, hidden=hidden)


registration = (('mimetypes_registry', IMimetypesRegistryTool),
                ('portal_transforms', IPortalTransformsTool),
                ('portal_atct', IATCTTool),
                ('portal_actionicons', IActionIconsTool),
                ('portal_discussion', IDiscussionTool),
                ('portal_metadata', IMetadataTool),
                ('portal_properties', IPropertiesTool),
                ('portal_syndication', ISyndicationTool),
                ('portal_undo', IUndoTool),
                ('portal_interface', IInterfaceTool),
                ('portal_migration', IMigrationTool),
                ('MailHost', IMailHost),
                ('portal_diff', IDiffTool),
                ('portal_uidannotation', IUniqueIdAnnotationManagement),
                ('portal_uidgenerator', IUniqueIdGenerator),
               )

invalid_regs = (ILanguageTool, IArchivistTool, IPortalModifierTool,
                IPurgePolicyTool, IRepositoryTool, IStorageTool,
                IFormControllerTool, IReferenceCatalog, IUIDCatalog,
                ICalendarTool, IActionsTool, ICatalogTool,
                IContentTypeRegistry, ISkinsTool, ITypesTool, IURLTool,
                IConfigurableWorkflowTool, IPloneTool, ICSSRegistry,
                IJSRegistry, IUniqueIdHandler, IFactoryTool, IMembershipTool,
                IGroupTool, IGroupDataTool, IMemberDataTool,
                ICachingPolicyManager, IRegistrationTool, IArchetypeTool,
                ITranslationServiceTool, IControlPanel, IQuickInstallerTool,
                ISetupTool,
               )

def registerToolsAsUtilities(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    sm = getSiteManager(portal)

    portalregistration = ((portal, ISiteRoot),
                          (portal, IPloneSiteRoot),)

    for reg in portalregistration:
        if sm.queryUtility(reg[1]) is None:
            sm.registerUtility(aq_base(reg[0]), reg[1])

    for reg in registration:
        if sm.queryUtility(reg[1]) is None:
            if reg[0] in portal.keys():
                tool = aq_base(portal[reg[0]])
                sm.registerUtility(tool, reg[1])

    for reg in invalid_regs:
        if sm.queryUtility(reg) is not None:
            sm.unregisterUtility(provided=reg)

    logger.info("Registered tools as utilities.")


def addReaderAndEditorRoles(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()    
    if 'Reader' not in portal.valid_roles():
        portal._addRole('Reader')
    if 'Editor' not in portal.valid_roles():
        portal._addRole('Editor')
    if 'Reader' not in portal.acl_users.portal_role_manager.listRoleIds():
        portal.acl_users.portal_role_manager.addRole('Reader')
    if 'Editor' not in portal.acl_users.portal_role_manager.listRoleIds():
        portal.acl_users.portal_role_manager.addRole('Editor')
    
    viewRoles = [r['name'] for r in portal.rolesOfPermission('View') if r['selected']]
    modifyRoles = [r['name'] for r in portal.rolesOfPermission('Modify portal content') if r['selected']]
    
    if 'Reader' not in viewRoles:
        viewRoles.append('Reader')
        portal.manage_permission('View', viewRoles, True)
        
    if 'Editor' not in modifyRoles:
        modifyRoles.append('Editor')
        portal.manage_permission('Modify portal content', modifyRoles, True)

    logger.info('Added reader and editor roles')


def migrateLocalroleForm(context):
    portal_types = getToolByName(context, 'portal_types', None)
    if portal_types is not None:
        for fti in portal_types.objectValues():
            if not hasattr(fti, '_aliases'):
                fti._aliases={}
            
            aliases = fti.getMethodAliases()
            new_aliases = aliases.copy()
            for k, v in aliases.items():
                if 'folder_localrole_form' in v:
                    new_aliases[k] = v.replace('folder_localrole_form', '@@sharing')
            fti.setMethodAliases(new_aliases)
            
            for a in fti.listActions():
                expr = a.getActionExpression()
                if 'folder_localrole_form' in expr:
                    a.setActionExpression(expr.replace('folder_localrole_form', '@@sharing'))
    logger.info('Ensured references to folder_localrole_form point to @@sharing now')


def reorderUserActions(context):
    portal_actions = getToolByName(context, 'portal_actions', None)
    if portal_actions is not None:
        user_category = getattr(portal_actions, 'user', None)
        if user_category is not None:        
            new_actions = ['login', 'join', 'mystuff', 'preferences', 'undo', 'logout']
            new_actions.reverse()
            for action in new_actions:
                if action in user_category.objectIds():
                    user_category.moveObjectsToTop([action])


def installS5(portal):
    portalTypes = getToolByName(portal, 'portal_types', None)
    if portalTypes is not None:
        document = portalTypes.restrictedTraverse('Document', None)
        if document:
            for action in document.listActions():
                if action.getId() == 's5_presentation':
                    break # We already have the action
            else:
                document.addAction('s5_presentation',
                    name='View as presentation',
                    action="string:${object/absolute_url}/document_s5_presentation",
                    condition='python:object.document_s5_alter(test=True)',
                    permission='View',
                    category='document_actions',
                    visible=1,
                    )
            logger.info("Added 's5_presentation' action to actions tool.")

    iconsTool = getToolByName(portal, 'portal_actionicons', None)
    if iconsTool is not None:
        for icon in iconsTool.listActionIcons():
            if icon.getActionId() == 's5_presentation':
                break # We already have the icon
        else:
            iconsTool.addActionIcon(
                category='plone',
                action_id='s5_presentation',
                icon_expr='fullscreenexpand_icon.gif',
                title='View as presentation',
                )
        logger.info("Added 's5_presentation' icon to actionicons tool.")


def addTableContents(portal):
    """ Adds in table of contents """
    csstool = getToolByName(portal, "portal_css", None)
    if csstool is not None:
        if 'toc.css' not in csstool.getResourceIds():
            csstool.manage_addStylesheet(id="toc.css",rel="stylesheet", enabled=True)
    jstool = getToolByName(portal, "portal_javascripts", None)
    if jstool is not None:
        if 'toc.js' not in jstool.getResourceIds():
            jstool.registerScript(id="toc.js", enabled=True)
    logger.info("Added in css and js for table of contents")


def updateMemberSecurity(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    pprop = getToolByName(portal, 'portal_properties')
    portal.manage_permission('Add portal member', roles=['Manager','Owner'], acquire=0)
    pprop.site_properties.manage_changeProperties(allowAnonymousViewAbout=False)

    portal.manage_changeProperties(validate_email=True)

    pmembership = getToolByName(portal, 'portal_membership')
    pmembership.memberareaCreationFlag = 0
    logger.info("Updated member management security")


def updatePASPlugins(context):
    from Products.PlonePAS.Extensions.Install import activatePluginInterfaces

    portal = getToolByName(context, 'portal_url').getPortalObject()
    sout=StringIO()

    activatePluginInterfaces(portal, 'mutable_properties')
    activatePluginInterfaces(portal, 'source_users')
    activatePluginInterfaces(portal, 'credentials_cookie_auth',
            disable=['ICredentialsResetPlugin', 'ICredentialsUpdatePlugin'])
    if not portal.acl_users.objectIds(['Plone Session Plugin']):
        from plone.session.plugins.session import manage_addSessionPlugin
        manage_addSessionPlugin(portal.acl_users, 'session')
        activatePluginInterfaces(portal, "session")
        logger.info("Added Plone Session Plugin.")


def updateKukitJS(context):
    """Use the unpacked kukit-src.js and pack it ourself.
    """
    jsreg = getToolByName(context, 'portal_javascripts', None)
    old_id = '++resource++kukit.js'
    new_id = '++resource++kukit-src.js'
    if jsreg is not None:
        script_ids = jsreg.getResourceIds()
        if old_id in script_ids and new_id in script_ids:
            jsreg.unregisterResource(old_id)
        elif old_id in script_ids:
            jsreg.renameResource(old_id, new_id)
            logger.info("Use %s instead of %s" % (new_id, old_id))
        resource = jsreg.getResource(new_id)
        if resource is not None:
            resource.setCompression('full')
            logger.info("Set 'full' compression on %s" % new_id)


def addCacheForResourceRegistry(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    ram_cache_id = 'ResourceRegistryCache'
    if not ram_cache_id in portal.objectIds():
        RAMCacheManager.manage_addRAMCacheManager(portal, ram_cache_id)
        cache = getattr(portal, ram_cache_id)
        settings = cache.getSettings()
        settings['max_age'] = 24*3600 # keep for up to 24 hours
        settings['request_vars'] = ('URL',)
        cache.manage_editProps('Cache for saved ResourceRegistry files', settings)
        logger.info('Created RAMCache %s for ResourceRegistry output' % ram_cache_id)
    reg = getToolByName(portal, 'portal_css', None)
    if reg is not None and getattr(aq_base(reg), 'ZCacheable_setManagerId', None) is not None:
        reg.ZCacheable_setManagerId(ram_cache_id)
        reg.ZCacheable_setEnabled(1)
        logger.info('Associated portal_css with %s' % ram_cache_id)
    reg = getToolByName(portal, 'portal_javascripts', None)
    if reg is not None and getattr(aq_base(reg), 'ZCacheable_setManagerId', None) is not None:
        reg.ZCacheable_setManagerId(ram_cache_id)
        reg.ZCacheable_setEnabled(1)
        logger.info('Associated portal_javascripts with %s' % ram_cache_id)


def removeTablelessSkin(context):
    st = getToolByName(context, 'portal_skins')
    if 'Plone Tableless' in st.getSkinSelections():
        st.manage_skinLayers(['Plone Tableless'], del_skin=True)
        logger.info("Removed the Plone Tableless skin")
    if st.default_skin=='Plone Tableless':
        st.default_skin='Plone Default'
        logger.info("Changed the default skin to 'Plone Default'")


def addObjectProvidesIndex(context):
    """Add the object_provides index to the portal_catalog.
    """
    catalog = getToolByName(context, 'portal_catalog')
    if 'object_provides' not in catalog.indexes():
        catalog.addIndex('object_provides', 'KeywordIndex')
        logger.info("Added object_provides index to portal_catalog")


def removeMyStuffAction(context):
    """The mystuff action is now covered by the dashboard"""
    actions = getToolByName(context, 'portal_actions')
    if getattr(actions, 'user', None) is None:
        return
    category=actions.user
    if 'mystuff' in category.objectIds():
        category.manage_delObjects(ids=['mystuff'])
        logger.info("Removed the mystuff user action")


def addMissingWorkflows(context):
    """Add new Plone 3.0 workflows
    """
    portal = getToolByName(context, 'portal_url').getPortalObject()
    wft = getToolByName(portal, 'portal_workflow', None)
    if wft is None:
        return

    new_workflow_ids = [ 'intranet_workflow', 'intranet_folder_workflow',
                        'one_state_workflow', 'simple_publication_workflow']
    encoding = 'utf-8'
    path_prefix = os.path.join(package_home(cmfplone_globals), 'profiles',
            'default', 'workflows')
    
    for wf_id in new_workflow_ids:
        if wf_id in wft.objectIds():
            logger.info("Workflow %s already installed; doing nothing" % wf_id)
            continue

        path = os.path.join(path_prefix, wf_id, 'definition.xml')
        body = open(path,'r').read()

        wft._setObject(wf_id, DCWorkflowDefinition(wf_id))
        wf = wft[wf_id]
        wfdc = WorkflowDefinitionConfigurator(wf)

        ( workflow_id
        , title
        , state_variable
        , initial_state
        , states
        , transitions
        , variables
        , worklists
        , permissions
        , scripts
        , description
        ) = wfdc.parseWorkflowXML(body, encoding)

        _initDCWorkflow( wf
                       , title
                       , description
                       , state_variable
                       , initial_state
                       , states
                       , transitions
                       , variables
                       , worklists
                       , permissions
                       , scripts
                       , portal     # not sure what to pass here
                                    # the site or the wft?
                                    # (does it matter at all?)
                      )
        logger.info("Added workflow %s" % wf_id)


def restorePloneTool(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    tool = getToolByName(portal, "plone_utils")
    if tool.meta_type == 'PlonePAS Utilities Tool':
        from Products.CMFPlone.PloneTool import PloneTool
        from Products.CMFDefault.Portal import CMFSite

        # PloneSite has its own security check for manage_delObjects which
        # breaks in the test runner. So we bypass this check.
        CMFSite.manage_delObjects(portal, ['plone_utils'])
        portal._setObject(PloneTool.id, PloneTool())
        logger.info("Replaced obsolete PlonePAS version of plone tool "
                    "with the normal one.")


def updateImportStepsFromBaseProfile(context):
    """Updates the available import steps for existing sites."""
    setup_tool = getToolByName(context, "portal_setup", None)
    if setup_tool is not None:
        # only rerun when unset
        if not setup_tool.getBaselineContextID():
            # make sure the profile is there
            if _DEFAULT_PROFILE in [i['id'] for i in setup_tool.listProfileInfo()]:
                setup_tool.setBaselineContext('profile-' + _DEFAULT_PROFILE)
                logger.info('Set plone GS profile as default')
