from types import InstanceType

from Products.CMFCore.utils import getToolByName
from Products.MimetypesRegistry.mime_types.mtr_mimetypes import text_web_intelligent
from Products.PortalTransforms.transforms.web_intelligent_plain_text_to_html import register as intel2html_register
from Products.PortalTransforms.transforms.html_to_web_intelligent_plain_text import register as html2intel_register

from Products.CMFPlone.migrations import logger
from Products.CMFPlone.migrations.migration_util import loadMigrationProfile


def rc2_final(context):
    loadMigrationProfile(context, 'profile-Products.CMFPlone.migrations:3.0rc2-3.0final')


def addIntelligentText(context):
    """ add intelligenttext mime type and transforms that have been
    introduced in MimetypesRegistry and PortalTransforms 1.6 and that
    are never updated anywhere (#6684)
    """
    # Add mime type
    # See MimetypesRegistry/mime_types/mtr_mimetypes.py
    mt = text_web_intelligent
    if type(mt) != InstanceType:
        mt = mt()
    mtr = getToolByName(context, 'mimetypes_registry')
    mtr.register(mt)
    logger.info("Added text_web_intelligent mime type to registry")

    # Add transforms
    # See PortalTransforms/transforms/__init__.py
    engine = getToolByName(context, 'portal_transforms')
    engine.registerTransform(intel2html_register())
    logger.info("Added intelligenttext to html transform to registry")
    engine.registerTransform(html2intel_register())
    logger.info("Added html to intelligenttext transform to registry")
