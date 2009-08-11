"""This module provides backwards compatiblity for products using the
SecureMailHost API.  It should be removed entirely for Plone 5.0."""
import sys
from copy import deepcopy
from email.Utils import formataddr
from email.Header import Header
from email.Message import Message
from email.MIMEText import MIMEText
from zope.deprecation import deprecate
from zope.deferredimport.deferredmodule import (ModuleProxy,
                                                DeferredAndDeprecated,)
from AccessControl.Permissions import use_mailhost_services
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.CMFPlone import PloneTool
from Products.MailHost.MailHost import MailHost


# The method we care about is now in PloneTool, we allow it to be imported from
# the original location which has been removed
fake_module = ModuleProxy(sys.modules[__name__])
deferred = fake_module.__deferred_definitions__
deferred['EMAIL_RE'] = DeferredAndDeprecated('EMAIL_RE',
                     'Products.CMFPlone.PloneTool:EMAIL_RE',
                     'EMAIL_RE has been moved from SecureMailHost, which is no '
                     'longer shipped with Plone.  It can be imported from '
                     'Products.CMFPlone.utils.EMAIL_RE')
deferred['EMAIL_CUTOFF_RE'] = DeferredAndDeprecated('EMAIL_CUTOFF_RE',
                     'Products.CMFPlone.PloneTool:EMAIL_CUTOFF_RE',
                     'EMAIL_CUTOFF_RE has been moved from SecureMailHost, '
                     'which is no longer shipped with Plone.  It can be '
                     'imported from Products.CMFPlone.utils.EMAIL_CUTOFF_RE')

def email_list_to_string(addr_list, charset='us-ascii'):
    """SecureMailHost's secureSend can take a list of email addresses
    in addition to a simple string.  We convert any email input into a
    properly encoded string."""
    header = Header()
    if addr_list is None:
        return
    if isinstance(addr_list, basestring):
        addr_str = addr_list
    else:
        # if the list item is a string include it, otherwise assume it's a
        # (name, address) tuple and turn it into an RFC compliant string

        addr_str = ', '.join(isinstance(a, basestring) and
                             a or formataddr(a) for a in addr_list)
    # split on word boundaries and encode piecewise, because making
    # the entire header encoded will result in SMTP errors
    for part in addr_str.split(' '):
        try:
            part.decode('ascii')
            header.append(part)
        except UnicodeDecodeError:
            header.append(part, charset)
    return str(header)

@deprecate('The MailHost secureSend method is deprecated, '
           'use send instead.  secureSend will be removed in Plone 5')
def secureSend(self, message, mto, mfrom, subject='[No Subject]',
               mcc=None, mbcc=None, subtype='plain', charset='us-ascii',
               debug=False, **kwargs):
    """Deprecated method attempting to maintain backwards
    compatibility for code depending on the SecureMailHost API."""
    # Convert all our address list inputs
    mfrom = email_list_to_string(mfrom, charset)
    mto = email_list_to_string(mto, charset)
    mcc = email_list_to_string(mcc, charset)
    mbcc = email_list_to_string(mbcc, charset)

    # Convert to a message for adding headers.  If it's already a
    # message, copy it to be safe.
    if not isinstance(message, Message):
        if isinstance(message, unicode):
            message.encode(charset)
        message = MIMEText(message, subtype, charset)
    else:
        message = deepcopy(message)

    # Add headers
    if mcc:
        message['CC'] = mcc
    if mbcc:
        message['BCC'] = mbcc
    for key, val in kwargs.iteritems():
        message[key] = val

    # Convert message back to string for sending
    self.send(str(message), mto, mfrom, subject, immediate=True)

ORIG_PERMS = MailHost.__ac_permissions__

msg = ('The %(name)s method of the MailHost is deprecated, '
       'it is now part of the PloneTool.  Use '
       'getToolByName(context, "plone_utils").%(name)s instead. '
       'this method will be removed in '
       'Plone 5.')

def applyPatches():
    if not hasattr(MailHost, 'secureSend'):
        pt = PloneTool.PloneTool
        MailHost.secureSend = secureSend
        MailHost.validateSingleNormalizedEmailAddress = deprecate(
            msg%{'name':'validateSingleNormalizedEmailAddress'})(
            pt.validateSingleNormalizedEmailAddress.im_func)
        MailHost.validateSingleEmailAddress = deprecate(
            msg%{'name':'validateSingleEmailAddress'})(
            pt.validateSingleEmailAddress.im_func)
        MailHost.validateEmailAddresses = deprecate(
            msg%{'name':'validateEmailAddresses'})(
            pt.validateEmailAddresses.im_func)
        MailHost.emailListToString = deprecate(
            'The MailHost method emailListToString is deprecated and '
            'will be removed in Plone 5')(classmethod(email_list_to_string))
        # set permissions
        MailHost.security = ClassSecurityInfo()
        MailHost.security.declareProtected(use_mailhost_services, 'secureSend')
        MailHost.security.declarePublic('validateSingleNormalizedEmailAddress',
                                        'validateSingleEmailAddress',
                                        'validateEmailAddresses',
                                        'emailListToString')
        # Merge old permissions with new permissions
        new_perms = dict(MailHost.__ac_permissions__)
        updated_perms = dict(ORIG_PERMS)
        for key, value in new_perms.iteritems():
            updated_perms[key] = updated_perms[key] + value
        MailHost.__ac_permissions__ = tuple(updated_perms.iteritems())
        # apply permisisons settings by reinitializing the class
        InitializeClass(MailHost)
    try:
        from Products.SecureMailHost.SecureMailHost import EMAIL_RE
    except ImportError:
        sys.modules['Products.SecureMailHost'] = fake_module
        sys.modules['Products.SecureMailHost.SecureMailHost'] = fake_module

def removePatches():
    smh = sys.modules.get('Products.SecureMailHost.SecureMailHost')
    if type(smh) is ModuleProxy:
        del sys.modules['Products.SecureMailHost']
        del sys.modules['Products.SecureMailHost.SecureMailHost']
    patched = getattr(MailHost, 'secureSend', None)
    if patched is not None and patched.im_func is secureSend:
        del MailHost.secureSend
        del MailHost.validateSingleNormalizedEmailAddress
        del MailHost.validateSingleEmailAddress
        del MailHost.validateEmailAddresses
        del MailHost.emailListToString
        del MailHost.secureSend__roles__
        del MailHost.validateSingleNormalizedEmailAddress__roles__
        del MailHost.validateSingleEmailAddress__roles__
        del MailHost.validateEmailAddresses__roles__
        del MailHost.emailListToString__roles__
        MailHost.__ac_permissions__ = ORIG_PERMS
