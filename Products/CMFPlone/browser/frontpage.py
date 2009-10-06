from zope.publisher.browser import BrowserView

from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile


class FrontPage(BrowserView):

    index = ViewPageTemplateFile('frontpage.pt')
