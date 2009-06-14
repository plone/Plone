# Plone 2.5 alphas

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.ActionInformation import Action
from Products.CMFCore.permissions import DeleteObjects
from Products.CMFPlone.UnicodeSplitter import Splitter, CaseNormalizer

from Products.CMFPlone.migrations import logger
from Products.CMFPlone.migrations.migration_util import loadMigrationProfile

def final_two51(context):
    """2.5-final -> 2.5.1
    """
    loadMigrationProfile(context, 'profile-Products.CMFPlone.migrations:2.5final-2.5.1')

    # Required for #5569 (is_folderish needs reindexing) and #5231 (all text
    # indices need to be reindexed so they are split properly)
    migtool = getToolByName(context, 'portal_migration')
    migtool._needRecatalog = True


def fixupPloneLexicon(context):
    """Updates the plone_lexicon pipeline with the new splitter
       and case normalizer.
    """
    catalog = getToolByName(context, 'portal_catalog', None)
    if catalog is not None:
        if 'plone_lexicon' in catalog.objectIds():
            lexicon = catalog.plone_lexicon
            pipeline = list(lexicon._pipeline)
            if len(pipeline) >= 2:
                if (not isinstance(pipeline[0], Splitter) or
                    not isinstance(pipeline[1], CaseNormalizer)):
                    pipeline[0] = Splitter()
                    pipeline[1] = CaseNormalizer()
                    lexicon._pipeline = tuple(pipeline)
                    # Clear the lexicon
                    from BTrees.OIBTree import OIBTree
                    from BTrees.IOBTree import IOBTree
                    from BTrees.Length import Length
                    lexicon._wids = OIBTree()
                    lexicon._words = IOBTree()
                    lexicon.length = Length()
                    logger.info('Updated plone_lexicon pipeline.')

def setLoginFormInCookieAuth(context):
    """Makes sure the cookie auth redirects to 'require_login' instead
       of 'login_form'."""
    uf = getattr(context, 'acl_users', None)
    if uf is None or getattr(uf.aq_base, '_getOb', None) is None:
        # we have no user folder or it's not a PAS folder, do nothing
        return
    cookie_auth = uf._getOb('credentials_cookie_auth', None)
    if cookie_auth is None:
        # there's no cookie auth object, do nothing
        return
    current_login_form = cookie_auth.getProperty('login_path')
    if current_login_form != 'login_form':
        # it's customized already, do nothing
        return
    cookie_auth.manage_changeProperties(login_path='require_login')
    logger.info("Changed credentials_cookie_path login_path property "
                "to 'require_login'.")

def addMissingMimeTypes(context):
    """ Add mime types that weren't included with the MimetypesRegistry that
        shipped with Plone 2.5.2 and are now required (#6695)
    """
    # manage_addMimeType handles existing types gracefully, so we can just go
    # ahead and add them without testing for existing ones
    mtr = getToolByName(context, 'mimetypes_registry', None)
    if mtr is not None:
        mtr.manage_addMimeType('text/x-web-markdown',
            ['text/x-web-markdown'], ['markdown'], 'text.png')
        mtr.manage_addMimeType('text/x-web-textile',
            ['text/x-web-textile'], ['textile'], 'text.png')
        logger.info("Added `text/x-web-markdown` and `text/x-web-textile`.")
