from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import registerToolInterface
from Products.CMFPlone.PloneBaseTool import PloneBaseTool
from Products.CMFPlone import ToolNames
from Products.CMFQuickInstallerTool.QuickInstallerTool \
   import QuickInstallerTool as BaseTool
from Products.CMFQuickInstallerTool.interfaces import IQuickInstallerTool


class QuickInstallerTool(PloneBaseTool, BaseTool):
    """ A tool to ease installing/uninstalling all sorts of products """

    meta_type = ToolNames.QuickInstallerTool
    security = ClassSecurityInfo()
    toolicon = 'skins/plone_images/product_icon.gif'

    __implements__ = (PloneBaseTool.__implements__, BaseTool.__implements__, )

    security.declareProtected(ManagePortal, 'upgradeInfo')
    def upgradeInfo(self, pid):
        """Returns a dict with two booleans values, stating if an upgrade
        is required and available.
        """
        available = self.isProductAvailable(pid)
        if not available:
            return False
        # Product version as per version.txt or fallback on metadata file
        product_version = str(self.getProductVersion(pid))
        installed_product_version = self._getOb(pid).getInstalledVersion()
        profile = self.getInstallProfile(pid)
        if profile is None:
            # No GS profile, simple case as before, we can always upgrade
            return dict(
                required=product_version != installed_product_version,
                available=True,
                )
        profile_id = profile['id']
        setup = getToolByName(self, 'portal_setup')
        profile_version = str(setup.getVersionForProfile(profile_id))
        if profile_version == 'unknown':
            # If a profile doesn't have a metadata.xml use product version
            profile_version = product_version
        installed_profile_version = setup.getLastVersionForProfile(profile_id)
        if installed_profile_version == 'unknown':
            # Inline migration, set profile version to last product version
            setup.setLastVersionForProfile(profile_id, installed_product_version)
            installed_profile_version = setup.getLastVersionForProfile(profile_id)
        # getLastVersionForProfile returns the version as a tuple
        installed_profile_version = str('.'.join(installed_profile_version))
        return dict(
            required=profile_version != installed_profile_version,
            available=len(setup.listUpgrades(profile_id))>0,
            )


QuickInstallerTool.__doc__ = BaseTool.__doc__

InitializeClass(QuickInstallerTool)
registerToolInterface('portal_quickinstaller', IQuickInstallerTool)
