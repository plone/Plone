#
# Plone CatalogTool
#
import re
import time
import urllib

from Products.CMFCore.CatalogTool import CatalogTool as BaseTool

from Products.CMFCore.permissions import AccessInactivePortalContent
from Products.CMFPlone import ToolNames
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Globals import DTMLFile
from Acquisition import aq_inner
from Acquisition import aq_parent
from Acquisition import aq_base
from DateTime import DateTime
from BTrees.Length import Length

from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.interfaces import ITypeInformation
from Products.CMFCore.utils import _getAuthenticatedUser
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CatalogTool import _mergedLocalRoles

from Products.CMFPlone.PloneBaseTool import PloneBaseTool
from Products.CMFPlone.interfaces import INonStructuralFolder
from Products.CMFPlone.interfaces.NonStructuralFolder import \
     INonStructuralFolder as z2INonStructuralFolder
from Products.CMFPlone.utils import base_hasattr
from Products.CMFPlone.utils import safe_callable
from Products.CMFPlone.utils import safe_unicode
from OFS.interfaces import IOrderedContainer
from OFS.IOrderSupport import IOrderedContainer as z2IOrderedContainer
from ZODB.POSException import ConflictError

from Products.ZCatalog.ZCatalog import ZCatalog
from Products.ZCatalog.interfaces import IZCatalog

from AccessControl.Permissions import manage_zcatalog_entries as ManageZCatalogEntries
from AccessControl.Permissions import search_zcatalog as SearchZCatalog
from AccessControl.PermissionRole import rolesForPermissionOn

from zope.interface import Interface, providedBy
from zope.component import queryMultiAdapter
from zope.deprecation import deprecate

from plone.indexer.interfaces import IIndexableObject
from plone.indexer import indexer

_marker = object()

## DEPRECATED: This is for compatibility in the 3.x series and should go away
## in Plone 4.

from zope.interface import implements
from zope.interface.declarations import Implements, implementedBy

from plone.indexer.interfaces import IIndexer
import zope.component.zcml
    
class BBBDelegatingIndexer(object):
    """An indexer that delegates to a given callable
    """
    implements(IIndexer)
    
    def __init__(self, context, catalog, callable):
        self.context = context
        self.catalog = catalog
        self.callable = callable
        
    def __call__(self):
        kwargs = {'portal': aq_parent(aq_inner(self.catalog))}
        return self.callable(self.context, **kwargs)

class BBBDelegatingIndexerFactory(object):
    """An adapter factory for an IIndexer that works by calling a
    BBBDelegatingIndexer.
    """
    
    def __init__(self, callable):
        self.callable = callable
        self.__implemented__ = Implements(implementedBy(BBBDelegatingIndexer))
        
    def __call__(self, object, catalog=None):
        return BBBDelegatingIndexer(object, catalog, self.callable)

# used by <plone:bbbIndexers /> directive to register indexers at config time
BBB_INDEXER_FACTORIES = {}

@deprecate("The registerIndexableAttribute hook has been deprecated and will be\n"
           "removed in Plone 4.0. Please use the following pattern instead:\n"
           "  >>> from plone.indexer.decorator import indexer\n"
           "  >>> @indexer(Interface)\n"
           "  ... def my_indexer(object):\n"
           "  ...     return <some value>\n"
           " Then register the indexer as an adapter in ZCML:\n"
           "     <adapter factory='.indexers.my_indexer' name='my_attribute' />\n"
           "Note that you can (and should) use a more specific interface for your\n"
           "indexer to ensure that it only applies to a particular content type.\n")
def registerIndexableAttribute(name, callable):
    """BBB function.
    """
    global BBB_INDEXER_FACTORIES    
    factory = BBBDelegatingIndexerFactory(callable)
    
    # delay registering these until ZCML configuration time
    BBB_INDEXER_FACTORIES[name] = factory

# This directive is used to delay registering indexable attributes until
# it's too late. It is used by CMFPlone only, should go away with this code.

class IBBBIndexersDirective(Interface):
    pass

def register_bbb_indexers():
    global BBB_INDEXER_FACTORIES
    for name, factory in BBB_INDEXER_FACTORIES.iteritems():
        zope.component.getGlobalSiteManager().registerAdapter(
            factory, (Interface, IZCatalog,), IIndexer, name)
    BBB_INDEXER_FACTORIES.clear()

