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

def three21_three22(portal):
    """3.2.1 -> 3.2.2
    N.B.: 3.2 -> 3.2.1 was broken, this migration includes steps that should
    have been applied then.
    """
    loadMigrationProfile(
            portal,
            'profile-Products.CMFPlone.migrations:3.2-3.2.1')

