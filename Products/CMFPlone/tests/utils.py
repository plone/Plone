from Products.SecureMailHost.SecureMailHost import SecureMailHost as Base
from persistent.list import PersistentList
import re

# regexp for a valid CSS identifier without the leading #
VALID_CSS_ID = re.compile("[A-Za-z_@][A-Za-z0-9_@-]*")

class MockMailHost(Base):
    """A MailHost that collects messages instead of sending them.

    Thanks to Rocky Burt for inspiration.
    """
    
    def __init__(self, id):
        Base.__init__(self, id, smtp_notls=True)
        self.reset()
    
    def reset(self):
        self.messages = PersistentList()

    def send(self, message, mto=None, mfrom=None, subject=None, encode=None):
        self.messages.append(message)

    def secureSend(self, message, mto, mfrom, **kwargs):
        kwargs['debug'] = True
        result = Base.secureSend(self, message=message, mto=mto, mfrom=mfrom, **kwargs)
        self.messages.append(result)

    def validateSingleEmailAddress(self, address):
        return True # why not


# a function to test if a string is a valid CSS identifier
def validateCSSIdentifier(identifier):
    match = VALID_CSS_ID.match(identifier)
    if not match is None:
        return match.end()== len(identifier)
    else:
        return False
