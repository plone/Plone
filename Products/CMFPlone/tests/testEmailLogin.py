from AccessControl import Unauthorized
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.tests import PloneTestCase
from Products.CMFPlone.utils import set_own_login_name


class TestEmailLogin(PloneTestCase.PloneTestCase):

    def afterSetUp(self):
        pass

    def testUseEmailProperty(self):
        props = getToolByName(self.portal, 'portal_properties').site_properties
        self.failUnless(props.hasProperty('use_email_as_login'))
        self.assertEqual(props.getProperty('use_email_as_login'), False)

    def testSetOwnLoginName(self):
        memship = self.portal.portal_membership
        users = self.portal.acl_users.source_users
        member = memship.getAuthenticatedMember()
        self.assertEqual(users.getLoginForUserId('test_user_1_'),
                         'test_user_1_')
        set_own_login_name(member, 'maurits')
        self.assertEqual(users.getLoginForUserId('test_user_1_'), 'maurits')

    def testSetLoginNameOfOther(self):
        memship = self.portal.portal_membership
        memship.addMember('maurits', 'secret', [], [])
        member = memship.getMemberById('maurits')
        self.assertRaises(Unauthorized, set_own_login_name, member, 'vanrees')
        # Not even the admin can change the login name of another user.
        self.loginAsPortalOwner()
        self.assertRaises(Unauthorized, set_own_login_name, member, 'vanrees')

    def testAdminSetOwnLoginName(self):
        memship = self.portal.portal_membership
        self.loginAsPortalOwner()
        member = memship.getAuthenticatedMember()
        # We are not allowed to change a user at the root zope level.
        self.assertRaises(KeyError, set_own_login_name, member, 'vanrees')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestEmailLogin))
    return suite