from zope.interface import implements
from zope.component import adapts
from plone.indexer.interfaces import IIndexer
from plone.indexer.wrapper import IndexableObjectWrapper as _BaseWrapper
from plone.app.content.interfaces import IIndexableObjectWrapper as _old_IIndexableObjectWrapper

class ExtensibleIndexableObjectWrapper(_BaseWrapper):
    """BBB alias retaining the API of the old ExtensibleIndexableObjectWrapper.
    This may be used as a base class. It delegates to the plone.indexer
    wrapper, with a few assumptions.
    """
    
    implements(_old_IIndexableObjectWrapper)
    adapts(Interface, ISiteRoot)
    
    def __init__(self, obj, portal, registry={}):
        catalog = getToolByName(portal, 'portal_catalog')
        super(ExtensibleIndexableObjectWrapper, self).__init__(obj, catalog)
        
        # Retain old mangled name
        self._IndexableObjectWrapper__ob = obj
        self._kwargs = {}
    
    def update(self, vars, **kwargs):
        # Note that this is not even used below, because kwargs were never
        # passed to catalog_object() in the first place, and workflow vars
        # are taken care of by __init__() now.
        pass
    
    def beforeGetattrHook(self, vars, obj, kwargs):
        return vars, obj, kwargs

    def __getattr__(self, name):
        
        # Make getattr continue to call the beforeGetattrHook
        
        vars = self._IndexableObjectWrapper__vars
        obj = self._IndexableObjectWrapper__ob
        catalog = self._IndexableObjectWrapper__catalog
        kwargs = self._kwargs
        
        vars, obj, kwargs = self.beforeGetattrHook(vars, obj, kwargs)
        
        # Use the possibly modified objects from beforeGetattrHook.
        register_bbb_indexers()
        indexer = queryMultiAdapter((obj, catalog,), IIndexer, name=name)
        if indexer is not None:
            return indexer()
        if name in vars:
            return vars[name]                    
        return getattr(obj, name)
        
    def allowedRolesAndUsers(self):
        # Disable CMFCore version of this method; use registry hook instead
        return self.__getattr__('allowedRolesAndUsers')

## End Deprecated BBB code

@indexer(Interface)
def allowedRolesAndUsers(obj):
    """Return a list of roles and users with View permission.

    Used by PortalCatalog to filter out items you're not allowed to see.
    """
    allowed = {}
    for r in rolesForPermissionOn('View', obj):
        allowed[r] = 1
    try:
        acl_users = getToolByName(obj, 'acl_users', None)
        if acl_users is not None:
            localroles = acl_users._getAllLocalRoles(obj)
    except AttributeError:
        localroles = _mergedLocalRoles(obj)
    for user, roles in localroles.items():
        for role in roles:
            if allowed.has_key(role):
                allowed['user:' + user] = 1
    if allowed.has_key('Owner'):
        del allowed['Owner']
    return list(allowed.keys())

@indexer(Interface)
def object_provides(obj):
    return [i.__identifier__ for i in providedBy(obj).flattened()]

def zero_fill(matchobj):
    return matchobj.group().zfill(8)

num_sort_regex = re.compile('\d+')

@indexer(Interface)
def sortable_title(obj):
    """ Helper method for to provide FieldIndex for Title.

    >>> from Products.CMFPlone.CatalogTool import sortable_title

    >>> self.folder.setTitle('Plone42 _foo')
    >>> sortable_title(self.folder, self.portal)
    'plone00000042 _foo'

    >>> self.folder.setTitle('Archive 2009-11-28')
    >>> sortable_title(self.folder, self.portal)
    'archive-00002009-00000011-00000028'
    """
    title = getattr(obj, 'Title', None)
    if title is not None:
        if safe_callable(title):
            title = title()
        if isinstance(title, basestring):
            sortabletitle = title.lower().strip()
            # Replace numbers with zero filled numbers
            sortabletitle = num_sort_regex.sub(zero_fill, sortabletitle)
            # Truncate to prevent bloat
            sortabletitle = safe_unicode(sortabletitle)[:40].encode('utf-8')
            return sortabletitle
    return ''

@indexer(Interface)
def getObjPositionInParent(obj):
    """ Helper method for catalog based folder contents.

    >>> from Products.CMFPlone.CatalogTool import getObjPositionInParent

    >>> getObjPositionInParent(self.folder)
    0
    """
    parent = aq_parent(aq_inner(obj))
    if IOrderedContainer.providedBy(parent) or z2IOrderedContainer.isImplementedBy(parent):
        try:
            return parent.getObjectPosition(obj.getId())
        except ConflictError:
            raise
        except:
            pass
            # XXX log
    return 0

