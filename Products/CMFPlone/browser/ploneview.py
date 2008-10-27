from urllib import unquote

from Acquisition import aq_inner
from Products.Five import BrowserView
from Products.CMFCore.permissions import AddPortalContent
from Products.CMFCore.permissions import DeleteObjects
from Products.CMFCore.permissions import ListFolderContents
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.permissions import ReviewPortalContent
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import utils
from Products.CMFPlone.browser.interfaces import IPlone

from zope.deprecation import deprecate
from zope.interface import implements
from zope.component import getMultiAdapter, queryMultiAdapter, getUtility

from plone.memoize.view import memoize
from plone.portlets.interfaces import IPortletManager, IPortletManagerRenderer

from plone.app.layout.icons.interfaces import IContentIcon

from plone.app.content.browser.folderfactories import _allowedTypes

_marker = []

class Plone(BrowserView):
    implements(IPlone)

    # XXX: This is lame
    def hide_columns(self, column_left, column_right):
        if not column_right and not column_left:
            return "visualColumnHideOneTwo"
        if column_right and not column_left:
            return "visualColumnHideOne"
        if not column_right and column_left:
            return "visualColumnHideTwo"
        return "visualColumnHideNone"

    # Utility methods

    @memoize
    def uniqueItemIndex(self, pos=0):
        """Return an index iterator."""
        return utils.RealIndexIterator(pos=pos)

    def toLocalizedTime(self, time, long_format=None):
        """Convert time to localized time
        """
        context = aq_inner(self.context)
        util = getToolByName(context, 'translation_service')
        return util.ulocalized_time(time, long_format, context=context,
                                    domain='plonelocales', request=self.request)
    
    @memoize
    def visibleIdsEnabled(self):
        """Determine if visible ids are enabled
        """
        context = aq_inner(self.context)
        props = getToolByName(context, "portal_properties").site_properties
        if not props.getProperty('visible_ids', False):
            return False

        pm = getToolByName(context, "portal_membership")
        if pm.isAnonymousUser():
            return False

        user = pm.getAuthenticatedMember()
        if user is not None:
            return user.getProperty('visible_ids', False)
        return False
    
    @memoize
    def prepareObjectTabs(self, default_tab='view', sort_first=['folderContents']):
        """Prepare the object tabs by determining their order and working
        out which tab is selected. Used in global_contentviews.pt
        """
        context = aq_inner(self.context)
        context_url = context.absolute_url()
        context_fti = context.getTypeInfo()
        
        site_properties = getToolByName(context, "portal_properties").site_properties

        context_state = getMultiAdapter((context, self.request), name=u'plone_context_state')
        actions = context_state.actions()

        action_list = []
        if context_state.is_structural_folder():
            action_list = actions['folder'] + actions['object']
        else:
            action_list = actions['object']

        tabs = []
        
        found_selected = False
        fallback_action = None

        request_url = self.request['ACTUAL_URL']
        request_url_path = request_url[len(context_url):]
        
        if request_url_path.startswith('/'):
            request_url_path = request_url_path[1:]

        for action in action_list:
            
            item = {'title'    : action['title'],
                    'id'       : action['id'],
                    'url'      : '',
                    'selected' : False}

            action_url = action['url'].strip()
            if action_url.startswith('http') or action_url.startswith('javascript'):
                item['url'] = action_url
            else:
                item['url'] = '%s/%s'%(context_url, action_url)

            action_method = item['url'].split('/')[-1]

            # Action method may be a method alias: Attempt to resolve to a template.
            action_method = context_fti.queryMethodID(action_method, default=action_method)
            if action_method:
                request_action = unquote(request_url_path)
                request_action = context_fti.queryMethodID(request_action, default=request_action)
    
                if action_method == request_action:
                    item['selected'] = True
                    found_selected = True

            current_id = item['id']
            if current_id == default_tab:
                fallback_action = item

            tabs.append(item)

        if not found_selected and fallback_action is not None:
            fallback_action['selected'] = True

        def sortOrder(tab):
            try:
                return sort_first.index(tab['id'])
            except ValueError:
                return 255

        tabs.sort(key=sortOrder)
        return tabs

    # XXX: This can't be request-memoized, because it won't necessarily remain
    # valid across traversals. For example, you may get tabs on an error 
    # message. :)
    # 
    # @memoize
    def showEditableBorder(self):
        """Determine if the editable border should be shown
        """
        request = self.request
        
        if request.has_key('disable_border'): #short circuit
            return False
        if request.has_key('enable_border'): #short circuit
            return True
        
        context = aq_inner(self.context)
        
        portal_membership = getToolByName(context, 'portal_membership')
        checkPerm = portal_membership.checkPermission

        if checkPerm('Modify portal content', context) or \
               checkPerm('Add portal content', context)  or \
               checkPerm('Review portal content', context):
            return True

        if portal_membership.isAnonymousUser():
            return False

        context_state = getMultiAdapter((context, request), name="plone_context_state")
        actions = context_state.actions()
            
        if actions.get('workflow', ()):
            return True

        if actions.get('batch', []):
            return True
            
        for action in actions.get('object', []):
            if action.get('id', '') != 'view':
                return True

        template_id = None
        if 'PUBLISHED' in request:
            if getattr(request['PUBLISHED'], 'getId', None):
                template_id=request['PUBLISHED'].getId()

        idActions = {}
        for obj in actions.get('object', ()) + actions.get('folder', ()):
            idActions[obj.get('id', '')] = 1

        if idActions.has_key('edit'):
            if (idActions.has_key(template_id) or \
                template_id in ['synPropertiesForm', 'folder_contents', 'folder_listing']) :
                return True

        # Check to see if the user is able to add content
        allowedTypes = [fti for fti in _allowedTypes(request, context)]
        if allowedTypes:
            return True

        return False
    
    @memoize
    def displayContentsTab(self):
        """Whether or not the contents tabs should be displayed
        """
        context = aq_inner(self.context)
        modification_permissions = (ModifyPortalContent,
                                    AddPortalContent,
                                    DeleteObjects,
                                    ReviewPortalContent)

        contents_object = context
        # If this object is the parent folder's default page, then the
        # folder_contents action is for the parent, we check permissions
        # there. Otherwise, if the object is not folderish, we don not display
        # the tab.
        if self.isDefaultPageInFolder():
            contents_object = self.getCurrentFolder()
        elif not self.isStructuralFolder():
            return 0

        # If this is not a structural folder, stop.
        plone_view = getMultiAdapter((contents_object, self.request),
                                     name='plone')
        if not plone_view.isStructuralFolder():
            return 0

        show = 0
        # We only want to show the 'contents' action under the following
        # conditions:
        # - If you have permission to list the contents of the relavant
        #   object, and you can DO SOMETHING in a folder_contents view. i.e.
        #   Copy or Move, or Modify portal content, Add portal content,
        #   or Delete objects.

        # Require 'List folder contents' on the current object
        if _checkPermission(ListFolderContents, contents_object):
            # If any modifications are allowed on object show the tab.
            for permission in modification_permissions:
                if _checkPermission(permission, contents_object):
                    show = 1
                    break

        return show

    @memoize
    def icons_visible(self):
        context = aq_inner(self.context)
        membership = getToolByName(context, "portal_membership")
        properties = getToolByName(context, "portal_properties")

        site_properties = getattr(properties, 'site_properties')
        icon_visibility = site_properties.getProperty('icon_visibility', 'enabled')

        if icon_visibility == 'enabled':
            return True
        elif icon_visibility == 'authenticated' and not membership.isAnonymousUser():
            return True
        else:
            return False

    def getIcon(self, item):
        """Returns an object which implements the IContentIcon interface and
           provides the informations necessary to render an icon.
           The item parameter needs to be adaptable to IContentIcon.
           Icons can be disabled globally or just for anonymous users with
           the icon_visibility property in site_properties."""
        context = aq_inner(self.context)
        if not self.icons_visible():
            icon = getMultiAdapter((context, self.request, None), IContentIcon)
        else:
            icon = getMultiAdapter((context, self.request, item), IContentIcon)
        return icon

    def normalizeString(self, text, relaxed=False):
        """Normalizes a title to an id.
        """
        return utils.normalizeString(text, context=self, relaxed=relaxed)

    def cropText(self, text, length, ellipsis='...'):
        """Crop text on a word boundary
        """
        converted = False
        if not isinstance(text, unicode):
            encoding = utils.getSiteEncoding(aq_inner(self.context))
            text = unicode(text, encoding)
            converted = True
        if len(text)>length:
            text = text[:length]
            l = text.rfind(' ')
            if l > length/2:
                text = text[:l+1]
            text += ellipsis
        if converted:
            # encode back from unicode
            text = text.encode(encoding)
        return text

    # Deprecated in favour of the @@plone_context_state and @@plone_portal_state views

    # @deprecate("The getCurrentUrl method of the Plone view has been "
    #            "deprecated and will be removed in Plone 5.0. Use the "
    #            "current_page_url method of the plone_context_state adapter "
    #            "instead.")
    def getCurrentUrl(self):
        context_state = getMultiAdapter((aq_inner(self.context), self.request), name=u'plone_context_state')
        return context_state.current_page_url()

    # @deprecate("The isDefaultPageInFolder method of the Plone view has been "
    #            "deprecated and will be removed in Plone 5.0. Use the "
    #            "is_default_page method of the plone_context_state adapter "
    #            "instead.")
    def isDefaultPageInFolder(self):
        context_state = getMultiAdapter((aq_inner(self.context), self.request), name=u'plone_context_state')
        return context_state.is_default_page()

    # @deprecate("The isStructuralFolder method of the Plone view has been "
    #            "deprecated and will be removed in Plone 5.0. Use the "
    #            "is_structural_folder method of the plone_context_state adapter "
    #            "instead.")
    def isStructuralFolder(self):
        context_state = getMultiAdapter((aq_inner(self.context), self.request), name=u'plone_context_state')
        return context_state.is_structural_folder()

    # @deprecate("The navigationRootPath method of the Plone view has been "
    #            "deprecated and will be removed in Plone 5.0. Use the "
    #            "navigation_root_path method of the plone_portal_state adapter "
    #            "instead.")
    def navigationRootPath(self):
        portal_state = getMultiAdapter((aq_inner(self.context), self.request), name=u'plone_portal_state')
        return portal_state.navigation_root_path()

    # @deprecate("The navigationRootUrl method of the Plone view has been "
    #            "deprecated and will be removed in Plone 5.0. Use the "
    #            "navigation_root_url method of the plone_portal_state adapter "
    #            "instead.")
    def navigationRootUrl(self):
        portal_state = getMultiAdapter((aq_inner(self.context), self.request), name=u'plone_portal_state')
        return portal_state.navigation_root_url()

    # @deprecate("The getParentObject method of the Plone view has been "
    #            "deprecated and will be removed in Plone 5.0. Use the "
    #            "parent method of the plone_context_state adapter instead.")
    def getParentObject(self):
        context_state = getMultiAdapter((aq_inner(self.context), self.request), name=u'plone_context_state')
        return context_state.parent()

    # @deprecate("The getCurrentFolder method of the Plone view has been "
    #            "deprecated and will be removed in Plone 5.0. Use the "
    #            "folder method of the plone_context_state adapter instead.")
    def getCurrentFolder(self):
        context_state = getMultiAdapter((aq_inner(self.context), self.request), name=u'plone_context_state')
        return context_state.folder()

    # @deprecate("The getCurrentFolderUrl method of the Plone view has been "
    #            "deprecated and will be removed in Plone 5.0. Use the "
    #            "absolute_url method on the result of the folder method of the "
    #            "plone_context_state adapter instead.")
    def getCurrentFolderUrl(self):
        context_state = getMultiAdapter((aq_inner(self.context), self.request), name=u'plone_context_state')
        return context_state.folder().absolute_url()

    # @deprecate("The getCurrentObjectUrl method of the Plone view has been "
    #            "deprecated and will be removed in Plone 5.0. Use the "
    #            "canonical_object_url method of the plone_context_state "
    #            "adapter instead.")
    @memoize
    def getCurrentObjectUrl(self):
        context_state = getMultiAdapter((aq_inner(self.context), self.request), name=u'plone_context_state')
        return context_state.canonical_object_url()

    # @deprecate("The isFolderOrFolderDefaultPage method of the Plone view has "
    #            "been deprecated and will be removed in Plone 5.0. Use either "
    #            "the is_structural_folder or is_default_page method of the "
    #            "plone_context_state adapter instead.")
    @memoize
    def isFolderOrFolderDefaultPage(self):
        context_state = getMultiAdapter((aq_inner(self.context), self.request), name=u'plone_context_state')
        return context_state.is_structural_folder() or context_state.is_default_page()

    # @deprecate("The isPortalOrPortalDefaultPage method of the Plone view has "
    #            "been deprecated and will be removed in Plone 5.0. Use the "
    #            "is_portal_root method of the plone_context_state adapter "
    #            "instead.")
    @memoize
    def isPortalOrPortalDefaultPage(self):
        context_state = getMultiAdapter((aq_inner(self.context), self.request), name=u'plone_context_state')
        return context_state.is_portal_root()
        
    # @deprecate("The getViewTemplateId method of the Plone view has been "
    #            "deprecated and will be removed in Plone 5.0. Use the "
    #            "view_template_id method of the plone_context_state adapter "
    #            "instead.")
    @memoize
    def getViewTemplateId(self):
        context_state = getMultiAdapter((aq_inner(self.context), self.request), name=u'plone_context_state')
        return context_state.view_template_id()

    # Helper methods
    def have_portlets(self, manager_name, view=None):
        """Determine whether a column should be shown.
        The left column is called plone.leftcolumn; the right column is called
        plone.rightcolumn. Custom skins may have more portlet managers defined
        (see portlets.xml).
        """
        
        context = aq_inner(self.context)
        if view is None:
            view = self

        manager = getUtility(IPortletManager, name=manager_name)
        renderer = queryMultiAdapter((context, self.request, view, manager), IPortletManagerRenderer)
        if renderer is None:
            renderer = getMultiAdapter((context, self.request, self, manager), IPortletManagerRenderer)

        return renderer.visible
