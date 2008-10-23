from Products.CMFPlone.migrations.migration_util import loadMigrationProfile

def three11_three12(portal):
    """3.1.1 -> 3.1.2"""
    
    out = []
    
    loadMigrationProfile(portal, 'profile-Products.CMFPlone.migrations:3.1.1-3.1.2')

def three14_three15(portal):
    """3.1.4 -> 3.1.5"""
    
    out = []
    
    loadMigrationProfile(portal, 'profile-Products.CMFPlone.migrations:3.1.3-3.1.4')

def three16_three17(portal):
    iterate_installed = filter(
        lambda info: info['id'] == 'plone.app.iterate',
        portal.portal_quickinstaller.listInstalledProducts())
    if iterate_installed:
        loadMigrationProfile(portal, 'profile-Products.CMFPlone.migrations:3.1.6-3.1.7-iterate')
