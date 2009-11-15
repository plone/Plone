from zope.i18n import translate
from zope.publisher.browser import BrowserView

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _


TEMPLATE = """\
var portal_url = '%(portal_url)s';
var form_modified_message = '%(form_modified)s';
var form_resubmit_message = '%(form_resubmit)s';
var external_links_open_new_window = '%(open_links)s';
var mark_special_links = '%(mark_links)s';
"""

FORM_MODIFIED = _(u'text_form_modified_message', default=u'Your form has not been saved. All changes you have made will be lost.')
FORM_RESUBMIT = _(u'text_form_resubmit_message', default=u'You already clicked the submit button. Do you really want to submit this form again?')


class JSVariables(BrowserView):

    def __call__(self, *args, **kwargs):
        context = self.context
        response = self.request.response
        response.setHeader('content-type','text/javascript;;charset=utf-8')

        props = getToolByName(context, 'portal_properties').site_properties
        portal_url = getToolByName(context, 'portal_url')()

        # the following are flags for mark_special_links.js
        # links get the target="_blank" attribute
        open_links = props.getProperty('external_links_open_new_window', 'false')
        mark_links = props.getProperty('mark_special_links', 'false')

        form_modified = translate(FORM_MODIFIED, context, self.request)
        form_resubmit = translate(FORM_RESUBMIT, context, self.request)

        # escape_for_js
        form_modified = form_modified.replace("'", "\\'")
        form_resubmit = form_resubmit.replace("'", "\\'")

        return TEMPLATE % dict(
            portal_url=portal_url,
            open_links=open_links,
            mark_links=mark_links,
            form_modified=form_modified,
            form_resubmit=form_resubmit,
        )
