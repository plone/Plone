## Script (Python) "prefs_group_edit"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=addname=None, groupname=None
##title=Edit user
##

from Products.CMFPlone import PloneMessageFactory as _

REQUEST=context.REQUEST
msg = _(u'No changes made.')
group = None

if addname:
    success = context.portal_groups.addGroup(addname,(),(),REQUEST=context.REQUEST)
    if not success:
        msg = _(u'Could not add group ${name}, perhaps a user or group with '
                u'this name already exists.', mapping={u'name' : addname})
        context.plone_utils.addPortalMessage(msg, 'error')
        return context.prefs_group_details()
    group=context.portal_groups.getGroupById(addname)
    msg = _(u'Group ${name} has been added.',
            mapping={u'name' : addname})
elif groupname:
    group=context.portal_groups.getGroupById(groupname)
    msg = _(u'Changes saved.')

else:
    msg = _(u'Group name required.')

processed={}
for id, property in context.portal_groupdata.propertyItems():
    processed[id]=REQUEST.get(id, None)

if group:
    # for what reason ever, the very first group created does not exist
    group.setGroupProperties(processed)

context.plone_utils.addPortalMessage(msg, type=group and 'info' or 'error')

target_url = group and context.prefs_groups_overview.absolute_url() or \
                context.prefs_group_details.absolute_url()

return REQUEST.RESPONSE.redirect(target_url)
