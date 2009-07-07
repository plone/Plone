from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.migrations.migration_util import loadMigrationProfile

def three23_three3_beta1(portal):
    """3.2.3 -> 3.3
    """
    loadMigrationProfile(portal, 'profile-Products.CMFPlone.migrations:3.2.3-3.3')
    maybeUpdateLinkView(portal)

def three3_rc3_three3_rc4(portal):
    loadMigrationProfile(portal,'profile-Products.CMFPlone.migrations:3.3rc3-3.3')
    cookCSSRegistries(portal)

def maybeUpdateLinkView(portal):
    ttool = getToolByName(portal, 'portal_types')
    link_fti = ttool.Link
    if link_fti.default_view == 'link_view':
        link_fti.view_methods = ('link_redirect_view',)
        link_fti.default_view = 'link_redirect_view'
        link_fti.immediate_view = 'link_redirect_view'

def cookCSSRegistries(portal):
    csstool = getToolByName(portal, 'portal_css')
    for resource in csstool.resources:
        resource.getCookedExpression()
    csstool.cookResources()
