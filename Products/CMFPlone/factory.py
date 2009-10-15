from operator import itemgetter

from zope.component import getAllUtilitiesRegisteredFor
from zope.event import notify
from zope.interface import implements
from zope.site.hooks import setSite

from Products.GenericSetup.tool import SetupTool
from Products.GenericSetup import profile_registry
from Products.GenericSetup import BASE, EXTENSION
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.CMFPlone.events import SiteManagerCreatedEvent
from Products.CMFPlone.interfaces import INonInstallable
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.Portal import PloneSite
from Products.CMFPlone.utils import WWW_DIR

_TOOL_ID = 'portal_setup'
_DEFAULT_PROFILE = 'Products.CMFPlone:plone'
_CONTENT_PROFILE = 'Products.CMFPlone:plone-content'

# A little hint for PloneTestCase
_IMREALLYPLONE4 = True

class HiddenProfiles(object):
    implements(INonInstallable)

    def getNonInstallableProfiles(self):
        return [_DEFAULT_PROFILE,
                _CONTENT_PROFILE,
                u'Products.Archetypes:Archetypes',
                u'Products.CMFDiffTool:CMFDiffTool',
                u'Products.CMFEditions:CMFEditions',
                u'Products.CMFFormController:CMFFormController',
                u'Products.CMFPlone:dependencies',
                u'Products.CMFPlone:testfixture',
                u'Products.CMFQuickInstallerTool:CMFQuickInstallerTool',
                u'Products.NuPlone:uninstall',
                u'Products.MimetypesRegistry:MimetypesRegistry',
                u'Products.PasswordResetTool:PasswordResetTool',
                u'Products.PortalTransforms:PortalTransforms',
                u'Products.PloneLanguageTool:PloneLanguageTool',
                u'Products.PlonePAS:PlonePAS',
                u'archetypes.referencebrowserwidget:default',
                u'borg.localrole:default',
                u'Products.TinyMCE:TinyMCE',
                u'Products.TinyMCE:upgrade_10_to_11',
                u'Products.TinyMCE:uninstall',
                u'plone.browserlayer:default',
                u'plone.keyring:default',
                u'plone.portlet.static:default',
                u'plone.portlet.collection:default',
                u'plone.protect:default',
                u'plonetheme.sunburst:uninstall',
                u'plone.app.blob:default',
                u'plone.app.blob:file-replacement',
                u'plone.app.blob:image-replacement',
                u'plone.app.blob:sample-type',
                u'plone.app.imaging:default',
                ]


def addPloneSiteForm(dispatcher):
    """
    Wrap the PTF in 'dispatcher'.
    """
    wrapped = PageTemplateFile('addSite', WWW_DIR).__of__(dispatcher)

    base_profiles = []
    extension_profiles = []
    not_installable = []
    default_extension_profiles = [
        'plonetheme.sunburst:default',
        ]

    utils = getAllUtilitiesRegisteredFor(INonInstallable)
    for util in utils:
        not_installable.extend(util.getNonInstallableProfiles())

    for info in profile_registry.listProfileInfo():
        if info.get('type') == EXTENSION and \
           info.get('for') in (IPloneSiteRoot, None):
            profile_id = info.get('id')
            if profile_id not in not_installable:
                if profile_id in default_extension_profiles:
                    info['selected'] = 'selected'
                extension_profiles.append(info)

    extension_profiles.sort(key=itemgetter('title'))

    for info in profile_registry.listProfileInfo():
        if info.get('type') == BASE and \
           info.get('for') in (IPloneSiteRoot, None):
            base_profiles.append(info)

    return wrapped(base_profiles=tuple(base_profiles),
                   extension_profiles=tuple(extension_profiles),
                   default_profile=_DEFAULT_PROFILE)

def addPloneSite(dispatcher, site_id, title='', description='',
                 create_userfolder=True, email_from_address='',
                 email_from_name='', validate_email=False,
                 profile_id=_DEFAULT_PROFILE, snapshot=False,
                 RESPONSE=None, extension_ids=(),
                 setup_content=True):
    """ Add a PloneSite to 'dispatcher', configured according to 'profile_id'.
    """
    dispatcher._setObject(site_id, PloneSite(site_id))
    site = dispatcher._getOb(site_id)

    site[_TOOL_ID] = SetupTool(_TOOL_ID)
    setup_tool = site[_TOOL_ID]

    notify(SiteManagerCreatedEvent(site))
    setSite(site)

    setup_tool.setBaselineContext('profile-%s' % profile_id)
    setup_tool.runAllImportStepsFromProfile('profile-%s' % profile_id)
    if setup_content:
        setup_tool.runAllImportStepsFromProfile('profile-%s' % _CONTENT_PROFILE)
    for extension_id in extension_ids:
        setup_tool.runAllImportStepsFromProfile('profile-%s' % extension_id)

    # Try to make the title work with Unicode
    if isinstance(title, str):
        title = unicode(title, 'utf-8', 'ignore')

    props = {}
    prop_keys = ['title', 'description', 'email_from_address',
                 'email_from_name', 'validate_email']
    loc_dict = locals()
    for key in prop_keys:
        if loc_dict[key]:
            props[key] = loc_dict[key]
    if props:
        site.manage_changeProperties(**props)

    if snapshot is True:
        setup_tool.createSnapshot('initial_configuration')

    if RESPONSE is not None:
        RESPONSE.redirect(site.absolute_url())