SIZE_CONST = {'kB': 1024, 'MB': 1024*1024, 'GB': 1024*1024*1024}
SIZE_ORDER = ('GB', 'MB', 'kB')

@indexer(Interface)
def getObjSize(obj):
    """ Helper method for catalog based folder contents.

    >>> from Products.CMFPlone.CatalogTool import getObjSize

    >>> getObjSize(self.folder)
    '1 kB'
    """
    smaller = SIZE_ORDER[-1]

    if base_hasattr(obj, 'get_size'):
        size = obj.get_size()
    else:
        size = 0

    # if the size is a float, then make it an int
    # happens for large files
    try:
        size = int(size)
    except (ValueError, TypeError):
        pass

    if not size:
        return '0 %s' % smaller

    if isinstance(size, (int, long)):
        if size < SIZE_CONST[smaller]:
            return '1 %s' % smaller
        for c in SIZE_ORDER:
            if size/SIZE_CONST[c] > 0:
                break
        return '%.1f %s' % (float(size/float(SIZE_CONST[c])), c)
    return size

@indexer(Interface)
def is_folderish(obj):
    """Should this item be treated as a folder?

    Checks isPrincipiaFolderish, as well as the INonStructuralFolder
    interfaces.

      >>> from Products.CMFPlone.CatalogTool import is_folderish
      >>> from Products.CMFPlone.interfaces import INonStructuralFolder
      >>> from Products.CMFPlone.interfaces.NonStructuralFolder import INonStructuralFolder as z2INonStructuralFolder
      >>> from zope.interface import directlyProvidedBy, directlyProvides

    A Folder is folderish generally::
      >>> is_folderish(self.folder)
      True

    But if we make it an INonStructuralFolder it is not::
      >>> base_implements = directlyProvidedBy(self.folder)
      >>> directlyProvides(self.folder, INonStructuralFolder, directlyProvidedBy(self.folder))
      >>> is_folderish(self.folder)
      False
      
    Now we revert our interface change and apply the z2 no-folderish interface::
      >>> directlyProvides(self.folder, base_implements)
      >>> is_folderish(self.folder)
      True
      >>> z2base_implements = self.folder.__implements__
      >>> self.folder.__implements__ = z2base_implements + (z2INonStructuralFolder,)
      >>> is_folderish(self.folder)
      False

    We again revert the interface change and check to make sure that
    PrincipiaFolderish is respected::
      >>> self.folder.__implements__ = z2base_implements
      >>> is_folderish(self.folder)
      True
      >>> self.folder.isPrincipiaFolderish = False
      >>> is_folderish(self.folder)
      False

    """
    # If the object explicitly states it doesn't want to be treated as a
    # structural folder, don't argue with it.
    folderish = bool(getattr(aq_base(obj), 'isPrincipiaFolderish', False))
    if not folderish:
        return False
    elif INonStructuralFolder.providedBy(obj):
        return False
    elif z2INonStructuralFolder.isImplementedBy(obj):
        # BBB: for z2 interface compat
        return False
    else:
        return folderish

@indexer(Interface)
def syndication_enabled(obj):
    """Get state of syndication.
    """
    syn = getattr(aq_base(obj), 'syndication_information', _marker)
    if syn is not _marker:
        return True
    return False

@indexer(Interface)
def is_default_page(obj):
    """Is this the default page in its folder
    """
    ptool = getToolByName(obj, 'plone_utils', None)
    if ptool is None:
        return False
    return ptool.isDefaultPage(obj)

@indexer(Interface)
def getIcon(obj):
    """Make sure we index icon relative to portal"""
    if ITypeInformation.providedBy(obj):
        return obj.getIcon()
    else:
        return obj.getIcon(True)
        

