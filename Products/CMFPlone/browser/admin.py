from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.component import adapts
from zope.component import queryMultiAdapter
from zope.interface import Interface
from zope.publisher.interfaces import IRequest
from zope.publisher.browser import BrowserView

from AccessControl import getSecurityManager
from AccessControl.Permissions import view as View
from OFS.interfaces import IApplication
from ZPublisher.BaseRequest import DefaultPublishTraverse

from Products.CMFPlone.interfaces import IPloneSiteRoot


class AppTraverser(DefaultPublishTraverse):
    adapts(IApplication, IRequest)

    def publishTraverse(self, request, name):
        if name == 'index_html':
            view = queryMultiAdapter((self.context, request),
                        Interface, 'plone-overview')
            if view is not None:
                return view
        return DefaultPublishTraverse.publishTraverse(self, request, name)


class Overview(BrowserView):

    def sites(self, root=None):
        if root is None:
            root = self.context
        
        result = []
        secman = getSecurityManager()
        for obj in root.values():
            if IPloneSiteRoot.providedBy(obj):
                if secman.checkPermission(View, obj):
                    result.append(obj)
            elif obj.getId() in getattr(root, '_mount_points', {}):
                result.extend(self.sites(root=obj))
        return result

    def outdated(self, obj):
        mig = obj.get('portal_migration', None)
        if mig is not None:
            return mig.needUpgrading()
        return False


class FrontPage(BrowserView):

    index = ViewPageTemplateFile('templates/plone-frontpage.pt')
