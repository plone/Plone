import re

from Products.MailHost.MailHost import _encode
from Products.MailHost.MailHost import _mungeHeaders
from Products.MailHost.MailHost import MailBase

# regexp for a valid CSS identifier without the leading #
VALID_CSS_ID = re.compile("[A-Za-z_@][A-Za-z0-9_@-]*")


class MockMailHost(MailBase):
    """A MailHost that collects messages instead of sending them.
    """

    def __init__(self, id):
        self.reset()

    def reset(self):
        self.messages = []

    def send(self, messageText, mto=None, mfrom=None, subject=None,
             encode=None, immediate=False):
        messageText, mto, mfrom = _mungeHeaders(messageText,
                                                mto, mfrom, subject)
        messageText = _encode(messageText, encode)
        self.messages.append(messageText)


# a function to test if a string is a valid CSS identifier
def validateCSSIdentifier(identifier):
    match = VALID_CSS_ID.match(identifier)
    if not match is None:
        return match.end()== len(identifier)
    else:
        return False
