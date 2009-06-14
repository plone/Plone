import logging
from StringIO import StringIO

import transaction
from zope.interface import implements

from AccessControl import ClassSecurityInfo
from AccessControl.requestmethod import postonly
from Globals import InitializeClass, DTMLFile, DevelopmentMode
from OFS.SimpleItem import SimpleItem
from ZODB.POSException import ConflictError

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import registerToolInterface
from Products.CMFCore.utils import UniqueObject
from Products.CMFCore.permissions import ManagePortal

from Products.CMFPlone.factory import _DEFAULT_PROFILE
from Products.CMFPlone.interfaces import IMigrationTool
from Products.CMFPlone.migrations import logger
from Products.CMFPlone.PloneBaseTool import PloneBaseTool

_upgradePaths = {}


class MigrationTool(PloneBaseTool, UniqueObject, SimpleItem):
    """Handles migrations between Plone releases"""

    implements(IMigrationTool)

    id = 'portal_migration'
    meta_type = 'Plone Migration Tool'
    toolicon = 'skins/plone_images/site_icon.gif'

    _needRecatalog = 0
    _needUpdateRole = 0

    manage_options = (
        { 'label' : 'Upgrade', 'action' : 'manage_migrate' },
        )

    security = ClassSecurityInfo()

    security.declareProtected(ManagePortal, 'manage_overview')
    security.declareProtected(ManagePortal, 'manage_results')
    security.declareProtected(ManagePortal, 'manage_migrate')

    manage_migrate = DTMLFile('www/migrationRun', globals())
    manage_overview = DTMLFile('www/migrationTool', globals())
    manage_results = DTMLFile('www/migrationResults', globals())

    # Add a visual note
    def om_icons(self):
        icons = ({
                    'path':'misc_/CMFPlone/tool.gif',
                    'alt':self.meta_type,
                    'title':self.meta_type,
                 },)
        if self.needUpgrading() \
           or self.needUpdateRole() \
           or self.needRecatalog():
            icons = icons + ({
                     'path':'misc_/PageTemplates/exclamation.gif',
                     'alt':'Error',
                     'title':'This Plone instance needs updating'
                  },)

        return icons

    ##############################################################
    # Public methods
    #
    # versions methods

    security.declareProtected(ManagePortal, 'getInstanceVersion')
    def getInstanceVersion(self):
        """ The version this instance of plone is on """
        setup = getToolByName(self, 'portal_setup')
        version = setup.getLastVersionForProfile(_DEFAULT_PROFILE)
        if isinstance(version, tuple):
            version = '.'.join(version)

        _version = getattr(self, '_version', None)
        if _version is None:
            self._version = False

        if version == 'unknown':
            if _version:
                # Instance version was not pkg_resources compatible...
                _version = _version.replace('devel (svn/unreleased)', 'dev')
                _version = _version.rstrip('-final')
                _version = _version.rstrip('final')
                _version = _version.replace('alpha', 'a')
                _version = _version.replace('beta', 'b')
                _version = _version.replace('-', '.')
                version = _version
            else:
                version = setup.getVersionForProfile(_DEFAULT_PROFILE)
            self.setInstanceVersion(version)
        return version

    security.declareProtected(ManagePortal, 'setInstanceVersion')
    def setInstanceVersion(self, version):
        """ The version this instance of plone is on """
        setup = getToolByName(self, 'portal_setup')
        setup.setLastVersionForProfile(_DEFAULT_PROFILE, version)
        self._version = False

    security.declareProtected(ManagePortal, 'getFileSystemVersion')
    def getFileSystemVersion(self):
        """ The version this instance of plone is on """
        setup = getToolByName(self, 'portal_setup')
        return setup.getVersionForProfile(_DEFAULT_PROFILE)

    security.declareProtected(ManagePortal, 'needUpgrading')
    def needUpgrading(self):
        """ Need upgrading? """
        return self.getInstanceVersion() != self.getFileSystemVersion()

    security.declareProtected(ManagePortal, 'coreVersions')
    def coreVersions(self):
        """ Useful core information """
        vars = {}
        cp = self.Control_Panel
        vars['Zope'] = cp.version_txt()
        vars['Python'] = cp.sys_version()
        vars['Platform'] = cp.sys_platform()
        vars['Plone Instance'] = self.getInstanceVersion()
        vars['Plone File System'] = self.getFileSystemVersion()
        vars['CMF'] = cp.Products.CMFCore.version
        vars['Debug mode'] = DevelopmentMode and 'Yes' or 'No'
        try:
            from PIL.Image import VERSION
        except ImportError:
            VERSION = ''
        vars['PIL'] = VERSION
        return vars

    security.declareProtected(ManagePortal, 'coreVersionsList')
    def coreVersionsList(self):
        """ Useful core information """
        res = self.coreVersions().items()
        res.sort()
        return res

    security.declareProtected(ManagePortal, 'needUpdateRole')
    def needUpdateRole(self):
        """ Do roles need to be updated? """
        return self._needUpdateRole

    security.declareProtected(ManagePortal, 'needRecatalog')
    def needRecatalog(self):
        """ Does this thing now need recataloging? """
        return self._needRecatalog

    security.declareProtected(ManagePortal,'getProductInfo')
    def getProductInfo(self):
        """Provide information about installed products for error reporting"""
        zope_products = self.getPhysicalRoot().Control_Panel.Products.objectValues()
        installed_products = getToolByName(self, 'portal_quickinstaller').listInstalledProducts(showHidden=1)
        products = {}
        for p in zope_products:
            product_info = {'id':p.id, 'version':p.version}
            for ip in installed_products:
                if ip['id'] == p.id:
                    product_info['status'] = ip['status']
                    product_info['hasError'] = ip['hasError']
                    product_info['installedVersion'] = ip['installedVersion']
                    break
            products[p.id] = product_info
        return products

    security.declareProtected(ManagePortal, 'upgrade')
    def upgrade(self, REQUEST=None, dry_run=None, swallow_errors=True):
        """ perform the upgrade """
        setup = getToolByName(self, 'portal_setup')

        # This sets the profile version if it wasn't set yet
        version = self.getInstanceVersion()
        upgrades = setup.listUpgrades(_DEFAULT_PROFILE)
        steps = []
        for u in upgrades:
            if isinstance(u, list):
                steps.extend(u)
            else:
                steps.append(u)

        try:
            stream = StringIO()
            handler = logging.StreamHandler(stream)
            handler.setLevel(logging.DEBUG)
            logger.addHandler(handler)
            gslogger = logging.getLogger('GenericSetup')
            gslogger.addHandler(handler)

            if dry_run:
                logger.info("Dry run selected.")

            logger.info("Starting the migration from version: %s" % version)

            for step in steps:
                try:
                    step['step'].doStep(setup)
                    setup.setLastVersionForProfile(_DEFAULT_PROFILE, step['dest'])
                    logger.info("Ran upgrade step: %s" % step['title'])
                except (ConflictError, KeyboardInterrupt):
                    raise
                except:
                    logger.error("Upgrade aborted. Error:\n", exc_info=True)

                    if not swallow_errors:
                        raise
                    else:
                        # abort transaction to safe the zodb
                        transaction.abort()
                        break

            logger.info("End of upgrade path, migration has finished")

            if self.needUpgrading():
                logger.error("The upgrade path did NOT reach current version")
                logger.error("Migration has failed")
            else:
                logger.info("Your Plone instance is now up-to-date.")

            # do this once all the changes have been done
            if self.needRecatalog():
                try:
                    catalog = self.portal_catalog
                    # Reduce threshold for the reindex run
                    old_threshold = catalog.threshold
                    pg_threshold = getattr(catalog, 'pgthreshold', 0)
                    catalog.pgthreshold = 300
                    catalog.threshold = 2000
                    catalog.refreshCatalog(clear=1)
                    catalog.threshold = old_threshold
                    catalog.pgthreshold = pg_threshold
                    self._needRecatalog = 0
                except (ConflictError, KeyboardInterrupt):
                    raise
                except:
                    logger.error("Exception was thrown while cataloging:\n",
                                 exc_info=True)
                    if not swallow_errors:
                        raise

            if self.needUpdateRole():
                try:
                    self.portal_workflow.updateRoleMappings()
                    self._needUpdateRole = 0
                except (ConflictError, KeyboardInterrupt):
                    raise
                except:
                    logger.error("Exception was thrown while updating role "
                                 "mappings", exc_info=True)
                    if not swallow_errors:
                        raise

            if dry_run:
                logger.info("Dry run selected, transaction aborted")
                transaction.abort()

            return self.manage_results(self, out=stream.getvalue())

        finally:
            logger.removeHandler(handler)
            gslogger.removeHandler(handler)

    upgrade = postonly(upgrade)

def registerUpgradePath(oldversion, newversion, function):
    """ Basic register func """
    pass

InitializeClass(MigrationTool)
registerToolInterface('portal_migration', IMigrationTool)
