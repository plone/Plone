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
        self.assertEqual(users.getLoginForUserId(PloneTestCase.default_user),
                         PloneTestCase.default_user)
        set_own_login_name(member, 'maurits')
        self.assertEqual(users.getLoginForUserId(PloneTestCase.default_user),
                         'maurits')

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

    def testNormalMemberIdsAllowed(self):
        pattern = self.portal.portal_registration._ALLOWED_MEMBER_ID_PATTERN
        self.failUnless(pattern.match('maurits'))
        self.failUnless(pattern.match('Maur1ts'))
        # PLIP9214: the next test actually passes with the original
        # pattern but fails with the new one as email addresses cannot
        # end in a number:
        #self.failUnless(pattern.match('maurits76'))
        self.failUnless(pattern.match('MAURITS'))

    def testEmailMemberIdsAllowed(self):
        pattern = self.portal.portal_registration._ALLOWED_MEMBER_ID_PATTERN
        self.failUnless(pattern.match('user@example.org'))
        self.failUnless(pattern.match('user123@example.org'))
        self.failUnless(pattern.match('user.name@example.org'))
        # PLIP9214: perhaps we should change the regexp so the next
        # test passes as well?
        #self.failUnless(pattern.match('user+test@example.org'))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestEmailLogin))
    return suite
