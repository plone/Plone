from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.migrations.migration_util import loadMigrationProfile

def alpha1_rc1(portal):
    """3.1.7 -> 3.2beta1
    """
    actions = getToolByName(portal, 'portal_actions')
    if 'iterate_checkin' in actions.object_buttons.objectIds():
        loadMigrationProfile(
            portal,
            'profile-Products.CMFPlone.migrations:3.2a1-3.2rc1-iterate')

