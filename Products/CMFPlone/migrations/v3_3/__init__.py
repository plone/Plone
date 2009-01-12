from Products.CMFPlone.migrations.migration_util import loadMigrationProfile

def three2_three3(portal):
    """3.2 -> 3.3
    """
    loadMigrationProfile(portal, 'profile-Products.CMFPlone.migrations:3.2-3.3')
