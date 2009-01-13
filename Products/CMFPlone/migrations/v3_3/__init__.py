from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.migrations.migration_util import loadMigrationProfile

def three2_three3(portal):
    """3.2 -> 3.3
    """
    loadMigrationProfile(portal, 'profile-Products.CMFPlone.migrations:3.2-3.3')
    maybeUpdateLinkView(portal)

def maybeUpdateLinkView(portal):
    ttool = getToolByName(portal, 'portal_types')
    link_fti = ttool.Link
    if link_fti.default_view == 'link_view':
        link_fti.view_methods = ('link_redirect_view',)
        link_fti.default_view = 'link_redirect_view'
        link_fti.immediate_view = 'link_redirect_view'
