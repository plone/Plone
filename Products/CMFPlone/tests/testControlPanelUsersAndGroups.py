#
# Test the member and group control panel
#

from Products.Five.testbrowser import Browser
from Products.CMFPlone.tests import PloneTestCase
from Products.CMFCore.utils import getToolByName


class TestGroupsControlPanel(PloneTestCase.FunctionalTestCase):

    def afterSetUp(self):
        self.browser = Browser()
        self.setRoles(['Manager'])
        self.portal.portal_membership.memberareaCreationFlag = 0
        self.portal.portal_membership.addMember('bribri',
                                                'secret',
                                                ['Manager'], [])
        self.properties = getToolByName(self.portal, 'portal_properties')
        self.portal_path = self.portal.absolute_url(1)
        self.login('bribri')
        self.setupAuthenticator()

    def test_many_groups(self):
        '''
        by default, many_groups is disabled and so we show the list of
        groups when calling the groups control panel. If we set many_groups,
        we just display the search form.
        '''
        path = self.portal_path + '/prefs_groups_overview'
        basic_auth = '%s:%s' % ('bribri', 'secret')
        env = dict()
        response = self.publish(path, basic_auth, env,
                                handle_errors=True)
        # by default all groups are listed
        self.assertTrue('href="http://nohost/plone/prefs_group_members?groupname=Administrators'
                        in response.getBody())
        self.assertTrue('href="http://nohost/plone/prefs_group_members?groupname=Reviewers'
                        in response.getBody())
        self.assertTrue('name="form.button.FindAll"'
                         in response.getBody())
        
        # if we set 'many_groups', we don't do a listing, we have no
        # "Show all" button, but it has a search fields
        self.properties.site_properties.many_groups = True
        response = self.publish(path, basic_auth, env,
                                handle_errors=True)
        self.assertFalse('href="http://nohost/plone/prefs_group_members?groupname=Administrators'
                         in response.getBody())
        self.assertFalse('name="form.button.FindAll"'
                         in response.getBody())
        self.assertTrue('name="searchstring"'
                         in response.getBody())

    def test_add_and_search_group(self):
        '''
        We can add a group through the form. We can search for the new group
        by id and by fullname
        '''
        browser = self.browser

        # login and navigate to the groups control panel
        browser.open('http://nohost/plone/login_form')
        browser.getControl(name='__ac_name').value = 'bribri'
        browser.getControl(name='__ac_password').value = 'secret'
        browser.getControl('Log in').click()
        browser.getLink('Site Setup').click()
        browser.getLink('Users and Groups').click()
        browser.getLink(url='http://nohost/plone/prefs_groups_overview').click()

        # add group
        #browser.open('http://nohost/plone/prefs_groups_overview')
        browser.getControl(name='form.button.AddGroup').click()
        browser.getControl(name='addname').value = 'agroupname'
        browser.getControl(name='title:string').value = 'agrouptitle'
        browser.getControl(name='description:text').value = 'agroupdescription'
        browser.getControl(name='prefs_group_edit:method').click()
        self.assertTrue('agroupname' in self.browser.contents)

        # search for group by name and by title
        browser.getControl(name='searchstring').value = 'agroupname'
        browser.getForm(name='groups_search').getControl('Search').click()
        self.assertTrue('agroupname' in self.browser.contents)

        browser.getControl(name='searchstring').value = 'agrouptitle'
        browser.getForm(name='groups_search').getControl('Search').click()
        self.assertTrue('agroupname' in self.browser.contents)

    def test_add_and_search_user(self):
        '''
        We can add a group through the form. We can search for the new group
        by id and by fullname
        '''
        browser = self.browser

        # we allow to set the password on registration to make the test
        # simpler
        self.portal.validate_email = False


        # login and navigate to the users control panel
        browser.open('http://nohost/plone/login_form')
        browser.getControl(name='__ac_name').value = 'bribri'
        browser.getControl(name='__ac_password').value = 'secret'
        browser.getControl('Log in').click()
        browser.getLink('Site Setup').click()
        browser.getLink('Users and Groups').click()

        # add group
        browser.getControl(name='form.button.AddUser').click()
        browser.getControl(name='fullname').value = 'fullname'
        browser.getControl(name='username').value = 'username'
        browser.getControl(name='email').value = 'test@test.test'
        browser.getControl(name='password').value = 'password'
        browser.getControl(name='password_confirm').value = 'password'
        browser.getControl(name='form.button.Register').click()
        
        # search for group by name and by title
        browser.getControl(name='searchstring').value = 'username'
        browser.getForm(name='users_search').getControl('Search').click()
        self.assertTrue('prefs_user_details?userid=username' in self.browser.contents)

        browser.getControl(name='searchstring').value = 'fullname'
        browser.getForm(name='users_search').getControl('Search').click()
        self.assertTrue('prefs_user_details?userid=username' in self.browser.contents)

    
def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestGroupsControlPanel))
    return suite
