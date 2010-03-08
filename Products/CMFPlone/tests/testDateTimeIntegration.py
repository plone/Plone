# tests for issues related to changes in `DateTime` 2.12
# please see tickets:
#
#   http://dev.plone.org/plone/ticket/10140
#   http://dev.plone.org/plone/ticket/10141
#   http://dev.plone.org/plone/ticket/10171
#
# for more information about this.  please also note that these tests
# may produce false positives when run in the GMT time zone!

from Products.CMFPlone.tests.PloneTestCase import PloneTestCase
from Products.CMFPlone.tests.PloneTestCase import FunctionalTestCase
from DateTime import DateTime


class DateTimeTests(PloneTestCase):

    def testModificationDate(self):
        obj = self.folder
        before = DateTime()
        obj.processForm(values=dict(Description='foo!'))
        after = DateTime()
        modified = obj.ModificationDate()   # the string representation...
        modified = DateTime(modified)       # is usually parsed again in Plone
        self.failUnless(int(before) <= int(modified) <= int(after),
            (before, modified, after))

    def testCreationDate(self):
        before = DateTime()
        obj = self.folder[self.folder.invokeFactory('Document', 'foo')]
        after = DateTime()
        creation = obj.CreationDate()       # the string representation...
        creation = DateTime(creation)       # is usually parsed again in Plone
        self.failUnless(int(before) <= int(creation) <= int(after),
            (before, creation, after))

    def testEffectiveDate(self):
        obj = self.folder
        date = DateTime() + 365             # expire one year from today
        date = DateTime(date.ISO8601())     # but strip off milliseconds
        obj.setEffectiveDate(date)
        obj.processForm(values=dict(Description='foo!'))
        effective = obj.EffectiveDate()     # the string representation...
        effective = DateTime(effective)     # is usually parsed again in Plone
        self.failUnless(date.equalTo(effective), (date, effective))

    def testExpirationDate(self):
        obj = self.folder
        date = DateTime() + 365             # expire one year from today
        date = DateTime(date.ISO8601())     # but strip off milliseconds
        obj.setExpirationDate(date)
        obj.processForm(values=dict(Description='foo!'))
        expired = obj.ExpirationDate()      # the string representation...
        expired = DateTime(expired)         # is usually parsed again in Plone
        self.failUnless(date.equalTo(expired), (date, expired))


class DateTimeTests(FunctionalTestCase):

    def testPublicationDateKeepsTimeZone(self):
        # see http://dev.plone.org/plone/ticket/10141
        localzone = DateTime._localzone0
        DateTime._localzone0 = 'GMT+3'
        self.setRoles(('Manager',))
        obj = self.portal['front-page']
        obj.setEffectiveDate('2020-02-20 16:00')
        browser = self.getBrowser()
        browser.open(obj.absolute_url())
        browser.getLink('Edit').click()
        browser.getControl('Save').click()
        self.assertEqual(obj.effective_date.ISO8601(),
                         '2020-02-20T16:00:00+03:00')
        DateTime._localzone0 = localzone

def test_suite():
    from unittest import defaultTestLoader
    return defaultTestLoader.loadTestsFromName(__name__)
