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


def test_suite():
    from unittest import defaultTestLoader
    return defaultTestLoader.loadTestsFromName(__name__)