class CatalogTool(PloneBaseTool, BaseTool):

    meta_type = ToolNames.CatalogTool
    security = ClassSecurityInfo()
    toolicon = 'skins/plone_images/book_icon.gif'
    _counter = None

    manage_catalogAdvanced = DTMLFile('www/catalogAdvanced', globals())

    __implements__ = (PloneBaseTool.__implements__, BaseTool.__implements__)

    def __init__(self):
        ZCatalog.__init__(self, self.getId())

    def _removeIndex(self, index):
        """Safe removal of an index.
        """
        try:
            self.manage_delIndex(index)
        except:
            pass

    def _listAllowedRolesAndUsers(self, user):
        """Makes sure the list includes the user's groups.
        """
        result = list(user.getRoles())
        if hasattr(aq_base(user), 'getGroups'):
            result = result + ['user:%s' % x for x in user.getGroups()]
        result.append('Anonymous')
        result.append('user:%s' % user.getId())
        return result

    security.declarePrivate('indexObject')
    def indexObject(self, object, idxs=[]):
        """Add object to catalog.

        The optional idxs argument is a list of specific indexes
        to populate (all of them by default).
        """
        self.reindexObject(object, idxs)

    security.declareProtected(ManageZCatalogEntries, 'catalog_object')
    def catalog_object(self, object, uid=None, idxs=[],
                       update_metadata=1, pghandler=None):
        self._increment_counter()
        
        w = object
        
        if not IIndexableObject.providedBy(object):
            
            # BBB: Compatibility wrapper lookup. Should be removed in Plone 4.
            portal = aq_parent(aq_inner(self))
            register_bbb_indexers()
            wrapper = queryMultiAdapter((object, portal), _old_IIndexableObjectWrapper)
            if wrapper is not None:
                w = wrapper
            else:
                # This is the CMF 2.2 compatible approach, which should be used going forward
                wrapper = queryMultiAdapter((object, self), IIndexableObject)
                if wrapper is not None:
                    w = wrapper
        
        ZCatalog.catalog_object(self, w, uid, idxs,
                                update_metadata, pghandler=pghandler)

    security.declareProtected(ManageZCatalogEntries, 'catalog_object')
    def uncatalog_object(self, *args, **kwargs):
        self._increment_counter()
        return BaseTool.uncatalog_object(self, *args, **kwargs)

    def _increment_counter(self):
        if self._counter is None:
            self._counter = Length()
        self._counter.change(1)

    security.declarePrivate('getCounter')
    def getCounter(self):
        return self._counter is not None and self._counter() or 0

    security.declareProtected(SearchZCatalog, 'searchResults')
    def searchResults(self, REQUEST=None, **kw):
        """Calls ZCatalog.searchResults with extra arguments that
        limit the results to what the user is allowed to see.

        This version uses the 'effectiveRange' DateRangeIndex.

        It also accepts a keyword argument show_inactive to disable
        effectiveRange checking entirely even for those without portal
        wide AccessInactivePortalContent permission.
        """
        kw = kw.copy()
        show_inactive = kw.get('show_inactive', False)

        user = _getAuthenticatedUser(self)
        kw['allowedRolesAndUsers'] = self._listAllowedRolesAndUsers(user)

        if not show_inactive and not _checkPermission(AccessInactivePortalContent, self):
            kw['effectiveRange'] = DateTime()

        return ZCatalog.searchResults(self, REQUEST, **kw)

    __call__ = searchResults

    security.declareProtected(ManageZCatalogEntries, 'clearFindAndRebuild')
    def clearFindAndRebuild(self):
        """Empties catalog, then finds all contentish objects (i.e. objects
           with an indexObject method), and reindexes them.
           This may take a long time.
        """
        def indexObject(obj, path):
            if (base_hasattr(obj, 'indexObject') and
                safe_callable(obj.indexObject)):
                try:
                    obj.indexObject()
                except TypeError:
                    # Catalogs have 'indexObject' as well, but they
                    # take different args, and will fail
                    pass
        self.manage_catalogClear()
        portal = aq_parent(aq_inner(self))
        portal.ZopeFindAndApply(portal, search_sub=True, apply_func=indexObject)

    security.declareProtected(ManageZCatalogEntries, 'manage_catalogRebuild')
    def manage_catalogRebuild(self, RESPONSE=None, URL1=None):
        """Clears the catalog and indexes all objects with an 'indexObject' method.
           This may take a long time.
        """
        elapse = time.time()
        c_elapse = time.clock()

        self.clearFindAndRebuild()

        elapse = time.time() - elapse
        c_elapse = time.clock() - c_elapse

        if RESPONSE is not None:
            RESPONSE.redirect(
              URL1 + '/manage_catalogAdvanced?manage_tabs_message=' +
              urllib.quote('Catalog Rebuilt\n'
                           'Total time: %s\n'
                           'Total CPU time: %s' % (`elapse`, `c_elapse`)))

CatalogTool.__doc__ = BaseTool.__doc__

InitializeClass(CatalogTool)
