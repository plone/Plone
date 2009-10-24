from operator import itemgetter

from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.component import adapts
from zope.component import getAllUtilitiesRegisteredFor
from zope.component import queryMultiAdapter
from zope.interface import Interface
from zope.publisher.interfaces import IRequest
from zope.publisher.browser import BrowserView

from AccessControl import getSecurityManager
from AccessControl.Permissions import view as View
from OFS.interfaces import IApplication
from Products.GenericSetup import profile_registry
from Products.GenericSetup import BASE, EXTENSION
from ZPublisher.BaseRequest import DefaultPublishTraverse

from Products.CMFPlone.factory import _DEFAULT_PROFILE
from Products.CMFPlone.factory import addPloneSite
from Products.CMFPlone.interfaces import INonInstallable
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


class AddPloneSite(BrowserView):

    def profiles(self):
        base_profiles = []
        extension_profiles = []
        default_extension_profiles = [
            'plonetheme.sunburst:default',
            ]

        not_installable = []
        utils = getAllUtilitiesRegisteredFor(INonInstallable)
        for util in utils:
            not_installable.extend(util.getNonInstallableProfiles())

        for info in profile_registry.listProfileInfo():
            if info.get('type') == EXTENSION and \
               info.get('for') in (IPloneSiteRoot, None):
                profile_id = info.get('id')
                if profile_id not in not_installable:
                    if profile_id in default_extension_profiles:
                        info['selected'] = 'selected'
                    extension_profiles.append(info)

        extension_profiles.sort(key=itemgetter('title'))

        for info in profile_registry.listProfileInfo():
            if info.get('type') == BASE and \
               info.get('for') in (IPloneSiteRoot, None):
                base_profiles.append(info)

        return dict(
            base = tuple(base_profiles),
            default = _DEFAULT_PROFILE,
            extensions = tuple(extension_profiles),
        )

    def __call__(self):
        context = self.context
        form = self.request.form
        submitted = form.get('form.submitted', False)
        if submitted:
            site_id = form.get('site_id', 'Plone')
            site = addPloneSite(
                context, site_id,
                title=form.get('title', ''),
                profile_id=form.get('profile_id', _DEFAULT_PROFILE),
                extension_ids=form.get('extension_ids', ()),
                setup_content=form.get('setup_content', False),
                )
            self.request.response.redirect(site.absolute_url())

        return self.index()
